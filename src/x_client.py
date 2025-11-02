"""Unified X API client supporting both Tweepy and OAuth 2.0 modes."""

from __future__ import annotations

import os
from typing import Any, cast

try:
    import requests
except ImportError:
    requests = None

from auth import UnifiedAuth
from reliability import DEFAULT_TIMEOUT, request_with_retries
from telemetry import start_span


class XClient:
    """Unified X API client with dual auth support.

    Supports both:
    - Tweepy mode: Uses Tweepy's OAuth 1.0a client
    - OAuth2 mode: Uses raw requests with OAuth 2.0 PKCE
    """

    BASE_URL_V2 = "https://api.twitter.com/2"
    BASE_URL_V1 = "https://upload.twitter.com/1.1"

    def __init__(self, auth: UnifiedAuth, dry_run: bool = False):
        self.auth = auth
        self.dry_run = dry_run
        self.me_id: str | None = None

    @classmethod
    def from_env(cls, dry_run: bool = False) -> XClient:
        """Create client from environment variables."""
        mode = os.getenv("X_AUTH_MODE", "tweepy")
        if mode not in ["tweepy", "oauth2"]:
            raise ValueError(f"Invalid X_AUTH_MODE: {mode}. Use 'tweepy' or 'oauth2'")

        # Cast is safe because we just validated mode is in ["tweepy", "oauth2"]
        from auth import AuthMode

        auth = UnifiedAuth.from_env(cast(AuthMode, mode))
        return cls(auth, dry_run)

    # ============================================================================
    # USER METHODS
    # ============================================================================

    def get_me(self) -> dict[str, Any]:
        """Get authenticated user's info."""
        with start_span("x_client.get_me") as span:
            try:
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print("[DRY RUN] get_me()")
                return {"data": {"id": "dummy_user_id", "username": "dummy_user"}}

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.get_me(user_fields=["id", "username", "name", "description"])
                if resp.data:
                    self.me_id = str(resp.data.id)
                    return {
                        "data": {
                            "id": str(resp.data.id),
                            "username": resp.data.username,
                            "name": getattr(resp.data, "name", ""),
                            "description": getattr(resp.data, "description", ""),
                        }
                    }
                return {"data": None}
            else:
                # OAuth 2.0 mode
                token = self.auth.access_token
                if not token:
                    raise RuntimeError("Not authenticated. Run with --authorize first.")

                if requests is None:
                    raise RuntimeError("requests library not installed")

                url = f"{self.BASE_URL_V2}/users/me"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                params = {"user.fields": "id,username,name,description"}
                resp = request_with_retries("GET", url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
                result = resp.json()

                if "data" in result and "id" in result["data"]:
                    self.me_id = result["data"]["id"]

                return result

    def get_user_by_username(self, username: str) -> dict[str, Any]:
        """Get user by username."""
        with start_span("x_client.get_user_by_username") as span:
            try:
                span.set_attribute("username", username)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] get_user_by_username({username})")
                return {"data": {"id": "dummy_id", "username": username}}

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.get_user(
                    username=username, user_fields=["id", "username", "name", "description", "public_metrics"]
                )
                if resp.data:
                    return {
                        "data": {
                            "id": str(resp.data.id),
                            "username": resp.data.username,
                            "name": getattr(resp.data, "name", ""),
                            "description": getattr(resp.data, "description", ""),
                            "public_metrics": getattr(resp.data, "public_metrics", {}),
                        }
                    }
                return {"data": None}
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                url = f"{self.BASE_URL_V2}/users/by/username/{username}"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                params = {"user.fields": "id,username,name,description,public_metrics"}
                resp = request_with_retries("GET", url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
                return resp.json()

    # ============================================================================
    # TWEET/POST METHODS
    # ============================================================================

    def get_tweet(self, tweet_id: str) -> dict[str, Any]:
        """Get a single tweet by ID (minimal example endpoint)."""
        with start_span("x_client.get_tweet") as span:
            try:
                span.set_attribute("tweet_id", tweet_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass

            if self.dry_run:
                print(f"[DRY RUN] get_tweet({tweet_id})")
                return {"data": {"id": tweet_id, "text": "[dry-run]"}}

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.get_tweet(tweet_id)
                if getattr(resp, "data", None):
                    data = resp.data
                    # Tweepy returns an object with id/text attributes
                    return {"data": {"id": str(getattr(data, "id", tweet_id)), "text": getattr(data, "text", "")}}
                return {"data": None}
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")
                url = f"{self.BASE_URL_V2}/tweets/{tweet_id}"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                resp = request_with_retries("GET", url, headers=headers, timeout=DEFAULT_TIMEOUT)
                return resp.json()

    def create_post(
        self,
        text: str,
        reply_to: str | None = None,
        media_ids: list[str] | None = None,
        quote_tweet_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a post (tweet)."""
        with start_span("x_client.create_post") as span:
            try:
                span.set_attribute("text_len", len(text))
                span.set_attribute("has_reply_to", bool(reply_to))
                span.set_attribute("media_count", len(media_ids) if media_ids else 0)
                span.set_attribute("has_quote", bool(quote_tweet_id))
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] create_post(text='{text[:50]}...', reply_to={reply_to}, media_ids={media_ids})")
                return {"data": {"id": "dummy_post_id", "text": text}}

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                kwargs: dict[str, Any] = {"text": text}

                if reply_to:
                    kwargs["in_reply_to_tweet_id"] = reply_to
                if media_ids:
                    kwargs["media_ids"] = media_ids
                if quote_tweet_id:
                    kwargs["quote_tweet_id"] = quote_tweet_id

                resp = client.create_tweet(**kwargs)
                return {"data": {"id": str(resp.data["id"]), "text": text}}
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                url = f"{self.BASE_URL_V2}/tweets"
                headers = {
                    "Authorization": f"Bearer {self.auth.access_token}",
                    "Content-Type": "application/json",
                }
                payload: dict[str, Any] = {"text": text}

                if reply_to:
                    payload["reply"] = {"in_reply_to_tweet_id": reply_to}
                if media_ids:
                    payload["media"] = {"media_ids": media_ids}
                if quote_tweet_id:
                    payload["quote_tweet_id"] = quote_tweet_id

                resp = request_with_retries("POST", url, headers=headers, json_body=payload, timeout=DEFAULT_TIMEOUT)
                return resp.json()

    def search_recent(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search recent tweets (7 days)."""
        with start_span("x_client.search_recent") as span:
            try:
                span.set_attribute("query", query)
                span.set_attribute("max_results", max_results)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] search_recent(query='{query}', max_results={max_results})")
                return []

            results: list[dict[str, Any]] = []

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.search_recent_tweets(
                    query=query,
                    max_results=max_results,
                    expansions=["author_id"],
                    tweet_fields=["id", "author_id", "public_metrics"],
                    user_fields=["id", "username"],
                )

                tweets = resp.data or []
                users = {u.id: u for u in (resp.includes.get("users", []) if resp.includes else [])}

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
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                url = f"{self.BASE_URL_V2}/tweets/search/recent"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                params = {
                    "query": query,
                    "max_results": max_results,
                    "expansions": "author_id",
                    "tweet.fields": "id,author_id,public_metrics",
                    "user.fields": "id,username",
                }
                resp = request_with_retries("GET", url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
                data = resp.json()

                tweets = data.get("data", [])
                users_list = data.get("includes", {}).get("users", [])
                users = {u["id"]: u for u in users_list}

                for t in tweets:
                    author = users.get(t.get("author_id", ""))
                    results.append(
                        {
                            "id": t["id"],
                            "author_id": t.get("author_id", ""),
                            "author_username": author.get("username") if author else None,
                            "public_metrics": t.get("public_metrics", {}),
                        }
                    )
                return results

    def delete_post(self, tweet_id: str) -> bool:
        """Delete a post."""
        with start_span("x_client.delete_post") as span:
            try:
                span.set_attribute("tweet_id", tweet_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] delete_post({tweet_id})")
                return True

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.delete_tweet(tweet_id)
                return resp.data.get("deleted", False) if resp.data else False
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                url = f"{self.BASE_URL_V2}/tweets/{tweet_id}"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                resp = request_with_retries("DELETE", url, headers=headers, timeout=DEFAULT_TIMEOUT)
                data = resp.json()
                return data.get("data", {}).get("deleted", False)

    # ============================================================================
    # ENGAGEMENT METHODS
    # ============================================================================

    def like_post(self, tweet_id: str) -> bool:
        """Like a tweet."""
        with start_span("x_client.like_post") as span:
            try:
                span.set_attribute("tweet_id", tweet_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] like_post({tweet_id})")
                return True

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.like(tweet_id)
                return resp.data.get("liked", False) if resp.data else False
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                if not self.me_id:
                    self.get_me()  # Populate me_id

                url = f"{self.BASE_URL_V2}/users/{self.me_id}/likes"
                headers = {
                    "Authorization": f"Bearer {self.auth.access_token}",
                    "Content-Type": "application/json",
                }
                payload = {"tweet_id": tweet_id}
                resp = request_with_retries("POST", url, headers=headers, json_body=payload, timeout=DEFAULT_TIMEOUT)
                data = resp.json()
                return data.get("data", {}).get("liked", False)

    def unlike_post(self, tweet_id: str) -> bool:
        """Unlike a tweet."""
        with start_span("x_client.unlike_post") as span:
            try:
                span.set_attribute("tweet_id", tweet_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] unlike_post({tweet_id})")
                return True

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.unlike(tweet_id)
                return resp.data.get("liked", False) if resp.data else True
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                if not self.me_id:
                    self.get_me()

                url = f"{self.BASE_URL_V2}/users/{self.me_id}/likes/{tweet_id}"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                resp = request_with_retries("DELETE", url, headers=headers, timeout=DEFAULT_TIMEOUT)
                data = resp.json()
                return data.get("data", {}).get("liked", False)

    def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet."""
        with start_span("x_client.retweet") as span:
            try:
                span.set_attribute("tweet_id", tweet_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] retweet({tweet_id})")
                return True

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.retweet(tweet_id)
                return resp.data.get("retweeted", False) if resp.data else False
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                if not self.me_id:
                    self.get_me()

                url = f"{self.BASE_URL_V2}/users/{self.me_id}/retweets"
                headers = {
                    "Authorization": f"Bearer {self.auth.access_token}",
                    "Content-Type": "application/json",
                }
                payload = {"tweet_id": tweet_id}
                resp = request_with_retries("POST", url, headers=headers, json_body=payload, timeout=DEFAULT_TIMEOUT)
                data = resp.json()
                return data.get("data", {}).get("retweeted", False)

    def unretweet(self, tweet_id: str) -> bool:
        """Remove a retweet."""
        with start_span("x_client.unretweet") as span:
            try:
                span.set_attribute("tweet_id", tweet_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] unretweet({tweet_id})")
                return True

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.unretweet(tweet_id)
                return not (resp.data.get("retweeted", True) if resp.data else False)
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                if not self.me_id:
                    self.get_me()

                url = f"{self.BASE_URL_V2}/users/{self.me_id}/retweets/{tweet_id}"
                headers = {"Authorization": f"Bearer {self.auth.access_token}"}
                request_with_retries("DELETE", url, headers=headers, timeout=DEFAULT_TIMEOUT)
                return True

    def follow_user(self, user_id: str) -> bool:
        """Follow a user."""
        with start_span("x_client.follow_user") as span:
            try:
                span.set_attribute("user_id", user_id)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] follow_user({user_id})")
                return True

            if self.auth.mode == "tweepy":
                client = cast(Any, self.auth.get_tweepy_client())
                resp = client.follow_user(user_id)
                return resp.data.get("following", False) if resp.data else False
            else:
                if requests is None:
                    raise RuntimeError("requests library not installed")

                if not self.me_id:
                    self.get_me()

                url = f"{self.BASE_URL_V2}/users/{self.me_id}/following"
                headers = {
                    "Authorization": f"Bearer {self.auth.access_token}",
                    "Content-Type": "application/json",
                }
                payload = {"target_user_id": user_id}
                resp = request_with_retries("POST", url, headers=headers, json_body=payload, timeout=DEFAULT_TIMEOUT)
                data = resp.json()
                return data.get("data", {}).get("following", False)

    # ============================================================================
    # MEDIA UPLOAD (v1.1)
    # ============================================================================

    def upload_media(self, path: str) -> str:
        """Upload media and return media_id_string."""
        with start_span("x_client.upload_media") as span:
            try:
                span.set_attribute("path", path)
                span.set_attribute("mode", self.auth.mode)
                span.set_attribute("dry_run", self.dry_run)
            except Exception:
                pass
            if self.dry_run:
                print(f"[DRY RUN] upload_media({path})")
                return "dummy_media_id"

            if self.auth.mode == "tweepy":
                api_v1 = cast(Any, self.auth.get_tweepy_api())
                media = api_v1.media_upload(filename=path, chunked=True)
                return str(media.media_id_string)
            else:
                # OAuth 2.0 doesn't support v1.1 media upload
                # Must use OAuth 1.0a for this endpoint
                raise NotImplementedError(
                    "Media upload via v1.1 API requires OAuth 1.0a (Tweepy mode). "
                    "OAuth 2.0 PKCE does not support v1.1 endpoints."
                )
