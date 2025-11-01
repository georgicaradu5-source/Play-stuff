"""X API v2 client with full endpoint support and v1.1 media upload."""

from __future__ import annotations

import os
from typing import Any, Optional

import requests

from auth import XAuth
from budget import BudgetManager
from rate_limiter import RateLimiter


class XClient:
    """Production-ready X API v2 client."""

    BASE_URL_V2 = "https://api.twitter.com/2"
    BASE_URL_V1 = "https://upload.twitter.com/1.1"

    def __init__(
        self,
        auth: XAuth,
        rate_limiter: RateLimiter,
        budget: BudgetManager,
        dry_run: bool = False,
    ):
        self.auth = auth
        self.rate_limiter = rate_limiter
        self.budget = budget
        self.dry_run = dry_run
        self.me_id: Optional[str] = None

    @classmethod
    def from_env(cls, budget: BudgetManager, dry_run: bool = False) -> XClient:
        """Create client from environment variables."""
        auth = XAuth.from_env()
        rate_limiter = RateLimiter()
        return cls(auth, rate_limiter, budget, dry_run)

    def _headers(self) -> dict[str, str]:
        """Get authorization headers."""
        token = self.auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        url: str,
        endpoint_name: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Optional[bytes] = None,
        headers: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make HTTP request with rate limiting and error handling."""
        # Check rate limits before calling
        self.rate_limiter.wait_if_needed(endpoint_name)

        # Use custom headers or default
        req_headers = headers or self._headers()

        # Make request with backoff
        def _call():
            resp = requests.request(
                method=method,
                url=url,
                json=json,
                params=params,
                data=data,
                headers=req_headers,
            )
            
            # Update rate limit info
            self.rate_limiter.update_from_headers(endpoint_name, resp.headers)
            
            # Handle errors
            if resp.status_code == 401:
                # Try to refresh token
                self.auth.refresh_access_token()
                req_headers["Authorization"] = f"Bearer {self.auth.access_token}"
                # Retry once
                resp = requests.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    data=data,
                    headers=req_headers,
                )
                self.rate_limiter.update_from_headers(endpoint_name, resp.headers)
            
            resp.raise_for_status()
            return resp.json() if resp.content else {}

        return self.rate_limiter.backoff_and_retry(_call)

    def get_me(self) -> dict[str, Any]:
        """Get authenticated user's info."""
        if self.dry_run:
            print("[DRY RUN] get_me()")
            return {"data": {"id": "dummy_user_id", "username": "dummy_user"}}

        url = f"{self.BASE_URL_V2}/users/me"
        params = {"user.fields": "id,username,name,description"}
        result = self._request("GET", url, "users/me", params=params)
        
        # Cache user ID
        if "data" in result and "id" in result["data"]:
            self.me_id = result["data"]["id"]
        
        return result

    def get_user_by_username(self, username: str) -> dict[str, Any]:
        """Get user by username."""
        if self.dry_run:
            print(f"[DRY RUN] get_user_by_username({username})")
            return {"data": {"id": "dummy_id", "username": username}}

        url = f"{self.BASE_URL_V2}/users/by/username/{username}"
        params = {"user.fields": "id,username,name,description,public_metrics"}
        return self._request("GET", url, f"users/by/username/{username}", params=params)

    def create_post(
        self,
        text: str,
        reply_to: Optional[str] = None,
        media_ids: Optional[list[str]] = None,
        quote_tweet_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a post (tweet).
        
        Args:
            text: Post text (max 280 chars for Free, more for Pro)
            reply_to: Tweet ID to reply to
            media_ids: List of media IDs from upload
            quote_tweet_id: Tweet ID to quote
        """
        if self.dry_run:
            print(f"[DRY RUN] create_post(text='{text[:50]}...', reply_to={reply_to}, media_ids={media_ids})")
            return {"data": {"id": "dummy_post_id", "text": text}}

        # Check budget
        can_write, msg = self.budget.can_write(1)
        if not can_write:
            raise RuntimeError(f"Budget exceeded: {msg}")

        payload: dict[str, Any] = {"text": text}
        
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}
        
        if media_ids:
            payload["media"] = {"media_ids": media_ids}
        
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id

        url = f"{self.BASE_URL_V2}/tweets"
        result = self._request("POST", url, "tweets", json=payload)
        
        # Update budget
        self.budget.add_writes(1)
        
        return result

    def delete_post(self, post_id: str) -> dict[str, Any]:
        """Delete a post."""
        if self.dry_run:
            print(f"[DRY RUN] delete_post({post_id})")
            return {"data": {"deleted": True}}

        url = f"{self.BASE_URL_V2}/tweets/{post_id}"
        result = self._request("DELETE", url, f"tweets/{post_id}")
        
        # Deletes count as writes
        self.budget.add_writes(1)
        
        return result

    def like_post(self, user_id: str, post_id: str) -> dict[str, Any]:
        """Like a post."""
        if self.dry_run:
            print(f"[DRY RUN] like_post(user_id={user_id}, post_id={post_id})")
            return {"data": {"liked": True}}

        # Likes are writes
        can_write, msg = self.budget.can_write(1)
        if not can_write:
            raise RuntimeError(f"Budget exceeded: {msg}")

        url = f"{self.BASE_URL_V2}/users/{user_id}/likes"
        payload = {"tweet_id": post_id}
        result = self._request("POST", url, f"users/{user_id}/likes", json=payload)
        
        self.budget.add_writes(1)
        return result

    def repost(self, user_id: str, post_id: str) -> dict[str, Any]:
        """Repost (retweet) a post."""
        if self.dry_run:
            print(f"[DRY RUN] repost(user_id={user_id}, post_id={post_id})")
            return {"data": {"retweeted": True}}

        can_write, msg = self.budget.can_write(1)
        if not can_write:
            raise RuntimeError(f"Budget exceeded: {msg}")

        url = f"{self.BASE_URL_V2}/users/{user_id}/retweets"
        payload = {"tweet_id": post_id}
        result = self._request("POST", url, f"users/{user_id}/retweets", json=payload)
        
        self.budget.add_writes(1)
        return result

    def follow_user(self, source_user_id: str, target_user_id: str) -> dict[str, Any]:
        """Follow a user."""
        if self.dry_run:
            print(f"[DRY RUN] follow_user(source={source_user_id}, target={target_user_id})")
            return {"data": {"following": True}}

        can_write, msg = self.budget.can_write(1)
        if not can_write:
            raise RuntimeError(f"Budget exceeded: {msg}")

        url = f"{self.BASE_URL_V2}/users/{source_user_id}/following"
        payload = {"target_user_id": target_user_id}
        result = self._request("POST", url, f"users/{source_user_id}/following", json=payload)
        
        self.budget.add_writes(1)
        return result

    def search_recent(
        self,
        query: str,
        max_results: int = 10,
        tweet_fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Search recent posts (7-day window).
        
        Args:
            query: Search query with operators
            max_results: Number of results (10-100 on Free/Basic, 10-500 on Pro)
            tweet_fields: Additional fields to retrieve
        """
        if self.dry_run:
            print(f"[DRY RUN] search_recent(query='{query}', max_results={max_results})")
            return {"data": [], "meta": {"result_count": 0}}

        # Check budget (reads = posts returned)
        can_read, msg = self.budget.can_read(max_results)
        if not can_read:
            raise RuntimeError(f"Budget exceeded: {msg}")

        url = f"{self.BASE_URL_V2}/tweets/search/recent"
        params: dict[str, Any] = {
            "query": query,
            "max_results": min(max_results, 100),  # API limit
        }
        
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        else:
            params["tweet.fields"] = "id,text,author_id,created_at,public_metrics"

        result = self._request("GET", url, "tweets/search/recent", params=params)
        
        # Update budget with actual posts returned
        posts_returned = result.get("meta", {}).get("result_count", 0)
        self.budget.add_reads(posts_returned)
        
        return result

    def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 10,
        tweet_fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Get a user's recent tweets."""
        if self.dry_run:
            print(f"[DRY RUN] get_user_tweets(user_id={user_id}, max_results={max_results})")
            return {"data": [], "meta": {"result_count": 0}}

        can_read, msg = self.budget.can_read(max_results)
        if not can_read:
            raise RuntimeError(f"Budget exceeded: {msg}")

        url = f"{self.BASE_URL_V2}/users/{user_id}/tweets"
        params: dict[str, Any] = {"max_results": min(max_results, 100)}
        
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        else:
            params["tweet.fields"] = "id,text,created_at,public_metrics"

        result = self._request("GET", url, f"users/{user_id}/tweets", params=params)
        
        posts_returned = result.get("meta", {}).get("result_count", 0)
        self.budget.add_reads(posts_returned)
        
        return result

    def get_tweet(self, tweet_id: str, tweet_fields: Optional[list[str]] = None) -> dict[str, Any]:
        """Get a single tweet by ID."""
        if self.dry_run:
            print(f"[DRY RUN] get_tweet({tweet_id})")
            return {"data": {"id": tweet_id}}

        can_read, msg = self.budget.can_read(1)
        if not can_read:
            raise RuntimeError(f"Budget exceeded: {msg}")

        url = f"{self.BASE_URL_V2}/tweets/{tweet_id}"
        params: dict[str, Any] = {}
        
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        else:
            params["tweet.fields"] = "id,text,author_id,created_at,public_metrics"

        result = self._request("GET", url, f"tweets/{tweet_id}", params=params)
        
        self.budget.add_reads(1)
        return result

    # === Media Upload (v1.1) ===

    def upload_media(self, file_path: str) -> str:
        """Upload media using v1.1 chunked upload.
        
        Returns:
            media_id string
        """
        if self.dry_run:
            print(f"[DRY RUN] upload_media({file_path})")
            return "dummy_media_id"

        # INIT
        file_size = os.path.getsize(file_path)
        media_type = self._get_media_type(file_path)
        
        media_id = self._upload_init(file_size, media_type)
        
        # APPEND
        self._upload_append(media_id, file_path)
        
        # FINALIZE
        self._upload_finalize(media_id)
        
        return media_id

    def _get_media_type(self, file_path: str) -> str:
        """Determine media MIME type from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
        }
        return types.get(ext, "application/octet-stream")

    def _upload_init(self, file_size: int, media_type: str) -> str:
        """Initialize chunked media upload."""
        url = f"{self.BASE_URL_V1}/media/upload.json"
        params = {
            "command": "INIT",
            "total_bytes": file_size,
            "media_type": media_type,
        }
        
        result = self._request("POST", url, "media/upload/INIT", params=params)
        return result["media_id_string"]

    def _upload_append(self, media_id: str, file_path: str, chunk_size: int = 1048576) -> None:
        """Upload file in chunks (default 1MB)."""
        url = f"{self.BASE_URL_V1}/media/upload.json"
        
        with open(file_path, "rb") as f:
            segment_index = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                params = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_index,
                }
                
                # For APPEND, we need multipart form data
                headers = self._headers()
                headers.pop("Content-Type")  # Let requests set it
                
                files = {"media": chunk}
                resp = requests.post(url, params=params, files=files, headers=headers)
                resp.raise_for_status()
                
                segment_index += 1
                self.rate_limiter.add_jitter(100, 500)

    def _upload_finalize(self, media_id: str) -> dict[str, Any]:
        """Finalize media upload."""
        url = f"{self.BASE_URL_V1}/media/upload.json"
        params = {
            "command": "FINALIZE",
            "media_id": media_id,
        }
        
        return self._request("POST", url, "media/upload/FINALIZE", params=params)
