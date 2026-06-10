"""AI output metadata value object."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AIOutputMetadata:
    """Metadata attached to every AI output for provenance."""

    model_used: str
    provider: str
    prompt_version_id: UUID
    system_prompt_hash: str  # SHA-256
    input_hash: str  # SHA-256
    generation_timestamp: str
    temperature: float
    max_tokens: int