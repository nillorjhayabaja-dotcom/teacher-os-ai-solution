"""Domain layer – pure business objects.

Only a minimal ``User`` aggregate is provided as an example. Real business
modules will add additional aggregates.
"""

try:
    from .user import User  # type: ignore # noqa: F401
except ImportError:  # pragma: no cover
    # Optional re-export; module may not exist yet.
    pass

