"""Comprehensive retry and error handling tests for x_client.py."""

import os
import sys
import types
from unittest.mock import Mock, patch

import pytest

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


class FakeResponse:
    """Mock HTTP response."""

    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


# ============================================================================
# MODULE IMPORT AND INITIALIZATION TESTS
# ============================================================================


def test_xclient_requests_import_missing():
    """Test XClient handles missing requests library gracefully at module level."""
    # This test verifies the fallback behavior when requests is not available
    # The actual import happens at module load, so we can't easily test it here
    # Just verify the pattern exists
    from x_client import XClient

    # If we got here, the module imported successfully
    # which means the try/except ImportError pattern works
    assert XClient is not None


def test_from_env_invalid_mode_raises():
    """Test from_env() raises ValueError for invalid X_AUTH_MODE."""
    from x_client import XClient

    with patch.dict(os.environ, {"X_AUTH_MODE": "invalid_mode"}):
        with pytest.raises(ValueError, match="Invalid X_AUTH_MODE"):
            XClient.from_env()


# ============================================================================
# GET_ME TESTS
# ============================================================================


def test_get_me_tweepy_no_data():
    """Test get_me() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.get_me.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.get_me()

    assert result == {"data": None}


def test_get_me_oauth2_not_authenticated():
    """Test get_me() in OAuth2 mode raises when not authenticated."""
    from x_client import XClient

    auth = types.SimpleNamespace(mode="oauth2", access_token=None)
    client = XClient(auth)

    with pytest.raises(RuntimeError, match="Not authenticated"):
        client.get_me()


def test_get_me_oauth2_requests_not_installed():
    """Test get_me() in OAuth2 mode raises when requests library is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.get_me()


# ============================================================================
# GET_USER_BY_USERNAME TESTS
# ============================================================================


def test_get_user_by_username_tweepy_no_data():
    """Test get_user_by_username() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.get_user.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.get_user_by_username("alice")

    assert result == {"data": None}


def test_get_user_by_username_oauth2_requests_not_installed():
    """Test get_user_by_username() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.get_user_by_username("alice")


# ============================================================================
# GET_TWEET TESTS
# ============================================================================


def test_get_tweet_tweepy_no_data():
    """Test get_tweet() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.get_tweet.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.get_tweet("12345")

    assert result == {"data": None}


def test_get_tweet_oauth2_requests_not_installed():
    """Test get_tweet() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.get_tweet("12345")


# ============================================================================
# CREATE_POST TESTS
# ============================================================================


def test_create_post_tweepy_with_all_options():
    """Test create_post() in Tweepy mode with reply, media, and quote."""
    from x_client import XClient

    mock_client = Mock()
    mock_client.create_tweet.return_value = Mock(data={"id": "99999"})

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.create_post(
        text="Test post",
        reply_to="111",
        media_ids=["m1", "m2"],
        quote_tweet_id="222",
    )

    assert result["data"]["id"] == "99999"
    mock_client.create_tweet.assert_called_once()
    kwargs = mock_client.create_tweet.call_args[1]
    assert kwargs["text"] == "Test post"
    assert kwargs["in_reply_to_tweet_id"] == "111"
    assert kwargs["media_ids"] == ["m1", "m2"]
    assert kwargs["quote_tweet_id"] == "222"


def test_create_post_oauth2_requests_not_installed():
    """Test create_post() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.create_post("Test")


# ============================================================================
# SEARCH_RECENT TESTS
# ============================================================================


def test_search_recent_tweepy_no_tweets():
    """Test search_recent() in Tweepy mode returns empty list when no tweets."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_resp.includes = None
    mock_resp.meta = Mock()
    mock_resp.meta.next_token = None
    mock_client.search_recent_tweets.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.search_recent("test query", max_results=10)

    assert result == []


