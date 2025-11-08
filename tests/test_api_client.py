"""Tests for API client module."""

from unittest.mock import MagicMock, patch

import pytest

from api.client import APIClient


@pytest.fixture
def mock_requests():
    """Mock the requests module."""
    with patch("api.client.requests") as mock:
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock.Response = MagicMock(return_value=mock_response)
        yield mock


def test_api_client_initialization():
    """Test APIClient initialization."""
    client = APIClient(dry_run=False)
    assert client.dry_run is False

    client_dry = APIClient(dry_run=True)
    assert client_dry.dry_run is True


def test_api_client_get_dry_run(capsys):
    """Test GET request in dry-run mode."""
    client = APIClient(dry_run=True)
    headers = {"Authorization": "Bearer test_token"}
    params = {"q": "test"}

    result = client.get("https://api.example.com/test", headers, params)

    assert result == {"data": None}
    captured = capsys.readouterr()
    assert "[DRY RUN] GET" in captured.out
    assert "https://api.example.com/test" in captured.out


def test_api_client_post_dry_run(capsys):
    """Test POST request in dry-run mode."""
    client = APIClient(dry_run=True)
    headers = {"Authorization": "Bearer test_token"}
    json_body = {"text": "test"}

    result = client.post("https://api.example.com/test", headers, json_body=json_body)

    assert result == {"data": None}
    captured = capsys.readouterr()
    assert "[DRY RUN] POST" in captured.out
    assert "https://api.example.com/test" in captured.out


def test_api_client_delete_dry_run(capsys):
    """Test DELETE request in dry-run mode."""
    client = APIClient(dry_run=True)
    headers = {"Authorization": "Bearer test_token"}

    result = client.delete("https://api.example.com/test", headers)

    assert result == {"data": None}
    captured = capsys.readouterr()
    assert "[DRY RUN] DELETE" in captured.out
    assert "https://api.example.com/test" in captured.out


@patch("api.client.request_with_retries")
def test_api_client_get_live(mock_retry):
    """Test GET request in live mode."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"id": "123"}}
    mock_retry.return_value = mock_response

    client = APIClient(dry_run=False)
    headers = {"Authorization": "Bearer test_token"}
    params = {"user.fields": "id,username"}

    result = client.get("https://api.twitter.com/2/users/me", headers, params)

    assert result == {"data": {"id": "123"}}
    mock_retry.assert_called_once()
    args, kwargs = mock_retry.call_args
    assert args[0] == "GET"
    assert args[1] == "https://api.twitter.com/2/users/me"
    assert kwargs["headers"] == headers
    assert kwargs["params"] == params


@patch("api.client.request_with_retries")
def test_api_client_post_live(mock_retry):
    """Test POST request in live mode."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"id": "456", "text": "test"}}
    mock_retry.return_value = mock_response

    client = APIClient(dry_run=False)
    headers = {"Authorization": "Bearer test_token", "Content-Type": "application/json"}
    json_body = {"text": "test tweet"}

    result = client.post("https://api.twitter.com/2/tweets", headers, json_body=json_body)

    assert result == {"data": {"id": "456", "text": "test"}}
    mock_retry.assert_called_once()
    args, kwargs = mock_retry.call_args
    assert args[0] == "POST"
    assert args[1] == "https://api.twitter.com/2/tweets"
    assert kwargs["json_body"] == json_body


@patch("api.client.request_with_retries")
def test_api_client_delete_live(mock_retry):
    """Test DELETE request in live mode."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"deleted": True}}
    mock_retry.return_value = mock_response

    client = APIClient(dry_run=False)
    headers = {"Authorization": "Bearer test_token"}

    result = client.delete("https://api.twitter.com/2/tweets/123", headers)

    assert result == {"data": {"deleted": True}}
    mock_retry.assert_called_once()
    args, kwargs = mock_retry.call_args
    assert args[0] == "DELETE"
    assert args[1] == "https://api.twitter.com/2/tweets/123"


@patch("api.client.requests", None)
def test_api_client_no_requests_library():
    """Test error when requests library not installed."""
    client = APIClient(dry_run=False)
    headers = {"Authorization": "Bearer test_token"}

    with pytest.raises(RuntimeError, match="requests library not installed"):
        client.get("https://api.example.com/test", headers)

    with pytest.raises(RuntimeError, match="requests library not installed"):
        client.post("https://api.example.com/test", headers, json_body={})

    with pytest.raises(RuntimeError, match="requests library not installed"):
        client.delete("https://api.example.com/test", headers)
