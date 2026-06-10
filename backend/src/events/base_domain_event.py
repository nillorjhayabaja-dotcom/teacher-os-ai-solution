"""Base class for domain events.

Concrete event classes can inherit from this class. It simply stores any
provided keyword arguments as attributes.
"""


class BaseDomainEvent:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"


__all__ = ["BaseDomainEvent"]