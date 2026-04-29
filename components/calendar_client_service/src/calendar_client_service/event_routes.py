"""Event CRUD endpoints for the calendar client service."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient  # noqa: TC002
from ospsd_calendar_api.models import Event  # noqa: TC002

from calendar_client_service.dependencies import get_calendar_client
from calendar_client_service.models import EventCreate, EventResponse, EventUpdate


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
    events = client.list_events(start_time, end_time)
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
    e = client.create_event(
        title=payload.title,
        start=payload.start_time,
        end=payload.end_time,
        description=payload.description or "",
        location=payload.location,
    )
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
    e = client.update_event(
        event_id,
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location,
        description=payload.description,
    )
    return _to_event_response(e)


@router.delete("/{event_id}", status_code=204, summary="Delete an event")
def delete_event(
    event_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> None:
    """Delete the event with the given ``event_id``."""
    client.delete_event(event_id)
