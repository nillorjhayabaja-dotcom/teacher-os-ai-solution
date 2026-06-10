"""Class/Section management API endpoints.

Provides endpoints for managing classes, sections, teacher assignments,
and student enrollments.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_STUDENT_READ, PERM_STUDENT_WRITE
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/classes", tags=["Classes"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ClassInfo(BaseModel):
    id: str
    name: str
    grade_level: str
    section: str
    subject: str
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    school_year: str
    room: Optional[str] = None
    schedule: Optional[str] = None
    student_count: int = 0


class ClassCreateRequest(BaseModel):
    name: str
    grade_level: str
    section: str
    subject: str
    teacher_id: Optional[str] = None
    school_year: str
    room: Optional[str] = None
    schedule: Optional[str] = None


class ClassUpdateRequest(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[str] = None
    section: Optional[str] = None
    subject: Optional[str] = None
    teacher_id: Optional[str] = None
    room: Optional[str] = None
    schedule: Optional[str] = None


class ClassListResponse(BaseModel):
    classes: List[ClassInfo]
    total: int
    page: int
    page_size: int


class Enrollment(BaseModel):
    id: str
    class_id: str
    student_id: str
    student_name: str
    enrolled_at: str
    status: str = "active"  # active, dropped, completed


class EnrollmentRequest(BaseModel):
    student_ids: List[str]


# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_classes_db: Dict[str, Dict[str, Any]] = {}
_enrollments_db: Dict[str, Dict[str, Any]] = {}
# Reference students DB for student names
from backend.src.api.v1.students import _students_db  # noqa: F401


def _require_permission(request: Request, permission: str) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        request.app.state.rbac_service.require_permission(user_id, permission)
    except InsufficientPermissionsError:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ClassListResponse)
def list_classes(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    grade_level: Optional[str] = None,
    section: Optional[str] = None,
    subject: Optional[str] = None,
    school_year: Optional[str] = None,
    teacher_id: Optional[str] = None,
):
    """List classes with pagination and filtering."""
    _require_permission(request, PERM_STUDENT_READ)

    classes = list(_classes_db.values())

    if grade_level:
        classes = [c for c in classes if c["grade_level"] == grade_level]
    if section:
        classes = [c for c in classes if c["section"] == section]
    if subject:
        classes = [c for c in classes if c["subject"] == subject]
    if school_year:
        classes = [c for c in classes if c["school_year"] == school_year]
    if teacher_id:
        classes = [c for c in classes if c.get("teacher_id") == teacher_id]

    # Compute student counts
    for c in classes:
        c["student_count"] = sum(
            1 for e in _enrollments_db.values()
            if e["class_id"] == c["id"] and e["status"] == "active"
        )

    total = len(classes)
    start = (page - 1) * page_size
    end = start + page_size
    page_classes = classes[start:end]

    return ClassListResponse(
        classes=[
            ClassInfo(
                id=c["id"],
                name=c["name"],
                grade_level=c["grade_level"],
                section=c["section"],
                subject=c["subject"],
                teacher_id=c.get("teacher_id"),
                teacher_name=c.get("teacher_name"),
                school_year=c["school_year"],
                room=c.get("room"),
                schedule=c.get("schedule"),
                student_count=c.get("student_count", 0),
            )
            for c in page_classes
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{class_id}", response_model=ClassInfo)
def get_class(class_id: str, request: Request):
    """Get a specific class details."""
    _require_permission(request, PERM_STUDENT_READ)

    cls = _classes_db.get(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    student_count = sum(
        1 for e in _enrollments_db.values()
        if e["class_id"] == class_id and e["status"] == "active"
    )

    return ClassInfo(
        id=cls["id"],
        name=cls["name"],
        grade_level=cls["grade_level"],
        section=cls["section"],
        subject=cls["subject"],
        teacher_id=cls.get("teacher_id"),
        teacher_name=cls.get("teacher_name"),
        school_year=cls["school_year"],
        room=cls.get("room"),
        schedule=cls.get("schedule"),
        student_count=student_count,
    )


@router.post("", response_model=ClassInfo, status_code=201)
def create_class(req: ClassCreateRequest, request: Request):
    """Create a new class/section."""
    _require_permission(request, PERM_STUDENT_WRITE)

    class_id = str(uuid4())

    # Resolve teacher name if teacher_id provided
    teacher_name = None
    if req.teacher_id:
        try:
            from backend.src.api.v1.auth import _get_user_or_404
            teacher = _get_user_or_404(req.teacher_id)
            teacher_name = f"{teacher['first_name']} {teacher['last_name']}"
        except HTTPException:
            pass

    _classes_db[class_id] = {
        "id": class_id,
        "name": req.name,
        "grade_level": req.grade_level,
        "section": req.section,
        "subject": req.subject,
        "teacher_id": req.teacher_id,
        "teacher_name": teacher_name,
        "school_year": req.school_year,
        "room": req.room,
        "schedule": req.schedule,
    }

    return get_class(class_id, request)


@router.put("/{class_id}", response_model=ClassInfo)
def update_class(class_id: str, req: ClassUpdateRequest, request: Request):
    """Update a class."""
    _require_permission(request, PERM_STUDENT_WRITE)

    cls = _classes_db.get(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    if req.name is not None:
        cls["name"] = req.name
    if req.grade_level is not None:
        cls["grade_level"] = req.grade_level
    if req.section is not None:
        cls["section"] = req.section
    if req.subject is not None:
        cls["subject"] = req.subject
    if req.teacher_id is not None:
        cls["teacher_id"] = req.teacher_id
        try:
            from backend.src.api.v1.auth import _get_user_or_404
            teacher = _get_user_or_404(req.teacher_id)
            cls["teacher_name"] = f"{teacher['first_name']} {teacher['last_name']}"
        except HTTPException:
            cls["teacher_name"] = None
    if req.room is not None:
        cls["room"] = req.room
    if req.schedule is not None:
        cls["schedule"] = req.schedule

    return get_class(class_id, request)


@router.delete("/{class_id}", status_code=204)
def delete_class(class_id: str, request: Request):
    """Delete a class."""
    _require_permission(request, PERM_STUDENT_WRITE)

    if class_id not in _classes_db:
        raise HTTPException(status_code=404, detail="Class not found")
    del _classes_db[class_id]


# ---------------------------------------------------------------------------
# Enrollment endpoints
# ---------------------------------------------------------------------------


@router.get("/{class_id}/enrollments", response_model=List[Enrollment])
def list_enrollments(class_id: str, request: Request):
    """List all enrollments for a class."""
    _require_permission(request, PERM_STUDENT_READ)

    if class_id not in _classes_db:
        raise HTTPException(status_code=404, detail="Class not found")

    enrollments = [
        e for e in _enrollments_db.values()
        if e["class_id"] == class_id
    ]

    return [
        Enrollment(
            id=e["id"],
            class_id=e["class_id"],
            student_id=e["student_id"],
            student_name=e.get("student_name", ""),
            enrolled_at=e["enrolled_at"],
            status=e.get("status", "active"),
        )
        for e in enrollments
    ]


@router.post("/{class_id}/enrollments", response_model=List[Enrollment], status_code=201)
def enroll_students(class_id: str, req: EnrollmentRequest, request: Request):
    """Enroll students into a class."""
    _require_permission(request, PERM_STUDENT_WRITE)

    if class_id not in _classes_db:
        raise HTTPException(status_code=404, detail="Class not found")

    results = []
    now = str(datetime.utcnow())

    for student_id in req.student_ids:
        # Check if already enrolled
        already = [
            e for e in _enrollments_db.values()
            if e["class_id"] == class_id and e["student_id"] == student_id and e["status"] == "active"
        ]
        if already:
            continue

        # Get student name
        student_name = ""
        student = _students_db.get(student_id)
        if student:
            student_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()

        enrollment_id = str(uuid4())
        _enrollments_db[enrollment_id] = {
            "id": enrollment_id,
            "class_id": class_id,
            "student_id": student_id,
            "student_name": student_name,
            "enrolled_at": now,
            "status": "active",
        }
        results.append(Enrollment(
            id=enrollment_id,
            class_id=class_id,
            student_id=student_id,
            student_name=student_name,
            enrolled_at=now,
            status="active",
        ))

    return results


@router.delete("/{class_id}/enrollments/{student_id}", status_code=204)
def unenroll_student(class_id: str, student_id: str, request: Request):
    """Remove a student from a class."""
    _require_permission(request, PERM_STUDENT_WRITE)

    for eid, e in list(_enrollments_db.items()):
        if e["class_id"] == class_id and e["student_id"] == student_id:
            e["status"] = "dropped"
            return

    raise HTTPException(status_code=404, detail="Enrollment not found")
