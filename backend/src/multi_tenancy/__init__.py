"""Multi‑tenancy utilities for TeacherOS.

Exports the resolver, middleware and context helpers that enable request‑level
tenant isolation across the platform.
"""

from .tenant_resolver import TenantResolver  # noqa: F401
from .tenant_middleware import TenantMiddleware  # noqa: F401
from .tenant_context import TenantContext  # noqa: F401
from .organization_scope import OrganizationScope  # noqa: F401

try:
    from .school_scope import SchoolScope  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    # Optional re-export; module may not exist yet.
    pass

