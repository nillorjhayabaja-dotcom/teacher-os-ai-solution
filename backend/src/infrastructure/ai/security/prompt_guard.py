"""Prompt Guard — detects and prevents prompt injection attacks."""

from __future__ import annotations

import re
from typing import Optional


class PromptInjectionGuard:
    """Detects and prevents prompt injection attacks."""

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"system\s*:\s*",
        r"<\|system\|>",
        r"\[SYSTEM\]",
        r"override\s+(system|safety)",
        r"jailbreak",
        r"DAN\s+mode",
        r"pretend\s+(you|that)\s+(are|is)",
    ]

    def __init__(self) -> None:
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    def detect(self, text: str) -> Optional[str]:
        for pattern in self._compiled:
            match = pattern.search(text)
            if match:
                return f"Potential injection detected: {match.group()}"
        return None

    def sanitize(self, text: str) -> str:
        text = re.sub(r"<\|.*?\|>", "", text)
        text = re.sub(r"\[SYSTEM\].*?\[/SYSTEM\]", "", text, flags=re.IGNORECASE)
        return text.strip()

    def is_safe(self, text: str) -> bool:
        return self.detect(text) is None


class PIIDetector:
    """Detects personally identifiable information in AI inputs/outputs."""

    PII_PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(?:\+63|0)9\d{9}",
        "lrn": r"\d{2}-\d{5}-\d{2}-\d{5}",  # DepEd LRN format
        "ssn_ph": r"\d{4}-\d{7}-\d{1}",  # PhilSys/SSS-like
    }

    def detect(self, text: str) -> dict[str, list[str]]:
        findings = {}
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                findings[pii_type] = matches
        return findings

    def redact(self, text: str) -> str:
        for pii_type, pattern in self.PII_PATTERNS.items():
            text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
        return text