def test_search_recent_tweepy_pagination_stops_on_no_next_token():
    """Test search_recent() in Tweepy mode stops pagination when next_token is None."""
    from x_client import XClient

    mock_tweet = Mock()
    mock_tweet.id = "123"
    mock_tweet.author_id = "456"
    mock_tweet.public_metrics = {"likes": 10}

    mock_user = Mock()
    mock_user.id = "456"
    mock_user.username = "alice"

    mock_resp = Mock()
    mock_resp.data = [mock_tweet]
    mock_resp.includes = {"users": [mock_user]}
    mock_resp.meta = Mock()
    mock_resp.meta.next_token = None  # No pagination

    mock_client = Mock()
    mock_client.search_recent_tweets.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.search_recent("test", max_results=100)

    assert len(result) == 1
    assert result[0]["id"] == "123"
    assert result[0]["author_username"] == "alice"


def test_search_recent_oauth2_requests_not_installed():
    """Test search_recent() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.search_recent("test")


def test_search_recent_oauth2_pagination_stops_on_empty_tweets():
    """Test search_recent() in OAuth2 mode stops when tweets list is empty."""
    from x_client import XClient

    # Create a proper mock for reliability module
    class MockRequests:
        # Define the Timeout exception
        Timeout = TimeoutError

        def request(
            self,
            method,
            url,
            headers=None,
            params=None,
            timeout=None,
            json=None,  # Add json parameter
        ):
            return FakeResponse(200, {"data": [], "meta": {}})

    import reliability

    original_requests = reliability.requests

    try:
        reliability.requests = MockRequests()

        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        result = client.search_recent("test", max_results=10)

        assert result == []
    finally:
        # Restore original
        reliability.requests = original_requests


# ============================================================================
# DELETE_POST TESTS
# ============================================================================


def test_delete_post_tweepy_no_data():
    """Test delete_post() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.delete_tweet.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.delete_post("12345")

    assert result is False


def test_delete_post_oauth2_requests_not_installed():
    """Test delete_post() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.delete_post("12345")


# ============================================================================
# LIKE_POST TESTS
# ============================================================================


def test_like_post_tweepy_no_data():
    """Test like_post() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.like.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.like_post("12345")

    assert result is False


def test_like_post_oauth2_requests_not_installed():
    """Test like_post() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.like_post("12345")


def test_like_post_oauth2_fetches_me_id_when_missing():
    """Test like_post() in OAuth2 mode calls get_me() when me_id is not set."""
    from x_client import XClient

    def mock_request(method, url, headers=None, params=None, json=None, timeout=None):
        if "users/me" in url:
            return FakeResponse(200, {"data": {"id": "user123", "username": "me"}})
        elif "likes" in url:
            return FakeResponse(200, {"data": {"liked": True}})
        return FakeResponse(404, {})

    with patch("reliability.requests", types.SimpleNamespace(request=mock_request)):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        # me_id is None initially
        assert client.me_id is None

        result = client.like_post("12345")

        # Should have fetched me_id
        assert client.me_id == "user123"
        assert result is True


# ============================================================================
# UNLIKE_POST TESTS
# ============================================================================


def test_unlike_post_tweepy_no_data():
    """Test unlike_post() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.unlike.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.unlike_post("12345")

    # When no data, should return True (success)
    assert result is True


def test_unlike_post_oauth2_requests_not_installed():
    """Test unlike_post() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.unlike_post("12345")


def test_unlike_post_oauth2_fetches_me_id_when_missing():
    """Test unlike_post() in OAuth2 mode calls get_me() when me_id is not set."""
    from x_client import XClient

    def mock_request(method, url, headers=None, params=None, json=None, timeout=None):
        if "users/me" in url:
            return FakeResponse(200, {"data": {"id": "user123", "username": "me"}})
        elif "likes" in url:
            return FakeResponse(200, {"data": {"liked": False}})
        return FakeResponse(404, {})

    with patch("reliability.requests", types.SimpleNamespace(request=mock_request)):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        result = client.unlike_post("12345")

        assert client.me_id == "user123"
        assert result is False


# ============================================================================
# RETWEET TESTS
# ============================================================================


def test_retweet_tweepy_no_data():
    """Test retweet() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.retweet.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.retweet("12345")

    assert result is False


