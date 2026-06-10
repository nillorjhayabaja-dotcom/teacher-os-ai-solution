"""Utility to replay stored events via a dispatcher."""

from .event_store import EventStore
from .event_dispatcher import EventDispatcher


class EventReplay:
    def __init__(self, store: EventStore, dispatcher: EventDispatcher) -> None:
        self.store = store
        self.dispatcher = dispatcher

    def replay_all(self) -> None:
        """Dispatch every stored event in order."""
        for event in self.store.all():
            self.dispatcher.dispatch(event)


__all__ = ["EventReplay"]