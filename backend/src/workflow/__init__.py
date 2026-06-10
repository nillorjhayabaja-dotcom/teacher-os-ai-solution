"""Workflow engine package.

Provides definition, state, transition handling and an executor that processes
workflow instances. The implementation is intentionally simple but follows a
clean‑architecture approach – domain objects are pure, while the executor lives
in the application layer.
"""

from .workflow_definition import WorkflowDefinition  # noqa: F401
from .workflow_state import WorkflowState  # noqa: F401
from .workflow_transition import WorkflowTransition  # noqa: F401
from .workflow_history import WorkflowHistory  # noqa: F401
from .workflow_engine import WorkflowEngine  # noqa: F401
from .workflow_executor import WorkflowExecutor  # noqa: F401


