"""Core utilities for TeacherOS backend.

Exports convenient aliases so that other modules can simply do::

    from backend.src.core import settings, container, exceptions, constants, logging, tenant_context

The individual sub‑modules are imported lazily to avoid circular import issues.
"""

from .settings import settings  # noqa: F401
from .container import container, register, resolve  # noqa: F401
from .exceptions import (  # noqa: F401
    ApplicationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
)
from .constants import (  # noqa: F401
    CLAIM_SUBJECT,
    CLAIM_TENANT,
    CLAIM_ROLES,
    CLAIM_PERMISSIONS,
    HEADER_AUTHORIZATION,
    HEADER_TENANT,
)
from .logging import get_logger  # noqa: F401
from .tenant_context import get_current_tenant, set_current_tenant  # noqa: F401
