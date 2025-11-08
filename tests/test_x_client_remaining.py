"""Coverage tests for remaining uncovered lines in x_client.py."""

from unittest.mock import MagicMock, patch

import pytest

from auth import UnifiedAuth
from x_client import XClient


class TestXClientTweepyMode:
    """Tests for XClient Tweepy-specific code paths."""

    @patch("auth.tweepy")
    def test_get_me_tweepy_mode(self, mock_tweepy_module):
        """Test get_me in Tweepy mode (covers lines 67-68)."""
        # Setup mock Tweepy client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = MagicMock(id=123456789, username="testuser")
        mock_client.get_me.return_value = mock_response

        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="access",
        )

        with patch.object(auth, "get_tweepy_client", return_value=mock_client):
            client = XClient(auth=auth, dry_run=False)

            result = client.get_me()

            # Verify Tweepy client was called
            mock_client.get_me.assert_called_once()
            assert result["data"]["id"] == "123456789"
            assert result["data"]["username"] == "testuser"
            assert client.me_id == "123456789"

    @patch("auth.tweepy")
    def test_get_tweet_tweepy_mode(self, mock_tweepy_module):
        """Test get_tweet in Tweepy mode (covers lines 161-163)."""
        # Setup mock Tweepy client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = MagicMock(id=999, text="Test tweet")
        mock_client.get_tweet.return_value = mock_response

        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="access",
        )

        with patch.object(auth, "get_tweepy_client", return_value=mock_client):
            client = XClient(auth=auth, dry_run=False)

            result = client.get_tweet("999")

            # Verify Tweepy client was called
            mock_client.get_tweet.assert_called_once_with("999")
            assert result["data"]["id"] == "999"
            assert result["data"]["text"] == "Test tweet"

    @patch("auth.tweepy")
    def test_create_post_tweepy_mode(self, mock_tweepy_module):
        """Test create_post in Tweepy mode (covers lines 189-190)."""
        # Setup mock Tweepy client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"id": "post123"}
        mock_client.create_tweet.return_value = mock_response

        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="access",
        )

        with patch.object(auth, "get_tweepy_client", return_value=mock_client):
            client = XClient(auth=auth, dry_run=False)

            result = client.create_post("Test post")

            # Verify Tweepy client was called
            mock_client.create_tweet.assert_called_once_with(text="Test post")
            assert result["data"]["id"] == "post123"

    @patch("auth.tweepy")
    def test_delete_post_tweepy_mode(self, mock_tweepy_module):
        """Test delete_post in Tweepy mode (covers lines 320-321)."""
        # Setup mock Tweepy client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"deleted": True}
        mock_client.delete_tweet.return_value = mock_response

        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="access",
        )

        with patch.object(auth, "get_tweepy_client", return_value=mock_client):
            client = XClient(auth=auth, dry_run=False)

            result = client.delete_post("tweet123")

            # Verify Tweepy client was called
            mock_client.delete_tweet.assert_called_once_with("tweet123")
            assert result is True

    @patch("auth.tweepy")
    def test_unlike_post_tweepy_mode(self, mock_tweepy_module):
        """Test unlike_post in Tweepy mode (covers lines 385-386)."""
        # Setup mock Tweepy client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"liked": False}
        mock_client.unlike.return_value = mock_response

        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="access",
        )

        with patch.object(auth, "get_tweepy_client", return_value=mock_client):
            client = XClient(auth=auth, dry_run=False)
            client.me_id = "user123"

            result = client.unlike_post("tweet123")

            # Verify Tweepy client was called
            mock_client.unlike.assert_called_once_with("tweet123")
            # Unlike returns False when liked=False (tweet is no longer liked)
            assert result is False

    @patch("auth.tweepy")
    def test_unretweet_tweepy_mode(self, mock_tweepy_module):
        """Test unretweet in Tweepy mode (covers lines 449-450)."""
        # Setup mock Tweepy client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = {"retweeted": False}
        mock_client.unretweet.return_value = mock_response

        auth = UnifiedAuth(
            mode="tweepy",
            api_key="key",
            api_secret="secret",
            access_token="token",
            access_secret="access",
        )

        with patch.object(auth, "get_tweepy_client", return_value=mock_client):
            client = XClient(auth=auth, dry_run=False)
            client.me_id = "user123"

            result = client.unretweet("tweet123")

            # Verify Tweepy client was called
            mock_client.unretweet.assert_called_once_with("tweet123")
            assert result is True


