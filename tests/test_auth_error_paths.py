"""Comprehensive error path coverage for auth.py dual-auth architecture.

Tests cover:
- Tweepy mode: missing credentials, import errors, get_me failures
- OAuth2 mode: PKCE flow, token refresh, file I/O, code exchange errors
- Mode validation and from_env factory
- me_id caching for both modes
"""

from __future__ import annotations

import json
import os
import types
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.auth import UnifiedAuth

# ==================== Mode Validation Tests ====================


def test_invalid_mode_from_env():
    """Test from_env with invalid X_AUTH_MODE."""
    with patch.dict(os.environ, {"X_AUTH_MODE": "invalid_mode"}):
        with pytest.raises(ValueError, match="Invalid X_AUTH_MODE"):
            UnifiedAuth.from_env()


def test_from_env_defaults_to_tweepy():
    """Test from_env defaults to tweepy when X_AUTH_MODE not set."""
    # Don't set X_AUTH_MODE at all, let from_env use default
    env_vars = {
        "X_API_KEY": "test_key",
        "X_API_SECRET": "test_secret",
        "X_ACCESS_TOKEN": "test_token",
        "X_ACCESS_SECRET": "test_access_secret",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        # Remove X_AUTH_MODE if present
        if "X_AUTH_MODE" in os.environ:
            del os.environ["X_AUTH_MODE"]

        with patch("src.auth.tweepy") as mock_tweepy:
            mock_tweepy.Client = MagicMock()
            auth = UnifiedAuth.from_env()
            assert auth.mode == "tweepy"


def test_from_env_oauth2_mode():
    """Test from_env with OAuth2 mode."""
    with patch.dict(
        os.environ,
        {
            "X_AUTH_MODE": "oauth2",
            "X_CLIENT_ID": "test_client_id",
            "X_CLIENT_SECRET": "test_secret",
        },
    ):
        auth = UnifiedAuth.from_env()
        assert auth.mode == "oauth2"
        assert auth.client_id == "test_client_id"
        assert auth.client_secret == "test_secret"


# ==================== Tweepy Mode Error Tests ====================


def test_tweepy_mode_missing_credentials():
    """Test get_tweepy_client with missing credentials."""
    with patch("src.auth.tweepy") as mock_tweepy:
        mock_tweepy.Client = MagicMock()
        auth = UnifiedAuth(mode="tweepy", api_key="key", api_secret="secret")
        # Missing access_token and access_secret
        with pytest.raises(RuntimeError, match="Missing Tweepy credentials"):
            auth.get_tweepy_client()


def test_tweepy_not_installed():
    """Test Tweepy methods when tweepy is not installed."""
    with patch("src.auth.tweepy", None):
        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="secret",
        )
        with pytest.raises(RuntimeError, match="Tweepy not installed"):
            auth.get_tweepy_client()


def test_tweepy_api_not_installed():
    """Test get_tweepy_api when tweepy is not installed."""
    with patch("src.auth.tweepy", None):
        auth = UnifiedAuth(mode="tweepy")
        with pytest.raises(RuntimeError, match="Tweepy not installed"):
            auth.get_tweepy_api()


def test_tweepy_api_missing_credentials():
    """Test get_tweepy_api with missing credentials."""
    mock_tweepy = types.SimpleNamespace(
        Client=MagicMock(),
        OAuth1UserHandler=MagicMock(),
        API=MagicMock(),
    )
    with patch("src.auth.tweepy", mock_tweepy):
        auth = UnifiedAuth(mode="tweepy", api_key="key")
        with pytest.raises(RuntimeError, match="Missing Tweepy credentials"):
            auth.get_tweepy_api()


def test_tweepy_get_me_returns_none():
    """Test get_me_user_id when Tweepy returns None."""
    mock_tweepy = types.SimpleNamespace(Client=MagicMock())
    mock_client = MagicMock()
    mock_client.get_me.return_value.data = None
    mock_tweepy.Client.return_value = mock_client

    with patch("src.auth.tweepy", mock_tweepy):
        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="secret",
        )
        with pytest.raises(RuntimeError, match="Unable to fetch authenticated user"):
            auth.get_me_user_id()


def test_tweepy_mode_wrong_method():
    """Test OAuth2 methods called in Tweepy mode."""
    auth = UnifiedAuth(mode="tweepy")
    with pytest.raises(RuntimeError, match="Not in OAuth 2.0 mode"):
        auth.authorize_oauth2(["tweet.read"])


# ==================== OAuth2 Mode Error Tests ====================


def test_oauth2_wrong_mode_get_tweepy():
    """Test get_tweepy_client in OAuth2 mode."""
    auth = UnifiedAuth(mode="oauth2")
    with pytest.raises(RuntimeError, match="Not in Tweepy mode"):
        auth.get_tweepy_client()


