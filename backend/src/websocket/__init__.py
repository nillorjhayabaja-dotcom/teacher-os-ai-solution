"""WebSocket framework – connection manager and channel abstractions.

The implementation is deliberately lightweight but functional. It supports
broadcast to all connected clients as well as targeted messages per tenant.
"""

try:
    from .connection_manager import ConnectionManager  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    pass

try:
    from .notification_channel import NotificationChannel  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    pass

try:
    from .tenant_channel import TenantChannel  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    pass

try:
    from .event_channel import EventChannel  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    pass

try:
    from .workflow_channel import WorkflowChannel  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    pass

