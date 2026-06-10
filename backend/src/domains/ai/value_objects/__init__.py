"""AI Value Objects — immutable domain primitives."""

from .agent_kind import AgentKind
from .model_config import ModelConfig
from .token_usage import TokenUsage
from .cost_breakdown import CostBreakdown
from .review_state import ReviewState
from .run_status import RunStatus
from .ai_input_context import AIInputContext
from .ai_output_metadata import AIOutputMetadata
from .output_supersession import OutputSupersessionReason

OutputSupersession = OutputSupersessionReason

__all__ = [
    "AgentKind",
    "ModelConfig",
    "TokenUsage",
    "CostBreakdown",
    "ReviewState",
    "RunStatus",
    "AIInputContext",
    "AIOutputMetadata",
    "OutputSupersessionReason",
    "OutputSupersession",
]