"""Grade management API endpoints.

Provides CRUD operations for grades, grade computation,
and grade book management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_GRADE_READ, PERM_GRADE_WRITE, PERM_GRADE_COMPUTE
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/grades", tags=["Grades"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class GradeEntry(BaseModel):
    id: str
    student_id: str
    subject: str
    quarter: int = Field(ge=1, le=4)
    score: float = Field(ge=0)
    max_score: float = Field(ge=1)
    weight: Optional[float] = Field(None, ge=0, le=1)
    remarks: Optional[str] = None
    graded_by: str
    school_year: str


class GradeCreateRequest(BaseModel):
    student_id: str
    subject: str
    quarter: int = Field(ge=1, le=4)
    score: float = Field(ge=0)
    max_score: float = Field(ge=1, default=100)
    weight: Optional[float] = Field(None, ge=0, le=1)
    remarks: Optional[str] = None
    school_year: str


class GradeUpdateRequest(BaseModel):
    score: Optional[float] = Field(None, ge=0)
    max_score: Optional[float] = Field(None, ge=1)
    weight: Optional[float] = Field(None, ge=0, le=1)
    remarks: Optional[str] = None


class GradeListResponse(BaseModel):
    grades: List[GradeEntry]
    total: int
    page: int
    page_size: int


class FinalGrade(BaseModel):
    student_id: str
    subject: str
    final_grade: float
    quarter: int
    school_year: str
    passed: bool


class ComputeRequest(BaseModel):
    student_id: str
    subject: str
    quarter: int = Field(ge=1, le=4)
    school_year: str


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_grades_db: Dict[str, Dict[str, Any]] = {}


def _require_permission(request: Request, permission: str) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        request.app.state.rbac_service.require_permission(user_id, permission)
    except InsufficientPermissionsError:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user_id


def _get_grade_or_404(grade_id: str) -> Dict[str, Any]:
    grade = _grades_db.get(grade_id)
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=GradeListResponse)
def list_grades(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[str] = None,
    subject: Optional[str] = None,
    quarter: Optional[int] = None,
    school_year: Optional[str] = None,
):
    """List grades with pagination and filtering."""
    _require_permission(request, PERM_GRADE_READ)

    grades_list = list(_grades_db.values())

    if student_id:
        grades_list = [g for g in grades_list if g["student_id"] == student_id]
    if subject:
        grades_list = [g for g in grades_list if g["subject"] == subject]
    if quarter:
        grades_list = [g for g in grades_list if g["quarter"] == quarter]
    if school_year:
        grades_list = [g for g in grades_list if g["school_year"] == school_year]

    total = len(grades_list)
    start = (page - 1) * page_size
    end = start + page_size
    page_grades = grades_list[start:end]

    return GradeListResponse(
        grades=[
            GradeEntry(
                id=g["id"],
                student_id=g["student_id"],
                subject=g["subject"],
                quarter=g["quarter"],
                score=g["score"],
                max_score=g["max_score"],
                weight=g.get("weight"),
                remarks=g.get("remarks"),
                graded_by=g["graded_by"],
                school_year=g["school_year"],
            )
            for g in page_grades
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{grade_id}", response_model=GradeEntry)
def get_grade(grade_id: str, request: Request):
    """Get a specific grade entry."""
    _require_permission(request, PERM_GRADE_READ)
    grade = _get_grade_or_404(grade_id)

    return GradeEntry(
        id=grade["id"],
        student_id=grade["student_id"],
        subject=grade["subject"],
        quarter=grade["quarter"],
        score=grade["score"],
        max_score=grade["max_score"],
        weight=grade.get("weight"),
        remarks=grade.get("remarks"),
        graded_by=grade["graded_by"],
        school_year=grade["school_year"],
    )


@router.post("", response_model=GradeEntry, status_code=201)
def create_grade(req: GradeCreateRequest, request: Request):
    """Create a new grade entry."""
    user_id = _require_permission(request, PERM_GRADE_WRITE)

    grade_id = str(uuid4())
    _grades_db[grade_id] = {
        "id": grade_id,
        "student_id": req.student_id,
        "subject": req.subject,
        "quarter": req.quarter,
        "score": req.score,
        "max_score": req.max_score,
        "weight": req.weight,
        "remarks": req.remarks,
        "graded_by": user_id,
        "school_year": req.school_year,
    }

    return get_grade(grade_id, request)


@router.put("/{grade_id}", response_model=GradeEntry)
def update_grade(grade_id: str, req: GradeUpdateRequest, request: Request):
    """Update a grade entry."""
    _require_permission(request, PERM_GRADE_WRITE)
    grade = _get_grade_or_404(grade_id)

    if req.score is not None:
        grade["score"] = req.score
    if req.max_score is not None:
        grade["max_score"] = req.max_score
    if req.weight is not None:
        grade["weight"] = req.weight
    if req.remarks is not None:
        grade["remarks"] = req.remarks

    return get_grade(grade_id, request)


@router.delete("/{grade_id}", status_code=204)
def delete_grade(grade_id: str, request: Request):
    """Delete a grade entry."""
    _require_permission(request, PERM_GRADE_WRITE)
    _get_grade_or_404(grade_id)
    del _grades_db[grade_id]


@router.post("/compute", response_model=FinalGrade)
def compute_grade(req: ComputeRequest, request: Request):
    """Compute the final grade for a student/subject/quarter."""
    _require_permission(request, PERM_GRADE_COMPUTE)

    # Fetch all grades for this student/subject/quarter/school_year
    relevant = [
        g for g in _grades_db.values()
        if g["student_id"] == req.student_id
        and g["subject"] == req.subject
        and g["quarter"] == req.quarter
        and g["school_year"] == req.school_year
    ]

    if not relevant:
        raise HTTPException(status_code=404, detail="No grade entries found for computation")

    # Compute weighted average
    total_weighted = 0.0
    total_weight = 0.0

    for g in relevant:
        percentage = (g["score"] / g["max_score"]) * 100
        w = g.get("weight", 1.0 / len(relevant))
        total_weighted += percentage * w
        total_weight += w

    final_grade = round(total_weighted / total_weight, 2) if total_weight > 0 else 0.0

    return FinalGrade(
        student_id=req.student_id,
        subject=req.subject,
        final_grade=final_grade,
        quarter=req.quarter,
        school_year=req.school_year,
        passed=final_grade >= 75.0,
    )