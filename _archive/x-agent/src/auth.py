"""OAuth 2.0 PKCE authentication for X API."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Simple HTTP server to capture OAuth callback."""

    auth_code: Optional[str] = None
    state: Optional[str] = None

    def do_GET(self) -> None:
        """Handle OAuth callback."""
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            OAuthCallbackHandler.auth_code = query["code"][0]
            if "state" in query:
                OAuthCallbackHandler.state = query["state"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization successful! You can close this window.</h1></body></html>")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        """Suppress default HTTP server logs."""
        pass


class XAuth:
    """X API OAuth 2.0 with PKCE."""

    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    AUTH_URL = "https://twitter.com/i/oauth2/authorize"

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        redirect_uri: str = "http://localhost:8080/callback",
        token_file: str = ".token.json",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_file = token_file
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> XAuth:
        """Create auth client from environment variables."""
        return cls(
            client_id=os.getenv("X_CLIENT_ID", ""),
            client_secret=os.getenv("X_CLIENT_SECRET"),
            redirect_uri=os.getenv("X_REDIRECT_URI", "http://localhost:8080/callback"),
            token_file=os.getenv("X_TOKEN_FILE", ".token.json"),
        )

    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")
        return verifier, challenge

    def authorize(self, scopes: list[str]) -> str:
        """Start OAuth 2.0 flow and return access token."""
        # Generate PKCE pair
        verifier, challenge = self._generate_pkce_pair()
        state = secrets.token_urlsafe(32)
        
        # Build authorization URL
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

        print(f"Opening browser for authorization: {auth_url}")
        webbrowser.open(auth_url)

        # Start local server to capture callback
        server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
        print("Waiting for authorization callback on http://localhost:8080/callback...")
        server.handle_request()

        if not OAuthCallbackHandler.auth_code:
            raise RuntimeError("Authorization failed: no code received")
        # Verify state
        returned_state = OAuthCallbackHandler.state
        if not returned_state or returned_state != state:
            raise RuntimeError("Authorization failed: state mismatch")

        # Exchange code for token
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
        
        # PKCE: public clients SHOULD NOT send client_secret. For confidential clients,
        # X supports client_secret_post; Basic auth may also work. Default to no secret.
        if self.client_secret:
            data_with_secret = {**data, "client_secret": self.client_secret}
            resp = requests.post(self.TOKEN_URL, data=data_with_secret, headers=headers)
        else:
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers)

        resp.raise_for_status()
        token_data = resp.json()

        self._ingest_token_response(token_data)
        return self.access_token

    def refresh_access_token(self) -> str:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            self._load_tokens()
            if not self.refresh_token:
                raise RuntimeError("No refresh token available. Re-authorize.")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        if self.client_secret:
            data_with_secret = {**data, "client_secret": self.client_secret}
            resp = requests.post(self.TOKEN_URL, data=data_with_secret, headers=headers)
        else:
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers)

        resp.raise_for_status()
        token_data = resp.json()
        self._ingest_token_response(token_data)
        return self.access_token

    def get_access_token(self) -> str:
        """Get valid access token (load from file or refresh if needed)."""
        # Attempt to load and refresh if expiring soon
        if not self.access_token:
            self._load_tokens()
        if self.access_token and not self._is_expired(buffer_seconds=60):
            return self.access_token
        if self.refresh_token:
            return self.refresh_access_token()
        raise RuntimeError("No access token available. Run authorization first.")

    def _save_tokens(self, token_data: dict) -> None:
        """Save tokens to file."""
        with open(self.token_file, "w") as f:
            json.dump(token_data, f, indent=2)
        print(f"Tokens saved to {self.token_file}")

    def _load_tokens(self) -> None:
        """Load tokens from file."""
        if not os.path.exists(self.token_file):
            return

        with open(self.token_file, "r") as f:
            token_data = json.load(f)

        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        # stash computed expiry if present
        self._expires_at = token_data.get("expires_at")

    # ----- helpers -----
    _expires_at: Optional[float] = None

    def _is_expired(self, buffer_seconds: int = 60) -> bool:
        if not self._expires_at:
            return False
        return time.time() + buffer_seconds >= float(self._expires_at)

    def _ingest_token_response(self, token_data: dict) -> None:
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        # Compute absolute expiry if provided
        expires_in = token_data.get("expires_in")
        if expires_in:
            self._expires_at = time.time() + float(expires_in)
            token_data["expires_at"] = self._expires_at
        self._save_tokens(token_data)

    def build_tweepy_client(self):  # optional convenience
        try:
            import tweepy  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("tweepy not installed; pip install tweepy") from e
        token = self.get_access_token()
        return tweepy.Client(access_token=token, wait_on_rate_limit=False)
