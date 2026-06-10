from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.unit
def test_ai_context_does_not_import_business_domain_models_directly():
    ai_files = list(Path("backend/src/domains/ai").rglob("*.py")) + list(Path("backend/src/infrastructure/ai").rglob("*.py"))
    forbidden = ["backend.src.domains.student", "backend.src.domains.gradebook", "backend.src.domains.lesson"]
    offenders = []
    for file in ai_files:
        text = file.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{file}:{token}")
    assert offenders == []


@pytest.mark.unit
def test_architecture_documents_remain_present_as_testing_source_of_truth():
    assert Path("ARCHITECTURE.md").exists()
    assert Path("AI_ARCHITECTURE.md").exists()
    assert Path("architecture/00-erd-summary.md").exists()


@pytest.mark.domain
@pytest.mark.xfail_architecture_gap(reason="Non-AI bounded contexts currently only have SQL architecture, not Python domain models/services/repositories yet.")
@pytest.mark.parametrize("domain", ["identity", "student", "gradebook", "forms", "lesson", "assessment", "communication", "reporting", "programs"])
def test_required_domain_packages_exist(domain):
    assert Path(f"backend/src/domains/{domain}").exists()
