"""Output supersession reason enumeration."""

from enum import Enum


class OutputSupersessionReason(str, Enum):
    """Why an output was superseded."""

    REGENERATED = "regenerated"
    EDITED = "edited"
    PROMPT_UPDATED = "prompt_updated"
    CORRECTION = "correction"