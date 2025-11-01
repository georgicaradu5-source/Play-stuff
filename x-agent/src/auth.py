"""OAuth 2.0 PKCE authentication for X API."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
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

    def do_GET(self) -> None:
        """Handle OAuth callback."""
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            OAuthCallbackHandler.auth_code = query["code"][0]
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
        
        # Add client secret for confidential clients
        if self.client_secret:
            auth = (self.client_id, self.client_secret)
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers, auth=auth)
        else:
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers)

        resp.raise_for_status()
        token_data = resp.json()

        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")

        # Save tokens
        self._save_tokens(token_data)
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
            auth = (self.client_id, self.client_secret)
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers, auth=auth)
        else:
            resp = requests.post(self.TOKEN_URL, data=data, headers=headers)

        resp.raise_for_status()
        token_data = resp.json()

        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)

        self._save_tokens(token_data)
        return self.access_token

    def get_access_token(self) -> str:
        """Get valid access token (load from file or refresh if needed)."""
        if self.access_token:
            return self.access_token

        self._load_tokens()
        if self.access_token:
            return self.access_token

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
