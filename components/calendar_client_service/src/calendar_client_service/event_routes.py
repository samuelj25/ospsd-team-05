"""Event CRUD endpoints for the calendar client service."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Annotated

from fastapi import APIRouter, Depends
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient  # noqa: TC002

from calendar_client_service.dependencies import get_calendar_client
from calendar_client_service.models import EventCreate, EventResponse, EventUpdate

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventResponse], summary="List events in a time range")
def list_events(
    start_time: datetime,
    end_time: datetime,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> list[EventResponse]:
    """
    Return all events between ``start_time`` and ``end_time``.

    TODO: Implement using ``client.get_events(start_time, end_time)``.
    """
    raise NotImplementedError


@router.get("/{event_id}", response_model=EventResponse, summary="Get a single event")
def get_event(
    event_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> EventResponse:
    """
    Return the event with the given ``event_id``.

    TODO: Implement using ``client.get_event(event_id)``.
    """
    raise NotImplementedError


@router.post("", response_model=EventResponse, status_code=201, summary="Create an event")
def create_event(
    payload: EventCreate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> EventResponse:
    """
    Create a new event from ``payload``.

    TODO: Build an Event object from payload fields and call ``client.create_event(event)``.
    """
    raise NotImplementedError


@router.put("/{event_id}", response_model=EventResponse, summary="Update an event")
def update_event(
    event_id: str,
    payload: EventUpdate,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> EventResponse:
    """
    Update the event identified by ``event_id`` with data from ``payload``.

    TODO: Build an Event object and call ``client.update_event(event)``.
    """
    raise NotImplementedError


@router.delete("/{event_id}", status_code=204, summary="Delete an event")
def delete_event(
    event_id: str,
    client: Annotated[GoogleCalendarClient, Depends(get_calendar_client)],
) -> None:
    """
    Delete the event with the given ``event_id``.

    TODO: Implement using ``client.delete_event(event_id)``.
    """
    raise NotImplementedError
