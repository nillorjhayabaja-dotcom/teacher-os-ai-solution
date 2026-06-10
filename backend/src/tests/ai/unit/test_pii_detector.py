"""Unit tests for PII detection and redaction."""

import pytest
from backend.src.infrastructure.ai.security.prompt_guard import PIIDetector


class TestPIIDetector:
    def test_detect_email(self):
        detector = PIIDetector()
        findings = detector.detect("Contact me at teacher@school.edu.ph")
        assert "email" in findings
        assert "teacher@school.edu.ph" in findings["email"]

    def test_detect_phone(self):
        detector = PIIDetector()
        findings = detector.detect("Call me at 09171234567")
        assert "phone" in findings
        assert "09171234567" in findings["phone"]

    def test_detect_lrn(self):
        detector = PIIDetector()
        findings = detector.detect("LRN: 12-34567-89-01234")
        assert "lrn" in findings

    def test_detect_multiple_pii(self):
        detector = PIIDetector()
        text = "Student: Juan, LRN: 12-34567-89-01234, Email: juan@school.ph"
        findings = detector.detect(text)
        assert len(findings) >= 2

    def test_redact_email(self):
        detector = PIIDetector()
        result = detector.redact("Email: teacher@school.edu.ph")
        assert "[REDACTED_EMAIL]" in result
        assert "teacher@school.edu.ph" not in result

    def test_redact_phone(self):
        detector = PIIDetector()
        result = detector.redact("Phone: 09171234567")
        assert "[REDACTED_PHONE]" in result

    def test_redact_lrn(self):
        detector = PIIDetector()
        result = detector.redact("LRN: 12-34567-89-01234")
        assert "[REDACTED_LRN]" in result

    def test_no_pii_unchanged(self):
        detector = PIIDetector()
        text = "This is a normal sentence without PII."
        result = detector.redact(text)
        assert result == text

    def test_empty_string(self):
        detector = PIIDetector()
        assert detector.detect("") == {}
        assert detector.redact("") == ""