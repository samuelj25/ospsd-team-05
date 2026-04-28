"""FastAPI application factory for the calendar client service."""

from __future__ import annotations

import logging
import os
import time
from http import HTTPStatus
from typing import TYPE_CHECKING

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
    from opentelemetry.metrics import Counter, Histogram
    from starlette.responses import Response

from opentelemetry import metrics, trace
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Telemetry: Global Instruments
# ---------------------------------------------------------------------------

_meter = metrics.get_meter("calendar_client_service")

_request_counter: Counter = _meter.create_counter(
    name="custom.googleapis.com/http/request_count",
    description="Total number of HTTP requests",
    unit="1",
)

_latency_histogram: Histogram = _meter.create_histogram(
    name="custom.googleapis.com/http/request_latency",
    description="Latency of HTTP requests",
    unit="ms",
)

# ---------------------------------------------------------------------------
# Telemetry: Latency Middleware
# ---------------------------------------------------------------------------

class TelemetryMiddleware(BaseHTTPMiddleware):
    """Records per-request wall-clock latency and pushes to OpenTelemetry."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Time the request, update OTel instruments, and forward the response."""
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000.0

        is_success = response.status_code < HTTPStatus.BAD_REQUEST
        status_category = "success" if is_success else "failure"

        attributes: dict[str, str] = {
            "status_code": str(response.status_code),
            "status_category": status_category,
            "route": request.url.path,
        }

        _request_counter.add(1, attributes)
        _latency_histogram.record(latency_ms, attributes)

        response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
        return response


# ---------------------------------------------------------------------------
# Telemetry: OpenTelemetry Setup
# ---------------------------------------------------------------------------

def _configure_telemetry(application: FastAPI) -> None:
    """Initialise OpenTelemetry tracing and metrics."""
    tracer_provider = TracerProvider()
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")

    trace_exporter: ConsoleSpanExporter | CloudTraceSpanExporter
    metrics_reader: PeriodicExportingMetricReader

    if gcp_project:
        trace_exporter = CloudTraceSpanExporter(project_id=gcp_project)  # type: ignore[no-untyped-call]
        metrics_exporter = CloudMonitoringMetricsExporter(project_id=gcp_project)
        metrics_reader = PeriodicExportingMetricReader(metrics_exporter)

        logger.info("OTel: GCP Trace & Monitoring active (project=%s).", gcp_project)
    else:
        trace_exporter = ConsoleSpanExporter()
        metrics_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        logger.info("OTel: console exporters active (set GOOGLE_CLOUD_PROJECT for GCP).")

    # Wire up tracing
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Wire up metrics
    meter_provider = MeterProvider(metric_readers=[metrics_reader])
    metrics.set_meter_provider(meter_provider)

    # Instrument FastAPI
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

    _configure_telemetry(application)

    return application


# Module-level app instance used by uvicorn:
#   uv run uvicorn calendar_client_service.app:app --reload --port 8000
app = create_app()
