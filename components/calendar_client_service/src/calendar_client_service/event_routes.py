"""Event CRUD endpoints for the calendar client service."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Annotated

from calendar_client_api.event import Event
from fastapi import APIRouter, Depends, HTTPException
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient  # noqa: TC002

from calendar_client_service.dependencies import get_calendar_client
from calendar_client_service.models import EventCreate, EventResponse, EventUpdate


class _ServiceEvent(Event):
    def __init__(  # noqa: PLR0913
        self,
        e_id: str,
        title: str,
        start: datetime,
        end: datetime,
        loc: str | None,
        desc: str | None,
    ) -> None:
        self._id = e_id
        self._title = title
        self._start = start
        self._end = end
        self._loc = loc
        self._desc = desc

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
        return self._loc

    @property
    def description(self) -> str | None:
        return self._desc

def _to_event_response(e: Event) -> EventResponse:
    return EventResponse(
        id=e.id,
        title=e.title,
        start_time=e.start_time,
        end_time=e.end_time,
        location=e.location,
        description=e.description,
    )

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventResponse], summary="List events in a time range")
def list_events(
    start_time: datetime,
    end_time: datetime,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> list[EventResponse]:
    """Return all events between ``start_time`` and ``end_time``."""
    events = client.get_events(start_time, end_time)
    return [_to_event_response(e) for e in events]


@router.get("/{event_id}", response_model=EventResponse, summary="Get a single event")
def get_event(
    event_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> EventResponse:
    """Return the event with the given ``event_id``."""
    e = client.get_event(event_id)
    return _to_event_response(e)


@router.post("", response_model=EventResponse, status_code=201, summary="Create an event")
def create_event(
    payload: EventCreate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> EventResponse:
    """Create a new event from ``payload``."""
    ev = _ServiceEvent(
        e_id="",
        title=payload.title,
        start=payload.start_time,
        end=payload.end_time,
        loc=payload.location,
        desc=payload.description,
    )
    e = client.create_event(ev)
    return _to_event_response(e)


@router.put("/{event_id}", response_model=EventResponse, summary="Update an event")
def update_event(
    event_id: str,
    payload: EventUpdate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> EventResponse:
    """Update the event identified by ``event_id`` with data from ``payload``."""
    if event_id != payload.id:
        raise HTTPException(status_code=422, detail="Event ID in path and payload must match")
    ev = _ServiceEvent(
        e_id=payload.id,
        title=payload.title,
        start=payload.start_time,
        end=payload.end_time,
        loc=payload.location,
        desc=payload.description,
    )
    e = client.update_event(ev)
    return _to_event_response(e)


@router.delete("/{event_id}", status_code=204, summary="Delete an event")
def delete_event(
    event_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> None:
    """Delete the event with the given ``event_id``."""
    client.delete_event(event_id)
