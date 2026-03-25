"""FastAPI application factory for the calendar client service."""

from fastapi import FastAPI

from calendar_client_service.auth_routes import router as auth_router
from calendar_client_service.event_routes import router as event_router
from calendar_client_service.models import HealthResponse
from calendar_client_service.task_routes import router as task_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Registers all routers (auth, events, tasks) and the health endpoint,
    then returns the configured app instance.

    Returns:
        A configured :class:`fastapi.FastAPI` instance.

    """
    application = FastAPI(
        title="Calendar Client Service",
        description=(
            "HTTP microservice exposing the GoogleCalendarClient over REST.\n\n"
            "Authenticate via `/auth/login` before calling any event or task endpoint."
        ),
        version="0.1.0",
    )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @application.get(
        "/health",
        tags=["health"],
        summary="Health check",
    )
    def health() -> HealthResponse:
        """Return HTTP 200 to confirm the service is running."""
        return HealthResponse(status="ok")

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------

    application.include_router(auth_router)
    application.include_router(event_router)
    application.include_router(task_router)

    return application


# Module-level app instance used by uvicorn:
#   uv run uvicorn calendar_client_service.app:app --reload --port 8000
app = create_app()
