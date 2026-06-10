from __future__ import annotations

import pytest

from backend.src.core.tenant_context import reset_current_tenant, set_current_tenant
from backend.src.workflow import WorkflowEngine, WorkflowExecutor, WorkflowHistory

DOMAIN_WORKFLOWS = {
    "lesson": {"draft": {"submit": "review"}, "review": {"approve": "approved", "reject": "draft"}},
    "gradebook": {"open": {"compute": "computed"}, "computed": {"publish": "published"}},
    "forms": {"draft": {"generate": "generated"}, "generated": {"validate": "validated"}},
    "communication": {"draft": {"send": "sent"}, "sent": {"archive": "archived"}},
    "reporting": {"draft": {"compile": "compiled"}, "compiled": {"submit": "submitted"}},
    "risk_assessment": {"identified": {"assess": "assessed"}, "assessed": {"intervene": "intervention_open"}},
}


@pytest.mark.workflows
@pytest.mark.domain
@pytest.mark.parametrize("name,transitions", DOMAIN_WORKFLOWS.items())
def test_documented_workflow_valid_and_invalid_transitions(name, transitions):
    engine = WorkflowEngine(transitions)
    first_state = next(iter(transitions))
    event, expected = next(iter(transitions[first_state].items()))

    assert engine.next_state(first_state, event).next_state == expected
    with pytest.raises(ValueError, match="Invalid transition"):
        engine.next_state(first_state, "not_allowed")


@pytest.mark.workflows
@pytest.mark.integration
def test_workflow_executor_persists_history_and_tenant_scope(tenant_id):
    token = set_current_tenant(str(tenant_id))
    history = WorkflowHistory()
    executor = WorkflowExecutor(WorkflowEngine(DOMAIN_WORKFLOWS["lesson"]), history=history)
    try:
        execution = executor.execute(
            workflow_id="lesson-1",
            current_state="draft",
            event="submit",
            actor_id="teacher-1",
            metadata={"source": "api"},
        )
    finally:
        reset_current_tenant(token)

    entries = history.all_for_workflow("lesson-1")
    assert execution.tenant_id == str(tenant_id)
    assert execution.to_state == "review"
    assert entries[0].from_state == "draft"
    assert entries[0].to_state == "review"
    assert entries[0].created_at


@pytest.mark.workflows
@pytest.mark.events
@pytest.mark.xfail_architecture_gap(reason="WorkflowExecutor currently records history but does not emit events/recovery checkpoints.")
def test_workflow_execution_emits_events_and_supports_recovery():
    executor = WorkflowExecutor(WorkflowEngine(DOMAIN_WORKFLOWS["forms"]), event_bus=object(), checkpoint_store=object())
    execution = executor.execute(workflow_id="form-1", current_state="draft", event="generate")
    assert execution.event_id
    assert executor.recover("form-1").to_state == "generated"
