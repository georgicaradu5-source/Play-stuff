"""Unified authentication supporting both Tweepy (OAuth 1.0a) and OAuth 2.0 PKCE."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Literal
from urllib.parse import parse_qs, urlencode, urlparse

import requests

try:
    import tweepy
except ImportError:
    tweepy = None  # type: ignore

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


AuthMode = Literal["tweepy", "oauth2"]


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to capture OAuth 2.0 callback."""
    auth_code: str | None = None

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            OAuthCallbackHandler.auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorized! Close this window.</h1></body></html>")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        pass


class UnifiedAuth:
    """Unified authentication supporting both Tweepy and OAuth 2.0 PKCE."""

    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    AUTH_URL = "https://twitter.com/i/oauth2/authorize"

    def __init__(
        self,
        mode: AuthMode,
        # Tweepy (OAuth 1.0a)
        api_key: str | None = None,
        api_secret: str | None = None,
        access_token: str | None = None,
        access_secret: str | None = None,
        # OAuth 2.0 PKCE
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str = "http://localhost:8080/callback",
        token_file: str = ".token.json",
    ):
        self.mode = mode

        # Tweepy credentials
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret

        # OAuth 2.0 credentials
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_file = token_file
        self.oauth2_access_token: str | None = None
        self.oauth2_refresh_token: str | None = None

        # Tweepy clients (lazy init)
        self._tweepy_client: object | None = None
        self._tweepy_api: object | None = None
        self._me_user_id: str | None = None

    @classmethod
    def from_env(cls, mode: AuthMode | None = None) -> UnifiedAuth:
        """Create auth client from environment variables.

        Accepts an optional mode parameter for compatibility with callers
        that explicitly pass the desired auth mode. If not provided, the
        mode is read from the X_AUTH_MODE environment variable (default: tweepy).
        """
        resolved_mode: str = (mode or os.getenv("X_AUTH_MODE", "tweepy"))  # type: ignore

        if resolved_mode not in ["tweepy", "oauth2"]:
            raise ValueError(f"Invalid X_AUTH_MODE: {resolved_mode}. Use 'tweepy' or 'oauth2'")

        return cls(
            mode=resolved_mode,  # type: ignore
            # Tweepy
            api_key=os.getenv("X_API_KEY"),
            api_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_secret=os.getenv("X_ACCESS_SECRET"),
            # OAuth 2.0
            client_id=os.getenv("X_CLIENT_ID"),
            client_secret=os.getenv("X_CLIENT_SECRET"),
            redirect_uri=os.getenv("X_REDIRECT_URI", "http://localhost:8080/callback"),
            token_file=os.getenv("X_TOKEN_FILE", ".token.json"),
        )

    # === Tweepy (OAuth 1.0a) Methods ===

    def get_tweepy_client(self):
        """Get Tweepy v2 client (lazy init)."""
        if self.mode != "tweepy":
            raise RuntimeError("Not in Tweepy mode")

        if tweepy is None:
            raise RuntimeError("Tweepy not installed. Install: pip install tweepy>=4.14.0")

        if self._tweepy_client is None:
            if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
                raise RuntimeError("Missing Tweepy credentials in environment")

            self._tweepy_client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
                wait_on_rate_limit=False,
            )

        return self._tweepy_client

    def get_tweepy_api(self):
        """Get Tweepy v1.1 API (for media upload)."""
        if self.mode != "tweepy":
            raise RuntimeError("Not in Tweepy mode")

        if tweepy is None:
            raise RuntimeError("Tweepy not installed")

        if self._tweepy_api is None:
            if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
                raise RuntimeError("Missing Tweepy credentials")

            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_secret,
            )
            self._tweepy_api = tweepy.API(auth)

        return self._tweepy_api

    def get_me_user_id(self) -> str:
        """Get authenticated user ID (works for both modes)."""
        if self._me_user_id:
            return self._me_user_id

        if self.mode == "tweepy":
            client = self.get_tweepy_client()
            me = client.get_me(user_fields=["id"]).data
            if me is None:
                raise RuntimeError("Unable to fetch authenticated user")
            self._me_user_id = str(me.id)
        else:
            # OAuth 2.0
            token = self.get_oauth2_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get("https://api.twitter.com/2/users/me", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            self._me_user_id = data["data"]["id"]

        return self._me_user_id

    # === OAuth 2.0 PKCE Methods ===

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("utf-8")).digest()
        ).decode("utf-8").rstrip("=")
        return verifier, challenge

    def authorize_oauth2(self, scopes: list[str]) -> str:
        """Start OAuth 2.0 flow and return access token."""
        if self.mode != "oauth2":
            raise RuntimeError("Not in OAuth 2.0 mode")

        verifier, challenge = self._generate_pkce_pair()
        state = secrets.token_urlsafe(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"

        print("Opening browser for authorization...")
        webbrowser.open(auth_url)

        server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
        print("Waiting for callback on http://localhost:8080/callback...")
        server.handle_request()

        if not OAuthCallbackHandler.auth_code:
            raise RuntimeError("Authorization failed: no code received")

        return self._exchange_code(OAuthCallbackHandler.auth_code, verifier)

    def _exchange_code(self, code: str, verifier: str) -> str:
        """Exchange authorization code for access token."""
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_verifier": verifier,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if self.client_secret:
            auth = (self.client_id, self.client_secret)
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers, auth=auth)
        else:
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers)

        resp.raise_for_status()
        token_data = resp.json()

        self.oauth2_access_token = token_data["access_token"]
        self.oauth2_refresh_token = token_data.get("refresh_token")

        self._save_tokens(token_data)
        return self.oauth2_access_token

    def refresh_oauth2_token(self) -> str:
        """Refresh OAuth 2.0 access token."""
        if self.mode != "oauth2":
            raise RuntimeError("Not in OAuth 2.0 mode")

        if not self.oauth2_refresh_token:
            self._load_tokens()
            if not self.oauth2_refresh_token:
                raise RuntimeError("No refresh token available. Re-authorize.")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.oauth2_refresh_token,
            "client_id": self.client_id,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if self.client_secret:
            auth = (self.client_id, self.client_secret)
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers, auth=auth)
        else:
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers)

        resp.raise_for_status()
        token_data = resp.json()

        self.oauth2_access_token = token_data["access_token"]
        self.oauth2_refresh_token = token_data.get("refresh_token", self.oauth2_refresh_token)

        self._save_tokens(token_data)
        return self.oauth2_access_token

    def get_oauth2_access_token(self) -> str:
        """Get valid OAuth 2.0 access token."""
        if self.mode != "oauth2":
            raise RuntimeError("Not in OAuth 2.0 mode")

        if self.oauth2_access_token:
            return self.oauth2_access_token

        self._load_tokens()
        if self.oauth2_access_token:
            return self.oauth2_access_token

        raise RuntimeError("No access token available. Run --authorize first.")

    def _save_tokens(self, token_data: dict) -> None:
        """Save OAuth 2.0 tokens to file."""
        with open(self.token_file, "w") as f:
            json.dump(token_data, f, indent=2)

    def _load_tokens(self) -> None:
        """Load OAuth 2.0 tokens from file."""
        if not os.path.exists(self.token_file):
            return

        with open(self.token_file) as f:
            token_data = json.load(f)

        self.oauth2_access_token = token_data.get("access_token")
        self.oauth2_refresh_token = token_data.get("refresh_token")
