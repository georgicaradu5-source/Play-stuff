"""X API endpoint definitions."""

from __future__ import annotations


class Endpoints:
    """X API endpoint URL definitions."""

    # Base URLs
    BASE_V2 = "https://api.twitter.com/2"
    BASE_V1_UPLOAD = "https://upload.twitter.com/1.1"

    # User endpoints
    @staticmethod
    def users_me() -> str:
        """Get authenticated user endpoint."""
        return f"{Endpoints.BASE_V2}/users/me"

    @staticmethod
    def user_by_username(username: str) -> str:
        """Get user by username endpoint."""
        return f"{Endpoints.BASE_V2}/users/by/username/{username}"

    @staticmethod
    def user_by_id(user_id: str) -> str:
        """Get user by ID endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}"

    # Tweet endpoints
    @staticmethod
    def tweets() -> str:
        """Create tweet endpoint."""
        return f"{Endpoints.BASE_V2}/tweets"

    @staticmethod
    def tweet_by_id(tweet_id: str) -> str:
        """Get tweet by ID endpoint."""
        return f"{Endpoints.BASE_V2}/tweets/{tweet_id}"

    @staticmethod
    def user_tweets(user_id: str) -> str:
        """Get user tweets endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}/tweets"

    # Engagement endpoints
    @staticmethod
    def likes(user_id: str) -> str:
        """Like endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}/likes"

    @staticmethod
    def unlike(user_id: str, tweet_id: str) -> str:
        """Unlike endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}/likes/{tweet_id}"

    @staticmethod
    def retweets(user_id: str) -> str:
        """Retweet endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}/retweets"

    @staticmethod
    def unretweet(user_id: str, source_tweet_id: str) -> str:
        """Unretweet endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}/retweets/{source_tweet_id}"

    # Social endpoints
    @staticmethod
    def following(user_id: str) -> str:
        """Follow endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}/following"

    @staticmethod
    def unfollow(user_id: str, target_user_id: str) -> str:
        """Unfollow endpoint."""
        return f"{Endpoints.BASE_V2}/users/{user_id}/following/{target_user_id}"

    # Search endpoints
    @staticmethod
    def search_recent() -> str:
        """Search recent tweets endpoint."""
        return f"{Endpoints.BASE_V2}/tweets/search/recent"

    # Media endpoints (v1.1)
    @staticmethod
    def media_upload() -> str:
        """Media upload endpoint (v1.1)."""
        return f"{Endpoints.BASE_V1_UPLOAD}/media/upload.json"