def test_oauth2_wrong_mode_get_api():
    """Test get_tweepy_api in OAuth2 mode."""
    auth = UnifiedAuth(mode="oauth2")
    with pytest.raises(RuntimeError, match="Not in Tweepy mode"):
        auth.get_tweepy_api()


def test_oauth2_no_access_token_available():
    """Test get_oauth2_access_token with no token available."""
    auth = UnifiedAuth(mode="oauth2", token_file="nonexistent.json")
    with pytest.raises(RuntimeError, match="No access token available"):
        auth.get_oauth2_access_token()


def test_oauth2_refresh_no_refresh_token():
    """Test refresh_oauth2_token with no refresh token."""
    auth = UnifiedAuth(mode="oauth2", token_file="nonexistent.json")
    with pytest.raises(RuntimeError, match="No refresh token available"):
        auth.refresh_oauth2_token()


def test_oauth2_authorize_no_code_received():
    """Test authorize_oauth2 when callback receives no code."""
    with patch("src.auth.webbrowser.open"), patch("src.auth.HTTPServer") as mock_server:
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance

        # Simulate no auth code received
        with patch("src.auth.OAuthCallbackHandler") as mock_handler:
            mock_handler.auth_code = None

            auth = UnifiedAuth(mode="oauth2", client_id="test_id", redirect_uri="http://localhost:8080/callback")

            with pytest.raises(RuntimeError, match="Authorization failed: no code received"):
                auth.authorize_oauth2(["tweet.read"])


def test_oauth2_exchange_code_with_client_secret():
    """Test _exchange_code with client_secret present."""

    class FakeResponse:
        def __init__(self, json_data):
            self._json = json_data
            self.status_code = 200

        def json(self):
            return self._json

        def raise_for_status(self):
            pass

    token_data = {"access_token": "test_token", "refresh_token": "test_refresh"}

    with (
        patch("src.auth.requests.post", return_value=FakeResponse(token_data)) as mock_post,
        patch.object(UnifiedAuth, "_save_tokens") as mock_save,
    ):
        auth = UnifiedAuth(
            mode="oauth2",
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080/callback",
        )
        result = auth._exchange_code("test_code", "test_verifier")

        assert result == "test_token"
        assert auth.oauth2_access_token == "test_token"
        assert auth.oauth2_refresh_token == "test_refresh"

        # Verify client_secret was used in auth
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["auth"] == ("test_id", "test_secret")
        mock_save.assert_called_once_with(token_data)


def test_oauth2_exchange_code_without_client_secret():
    """Test _exchange_code without client_secret."""

    class FakeResponse:
        def __init__(self, json_data):
            self._json = json_data

        def json(self):
            return self._json

        def raise_for_status(self):
            pass

    token_data = {"access_token": "test_token"}

    with (
        patch("src.auth.requests.post", return_value=FakeResponse(token_data)) as mock_post,
        patch.object(UnifiedAuth, "_save_tokens"),
    ):
        auth = UnifiedAuth(mode="oauth2", client_id="test_id", redirect_uri="http://localhost:8080/callback")
        result = auth._exchange_code("test_code", "test_verifier")

        assert result == "test_token"
        # Verify no auth parameter was passed
        assert "auth" not in mock_post.call_args.kwargs


def test_oauth2_refresh_with_client_secret():
    """Test refresh_oauth2_token with client_secret."""

    class FakeResponse:
        def __init__(self, json_data):
            self._json = json_data

        def json(self):
            return self._json

        def raise_for_status(self):
            pass

    token_data = {"access_token": "new_token", "refresh_token": "new_refresh"}

    with (
        patch("src.auth.requests.post", return_value=FakeResponse(token_data)) as mock_post,
        patch.object(UnifiedAuth, "_save_tokens"),
    ):
        auth = UnifiedAuth(mode="oauth2", client_id="test_id", client_secret="test_secret")
        auth.oauth2_refresh_token = "old_refresh"

        result = auth.refresh_oauth2_token()

        assert result == "new_token"
        assert auth.oauth2_access_token == "new_token"
        mock_post.assert_called_once()
        assert mock_post.call_args.kwargs["auth"] == ("test_id", "test_secret")


def test_oauth2_refresh_without_client_secret():
    """Test refresh_oauth2_token without client_secret."""

    class FakeResponse:
        def __init__(self, json_data):
            self._json = json_data

        def json(self):
            return self._json

        def raise_for_status(self):
            pass

    token_data = {"access_token": "new_token"}

    with (
        patch("src.auth.requests.post", return_value=FakeResponse(token_data)) as mock_post,
        patch.object(UnifiedAuth, "_save_tokens"),
    ):
        auth = UnifiedAuth(mode="oauth2", client_id="test_id")
        auth.oauth2_refresh_token = "old_refresh"

        result = auth.refresh_oauth2_token()

        assert result == "new_token"
        assert "auth" not in mock_post.call_args.kwargs


