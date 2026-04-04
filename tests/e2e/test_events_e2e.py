"""End-To-End tests for compiling Event operations together into a full lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from calendar_client_adapter.adapter import ServiceAdapterClient
from calendar_client_api import Event, EventNotFoundError


@pytest.mark.e2e
def test_event_lifecycle(live_client: ServiceAdapterClient) -> None:
    """Create an event, verify it exists, update it, verify the modification, and delete it."""
    now = datetime.now(tz=UTC)
    start = (now + timedelta(hours=1)).replace(microsecond=0)
    end = (start + timedelta(hours=1)).replace(microsecond=0)

    # 1. Create Event
    created = live_client.create_event(
        _make_event(title="E2E Lifecycle Event Original", start=start, end=end),
    )
    assert created.id is not None
    assert created.title == "E2E Lifecycle Event Original"

    try:
        # 2. Verify it exists via Get
        fetched = live_client.get_event(created.id)
        assert fetched.title == "E2E Lifecycle Event Original"

        # 3. Update it
        updated = live_client.update_event(
            _make_event(
                title="E2E Lifecycle Event Updated",
                start=start,
                end=end,
                event_id=created.id,
            ),
        )
        assert updated.title == "E2E Lifecycle Event Updated"

        # 4. Verify modification via Get
        refetched = live_client.get_event(created.id)
        assert refetched.title == "E2E Lifecycle Event Updated"

    finally:
        # 5. Delete it
        live_client.delete_event(created.id)

        # Verify it is deleted — the adapter raises EventNotFoundError on 404.
        with pytest.raises(EventNotFoundError):
            live_client.get_event(created.id)


@pytest.mark.e2e
def test_list_events_lifecycle(live_client: ServiceAdapterClient) -> None:
    """Create a couple events, verify they show up in get_events() with date ranges."""
    now = datetime.now(tz=UTC)
    start1 = (now + timedelta(hours=1)).replace(microsecond=0)
    end1 = (start1 + timedelta(hours=1)).replace(microsecond=0)

    start2 = (now + timedelta(hours=3)).replace(microsecond=0)
    end2 = (start2 + timedelta(hours=1)).replace(microsecond=0)

    ids_to_clean: list[str] = []

    try:
        ev1 = live_client.create_event(
            _make_event(title="E2E List Event 1", start=start1, end=end1),
        )
        ids_to_clean.append(ev1.id)

        ev2 = live_client.create_event(
            _make_event(title="E2E List Event 2", start=start2, end=end2),
        )
        ids_to_clean.append(ev2.id)

        # Fetch events in range
        events_list = list(live_client.get_events(now, now + timedelta(days=1)))

        # Verify our created events are returned in the list
        found_ids = [e.id for e in events_list]
        assert ev1.id in found_ids
        assert ev2.id in found_ids

    finally:
        for ev_id in ids_to_clean:
            live_client.delete_event(ev_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SimpleEvent(Event):
    """Minimal in-process Event implementation for constructing request payloads."""

    def __init__(  # noqa: PLR0913
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        event_id: str = "",
        location: str | None = None,
        description: str | None = None,
    ) -> None:
        self._id = event_id
        self._title = title
        self._start = start_time
        self._end = end_time
        self._location = location
        self._description = description

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def start_time(self) -> datetime:
        return self._start

    @property
    def end_time(self) -> datetime:
        return self._end

    @property
    def location(self) -> str | None:
        return self._location

    @property
    def description(self) -> str | None:
        return self._description


def _make_event(  # noqa: PLR0913
    title: str,
    start: datetime,
    end: datetime,
    event_id: str = "",
    location: str | None = None,
    description: str | None = None,
) -> _SimpleEvent:
    return _SimpleEvent(
        title=title,
        start_time=start,
        end_time=end,
        event_id=event_id,
        location=location,
        description=description,
    )
