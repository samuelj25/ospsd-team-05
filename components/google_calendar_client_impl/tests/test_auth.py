"""Tests for the Google OAuth authentication manager."""

# ruff: noqa: S105, S106  # Ignore hardcoded credential strings in tests

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


# ---------------------------------------------------------------------------
# WebOAuthManager tests
# ---------------------------------------------------------------------------

from google_calendar_client_impl.auth import WebOAuthManager  # noqa: E402


class TestWebOAuthManagerInit:
    """Verify constructor resolution order and validation."""

    def test_raises_when_client_id_missing(self) -> None:
        """ValueError when no client_id and env var not set."""
        with pytest.raises(ValueError, match="client_id"):
            WebOAuthManager(client_id="", client_secret="secret")

    def test_raises_when_client_secret_missing(self) -> None:
        """ValueError when no client_secret and env var not set."""
        with pytest.raises(ValueError, match="client_secret"):
            WebOAuthManager(client_id="id", client_secret="")

    def test_reads_from_env_vars(self) -> None:
        """Falls back to environment variables when kwargs are omitted."""
        with patch.dict(
            "os.environ",
            {
                "GOOGLE_OAUTH_CLIENT_ID": "env-id",
                "GOOGLE_OAUTH_CLIENT_SECRET": "env-secret",
                "OAUTH_REDIRECT_URI": "https://example.com/callback",
            },
        ):
            mgr = WebOAuthManager()
        assert mgr.client_id == "env-id"
        assert mgr.client_secret == "env-secret"
        assert mgr.redirect_uri == "https://example.com/callback"

    def test_kwargs_take_precedence_over_env(self) -> None:
        """Explicit kwargs override environment variables."""
        with patch.dict(
            "os.environ",
            {"GOOGLE_OAUTH_CLIENT_ID": "env-id", "GOOGLE_OAUTH_CLIENT_SECRET": "env-secret"},
        ):
            mgr = WebOAuthManager(client_id="kwarg-id", client_secret="kwarg-secret")
        assert mgr.client_id == "kwarg-id"
        assert mgr.client_secret == "kwarg-secret"

    def test_default_redirect_uri(self) -> None:
        """Default redirect URI points to localhost when env var is absent."""
        with patch.dict("os.environ", {}, clear=False):
            # Remove if present
            env = {k: v for k, v in __import__("os").environ.items()
                   if k != "OAUTH_REDIRECT_URI"}
            with patch.dict("os.environ", env, clear=True):
                mgr = WebOAuthManager(client_id="id", client_secret="secret")
        assert "localhost" in mgr.redirect_uri


class TestWebOAuthManagerGetAuthorizationUrl:
    """get_authorization_url delegates to google_auth_oauthlib Flow."""

    def test_returns_url_and_state(self) -> None:
        """Returns a URL and state string."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("https://google.com/auth", "state-abc")

        with patch.object(mgr, "_build_flow", return_value=mock_flow):
            url, state = mgr.get_authorization_url(state="state-abc")

        assert url == "https://google.com/auth"
        assert state == "state-abc"
        mock_flow.authorization_url.assert_called_once_with(
            access_type="offline",
            include_granted_scopes="true",
            state="state-abc",
            prompt="consent",
        )

    def test_generates_state_when_none_given(self) -> None:
        """Auto-generates a CSRF state token when caller passes None."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("https://google.com/auth", "generated")

        with patch.object(mgr, "_build_flow", return_value=mock_flow):
            url, state = mgr.get_authorization_url()

        assert url == "https://google.com/auth"
        assert state == "generated"
        # Verify state was generated and passed through
        _, kwargs = mock_flow.authorization_url.call_args
        assert "state" in kwargs


class TestWebOAuthManagerHandleCallback:
    """handle_callback exchanges a code for a session."""

    def test_stores_session_and_returns_id(self) -> None:
        """A unique session ID is generated and credentials are stored."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mock_creds = MagicMock()
        mock_flow = MagicMock()
        mock_flow.credentials = mock_creds

        with patch.object(mgr, "_build_flow", return_value=mock_flow):
            session_id, returned_creds = mgr.handle_callback(code="auth-code")

        mock_flow.fetch_token.assert_called_once_with(code="auth-code")
        assert returned_creds is mock_creds
        assert session_id in mgr._sessions  # noqa: SLF001
        assert mgr._sessions[session_id] is mock_creds  # noqa: SLF001

    def test_each_callback_gets_unique_session(self) -> None:
        """Two callbacks produce two different session IDs."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mock_flow = MagicMock()
        mock_flow.credentials = MagicMock()

        with patch.object(mgr, "_build_flow", return_value=mock_flow):
            sid1, _ = mgr.handle_callback(code="code-1")
            sid2, _ = mgr.handle_callback(code="code-2")

        assert sid1 != sid2


class TestWebOAuthManagerGetCredentials:
    """get_credentials retrieves stored sessions."""

    def test_returns_credentials_for_known_session(self) -> None:
        """Returns the stored creds when the session exists."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mock_creds = MagicMock()
        mgr._sessions["existing-session"] = mock_creds  # noqa: SLF001

        result = mgr.get_credentials("existing-session")
        assert result is mock_creds

    def test_returns_none_for_unknown_session(self) -> None:
        """Returns None when no session exists."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        assert mgr.get_credentials("nonexistent") is None


class TestWebOAuthManagerRevokeSession:
    """revoke_session removes a session."""

    def test_removes_existing_session(self) -> None:
        """Session is removed from the store."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mgr._sessions["to-remove"] = MagicMock()  # noqa: SLF001

        mgr.revoke_session("to-remove")
        assert "to-remove" not in mgr._sessions  # noqa: SLF001

    def test_revoke_nonexistent_session_is_noop(self) -> None:
        """Revoking a session that doesn't exist does not raise."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mgr.revoke_session("does-not-exist")  # should not raise


class TestWebOAuthManagerIsAuthenticated:
    """is_authenticated checks session presence."""

    def test_returns_true_for_active_session(self) -> None:
        """Returns True when the session exists."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        mgr._sessions["active"] = MagicMock()  # noqa: SLF001
        assert mgr.is_authenticated("active") is True

    def test_returns_false_for_missing_session(self) -> None:
        """Returns False when the session does not exist."""
        mgr = WebOAuthManager(client_id="id", client_secret="secret")
        assert mgr.is_authenticated("ghost") is False
