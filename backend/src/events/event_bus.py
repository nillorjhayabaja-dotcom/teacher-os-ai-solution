"""Simple in‑memory event bus implementation."""

from typing import Callable, Dict, List, Type
from .base_domain_event import BaseDomainEvent


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[Type[BaseDomainEvent], List[Callable[[BaseDomainEvent], None]]] = {}

    def subscribe(self, event_type: Type[BaseDomainEvent], handler: Callable[[BaseDomainEvent], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: BaseDomainEvent) -> None:
        for handler in self._subscribers.get(type(event), []):
            handler(event)


__all__ = ["EventBus"]