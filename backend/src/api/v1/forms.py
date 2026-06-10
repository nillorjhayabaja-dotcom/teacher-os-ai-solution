"""School forms management API endpoints.

Provides endpoints for generating and managing school forms
(SF1, SF2, SF3, SF4, SF5, SF6, etc.).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.src.core.constants import PERM_FORM_READ, PERM_FORM_WRITE, PERM_FORM_GENERATE
from backend.src.core.exceptions import InsufficientPermissionsError

router = APIRouter(prefix="/api/v1/forms", tags=["Forms"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FormSchema(BaseModel):
    id: str
    name: str
    form_type: str  # sf1, sf2, sf3, sf4, sf5, sf6, custom
    version: str = "1.0"
    description: Optional[str] = None
    fields: List[Dict[str, Any]] = []
    is_active: bool = True


class FormCreateRequest(BaseModel):
    name: str
    form_type: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]] = []


class FormUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class FormListResponse(BaseModel):
    forms: List[FormSchema]
    total: int
    page: int
    page_size: int


class FormInstance(BaseModel):
    id: str
    form_type: str
    student_id: Optional[str] = None
    school_year: str
    quarter: Optional[int] = None
    data: Dict[str, Any] = {}
    status: str = "draft"  # draft, completed, submitted
    created_by: str
    created_at: str
    updated_at: str


class FormGenerateRequest(BaseModel):
    form_type: str
    student_ids: List[str]
    school_year: str
    quarter: Optional[int] = None
    template_data: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_forms_db: Dict[str, Dict[str, Any]] = {}
_form_instances_db: Dict[str, Dict[str, Any]] = {}
_FORM_TYPES = ["sf1", "sf2", "sf3", "sf4", "sf5", "sf6", "custom"]


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


@router.get("/templates", response_model=FormListResponse)
def list_form_templates(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    form_type: Optional[str] = None,
):
    """List available form templates."""
    _require_permission(request, PERM_FORM_READ)

    forms = list(_forms_db.values())
    if form_type:
        forms = [f for f in forms if f["form_type"] == form_type]

    total = len(forms)
    start = (page - 1) * page_size
    end = start + page_size
    page_forms = forms[start:end]

    return FormListResponse(
        forms=[
            FormSchema(
                id=f["id"],
                name=f["name"],
                form_type=f["form_type"],
                version=f.get("version", "1.0"),
                description=f.get("description"),
                fields=f.get("fields", []),
                is_active=f.get("is_active", True),
            )
            for f in page_forms
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/templates/types")
def list_form_types():
    """List available form types."""
    return {"form_types": _FORM_TYPES}


@router.get("/templates/{form_id}", response_model=FormSchema)
def get_form_template(form_id: str, request: Request):
    """Get a form template details."""
    _require_permission(request, PERM_FORM_READ)

    form = _forms_db.get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form template not found")

    return FormSchema(
        id=form["id"],
        name=form["name"],
        form_type=form["form_type"],
        version=form.get("version", "1.0"),
        description=form.get("description"),
        fields=form.get("fields", []),
        is_active=form.get("is_active", True),
    )


@router.post("/templates", response_model=FormSchema, status_code=201)
def create_form_template(req: FormCreateRequest, request: Request):
    """Create a new form template."""
    _require_permission(request, PERM_FORM_WRITE)

    form_id = str(uuid4())
    _forms_db[form_id] = {
        "id": form_id,
        "name": req.name,
        "form_type": req.form_type,
        "version": "1.0",
        "description": req.description,
        "fields": req.fields,
        "is_active": True,
    }

    return get_form_template(form_id, request)


@router.put("/templates/{form_id}", response_model=FormSchema)
def update_form_template(form_id: str, req: FormUpdateRequest, request: Request):
    """Update a form template."""
    _require_permission(request, PERM_FORM_WRITE)

    form = _forms_db.get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form template not found")

    if req.name is not None:
        form["name"] = req.name
    if req.description is not None:
        form["description"] = req.description
    if req.fields is not None:
        form["fields"] = req.fields
    if req.is_active is not None:
        form["is_active"] = req.is_active

    return get_form_template(form_id, request)


@router.post("/generate", response_model=List[FormInstance], status_code=201)
def generate_forms(req: FormGenerateRequest, request: Request):
    """Generate form instances for specified students."""
    user_id = _require_permission(request, PERM_FORM_GENERATE)

    instances = []
    for student_id in req.student_ids:
        instance_id = str(uuid4())
        now = str(datetime.utcnow())

        _form_instances_db[instance_id] = {
            "id": instance_id,
            "form_type": req.form_type,
            "student_id": student_id,
            "school_year": req.school_year,
            "quarter": req.quarter,
            "data": req.template_data.copy(),
            "status": "draft",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        }
        instances.append(get_form_instance(instance_id, request))

    return instances


@router.get("/instances", response_model=FormListResponse)
def list_form_instances(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    form_type: Optional[str] = None,
    student_id: Optional[str] = None,
    school_year: Optional[str] = None,
):
    """List generated form instances."""
    _require_permission(request, PERM_FORM_READ)

    instances = list(_form_instances_db.values())

    if form_type:
        instances = [i for i in instances if i["form_type"] == form_type]
    if student_id:
        instances = [i for i in instances if i["student_id"] == student_id]
    if school_year:
        instances = [i for i in instances if i["school_year"] == school_year]

    total = len(instances)
    start = (page - 1) * page_size
    end = start + page_size
    page_instances = instances[start:end]

    return FormListResponse(
        forms=[
            FormInstance(
                id=i["id"],
                form_type=i["form_type"],
                student_id=i.get("student_id"),
                school_year=i["school_year"],
                quarter=i.get("quarter"),
                data=i.get("data", {}),
                status=i.get("status", "draft"),
                created_by=i["created_by"],
                created_at=i["created_at"],
                updated_at=i["updated_at"],
            )
            for i in page_instances
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_form_instance(instance_id: str, request: Request) -> FormInstance:
    """Helper to retrieve and validate a form instance."""
    instance = _form_instances_db.get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Form instance not found")

    return FormInstance(
        id=instance["id"],
        form_type=instance["form_type"],
        student_id=instance.get("student_id"),
        school_year=instance["school_year"],
        quarter=instance.get("quarter"),
        data=instance.get("data", {}),
        status=instance.get("status", "draft"),
        created_by=instance["created_by"],
        created_at=instance["created_at"],
        updated_at=instance["updated_at"],
    )


@router.get("/instances/{instance_id}", response_model=FormInstance)
def get_form_instance_endpoint(instance_id: str, request: Request):
    """Get a specific form instance."""
    _require_permission(request, PERM_FORM_READ)
    return get_form_instance(instance_id, request)


@router.put("/instances/{instance_id}", response_model=FormInstance)
def update_form_instance(instance_id: str, data: Dict[str, Any], request: Request):
    """Update form instance data."""
    _require_permission(request, PERM_FORM_WRITE)

    instance = _form_instances_db.get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Form instance not found")

    instance["data"] = data
    instance["updated_at"] = str(datetime.utcnow())

    return get_form_instance(instance_id, request)


@router.post("/instances/{instance_id}/submit", response_model=FormInstance)
def submit_form_instance(instance_id: str, request: Request):
    """Submit a form instance (marks as completed/submitted)."""
    _require_permission(request, PERM_FORM_WRITE)

    instance = _form_instances_db.get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Form instance not found")

    instance["status"] = "completed"
    instance["updated_at"] = str(datetime.utcnow())

    return get_form_instance(instance_id, request)


@router.delete("/instances/{instance_id}", status_code=204)
def delete_form_instance(instance_id: str, request: Request):
    """Delete a form instance."""
    _require_permission(request, PERM_FORM_WRITE)

    if instance_id not in _form_instances_db:
        raise HTTPException(status_code=404, detail="Form instance not found")
    del _form_instances_db[instance_id]


@router.delete("/templates/{form_id}", status_code=204)
def delete_form_template(form_id: str, request: Request):
    """Delete a form template."""
    _require_permission(request, PERM_FORM_WRITE)

    if form_id not in _forms_db:
        raise HTTPException(status_code=404, detail="Form template not found")
    del _forms_db[form_id]
