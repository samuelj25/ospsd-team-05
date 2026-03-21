"""Smoke tests for the generated client."""

from unittest.mock import MagicMock, patch
import pytest
import httpx

from calendar_client_service_api_client.api.auth import auth_status_auth_status_get
from calendar_client_service_api_client.api.health import health_health_get
from calendar_client_service_api_client.client import Client


@pytest.mark.parametrize(
    ("endpoint_method", "expected_status"),
    [
        (health_health_get.sync, 200),
        (auth_status_auth_status_get.sync, 200),
    ]
)
def test_smoke_endpoints(endpoint_method, expected_status) -> None:
    """Parameterized smoke test ensuring core client functions are importable and callable."""
    client = Client(base_url="http://testserver", cookies={"session_id": "fake_cookie"})
    
    with patch("httpx.Client.request") as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = expected_status
        mock_response.content = b'{"status": "ok", "authenticated": true, "session_id": "fake"}'
        mock_response.json.return_value = {"status": "ok", "authenticated": True, "session_id": "fake"}
        mock_response.headers = httpx.Headers()
        mock_request.return_value = mock_response
        
        response = endpoint_method(client=client)
        assert response is not None
        mock_request.assert_called_once()
