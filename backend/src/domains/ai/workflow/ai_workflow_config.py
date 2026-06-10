"""AI Run State Machine — integrates with the existing WorkflowEngine."""

from __future__ import annotations

from backend.src.workflow.workflow_engine import WorkflowEngine

# AI run transitions matching architecture §8.1 state machine
AI_RUN_TRANSITIONS = {
    "queued": {
        "start": "running",
        "cancel": "cancelled",
    },
    "running": {
        "complete": "completed",
        "fail": "failed",
        "timeout": "timed_out",
        "cancel": "cancelled",
    },
    "completed": {
        "approve": "approved",
        "submit_for_review": "pending_review",
        "regenerate": "running",
    },
    "pending_review": {
        "start_review": "in_review",
    },
    "in_review": {
        "approve": "approved",
        "reject": "rejected",
        "edit": "edited",
    },
    "rejected": {
        "regenerate": "running",
        "cancel": "cancelled",
    },
    "failed": {
        "retry": "running",
        "cancel": "cancelled",
    },
    # Terminal states
    "approved": {},
    "edited": {},
    "cancelled": {},
    "timed_out": {"retry": "running"},
}


def create_ai_run_engine() -> WorkflowEngine:
    """Create a WorkflowEngine instance configured for AI run state machine."""
    return WorkflowEngine(transitions=AI_RUN_TRANSITIONS)