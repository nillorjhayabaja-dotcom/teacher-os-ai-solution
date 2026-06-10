"""API package – FastAPI routers and endpoints.

Provides all business domain API endpoints for the TeacherOS platform.
"""

from fastapi import APIRouter

from backend.src.api.v1.auth import router as auth_router
from backend.src.api.v1.users import router as users_router
from backend.src.api.v1.students import router as students_router
from backend.src.api.v1.grades import router as grades_router
from backend.src.api.v1.attendance import router as attendance_router
from backend.src.api.v1.reports import router as reports_router
from backend.src.api.v1.forms import router as forms_router
from backend.src.api.v1.classes import router as classes_router
from backend.src.api.v1.audit import router as audit_router
from backend.src.api.v1.settings import router as settings_router
from backend.src.api.v1.ai.agents import router as ai_agents_router

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


# Business domain v1 routers
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(students_router)
router.include_router(grades_router)
router.include_router(attendance_router)
router.include_router(reports_router)
router.include_router(forms_router)
router.include_router(classes_router)
router.include_router(audit_router)
router.include_router(settings_router)
router.include_router(ai_agents_router)


