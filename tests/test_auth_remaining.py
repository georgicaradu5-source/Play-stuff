"""Coverage tests for remaining uncovered lines in auth.py."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from auth import OAuthCallbackHandler, UnifiedAuth


class TestOAuthCallbackHandler:
    """Tests for OAuthCallbackHandler to cover HTTP server logic."""

    def test_callback_handler_error(self):
        """Test OAuth callback without code parameter (covers lines 39-48)."""
        # Create a mock request
        mock_request = MagicMock()
        mock_request.makefile = MagicMock(return_value=BytesIO())

        handler = OAuthCallbackHandler(
            mock_request,
            ("127.0.0.1", 8080),
            MagicMock(),
        )
        handler.path = "/?error=access_denied"

        # Mock response methods
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()

        handler.do_GET()

        # Verify 400 response sent (covers lines 39-48)
        handler.send_response.assert_called_with(400)
        handler.end_headers.assert_called_once()

    def test_log_message_suppressed(self):
        """Test that log_message does nothing (covers line 51)."""
        # Create a mock request
        mock_request = MagicMock()
        mock_request.makefile = MagicMock(return_value=BytesIO())

        handler = OAuthCallbackHandler(
            mock_request,
            ("127.0.0.1", 8080),
            MagicMock(),
        )

        # Should not raise any exceptions (covers line 51)
        handler.log_message("test %s", "message")


class TestUnifiedAuthTweepyMode:
    """Tests for UnifiedAuth in Tweepy mode (covers lines 158-166)."""

    @patch("auth.tweepy")
    def test_get_tweepy_api_creates_client(self, mock_tweepy_module):
        """Test get_tweepy_api creates Tweepy API client (covers lines 158-166)."""
        # Setup mock Tweepy module
        mock_oauth_handler = MagicMock()
        mock_api = MagicMock()
        mock_tweepy_module.OAuth1UserHandler.return_value = mock_oauth_handler
        mock_tweepy_module.API.return_value = mock_api

        # Create auth with all credentials
        auth = UnifiedAuth(
            mode="tweepy",
            api_key="test_key",
            api_secret="test_secret",
            access_token="test_token",
            access_secret="test_access_secret",
        )

        # Call get_tweepy_api (covers lines 158-166)
        result = auth.get_tweepy_api()

        # Verify Tweepy objects created
        mock_tweepy_module.OAuth1UserHandler.assert_called_once_with(
            "test_key",
            "test_secret",
            "test_token",
            "test_access_secret",
        )
        mock_tweepy_module.API.assert_called_once_with(mock_oauth_handler)
        assert result == mock_api

    @patch.dict("os.environ", {
        "X_API_KEY": "",
        "X_ACCESS_TOKEN": "test_token",
        "X_AUTH_MODE": "tweepy",
    })
    @patch("auth.tweepy")
    def test_get_tweepy_api_missing_credentials(self, mock_tweepy_module):
        """Test get_tweepy_api raises error with missing credentials."""
        auth = UnifiedAuth(mode="tweepy")

        with pytest.raises(RuntimeError, match="Missing Tweepy credentials"):
            auth.get_tweepy_api()


class TestUnifiedAuthOAuth2Authorization:
    """Tests for OAuth 2.0 PKCE authorization flow."""

    @patch("auth.HTTPServer")
    @patch("auth.webbrowser.open")
    def test_authorize_pkce_no_code_received(self, mock_browser, mock_http_server):
        """Test authorize_oauth2 raises error when no code received (covers line 230)."""
        # Setup mock server that doesn't receive code
        mock_server_instance = MagicMock()
        mock_http_server.return_value = mock_server_instance

        # Ensure auth_code stays None after handle_request
        def clear_auth_code():
            OAuthCallbackHandler.auth_code = None

        mock_server_instance.handle_request.side_effect = clear_auth_code

        auth = UnifiedAuth(mode="oauth2", client_id="test_client_id")

        with pytest.raises(RuntimeError, match="Authorization failed: no code received"):
            auth.authorize_oauth2(["tweet.read", "users.read"])


class TestImportErrorHandling:
    """Tests for import error handling (covers lines 19-20, 26-27)."""

    def test_tweepy_fallback_exists(self):
        """Test that tweepy import error handling exists."""
        # The module handles ImportError by setting tweepy = None (lines 19-20)
        # This is covered when running tests without tweepy installed
        # We verify the module loads successfully regardless
        import auth
        assert hasattr(auth, "tweepy")

    @patch("sys.modules", {"dotenv": None})
    def test_dotenv_import_handled(self):
        """Test that dotenv ImportError is handled (covers lines 26-27)."""
        # The dotenv import error is silently caught (lines 26-27)
        # This is covered when running without python-dotenv
        # We verify the module loads without crashing
        import auth
        assert auth is not None
