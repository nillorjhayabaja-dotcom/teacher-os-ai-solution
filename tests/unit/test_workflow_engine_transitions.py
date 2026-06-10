import pytest

from backend.src.workflow.workflow_engine import WorkflowEngine


def test_workflow_engine_next_state_valid_transition():
    transitions = {"a": {"go": "b"}, "b": {"done": "c"}}
    engine = WorkflowEngine(transitions=transitions)

    res1 = engine.next_state("a", "go")
    assert res1.next_state == "b"

    res2 = engine.next_state("b", "done")
    assert res2.next_state == "c"


def test_workflow_engine_next_state_invalid_transition_raises():
    transitions = {"a": {"go": "b"}}
    engine = WorkflowEngine(transitions=transitions)
    with pytest.raises(ValueError):
        engine.next_state("a", "nope")


def test_workflow_engine_next_state_missing_state_raises():
    transitions = {"a": {"go": "b"}}
    engine = WorkflowEngine(transitions=transitions)
    with pytest.raises(ValueError):
        engine.next_state("missing", "go")

