"""
Pytest config for E2E tests.

Starts the FastAPI calendar-client service as a subprocess on a free port,
waits until it is healthy, then yields a ``ServiceAdapterClient`` that speaks
to the server over HTTP.  This demonstrates location transparency: the test
bodies talk through the ``calendar_client_api.Client`` interface without
knowing they are crossing an HTTP boundary.

Session bootstrapping (Option B — env-var pre-load):
    The subprocess is started with ``E2E_SESSION_ID=e2e-session`` in its
    environment.  The service's ``get_oauth_manager()`` detects this variable
    and calls ``seed_session_from_token_file("e2e-session")`` on first use,
    loading credentials from the local ``token.json`` (path controlled by
    ``GOOGLE_OAUTH_TOKEN_PATH``).  The adapter client is then constructed with
    the same ``session_id`` value.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


import httpx
import pytest
from calendar_client_adapter.adapter import ServiceAdapterClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_E2E_SESSION_ID = "e2e-session"
_STARTUP_TIMEOUT_S = 15  # seconds to wait for the server to become healthy
_POLL_INTERVAL_S = 0.3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_free_port() -> int:
    """Return a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        assert isinstance(port, int)
        return port


def _wait_for_health(base_url: str, timeout: float = _STARTUP_TIMEOUT_S) -> None:
    """Poll *base_url*/health until 200 or *timeout* seconds elapse."""
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{base_url}/health", timeout=2)
            if resp.status_code == 200:  # noqa: PLR2004
                return
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
        time.sleep(_POLL_INTERVAL_S)

    msg = f"Server at {base_url} did not become healthy within {timeout}s."
    if last_exc:
        msg += f" Last error: {last_exc}"
    pytest.fail(msg)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def live_client() -> Generator[ServiceAdapterClient, None, None]:
    """
    Spin up the FastAPI service as a subprocess and return an adapter client.

    The fixture:

    1. Verifies that ``token.json`` is present (required for credential seeding).
    2. Picks a free port and spawns ``uvicorn calendar_client_service.app:app``.
    3. Passes ``E2E_SESSION_ID`` and ``GOOGLE_OAUTH_TOKEN_PATH`` to the
       subprocess environment so the service can pre-seed its OAuth session.
    4. Polls ``/health`` until the service is ready.
    5. Returns a :class:`~calendar_client_adapter.adapter.ServiceAdapterClient`
       configured to talk to the subprocess.
    6. Terminates the subprocess after the test session ends.
    """
    token_path = os.environ.get("GOOGLE_OAUTH_TOKEN_PATH", "token.json")

    if not Path(token_path).exists():
        pytest.fail(
            f"E2E tests require a valid token file at '{token_path}'. "
            "Run the OAuth flow locally first (uv run python test_live.py) "
            "or set GOOGLE_OAUTH_TOKEN_PATH.",
        )

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    # Inherit the current process environment and layer on E2E overrides.
    env = {
        **os.environ,
        "E2E_SESSION_ID": _E2E_SESSION_ID,
        "GOOGLE_OAUTH_TOKEN_PATH": str(Path(token_path).resolve()),
    }

    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "calendar_client_service.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _wait_for_health(base_url)
        yield ServiceAdapterClient(base_url=base_url, session_id=_E2E_SESSION_ID)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
