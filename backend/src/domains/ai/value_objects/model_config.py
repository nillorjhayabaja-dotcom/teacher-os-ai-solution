"""LLM model configuration value object."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ModelConfig:
    """LLM model configuration for an agent."""

    provider: str  # "openai", "anthropic", "ollama"
    model_name: str  # "gpt-4o", "claude-3.5-sonnet", etc.
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stop_sequences: tuple = ()
    timeout_seconds: int = 120
    retry_attempts: int = 3
    fallback_model: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop_sequences": list(self.stop_sequences),
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "fallback_model": self.fallback_model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ModelConfig:
        return cls(
            provider=data["provider"],
            model_name=data["model_name"],
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
            top_p=data.get("top_p", 1.0),
            stop_sequences=tuple(data.get("stop_sequences", ())),
            timeout_seconds=data.get("timeout_seconds", 120),
            retry_attempts=data.get("retry_attempts", 3),
            fallback_model=data.get("fallback_model"),
        )