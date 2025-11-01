from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

try:
    import tweepy  # type: ignore
except Exception:  # pragma: no cover - dry-run env
    tweepy = None  # type: ignore
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - dry-run env
    def load_dotenv(*args, **kwargs):  # type: ignore
        return None

from util import backoff_retry
try:
    import budget  # type: ignore
except Exception:  # pragma: no cover
    budget = None  # type: ignore
try:
    from rate_limit import record_api_call  # type: ignore
except Exception:  # pragma: no cover
    def record_api_call(*args, **kwargs):  # type: ignore
        return None


@dataclass
class XApi:
    """Wrapper around Tweepy v2 Client (and v1.1 for media).

    Uses user-context OAuth tokens only. All calls respect X Automation Rules.
    """

    client: Any
    api_v1: Any
    me_user_id: str

    @staticmethod
    def from_env() -> "XApi":
        # Try local project .env first, then fallback to process env
        project_root = os.path.dirname(os.path.dirname(__file__))
        env_path = os.path.join(project_root, ".env")
        load_dotenv(env_path)
        load_dotenv()
        consumer_key = os.getenv("X_API_KEY")
        consumer_secret = os.getenv("X_API_SECRET")
        access_token = os.getenv("X_ACCESS_TOKEN")
        access_secret = os.getenv("X_ACCESS_SECRET")
        if not all([consumer_key, consumer_secret, access_token, access_secret]):
            raise RuntimeError("Missing X API credentials in environment")

        if tweepy is None:
            raise RuntimeError("tweepy is not installed. Install requirements to use live mode.")

        # v2 client for Tweets, likes, follows, retweets
        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_secret,
            wait_on_rate_limit=False,  # We implement our own backoff
        )

        # v1.1 API for media upload
        auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_secret)
        api_v1 = tweepy.API(auth)

        me = client.get_me(user_fields=["id"]).data
        if me is None:
            raise RuntimeError("Unable to fetch authenticated user")
        return XApi(client=client, api_v1=api_v1, me_user_id=str(me.id))

    # ---- Media (v1.1) ----
    @backoff_retry((Exception,))
    def upload_media(self, path: str) -> str:
        """Upload media via v1.1 media/upload and return media_id string.

        API: POST media/upload (v1.1)
        Docs: https://developer.twitter.com/en/docs/twitter-api/v1/media/upload-media/api-reference/post-media-upload
        """
        media = self.api_v1.media_upload(filename=path, chunked=True)
        # Try to record headers if available
        headers = None
        status = None
        try:
            if hasattr(self.api_v1, "last_response") and self.api_v1.last_response is not None:
                status = self.api_v1.last_response.status_code
                headers = getattr(self.api_v1.last_response, "headers", None)
        except Exception:
            pass
        record_api_call("v1.1 media/upload", "POST", status, f"filename={path}", headers)
        return str(media.media_id_string)

    # ---- Tweets (v2) ----
    @backoff_retry((Exception,))
    def create_post(self, text: str, media_ids: Optional[List[str]] = None) -> str:
        """Create a Tweet.

        API: POST /2/tweets
        """
        payload: Dict[str, Any] = {"text": text}
        if media_ids:
            payload["media"] = {"media_ids": media_ids}
        resp = self.client.create_tweet(**payload)
        # Record limits if Tweepy exposes headers (not guaranteed in v2 Client)
        headers = getattr(resp, "headers", None)
        record_api_call("POST /2/tweets", "POST", 200, str({k: v for k, v in payload.items() if k != 'text'}), headers)
        try:
            if budget:
                budget.add_create(1)
        except Exception:
            pass
        return str(resp.data["id"])  # type: ignore[index]

    @backoff_retry((Exception,))
    def search_recent(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search recent Tweets (7-day) with authors.

        API: GET /2/tweets/search/recent
        """
        resp = self.client.search_recent_tweets(
            query=query,
            max_results=max_results,
            expansions=["author_id"],
            tweet_fields=["id", "author_id", "public_metrics"],
            user_fields=["id", "username"],
        )
        tweets = resp.data or []
        headers = getattr(resp, "headers", None)
        record_api_call("GET /2/tweets/search/recent", "GET", 200, f"max_results={max_results}", headers)
        try:
            if budget:
                budget.add_reads(len(tweets))
        except Exception:
            pass
        users = {u.id: u for u in (resp.includes.get("users", []) if resp.includes else [])}
        results: list[dict[str, Any]] = []
        for t in tweets:
            author = users.get(t.author_id) if hasattr(t, "author_id") else None
            results.append(
                {
                    "id": str(t.id),
                    "author_id": str(getattr(t, "author_id", "")),
                    "author_username": getattr(author, "username", None),
                    "public_metrics": getattr(t, "public_metrics", {}),
                }
            )
        return results

    @backoff_retry((Exception,))
    def reply(self, post_id: str, text: str) -> str:
        """Reply to a Tweet.

        API: POST /2/tweets (with in_reply_to_tweet_id)
        """
        resp = self.client.create_tweet(text=text, in_reply_to_tweet_id=post_id)
        headers = getattr(resp, "headers", None)
        record_api_call("POST /2/tweets (reply)", "POST", 200, f"in_reply_to_tweet_id={post_id}", headers)
        try:
            if budget:
                budget.add_create(1)
        except Exception:
            pass
        return str(resp.data["id"])  # type: ignore[index]

    @backoff_retry((Exception,))
    def like(self, post_id: str) -> None:
        """Like a Tweet as the authenticated user.

        API: POST /2/users/:id/likes
        """
        resp = self.client.like(tweet_id=post_id)
        headers = getattr(resp, "headers", None)
        record_api_call("POST /2/users/:id/likes", "POST", 200, f"tweet_id={post_id}", headers)

    @backoff_retry((Exception,))
    def repost(self, post_id: str) -> None:
        """Retweet a Tweet as the authenticated user.

        API: POST /2/users/:id/retweets
        """
        resp = self.client.retweet(tweet_id=post_id)
        headers = getattr(resp, "headers", None)
        record_api_call("POST /2/users/:id/retweets", "POST", 200, f"tweet_id={post_id}", headers)
        try:
            if budget:
                budget.add_create(1)
        except Exception:
            pass

    @backoff_retry((Exception,))
    def follow(self, target_user_id: str) -> None:
        """Follow a user.

        API: POST /2/users/:id/following
        """
        resp = self.client.follow_user(target_user_id=target_user_id)
        headers = getattr(resp, "headers", None)
        record_api_call("POST /2/users/:id/following", "POST", 200, f"target_user_id={target_user_id}", headers)

    @backoff_retry((Exception,))
    def fetch_metrics(self, post_id: str) -> dict[str, int]:
        """Fetch public metrics for a Tweet.

        API: GET /2/tweets/:id (tweet.fields=public_metrics)
        """
        resp = self.client.get_tweet(id=post_id, tweet_fields=["public_metrics"]) 
        headers = getattr(resp, "headers", None)
        record_api_call("GET /2/tweets/:id", "GET", 200, f"id={post_id}", headers)
        try:
            if budget:
                budget.add_reads(1)
        except Exception:
            pass
        t = resp.data
        if t is None:
            return {"like_count": 0, "reply_count": 0, "retweet_count": 0, "quote_count": 0}
        m = t.public_metrics or {}
        return {
            "like_count": int(m.get("like_count", 0)),
            "reply_count": int(m.get("reply_count", 0)),
            "retweet_count": int(m.get("retweet_count", 0)),
            "quote_count": int(m.get("quote_count", 0)),
        }

    @backoff_retry((Exception,))
    def get_user_tweets(self, user_id: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Fetch user's recent tweets (v2).

        API: GET /2/users/:id/tweets
        """
        resp = self.client.get_users_tweets(
            id=user_id,
            max_results=max_results,
            tweet_fields=["id", "author_id", "public_metrics"],
        )
        tweets = resp.data or []
        headers = getattr(resp, "headers", None)
        record_api_call("GET /2/users/:id/tweets", "GET", 200, f"max_results={max_results}", headers)
        try:
            if budget:
                budget.add_reads(len(tweets))
        except Exception:
            pass
        results: list[dict[str, Any]] = []
        for t in tweets:
            results.append(
                {
                    "id": str(t.id),
                    "author_id": str(getattr(t, "author_id", "")),
                    "public_metrics": getattr(t, "public_metrics", {}),
                }
            )
        return results


@dataclass
class NullXApi:
    """No-op API used for dry-run mode. Never performs network calls."""

    me_user_id: str = "0"

    def upload_media(self, path: str) -> str:  # pragma: no cover - dry-run only
        return "dry-media-id"

    def create_post(self, text: str, media_ids: Optional[List[str]] = None) -> str:  # pragma: no cover
        return "dry-post-id"

    def search_recent(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:  # pragma: no cover
        return []

    def reply(self, post_id: str, text: str) -> str:  # pragma: no cover
        return "dry-reply-id"

    def like(self, post_id: str) -> None:  # pragma: no cover
        return None

    def repost(self, post_id: str) -> None:  # pragma: no cover
        return None

    def follow(self, target_user_id: str) -> None:  # pragma: no cover
        return None

    def fetch_metrics(self, post_id: str) -> dict[str, int]:  # pragma: no cover
        return {"like_count": 0, "reply_count": 0, "retweet_count": 0, "quote_count": 0}
    @backoff_retry((Exception,))
    def delete_post(self, post_id: str) -> bool:
        resp = self.client.delete_tweet(id=post_id)
        headers = getattr(resp, "headers", None)
        record_api_call("DELETE /2/tweets/:id", "DELETE", 200, f"id={post_id}", headers)
        return True

    @backoff_retry((Exception,))
    def get_user_by_username(self, username: str) -> Optional[dict[str, Any]]:
        resp = self.client.get_user(username=username, user_fields=["id", "username", "name"])  # type: ignore
        headers = getattr(resp, "headers", None)
        record_api_call("GET /2/users/by/username/:username", "GET", 200, f"username={username}", headers)
        if resp and resp.data:
            u = resp.data
            return {"id": str(u.id), "username": u.username, "name": getattr(u, "name", None)}
        return None

    @backoff_retry((Exception,))
    def get_me(self) -> dict[str, Any]:
        resp = self.client.get_me(user_fields=["id", "username", "name"])  # type: ignore
        headers = getattr(resp, "headers", None)
        record_api_call("GET /2/users/me", "GET", 200, None, headers)
        u = resp.data
        return {"id": str(u.id), "username": u.username, "name": getattr(u, "name", None)}
