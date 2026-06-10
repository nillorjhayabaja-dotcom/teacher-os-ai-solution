"""Student management API endpoints.

Provides CRUD operations for student records with tenant isolation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_STUDENT_READ, PERM_STUDENT_WRITE, PERM_STUDENT_DELETE
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/students", tags=["Students"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class StudentProfile(BaseModel):
    id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[str] = None
    student_id: str  # LRN (Learner Reference Number)
    grade_level: str
    section: Optional[str] = None
    school_id: Optional[str] = None
    organization_id: Optional[str] = None
    is_active: bool = True
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    address: Optional[str] = None


class StudentCreateRequest(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[str] = None
    student_id: str = Field(..., description="LRN - Learner Reference Number")
    grade_level: str
    section: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    address: Optional[str] = None


class StudentUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[str] = None
    grade_level: Optional[str] = None
    section: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class StudentListResponse(BaseModel):
    students: List[StudentProfile]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_students_db: Dict[str, Dict[str, Any]] = {}


def _require_permission(request: Request, permission: str) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        request.app.state.rbac_service.require_permission(user_id, permission)
    except InsufficientPermissionsError:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user_id


def _get_student_or_404(student_id: str) -> Dict[str, Any]:
    student = _students_db.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=StudentListResponse)
def list_students(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    grade_level: Optional[str] = None,
    section: Optional[str] = None,
    search: Optional[str] = None,
):
    """List students with pagination and filtering."""
    _require_permission(request, PERM_STUDENT_READ)

    students_list = list(_students_db.values())

    # Tenant isolation
    tenant_id = getattr(request.state, "user_tenant_id", None)
    if tenant_id:
        students_list = [s for s in students_list if s.get("organization_id") == tenant_id]

    if grade_level:
        students_list = [s for s in students_list if s["grade_level"] == grade_level]
    if section:
        students_list = [s for s in students_list if s.get("section") == section]
    if search:
        search_lower = search.lower()
        students_list = [
            s for s in students_list
            if search_lower in s["first_name"].lower()
            or search_lower in s["last_name"].lower()
            or search_lower in s.get("student_id", "").lower()
        ]

    total = len(students_list)
    start = (page - 1) * page_size
    end = start + page_size
    page_students = students_list[start:end]

    return StudentListResponse(
        students=[
            StudentProfile(
                id=s["id"],
                first_name=s["first_name"],
                last_name=s["last_name"],
                middle_name=s.get("middle_name"),
                email=s.get("email"),
                student_id=s["student_id"],
                grade_level=s["grade_level"],
                section=s.get("section"),
                school_id=s.get("school_id"),
                organization_id=s.get("organization_id"),
                is_active=s.get("is_active", True),
                guardian_name=s.get("guardian_name"),
                guardian_contact=s.get("guardian_contact"),
                address=s.get("address"),
            )
            for s in page_students
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{student_id}", response_model=StudentProfile)
def get_student(student_id: str, request: Request):
    """Get a specific student's details."""
    _require_permission(request, PERM_STUDENT_READ)
    student = _get_student_or_404(student_id)

    return StudentProfile(
        id=student["id"],
        first_name=student["first_name"],
        last_name=student["last_name"],
        middle_name=student.get("middle_name"),
        email=student.get("email"),
        student_id=student["student_id"],
        grade_level=student["grade_level"],
        section=student.get("section"),
        school_id=student.get("school_id"),
        organization_id=student.get("organization_id"),
        is_active=student.get("is_active", True),
        guardian_name=student.get("guardian_name"),
        guardian_contact=student.get("guardian_contact"),
        address=student.get("address"),
    )


@router.post("", response_model=StudentProfile, status_code=201)
def create_student(req: StudentCreateRequest, request: Request):
    """Create a new student record."""
    _require_permission(request, PERM_STUDENT_WRITE)

    # Check for duplicate LRN
    for s in _students_db.values():
        if s["student_id"] == req.student_id:
            raise HTTPException(status_code=409, detail="Student with this LRN already exists")

    student_id = str(uuid4())
    tenant_id = getattr(request.state, "user_tenant_id", None)
    org_id = getattr(request.state, "user_organization_id", None)
    school_id = getattr(request.state, "user_school_id", None)

    _students_db[student_id] = {
        "id": student_id,
        "first_name": req.first_name,
        "last_name": req.last_name,
        "middle_name": req.middle_name,
        "email": req.email,
        "student_id": req.student_id,
        "grade_level": req.grade_level,
        "section": req.section,
        "organization_id": org_id or tenant_id,
        "school_id": school_id,
        "is_active": True,
        "guardian_name": req.guardian_name,
        "guardian_contact": req.guardian_contact,
        "address": req.address,
    }

    return get_student(student_id, request)


@router.put("/{student_id}", response_model=StudentProfile)
def update_student(student_id: str, req: StudentUpdateRequest, request: Request):
    """Update a student record."""
    _require_permission(request, PERM_STUDENT_WRITE)
    student = _get_student_or_404(student_id)

    if req.first_name is not None:
        student["first_name"] = req.first_name
    if req.last_name is not None:
        student["last_name"] = req.last_name
    if req.middle_name is not None:
        student["middle_name"] = req.middle_name
    if req.email is not None:
        student["email"] = req.email
    if req.grade_level is not None:
        student["grade_level"] = req.grade_level
    if req.section is not None:
        student["section"] = req.section
    if req.guardian_name is not None:
        student["guardian_name"] = req.guardian_name
    if req.guardian_contact is not None:
        student["guardian_contact"] = req.guardian_contact
    if req.address is not None:
        student["address"] = req.address
    if req.is_active is not None:
        student["is_active"] = req.is_active

    return get_student(student_id, request)


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: str, request: Request):
    """Soft-delete a student record."""
    _require_permission(request, PERM_STUDENT_DELETE)
    student = _get_student_or_404(student_id)
    student["is_active"] = False