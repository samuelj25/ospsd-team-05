"""Unit tests for FastAPI dependencies."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

import calendar_client_service.dependencies as deps
from calendar_client_service.dependencies import (
    get_ai_client,
    get_calendar_client,
    get_oauth_manager,
    get_slack_client,
)


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Reset singletons before each test."""
    deps._oauth_manager = None  # noqa: SLF001
    deps._ai_client = None  # noqa: SLF001
    deps._slack_client = None  # noqa: SLF001


def test_get_oauth_manager() -> None:
    """Test getting the OAuth manager singleton."""
    with patch("calendar_client_service.dependencies.WebOAuthManager") as mock_manager:
        manager = get_oauth_manager()
        assert manager == mock_manager.return_value

        # Test caching
        manager2 = get_oauth_manager()
        assert manager2 == manager
        mock_manager.assert_called_once()


def test_get_oauth_manager_with_e2e_session() -> None:
    """Test getting the OAuth manager with E2E_SESSION_ID."""
    with patch("calendar_client_service.dependencies.WebOAuthManager"), \
         patch.dict(os.environ, {"E2E_SESSION_ID": "test_session"}):
        manager = get_oauth_manager()
        manager.seed_session_from_token_file.assert_called_once_with("test_session")  # type: ignore[attr-defined]


def test_get_calendar_client_authenticated() -> None:
    """Test getting the calendar client when authenticated."""
    mock_manager = MagicMock()
    mock_manager.is_authenticated.return_value = True
    mock_manager.get_credentials.return_value = "mock_creds"

    with patch("calendar_client_service.dependencies.GoogleCalendarClient") as mock_client:
        client = get_calendar_client(mock_manager, "test_session")
        assert client == mock_client.return_value
        client.connect_with_credentials.assert_called_once_with("mock_creds")  # type: ignore[attr-defined]


def test_get_calendar_client_unauthenticated() -> None:
    """Test getting the calendar client when unauthenticated."""
    mock_manager = MagicMock()
    mock_manager.is_authenticated.return_value = False

    with pytest.raises(HTTPException) as excinfo:
        get_calendar_client(mock_manager, "test_session")

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in excinfo.value.detail


def test_get_calendar_client_no_creds() -> None:
    """Test getting the calendar client when credentials are missing."""
    mock_manager = MagicMock()
    mock_manager.is_authenticated.return_value = True
    mock_manager.get_credentials.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        get_calendar_client(mock_manager, "test_session")

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Session credentials not found" in excinfo.value.detail


def test_get_calendar_client_fallback_session() -> None:
    """Test getting the calendar client with fallback E2E_SESSION_ID."""
    mock_manager = MagicMock()
    mock_manager.is_authenticated.return_value = True
    mock_manager.get_credentials.return_value = "mock_creds"

    with patch.dict(os.environ, {"E2E_SESSION_ID": "fallback_session"}), \
         patch("calendar_client_service.dependencies.GoogleCalendarClient") as mock_client:
        client = get_calendar_client(mock_manager, None)
        assert client == mock_client.return_value
        mock_manager.is_authenticated.assert_called_once_with("fallback_session")


def test_get_ai_client() -> None:
    """Test getting the AI client singleton."""
    with patch("calendar_client_service.dependencies.GeminiAIClient") as mock_ai:
        client = get_ai_client()
        assert client == mock_ai.return_value

        client2 = get_ai_client()
        assert client2 == client
        mock_ai.assert_called_once()


def test_get_slack_client() -> None:
    """Test getting the Slack client singleton."""
    with patch("calendar_client_service.dependencies.SlackChatAdapter") as mock_slack:
        client = get_slack_client()
        assert client == mock_slack.return_value

        client2 = get_slack_client()
        assert client2 == client
        mock_slack.assert_called_once()
