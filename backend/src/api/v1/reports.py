"""Report management API endpoints.

Provides report generation, submission, and management for school reports.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_REPORT_READ, PERM_REPORT_WRITE, PERM_REPORT_SUBMIT
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class Report(BaseModel):
    id: str
    title: str
    report_type: str  # sf1, sf2, sf3, sf4, sf5, sf6, rpms, etc.
    school_year: str
    quarter: Optional[int] = None
    status: str  # draft, submitted, approved, rejected
    created_by: str
    data: Dict[str, Any] = {}
    remarks: Optional[str] = None
    created_at: str
    updated_at: str


class ReportCreateRequest(BaseModel):
    title: str
    report_type: str
    school_year: str
    quarter: Optional[int] = Field(None, ge=1, le=4)
    data: Dict[str, Any] = {}


class ReportUpdateRequest(BaseModel):
    title: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    remarks: Optional[str] = None


class ReportListResponse(BaseModel):
    reports: List[Report]
    total: int
    page: int
    page_size: int


class SubmitResponse(BaseModel):
    id: str
    status: str = "submitted"
    detail: str


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_reports_db: Dict[str, Dict[str, Any]] = {}
_REPORT_TYPES = ["sf1", "sf2", "sf3", "sf4", "sf5", "sf6", "rpms", "custom"]


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


@router.get("", response_model=ReportListResponse)
def list_reports(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    school_year: Optional[str] = None,
):
    """List reports with pagination and filtering."""
    _require_permission(request, PERM_REPORT_READ)

    reports = list(_reports_db.values())

    if report_type:
        reports = [r for r in reports if r["report_type"] == report_type]
    if status:
        reports = [r for r in reports if r["status"] == status]
    if school_year:
        reports = [r for r in reports if r["school_year"] == school_year]

    total = len(reports)
    start = (page - 1) * page_size
    end = start + page_size
    page_reports = reports[start:end]

    return ReportListResponse(
        reports=[
            Report(
                id=r["id"],
                title=r["title"],
                report_type=r["report_type"],
                school_year=r["school_year"],
                quarter=r.get("quarter"),
                status=r["status"],
                created_by=r["created_by"],
                data=r.get("data", {}),
                remarks=r.get("remarks"),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in page_reports
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/types")
def list_report_types():
    """List available report types."""
    return {"report_types": _REPORT_TYPES}


@router.get("/{report_id}", response_model=Report)
def get_report(report_id: str, request: Request):
    """Get a specific report."""
    _require_permission(request, PERM_REPORT_READ)

    report = _reports_db.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return Report(
        id=report["id"],
        title=report["title"],
        report_type=report["report_type"],
        school_year=report["school_year"],
        quarter=report.get("quarter"),
        status=report["status"],
        created_by=report["created_by"],
        data=report.get("data", {}),
        remarks=report.get("remarks"),
        created_at=report["created_at"],
        updated_at=report["updated_at"],
    )


@router.post("", response_model=Report, status_code=201)
def create_report(req: ReportCreateRequest, request: Request):
    """Create a new report."""
    user_id = _require_permission(request, PERM_REPORT_WRITE)

    report_id = str(uuid4())
    now = str(datetime.utcnow())

    _reports_db[report_id] = {
        "id": report_id,
        "title": req.title,
        "report_type": req.report_type,
        "school_year": req.school_year,
        "quarter": req.quarter,
        "status": "draft",
        "created_by": user_id,
        "data": req.data,
        "remarks": None,
        "created_at": now,
        "updated_at": now,
    }

    return get_report(report_id, request)


@router.put("/{report_id}", response_model=Report)
def update_report(report_id: str, req: ReportUpdateRequest, request: Request):
    """Update a report."""
    _require_permission(request, PERM_REPORT_WRITE)

    report = _reports_db.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if req.title is not None:
        report["title"] = req.title
    if req.data is not None:
        report["data"] = req.data
    if req.remarks is not None:
        report["remarks"] = req.remarks

    report["updated_at"] = str(datetime.utcnow())

    return get_report(report_id, request)


@router.post("/{report_id}/submit", response_model=SubmitResponse)
def submit_report(report_id: str, request: Request):
    """Submit a report for approval."""
    _require_permission(request, PERM_REPORT_SUBMIT)

    report = _reports_db.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report["status"] == "submitted":
        raise HTTPException(status_code=409, detail="Report already submitted")

    report["status"] = "submitted"
    report["updated_at"] = str(datetime.utcnow())

    return SubmitResponse(id=report_id, status="submitted", detail="Report submitted for approval")


@router.post("/{report_id}/approve", response_model=SubmitResponse)
def approve_report(report_id: str, request: Request):
    """Approve a submitted report."""
    _require_permission(request, PERM_REPORT_SUBMIT)

    report = _reports_db.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report["status"] != "submitted":
        raise HTTPException(status_code=409, detail="Report must be in submitted status")

    report["status"] = "approved"
    report["updated_at"] = str(datetime.utcnow())

    return SubmitResponse(id=report_id, status="approved", detail="Report approved")


@router.post("/{report_id}/reject", response_model=SubmitResponse)
def reject_report(report_id: str, request: Request, remarks: str = "Rejected"):
    """Reject a submitted report."""
    _require_permission(request, PERM_REPORT_SUBMIT)

    report = _reports_db.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report["status"] = "rejected"
    report["remarks"] = remarks
    report["updated_at"] = str(datetime.utcnow())

    return SubmitResponse(id=report_id, status="rejected", detail="Report rejected")


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: str, request: Request):
    """Delete a report."""
    _require_permission(request, PERM_REPORT_WRITE)

    if report_id not in _reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    del _reports_db[report_id]
