"""Simple publisher wrapper around :class:`EventBus`."""

from .event_bus import EventBus
from .base_domain_event import BaseDomainEvent


class EventPublisher:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def publish(self, event: BaseDomainEvent) -> None:
        self.bus.publish(event)


__all__ = ["EventPublisher"]