class TestXClientOAuth2Paths:
    """Tests for OAuth2-specific code paths."""

    @patch("x_client.request_with_retries")
    def test_search_recent_with_pagination(self, mock_request_with_retries):
        """Test search_recent with pagination (covers line 291)."""
        # Setup mock responses for pagination
        # First response with next_token
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {
            "data": [{"id": "1", "text": "Tweet 1", "author_id": "user1", "public_metrics": {}}],
            "meta": {"next_token": "token456"},
            "includes": {"users": [{"id": "user1", "username": "user1"}]},
        }
        # Second response without next_token (end of results)
        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = {
            "data": [{"id": "2", "text": "Tweet 2", "author_id": "user2", "public_metrics": {}}],
            "meta": {},
            "includes": {"users": [{"id": "user2", "username": "user2"}]},
        }
        mock_request_with_retries.side_effect = [mock_response_1, mock_response_2]

        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        auth.access_token = "access_token"

        client = XClient(auth=auth, dry_run=False)

        result = client.search_recent("test query", max_results=200)

        # Verify request_with_retries was called twice (pagination)
        assert mock_request_with_retries.call_count == 2
        # Second call should include next_token parameter
        second_call_kwargs = mock_request_with_retries.call_args_list[1][1]
        assert second_call_kwargs["params"]["next_token"] == "token456"
        
        # Verify results
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    @patch("x_client.requests", None)
    def test_create_post_oauth2_no_requests_library(self):
        """Test create_post OAuth2 mode without requests library (covers line 237)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        auth.access_token = "access_token"

        client = XClient(auth=auth, dry_run=False)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.create_post("Test post")

    @patch("x_client.requests", None)
    def test_delete_post_oauth2_no_requests_library(self):
        """Test delete_post OAuth2 mode without requests library (covers line 351)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        auth.access_token = "access_token"

        client = XClient(auth=auth, dry_run=False)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.delete_post("tweet123")

    @patch("x_client.requests", None)
    def test_unlike_post_oauth2_no_requests_library(self):
        """Test unlike_post OAuth2 mode without requests library (covers line 415)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        auth.access_token = "access_token"

        client = XClient(auth=auth, dry_run=False)
        client.me_id = "user123"

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.unlike_post("tweet123")

    @patch("x_client.requests", None)
    def test_unretweet_oauth2_no_requests_library(self):
        """Test unretweet OAuth2 mode without requests library (covers line 478)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        auth.access_token = "access_token"

        client = XClient(auth=auth, dry_run=False)
        client.me_id = "user123"

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.unretweet("tweet123")


class TestXClientDryRunPaths:
    """Tests for dry-run print statements."""

    def test_get_me_dry_run(self):
        """Test get_me dry-run mode (covers lines 57-58)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        client = XClient(auth=auth, dry_run=True)

        result = client.get_me()

        assert result["data"]["id"] == "dummy_user_id"
        assert result["data"]["username"] == "dummy_user"

    def test_get_tweet_dry_run(self):
        """Test get_tweet dry-run mode (covers lines 150-151)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        client = XClient(auth=auth, dry_run=True)

        result = client.get_tweet("123")

        assert result["data"]["id"] == "123"
        assert result["data"]["text"] == "[dry-run]"

    def test_create_post_dry_run(self):
        """Test create_post dry-run mode (covers line 461)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        client = XClient(auth=auth, dry_run=True)

        result = client.create_post("Test post")

        assert result["data"]["id"] == "dummy_post_id"
        assert result["data"]["text"] == "Test post"

    def test_delete_post_dry_run(self):
        """Test delete_post dry-run mode (covers line 516)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        client = XClient(auth=auth, dry_run=True)

        result = client.delete_post("123")

        assert result is True

    def test_unlike_post_dry_run(self):
        """Test unlike_post dry-run mode (covers line 517)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        client = XClient(auth=auth, dry_run=True)

        result = client.unlike_post("123")

        assert result is True

    def test_unretweet_dry_run(self):
        """Test unretweet dry-run mode (covers line 519)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        client = XClient(auth=auth, dry_run=True)

        result = client.unretweet("123")

        assert result is True

    def test_upload_media_dry_run(self):
        """Test upload_media dry-run mode (covers line 520)."""
        auth = UnifiedAuth(mode="oauth2", client_id="client123")
        client = XClient(auth=auth, dry_run=True)

        result = client.upload_media("/tmp/test.png")

        assert result == "dummy_media_id"
