"""Dependency injection container for the TeacherOS backend.

The project uses **punq** as a lightweight IoC container. This module
initialises a global :class:`punq.Container` instance and provides helper
functions for registering and resolving dependencies throughout the codebase.
"""

from __future__ import annotations

from typing import Any, Callable, Type, TypeVar

import punq

# Global container instance – imported by modules that need to register or
# resolve services. The container is created lazily on first import.
container = punq.Container()

T = TypeVar("T")


def register(interface: Type[T], implementation: Callable[..., T] | Type[T] | Any, *, singleton: bool = False) -> None:
    """Register a service implementation.

    Args:
        interface: The abstract type or identifier used for resolution.
        implementation: Either a class, a factory callable, or an already
            instantiated object.
        singleton: If ``True`` the same instance will be returned for all
            resolutions; otherwise a new instance is created each time.
    """
    if singleton:
        # When a singleton is provided as an instance we store it directly.
        container.register(interface, implementation, singleton=True)
    else:
        container.register(interface, implementation)


def resolve(interface: Type[T]) -> T:
    """Resolve a registered service.

    Args:
        interface: The type or key previously registered.
    Returns:
        The concrete implementation instance.
    """
    return container.resolve(interface)
