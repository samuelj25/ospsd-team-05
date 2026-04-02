"""Tests for the Google OAuth authentication manager."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from google_calendar_client_impl.auth import SCOPES, get_credentials

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_creds_mock(
    *,
    valid: bool = True,
    expired: bool = False,
    has_refresh_token: bool = True,
) -> MagicMock:
    """Return a ``MagicMock`` imitating ``google.oauth2.credentials.Credentials``."""
    creds = MagicMock()
    creds.valid = valid
    creds.expired = expired
    creds.refresh_token = "fake-refresh-token" if has_refresh_token else None
    creds.to_json.return_value = json.dumps({"token": "fake"})
    return creds


def _write_dummy_token(path: Path) -> None:
    """Write a minimal JSON file that ``Credentials.from_authorized_user_file`` could read."""
    path.write_text(json.dumps({"token": "cached"}))


def _write_dummy_credentials(path: Path) -> None:
    """Write a minimal ``credentials.json`` so ``InstalledAppFlow`` can be instantiated."""
    path.write_text(json.dumps({
        "installed": {
            "client_id": "test-id",
            "client_secret": "test-secret",
            "redirect_uris": ["http://localhost"],
        },
    }))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetCredentialsLoadsExistingToken:
    """Scenario: ``token.json`` exists and the token is still valid."""

    @patch("google_calendar_client_impl.auth.Credentials")
    def test_returns_cached_credentials(
        self,
        mock_creds_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Return cached creds when token.json is valid."""
        token_path = tmp_path / "token.json"
        _write_dummy_token(token_path)

        valid_creds = _make_creds_mock(valid=True)
        mock_creds_cls.from_authorized_user_file.return_value = valid_creds

        result = get_credentials(
            credentials_path=str(tmp_path / "credentials.json"),
            token_path=str(token_path),
        )

        mock_creds_cls.from_authorized_user_file.assert_called_once_with(
            str(token_path), SCOPES,
        )
        assert result is valid_creds


class TestGetCredentialsRefreshesExpiredToken:
    """Scenario: cached token exists but is expired; refresh token available."""

    @patch("google_calendar_client_impl.auth.Request")
    @patch("google_calendar_client_impl.auth.Credentials")
    def test_refreshes_and_persists(
        self,
        mock_creds_cls: MagicMock,
        mock_request_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Refresh expired token and write it back to disk."""
        token_path = tmp_path / "token.json"
        _write_dummy_token(token_path)

        expired_creds = _make_creds_mock(valid=False, expired=True, has_refresh_token=True)
        mock_creds_cls.from_authorized_user_file.return_value = expired_creds

        result = get_credentials(
            credentials_path=str(tmp_path / "credentials.json"),
            token_path=str(token_path),
        )

        expired_creds.refresh.assert_called_once_with(mock_request_cls())
        assert result is expired_creds
        # Token should be re-persisted after refresh
        assert token_path.read_text() == expired_creds.to_json()


class TestGetCredentialsRunsFlowWhenNoToken:
    """Scenario: no ``token.json`` — must run the interactive OAuth flow."""

    @patch("google_calendar_client_impl.auth.InstalledAppFlow")
    def test_runs_flow_and_saves_token(
        self,
        mock_flow_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Run the OAuth consent flow and persist the resulting token."""
        creds_path = tmp_path / "credentials.json"
        token_path = tmp_path / "token.json"
        _write_dummy_credentials(creds_path)

        new_creds = _make_creds_mock(valid=True)
        mock_flow_instance = MagicMock()
        mock_flow_instance.run_local_server.return_value = new_creds
        mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance

        result = get_credentials(
            credentials_path=str(creds_path),
            token_path=str(token_path),
        )

        mock_flow_cls.from_client_secrets_file.assert_called_once_with(
            str(creds_path), SCOPES,
        )
        mock_flow_instance.run_local_server.assert_called_once_with(port=0)
        assert result is new_creds
        # Token should be persisted
        assert token_path.exists()
        assert token_path.read_text() == new_creds.to_json()


class TestGetCredentialsRaisesWhenNoCredentialsFile:
    """Scenario: no ``token.json`` AND no ``credentials.json`` → FileNotFoundError."""

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError when credentials.json is missing."""
        with pytest.raises(FileNotFoundError, match="client-secrets file not found"):
            get_credentials(
                credentials_path=str(tmp_path / "missing_credentials.json"),
                token_path=str(tmp_path / "token.json"),
            )


class TestGetCredentialsCustomPaths:
    """Verify that custom paths are respected over defaults."""

    @patch("google_calendar_client_impl.auth.Credentials")
    def test_uses_custom_paths(
        self,
        mock_creds_cls: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Use caller-supplied paths instead of defaults."""
        custom_token = tmp_path / "my_custom_token.json"
        _write_dummy_token(custom_token)

        valid_creds = _make_creds_mock(valid=True)
        mock_creds_cls.from_authorized_user_file.return_value = valid_creds

        result = get_credentials(
            credentials_path=str(tmp_path / "my_creds.json"),
            token_path=str(custom_token),
        )

        mock_creds_cls.from_authorized_user_file.assert_called_once_with(
            str(custom_token), SCOPES,
        )
        assert result is valid_creds


class TestGetCredentialsEnvVarFallback:
    """Verify fallback to environment variables when no explicit paths given."""

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_OAUTH_CREDENTIALS_PATH": "/custom/creds.json",
            "GOOGLE_OAUTH_TOKEN_PATH": "/custom/token.json",
        },
    )
    @patch("google_calendar_client_impl.auth.Path")
    @patch("google_calendar_client_impl.auth.Credentials")
    def test_reads_env_vars(
        self,
        mock_creds_cls: MagicMock,
        mock_path_cls: MagicMock,
    ) -> None:
        """Fall back to env vars when no explicit paths are given."""
        # Simulate token file existing and returning valid creds
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        valid_creds = _make_creds_mock(valid=True)
        mock_creds_cls.from_authorized_user_file.return_value = valid_creds

        result = get_credentials()

        # Should have used the env-var paths
        mock_creds_cls.from_authorized_user_file.assert_called_once_with(
            "/custom/token.json", SCOPES,
        )
        assert result is valid_creds
