"""Agent kind enumeration — 12 specialized agent kinds (7 MVP, 5 post-MVP)."""

from enum import Enum


class AgentKind(str, Enum):
    """Enumeration of all supported AI agent kinds."""

    # MVP agents
    LESSON_PLANNING = "lesson_planning"
    ASSESSMENT = "assessment"
    GRADEBOOK = "gradebook"
    FORMS = "forms"
    STUDENT_RISK = "student_risk"
    REPORT = "report"
    COMMUNICATION = "communication"

    # Post-MVP agents
    RUBRIC_GENERATION = "rubric_generation"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    ATTENDANCE_ANALYSIS = "attendance_analysis"
    PARENT_SUMMARY = "parent_summary"
    COMPLIANCE_CHECK = "compliance_check"

    @classmethod
    def mvp_kinds(cls) -> list["AgentKind"]:
        """Return only MVP agent kinds."""
        return [
            cls.LESSON_PLANNING,
            cls.ASSESSMENT,
            cls.GRADEBOOK,
            cls.FORMS,
            cls.STUDENT_RISK,
            cls.REPORT,
            cls.COMMUNICATION,
        ]

    @property
    def display_name(self) -> str:
        return self.value.replace("_", " ").title()