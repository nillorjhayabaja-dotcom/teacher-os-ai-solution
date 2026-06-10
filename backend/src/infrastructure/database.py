"""Minimal database stub used for import resolution.

In a full application this would configure an SQLAlchemy engine and declarative
base.  For the purpose of fixing the import errors we expose a dummy ``engine``
object and a placeholder ``Base`` class.
"""


class DummyEngine:
    def connect(self):
        raise NotImplementedError("Database engine not configured.")


class Base:  # Placeholder for ORM base class
    pass


engine = DummyEngine()

__all__ = ["engine", "Base"]