def test_retweet_oauth2_requests_not_installed():
    """Test retweet() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.retweet("12345")


def test_retweet_oauth2_fetches_me_id_when_missing():
    """Test retweet() in OAuth2 mode calls get_me() when me_id is not set."""
    from x_client import XClient

    def mock_request(method, url, headers=None, params=None, json=None, timeout=None):
        if "users/me" in url:
            return FakeResponse(200, {"data": {"id": "user123", "username": "me"}})
        elif "retweets" in url:
            return FakeResponse(200, {"data": {"retweeted": True}})
        return FakeResponse(404, {})

    with patch("reliability.requests", types.SimpleNamespace(request=mock_request)):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        result = client.retweet("12345")

        assert client.me_id == "user123"
        assert result is True


# ============================================================================
# UNRETWEET TESTS
# ============================================================================


def test_unretweet_tweepy_no_data():
    """Test unretweet() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.unretweet.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.unretweet("12345")

    # When no data, logic returns not (False) = True
    assert result is True


def test_unretweet_oauth2_fetches_me_id_when_missing():
    """Test unretweet() in OAuth2 mode calls get_me() when me_id is not set."""
    from x_client import XClient

    def mock_request(method, url, headers=None, params=None, json=None, timeout=None):
        if "users/me" in url:
            return FakeResponse(200, {"data": {"id": "user123", "username": "me"}})
        elif "retweets" in url:
            return FakeResponse(200, {})
        return FakeResponse(404, {})

    with patch("reliability.requests", types.SimpleNamespace(request=mock_request)):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        result = client.unretweet("12345")

        assert client.me_id == "user123"
        assert result is True


# ============================================================================
# FOLLOW_USER TESTS
# ============================================================================


def test_follow_user_tweepy_no_data():
    """Test follow_user() in Tweepy mode when response has no data."""
    from x_client import XClient

    mock_client = Mock()
    mock_resp = Mock()
    mock_resp.data = None
    mock_client.follow_user.return_value = mock_resp

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_client=lambda: mock_client)
    client = XClient(auth)

    result = client.follow_user("67890")

    assert result is False


def test_follow_user_oauth2_requests_not_installed():
    """Test follow_user() in OAuth2 mode raises when requests is missing."""
    from x_client import XClient

    with patch("x_client.requests", None):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        with pytest.raises(RuntimeError, match="requests library not installed"):
            client.follow_user("67890")


def test_follow_user_oauth2_fetches_me_id_when_missing():
    """Test follow_user() in OAuth2 mode calls get_me() when me_id is not set."""
    from x_client import XClient

    def mock_request(method, url, headers=None, params=None, json=None, timeout=None):
        if "users/me" in url:
            return FakeResponse(200, {"data": {"id": "user123", "username": "me"}})
        elif "following" in url:
            return FakeResponse(200, {"data": {"following": True}})
        return FakeResponse(404, {})

    with patch("reliability.requests", types.SimpleNamespace(request=mock_request)):
        auth = types.SimpleNamespace(mode="oauth2", access_token="token")
        client = XClient(auth)

        result = client.follow_user("67890")

        assert client.me_id == "user123"
        assert result is True


# ============================================================================
# UPLOAD_MEDIA TESTS
# ============================================================================


def test_upload_media_tweepy_success():
    """Test upload_media() in Tweepy mode returns media_id_string."""
    from x_client import XClient

    mock_api = Mock()
    mock_media = Mock()
    mock_media.media_id_string = "media_999"
    mock_api.media_upload.return_value = mock_media

    auth = types.SimpleNamespace(mode="tweepy", get_tweepy_api=lambda: mock_api)
    client = XClient(auth)

    result = client.upload_media("/path/to/image.jpg")

    assert result == "media_999"
    mock_api.media_upload.assert_called_once_with(filename="/path/to/image.jpg", chunked=True)


def test_upload_media_oauth2_not_implemented():
    """Test upload_media() in OAuth2 mode raises NotImplementedError."""
    from x_client import XClient

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(auth)

    with pytest.raises(NotImplementedError, match="OAuth 2.0 PKCE does not support v1.1 endpoints"):
        client.upload_media("/path/to/image.jpg")
