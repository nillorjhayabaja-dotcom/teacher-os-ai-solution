from __future__ import annotations

import pytest

from backend.src.events.base_domain_event import BaseDomainEvent
from backend.src.events.event_bus import EventBus
from backend.src.events.event_dispatcher import EventDispatcher
from backend.src.events.event_publisher import EventPublisher
from backend.src.events.event_replay import EventReplay
from backend.src.events.event_store import EventStore
from backend.src.infrastructure.event_store_db import DBEventStore


class StudentCreated(BaseDomainEvent):
    pass


@pytest.mark.events
@pytest.mark.unit
def test_event_bus_publication_order():
    bus = EventBus()
    calls = []

    def first(event):
        calls.append(("first", event.student_id))

    def second(event):
        calls.append(("second", event.student_id))

    bus.subscribe(StudentCreated, first)
    bus.subscribe(StudentCreated, second)
    bus.publish(StudentCreated(student_id="s1", payload={"student_id": "s1"}))

    assert calls == [("first", "s1"), ("second", "s1")]


@pytest.mark.events
@pytest.mark.unit
def test_event_store_persists_events_in_order():
    store = EventStore()
    event1 = StudentCreated(event_id="e1", payload={"seq": 1})
    event2 = StudentCreated(event_id="e2", payload={"seq": 2})

    store.append(event1)
    store.append(event2)

    assert store.all() == [event1, event2]


@pytest.mark.events
@pytest.mark.unit
def test_event_dispatcher_and_publisher_delegate_to_bus():
    bus = EventBus()
    seen = []
    bus.subscribe(StudentCreated, lambda event: seen.append(event.student_id))

    dispatcher = EventDispatcher(bus)
    publisher = EventPublisher(bus)
    dispatcher.dispatch(StudentCreated(student_id="s1"))
    publisher.publish(StudentCreated(student_id="s2"))

    assert seen == ["s1", "s2"]


@pytest.mark.events
@pytest.mark.integration
def test_db_event_store_is_tenant_scoped(tenant_id, other_tenant_id):
    store = DBEventStore()
    store.append(tenant_id=str(tenant_id), event=StudentCreated(event_id="e1", payload={"name": "Ana"}))
    store.append(tenant_id=str(other_tenant_id), event=StudentCreated(event_id="e2", payload={"name": "Ben"}))

    assert [e.id for e in store.all(tenant_id=str(tenant_id))] == ["e1"]
    assert [e.id for e in store.all(tenant_id=str(other_tenant_id))] == ["e2"]


@pytest.mark.events
@pytest.mark.xfail_architecture_gap(reason="EventReplay placeholder does not reconstruct/version/replay persisted events yet.")
def test_event_replay_reconstructs_events_with_versioning_and_order():
    store = EventStore()
    dispatcher = EventDispatcher(EventBus())
    replay = EventReplay(store, dispatcher)
    store.append(StudentCreated(event_id="e1", version=1, payload={"seq": 1}))
    assert replay.replay_all()[0].event_id == "e1"