def test_oauth2_refresh_preserves_refresh_token():
    """Test that refresh keeps old refresh_token if new one not provided."""

    class FakeResponse:
        def json(self):
            return {"access_token": "new_access"}

        def raise_for_status(self):
            pass

    with patch("src.auth.requests.post", return_value=FakeResponse()), patch.object(UnifiedAuth, "_save_tokens"):
        auth = UnifiedAuth(mode="oauth2", client_id="test_id")
        auth.oauth2_refresh_token = "old_refresh"

        auth.refresh_oauth2_token()

        # Refresh token should be preserved
        assert auth.oauth2_refresh_token == "old_refresh"


# ==================== File I/O Tests ====================


def test_save_tokens():
    """Test _save_tokens writes to file."""
    token_data = {"access_token": "test", "refresh_token": "refresh"}

    with patch("builtins.open", mock_open()) as mock_file:
        auth = UnifiedAuth(mode="oauth2", token_file="test.json")
        auth._save_tokens(token_data)

        mock_file.assert_called_once_with("test.json", "w")
        handle = mock_file()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        assert "test" in written_data
        assert "refresh" in written_data


def test_load_tokens_file_exists():
    """Test _load_tokens loads from existing file."""
    token_data = {"access_token": "loaded_token", "refresh_token": "loaded_refresh"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(token_data))),
    ):
        auth = UnifiedAuth(mode="oauth2", token_file="test.json")
        auth._load_tokens()

        assert auth.oauth2_access_token == "loaded_token"
        assert auth.oauth2_refresh_token == "loaded_refresh"


def test_load_tokens_file_not_exists():
    """Test _load_tokens when file doesn't exist."""
    with patch("os.path.exists", return_value=False):
        auth = UnifiedAuth(mode="oauth2", token_file="missing.json")
        auth._load_tokens()

        # Should not raise, tokens should remain None
        assert auth.oauth2_access_token is None
        assert auth.oauth2_refresh_token is None


def test_get_oauth2_access_token_loads_from_file():
    """Test get_oauth2_access_token loads from file when token not in memory."""
    token_data = {"access_token": "file_token", "refresh_token": "file_refresh"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(token_data))),
    ):
        auth = UnifiedAuth(mode="oauth2", token_file="test.json")

        result = auth.get_oauth2_access_token()

        assert result == "file_token"
        assert auth.oauth2_access_token == "file_token"


def test_get_oauth2_access_token_returns_cached():
    """Test get_oauth2_access_token returns cached token."""
    auth = UnifiedAuth(mode="oauth2")
    auth.oauth2_access_token = "cached_token"

    result = auth.get_oauth2_access_token()

    assert result == "cached_token"


# ==================== me_id Caching Tests ====================


def test_tweepy_me_id_caching():
    """Test get_me_user_id caches result in Tweepy mode."""
    mock_tweepy = types.SimpleNamespace(Client=MagicMock())
    mock_user = types.SimpleNamespace(id="12345")
    mock_client = MagicMock()
    mock_client.get_me.return_value.data = mock_user
    mock_tweepy.Client.return_value = mock_client

    with patch("src.auth.tweepy", mock_tweepy):
        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="secret",
        )

        # First call
        result1 = auth.get_me_user_id()
        assert result1 == "12345"

        # Second call should use cache
        result2 = auth.get_me_user_id()
        assert result2 == "12345"

        # get_me should only be called once
        assert mock_client.get_me.call_count == 1


def test_oauth2_me_id_caching():
    """Test get_me_user_id caches result in OAuth2 mode."""

    class FakeResponse:
        def json(self):
            return {"data": {"id": "67890"}}

        def raise_for_status(self):
            pass

    with patch("src.auth.requests.get", return_value=FakeResponse()):
        auth = UnifiedAuth(mode="oauth2", client_id="test_id")
        auth.oauth2_access_token = "test_token"

        # First call
        result1 = auth.get_me_user_id()
        assert result1 == "67890"

        # Second call should use cache
        result2 = auth.get_me_user_id()
        assert result2 == "67890"


# ==================== PKCE Flow Tests ====================


def test_generate_pkce_pair():
    """Test PKCE verifier and challenge generation."""
    auth = UnifiedAuth(mode="oauth2", client_id="test_id")
    verifier, challenge = auth._generate_pkce_pair()

    # Verifier should be URL-safe base64, ~43 chars
    assert isinstance(verifier, str)
    assert len(verifier) >= 40
    assert all(c.isalnum() or c in "-_" for c in verifier)

    # Challenge should be URL-safe base64, ~43 chars
    assert isinstance(challenge, str)
    assert len(challenge) >= 40
    assert all(c.isalnum() or c in "-_" for c in challenge)

    # Verify challenge is SHA256(verifier)
    import base64
    import hashlib

    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    assert challenge == expected
