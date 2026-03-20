"""Unit tests for the OAuth 2.0 auth routes."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from calendar_client_service.app import create_app
from calendar_client_service.dependencies import get_oauth_manager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_oauth_manager() -> MagicMock:
    """Return a mock WebOAuthManager."""
    mgr = MagicMock()
    mgr.get_authorization_url.return_value = ("https://google.com/auth?foo=bar", "test-state")
    mgr.is_authenticated.return_value = False
    return mgr


@pytest.fixture
def client(mock_oauth_manager: MagicMock) -> TestClient:
    """Return a TestClient with the OAuth manager dependency overridden."""
    app = create_app()
    app.dependency_overrides[get_oauth_manager] = lambda: mock_oauth_manager
    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    """Tests for the /health endpoint."""

    def test_returns_200(self, client: TestClient) -> None:
        """Health endpoint returns HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200  # noqa: PLR2004

    def test_returns_ok_status(self, client: TestClient) -> None:
        """Health endpoint returns {"status": "ok"}."""
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /auth/login
# ---------------------------------------------------------------------------


class TestAuthLogin:
    """Tests for GET /auth/login."""

    def test_redirects_to_google(self, client: TestClient) -> None:
        """Login redirects to the URL returned by get_authorization_url."""
        response = client.get("/auth/login")
        assert response.status_code == 302  # noqa: PLR2004
        assert response.headers["location"] == "https://google.com/auth?foo=bar"

    def test_calls_get_authorization_url(
        self, client: TestClient, mock_oauth_manager: MagicMock,
    ) -> None:
        """Login calls get_authorization_url once."""
        client.get("/auth/login")
        mock_oauth_manager.get_authorization_url.assert_called_once()


# ---------------------------------------------------------------------------
# /auth/callback
# ---------------------------------------------------------------------------


class TestAuthCallback:
    """Tests for GET /auth/callback."""

    def test_sets_session_cookie_on_success(
        self, client: TestClient, mock_oauth_manager: MagicMock,
    ) -> None:
        """Callback sets a session_id cookie when the code exchange succeeds."""
        mock_oauth_manager.handle_callback.return_value = ("test-session-id", MagicMock())

        response = client.get("/auth/callback", params={"code": "valid-code"})

        assert response.status_code == 200  # noqa: PLR2004
        assert "session_id" in response.cookies
        assert response.cookies["session_id"] == "test-session-id"

    def test_returns_authenticated_true_on_success(
        self, client: TestClient, mock_oauth_manager: MagicMock,
    ) -> None:
        """Callback returns authenticated=True in the body."""
        mock_oauth_manager.handle_callback.return_value = ("test-session-id", MagicMock())

        response = client.get("/auth/callback", params={"code": "valid-code"})

        data = response.json()
        assert data["authenticated"] is True
        assert data["session_id"] == "test-session-id"

    def test_returns_400_when_code_exchange_fails(
        self, client: TestClient, mock_oauth_manager: MagicMock,
    ) -> None:
        """Callback returns HTTP 400 when handle_callback raises an exception."""
        mock_oauth_manager.handle_callback.side_effect = ValueError("bad code")

        response = client.get("/auth/callback", params={"code": "bad-code"})

        assert response.status_code == 400  # noqa: PLR2004
        assert "bad code" in response.json()["detail"]


# ---------------------------------------------------------------------------
# /auth/status
# ---------------------------------------------------------------------------


class TestAuthStatus:
    """Tests for GET /auth/status."""

    def test_unauthenticated_when_no_cookie(
        self, client: TestClient, mock_oauth_manager: MagicMock,
    ) -> None:
        """Status returns authenticated=False when no session cookie is present."""
        mock_oauth_manager.is_authenticated.return_value = False

        response = client.get("/auth/status")

        assert response.status_code == 200  # noqa: PLR2004
        assert response.json()["authenticated"] is False

    def test_authenticated_when_valid_session(
        self, client: TestClient, mock_oauth_manager: MagicMock,
    ) -> None:
        """Status returns authenticated=True when a valid session cookie is present."""
        mock_oauth_manager.is_authenticated.return_value = True

        response = client.get("/auth/status", cookies={"session_id": "active-session"})

        assert response.status_code == 200  # noqa: PLR2004
        assert response.json()["authenticated"] is True


# ---------------------------------------------------------------------------
# /auth/logout
# ---------------------------------------------------------------------------


class TestAuthLogout:
    """Tests for POST /auth/logout."""

    def test_revokes_session(
        self, client: TestClient, mock_oauth_manager: MagicMock,
    ) -> None:
        """Logout calls revoke_session with the session ID from the cookie."""
        response = client.post("/auth/logout", cookies={"session_id": "my-session"})

        mock_oauth_manager.revoke_session.assert_called_once_with("my-session")
        assert response.status_code == 200  # noqa: PLR2004
        assert response.json()["authenticated"] is False

    def test_logout_without_cookie_does_not_raise(self, client: TestClient) -> None:
        """Logout without a session cookie completes without error."""
        response = client.post("/auth/logout")
        assert response.status_code == 200  # noqa: PLR2004
