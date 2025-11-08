"""Tests for API endpoints module."""

from api.endpoints import Endpoints


def test_endpoints_users_me():
    """Test users/me endpoint URL."""
    assert Endpoints.users_me() == "https://api.twitter.com/2/users/me"


def test_endpoints_user_by_username():
    """Test user by username endpoint URL."""
    url = Endpoints.user_by_username("testuser")
    assert url == "https://api.twitter.com/2/users/by/username/testuser"


def test_endpoints_user_by_id():
    """Test user by ID endpoint URL."""
    url = Endpoints.user_by_id("123456")
    assert url == "https://api.twitter.com/2/users/123456"


def test_endpoints_tweets():
    """Test tweets endpoint URL."""
    assert Endpoints.tweets() == "https://api.twitter.com/2/tweets"


def test_endpoints_tweet_by_id():
    """Test tweet by ID endpoint URL."""
    url = Endpoints.tweet_by_id("987654")
    assert url == "https://api.twitter.com/2/tweets/987654"


def test_endpoints_user_tweets():
    """Test user tweets endpoint URL."""
    url = Endpoints.user_tweets("123456")
    assert url == "https://api.twitter.com/2/users/123456/tweets"


def test_endpoints_likes():
    """Test likes endpoint URL."""
    url = Endpoints.likes("123456")
    assert url == "https://api.twitter.com/2/users/123456/likes"


def test_endpoints_unlike():
    """Test unlike endpoint URL."""
    url = Endpoints.unlike("123456", "987654")
    assert url == "https://api.twitter.com/2/users/123456/likes/987654"


def test_endpoints_retweets():
    """Test retweets endpoint URL."""
    url = Endpoints.retweets("123456")
    assert url == "https://api.twitter.com/2/users/123456/retweets"


def test_endpoints_unretweet():
    """Test unretweet endpoint URL."""
    url = Endpoints.unretweet("123456", "987654")
    assert url == "https://api.twitter.com/2/users/123456/retweets/987654"


def test_endpoints_following():
    """Test following endpoint URL."""
    url = Endpoints.following("123456")
    assert url == "https://api.twitter.com/2/users/123456/following"


def test_endpoints_unfollow():
    """Test unfollow endpoint URL."""
    url = Endpoints.unfollow("123456", "789012")
    assert url == "https://api.twitter.com/2/users/123456/following/789012"


def test_endpoints_search_recent():
    """Test search recent endpoint URL."""
    assert Endpoints.search_recent() == "https://api.twitter.com/2/tweets/search/recent"


def test_endpoints_media_upload():
    """Test media upload endpoint URL."""
    assert Endpoints.media_upload() == "https://upload.twitter.com/1.1/media/upload.json"
