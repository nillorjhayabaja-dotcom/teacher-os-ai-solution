"""Dispatcher that forwards events to an :class:`EventBus`."""

from .event_bus import EventBus
from .base_domain_event import BaseDomainEvent


class EventDispatcher:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def dispatch(self, event: BaseDomainEvent) -> None:
        self.bus.publish(event)


__all__ = ["EventDispatcher"]