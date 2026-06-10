"""Component tests for AI Workflow Engine integration."""

import pytest
from backend.src.domains.ai.workflow import AI_RUN_TRANSITIONS, create_ai_run_engine
from backend.src.workflow.workflow_engine import WorkflowEngine


class TestAIWorkflowConfig:
    def test_transitions_definition(self):
        assert "queued" in AI_RUN_TRANSITIONS
        assert "running" in AI_RUN_TRANSITIONS
        assert "completed" in AI_RUN_TRANSITIONS
        assert "failed" in AI_RUN_TRANSITIONS

    def test_queued_transitions(self):
        t = AI_RUN_TRANSITIONS["queued"]
        assert t["start"] == "running"
        assert t["cancel"] == "cancelled"

    def test_running_transitions(self):
        t = AI_RUN_TRANSITIONS["running"]
        assert t["complete"] == "completed"
        assert t["fail"] == "failed"
        assert t["timeout"] == "timed_out"
        assert t["cancel"] == "cancelled"

    def test_completed_transitions(self):
        t = AI_RUN_TRANSITIONS["completed"]
        assert t["approve"] == "approved"
        assert t["submit_for_review"] == "pending_review"
        assert t["regenerate"] == "running"

    def test_pending_review_transitions(self):
        t = AI_RUN_TRANSITIONS["pending_review"]
        assert t["start_review"] == "in_review"

    def test_in_review_transitions(self):
        t = AI_RUN_TRANSITIONS["in_review"]
        assert t["approve"] == "approved"
        assert t["reject"] == "rejected"
        assert t["edit"] == "edited"

    def test_rejected_transitions(self):
        t = AI_RUN_TRANSITIONS["rejected"]
        assert t["regenerate"] == "running"

    def test_failed_transitions(self):
        t = AI_RUN_TRANSITIONS["failed"]
        assert t["retry"] == "running"
        assert t["cancel"] == "cancelled"

    def test_timed_out_retry(self):
        t = AI_RUN_TRANSITIONS["timed_out"]
        assert t["retry"] == "running"

    def test_terminal_states_have_no_outgoing(self):
        for state in ["approved", "edited", "cancelled"]:
            assert AI_RUN_TRANSITIONS[state] == {}


class TestWorkflowEngineIntegration:
    def test_create_engine(self):
        engine = create_ai_run_engine()
        assert isinstance(engine, WorkflowEngine)

    def test_valid_transition(self):
        engine = create_ai_run_engine()
        result = engine.next_state("queued", "start")
        assert result.next_state == "running"

    def test_complete_workflow(self):
        engine = create_ai_run_engine()
        state = "queued"
        for action, expected in [("start", "running"), ("complete", "completed"), ("approve", "approved")]:
            result = engine.next_state(state, action)
            assert result.next_state == expected
            state = result.next_state

    def test_review_workflow(self):
        engine = create_ai_run_engine()
        state = "queued"
        for action, expected in [
            ("start", "running"),
            ("complete", "completed"),
            ("submit_for_review", "pending_review"),
            ("start_review", "in_review"),
            ("approve", "approved"),
        ]:
            result = engine.next_state(state, action)
            assert result.next_state == expected
            state = result.next_state

    def test_reject_regenerate_workflow(self):
        engine = create_ai_run_engine()
        state = "queued"
        for action, expected in [
            ("start", "running"), ("complete", "completed"),
            ("submit_for_review", "pending_review"), ("start_review", "in_review"),
            ("reject", "rejected"), ("regenerate", "running"),
        ]:
            result = engine.next_state(state, action)
            assert result.next_state == expected
            state = result.next_state

    def test_invalid_transition_raises(self):
        engine = create_ai_run_engine()
        with pytest.raises(ValueError):
            engine.next_state("queued", "invalid_action")

    def test_invalid_state_raises(self):
        engine = create_ai_run_engine()
        with pytest.raises(ValueError):
            engine.next_state("nonexistent_state", "start")