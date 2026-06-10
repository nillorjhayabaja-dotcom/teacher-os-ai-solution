"""AI Tool definitions."""

from .base_tool import AITool
from .curriculum_search import CurriculumSearchTool
from .melc_lookup import MelcLookupTool

MELCLookupTool = MelcLookupTool
from .student_search import StudentSearchTool
from .attendance_analyzer import AttendanceAnalyzerTool
from .grade_lookup import GradeLookupTool
from .rubric_generator import RubricGeneratorTool
from .form_template_lookup import FormTemplateLookupTool
from .transmutation_lookup import TransmutationLookupTool
from .notification_sender import NotificationSenderTool
from .student_risk_score import StudentRiskScoreTool
from .form_validator import FormValidatorTool
from .school_config_lookup import SchoolConfigLookupTool

__all__ = [
    "AITool",
    "CurriculumSearchTool",
    "MelcLookupTool",
    "MELCLookupTool",
    "StudentSearchTool",
    "AttendanceAnalyzerTool",
    "GradeLookupTool",
    "RubricGeneratorTool",
    "FormTemplateLookupTool",
    "TransmutationLookupTool",
    "NotificationSenderTool",
    "StudentRiskScoreTool",
    "FormValidatorTool",
    "SchoolConfigLookupTool",
]