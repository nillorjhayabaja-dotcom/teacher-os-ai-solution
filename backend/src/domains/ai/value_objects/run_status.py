"""Run status enumeration."""

from enum import Enum


class RunStatus(str, Enum):
    """Agent execution lifecycle."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"