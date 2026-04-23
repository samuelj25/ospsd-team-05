"""FastAPI application factory for the calendar client service."""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import TYPE_CHECKING, Any

from calendar_client_api.exceptions import TaskNotFoundError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ospsd_calendar_api.exceptions import CalendarOperationError, EventNotFoundError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from calendar_client_service.auth_routes import router as auth_router
from calendar_client_service.event_routes import router as event_router
from calendar_client_service.models import HealthResponse
from calendar_client_service.slack_routes import router as slack_router
from calendar_client_service.task_routes import router as task_router

if TYPE_CHECKING:
    from starlette.responses import Response

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Telemetry: in-memory metrics store
# ---------------------------------------------------------------------------


class _MetricsStore:
    """Thread-safe counters for request latency, success, and failure totals."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._success_total: int = 0
        self._failure_total: int = 0
        self._latency_sum_ms: float = 0.0
        self._request_count: int = 0

    def record(self, status_code: int, latency_ms: float) -> None:
        """Record a single request outcome into the running totals."""
        with self._lock:
            self._request_count += 1
            self._latency_sum_ms += latency_ms
            if status_code < 400:  # noqa: PLR2004
                self._success_total += 1
            else:
                self._failure_total += 1

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time copy of all counters."""
        with self._lock:
            avg_ms = (
                self._latency_sum_ms / self._request_count
                if self._request_count > 0
                else 0.0
            )
            return {
                "request_success_total": self._success_total,
                "request_failure_total": self._failure_total,
                "request_count": self._request_count,
                "request_latency_avg_ms": round(avg_ms, 2),
            }


_metrics = _MetricsStore()


# ---------------------------------------------------------------------------
# Telemetry: latency middleware
# ---------------------------------------------------------------------------


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Records per-request wall-clock latency and updates the metrics store."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Time the request, update counters, and forward the response."""
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000.0
        _metrics.record(response.status_code, latency_ms)
        response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
        return response


# ---------------------------------------------------------------------------
# Telemetry: OpenTelemetry tracing
# ---------------------------------------------------------------------------


def _configure_tracing(application: FastAPI) -> None:
    """
    Initialise OpenTelemetry tracing and instrument the FastAPI app.

    Uses ``CloudTraceSpanExporter`` when ``GOOGLE_CLOUD_PROJECT`` is set;
    falls back to a ``ConsoleSpanExporter`` for local / CI environments.
    Silently disables telemetry if OTel packages are not installed.

    Args:
        application: The FastAPI instance to instrument.

    """
    try:
        from opentelemetry import trace  # noqa: PLC0415
        from opentelemetry.instrumentation.fastapi import (  # noqa: PLC0415
            FastAPIInstrumentor,
        )
        from opentelemetry.sdk.trace import (  # noqa: PLC0415
            TracerProvider,
        )
        from opentelemetry.sdk.trace.export import (  # noqa: PLC0415
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
    except ImportError:
        logger.warning("OTel: opentelemetry packages not installed — tracing disabled.")
        return

    provider = TracerProvider()
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")

    exporter: object  # typed as object so CloudTrace/Console are both assignable
    if gcp_project:
        try:
            from opentelemetry.exporter.cloud_trace import (  # noqa: PLC0415
                CloudTraceSpanExporter,
            )
            exporter = CloudTraceSpanExporter(project_id=gcp_project)  # type: ignore[no-untyped-call]
            logger.info("OTel: Cloud Trace exporter active (project=%s).", gcp_project)
        except Exception:  # noqa: BLE001
            logger.warning("OTel: Cloud Trace unavailable — falling back to console exporter.")
            exporter = ConsoleSpanExporter()
    else:
        exporter = ConsoleSpanExporter()
        logger.info("OTel: console span exporter active (set GOOGLE_CLOUD_PROJECT for GCP).")

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(application)
    logger.info("OTel: FastAPI instrumented successfully.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Registers all routers (auth, events, tasks, slack), attaches the
    telemetry middleware, adds the ``/metrics`` endpoint, configures
    OpenTelemetry tracing, and registers exception handlers.

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
    # Middleware (registered before routes so every request is timed)
    # ------------------------------------------------------------------

    application.add_middleware(TelemetryMiddleware)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @application.get("/health", tags=["health"], summary="Health check")
    def health() -> HealthResponse:
        """Return HTTP 200 to confirm the service is running."""
        return HealthResponse(status="ok")

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @application.get("/metrics", tags=["observability"], summary="Service metrics")
    def metrics() -> dict[str, Any]:
        """Return request success/failure counters and average latency (ms)."""
        return _metrics.snapshot()

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------

    application.include_router(auth_router)
    application.include_router(event_router)
    application.include_router(task_router)
    application.include_router(slack_router)

    # ------------------------------------------------------------------
    # Exception Handlers
    # ------------------------------------------------------------------

    @application.exception_handler(EventNotFoundError)
    async def event_not_found_exception_handler(
        _: Request, exc: EventNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"message": str(exc)})

    @application.exception_handler(TaskNotFoundError)
    async def task_not_found_exception_handler(
        _: Request, exc: TaskNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"message": str(exc)})

    @application.exception_handler(CalendarOperationError)
    async def calendar_operation_exception_handler(
        _: Request, exc: CalendarOperationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"message": str(exc)})

    # ------------------------------------------------------------------
    # OpenTelemetry tracing (after routes are registered)
    # ------------------------------------------------------------------

    _configure_tracing(application)

    return application


# Module-level app instance used by uvicorn:
#   uv run uvicorn calendar_client_service.app:app --reload --port 8000
app = create_app()
