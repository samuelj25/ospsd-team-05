"""Pydantic request / response models for the calendar client service."""

from datetime import datetime

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Event models
# ---------------------------------------------------------------------------


class EventCreate(BaseModel):
    """Payload for creating a new calendar event."""

    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None
    description: str | None = None


class EventUpdate(BaseModel):
    """Payload for updating an existing calendar event."""

    id: str
    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None
    description: str | None = None


class EventResponse(BaseModel):
    """Response model representing a calendar event."""

    id: str
    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None
    description: str | None = None


# ---------------------------------------------------------------------------
# Task models
# ---------------------------------------------------------------------------


class TaskCreate(BaseModel):
    """Payload for creating a new task."""

    title: str
    end_time: datetime
    description: str | None = None


class TaskUpdate(BaseModel):
    """Payload for updating an existing task."""

    id: str
    title: str
    end_time: datetime
    description: str | None = None
    is_completed: bool = False


class TaskResponse(BaseModel):
    """Response model representing a task."""

    id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: str | None = None
    is_completed: bool


# ---------------------------------------------------------------------------
# Auth / misc models
# ---------------------------------------------------------------------------


class AuthStatusResponse(BaseModel):
    """Response model for the /auth/status endpoint."""

    authenticated: bool
    session_id: str | None = None


class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""

    status: str
