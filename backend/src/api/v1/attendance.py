"""Attendance management API endpoints.

Provides attendance tracking, reporting, and analytics.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_ATTENDANCE_READ, PERM_ATTENDANCE_WRITE
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/attendance", tags=["Attendance"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AttendanceRecord(BaseModel):
    id: str
    student_id: str
    date: str
    status: str  # present, absent, late, excused
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    remarks: Optional[str] = None
    recorded_by: str


class AttendanceCreateRequest(BaseModel):
    student_id: str
    date: str
    status: str = Field(..., pattern="^(present|absent|late|excused)$")
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(present|absent|late|excused)$")
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    remarks: Optional[str] = None


class AttendanceListResponse(BaseModel):
    records: List[AttendanceRecord]
    total: int
    page: int
    page_size: int


class AttendanceBulkCreateRequest(BaseModel):
    records: List[AttendanceCreateRequest]


class AttendanceSummary(BaseModel):
    student_id: str
    total_days: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_rate: float


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_attendance_db: Dict[str, Dict[str, Any]] = {}


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


@router.get("", response_model=AttendanceListResponse)
def list_attendance(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
):
    """List attendance records with pagination and filtering."""
    _require_permission(request, PERM_ATTENDANCE_READ)

    records = list(_attendance_db.values())

    if student_id:
        records = [r for r in records if r["student_id"] == student_id]
    if status:
        records = [r for r in records if r["status"] == status]
    if date_from:
        records = [r for r in records if r["date"] >= date_from]
    if date_to:
        records = [r for r in records if r["date"] <= date_to]

    total = len(records)
    start = (page - 1) * page_size
    end = start + page_size
    page_records = records[start:end]

    return AttendanceListResponse(
        records=[
            AttendanceRecord(
                id=r["id"],
                student_id=r["student_id"],
                date=r["date"],
                status=r["status"],
                time_in=r.get("time_in"),
                time_out=r.get("time_out"),
                remarks=r.get("remarks"),
                recorded_by=r["recorded_by"],
            )
            for r in page_records
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=AttendanceRecord, status_code=201)
def create_attendance(req: AttendanceCreateRequest, request: Request):
    """Create a single attendance record."""
    user_id = _require_permission(request, PERM_ATTENDANCE_WRITE)

    record_id = str(uuid4())
    _attendance_db[record_id] = {
        "id": record_id,
        "student_id": req.student_id,
        "date": req.date,
        "status": req.status,
        "time_in": req.time_in,
        "time_out": req.time_out,
        "remarks": req.remarks,
        "recorded_by": user_id,
    }

    return AttendanceRecord(
        id=record_id,
        student_id=req.student_id,
        date=req.date,
        status=req.status,
        time_in=req.time_in,
        time_out=req.time_out,
        remarks=req.remarks,
        recorded_by=user_id,
    )


@router.post("/bulk", response_model=List[AttendanceRecord], status_code=201)
def bulk_create_attendance(req: AttendanceBulkCreateRequest, request: Request):
    """Create multiple attendance records at once."""
    user_id = _require_permission(request, PERM_ATTENDANCE_WRITE)
    results = []

    for record_req in req.records:
        record_id = str(uuid4())
        _attendance_db[record_id] = {
            "id": record_id,
            "student_id": record_req.student_id,
            "date": record_req.date,
            "status": record_req.status,
            "time_in": record_req.time_in,
            "time_out": record_req.time_out,
            "remarks": record_req.remarks,
            "recorded_by": user_id,
        }
        results.append(AttendanceRecord(
            id=record_id,
            student_id=record_req.student_id,
            date=record_req.date,
            status=record_req.status,
            time_in=record_req.time_in,
            time_out=record_req.time_out,
            remarks=record_req.remarks,
            recorded_by=user_id,
        ))

    return results


@router.get("/summary/{student_id}", response_model=AttendanceSummary)
def get_attendance_summary(student_id: str, request: Request, school_year: Optional[str] = None):
    """Get attendance summary for a student."""
    _require_permission(request, PERM_ATTENDANCE_READ)

    records = [r for r in _attendance_db.values() if r["student_id"] == student_id]

    total = len(records)
    present = sum(1 for r in records if r["status"] == "present")
    absent = sum(1 for r in records if r["status"] == "absent")
    late = sum(1 for r in records if r["status"] == "late")
    excused = sum(1 for r in records if r["status"] == "excused")
    rate = round((present / total * 100), 2) if total > 0 else 0.0

    return AttendanceSummary(
        student_id=student_id,
        total_days=total,
        present=present,
        absent=absent,
        late=late,
        excused=excused,
        attendance_rate=rate,
    )


@router.put("/{record_id}", response_model=AttendanceRecord)
def update_attendance(record_id: str, req: AttendanceUpdateRequest, request: Request):
    """Update an attendance record."""
    _require_permission(request, PERM_ATTENDANCE_WRITE)

    if record_id not in _attendance_db:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    record = _attendance_db[record_id]
    if req.status is not None:
        record["status"] = req.status
    if req.time_in is not None:
        record["time_in"] = req.time_in
    if req.time_out is not None:
        record["time_out"] = req.time_out
    if req.remarks is not None:
        record["remarks"] = req.remarks

    return AttendanceRecord(
        id=record["id"],
        student_id=record["student_id"],
        date=record["date"],
        status=record["status"],
        time_in=record.get("time_in"),
        time_out=record.get("time_out"),
        remarks=record.get("remarks"),
        recorded_by=record["recorded_by"],
    )


@router.delete("/{record_id}", status_code=204)
def delete_attendance(record_id: str, request: Request):
    """Delete an attendance record."""
    _require_permission(request, PERM_ATTENDANCE_WRITE)

    if record_id not in _attendance_db:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    del _attendance_db[record_id]