"""Review state enumeration."""

from enum import Enum


class ReviewState(str, Enum):
    """Human-in-the-loop review lifecycle."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    AUTO_APPROVED = "auto_approved"