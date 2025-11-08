"""Low-level HTTP client for X API communication."""

from __future__ import annotations

from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from reliability import DEFAULT_TIMEOUT, request_with_retries


class APIClient:
    """Low-level HTTP client for X API.

    Handles HTTP communication, headers, retries, and error handling.
    Auth-agnostic: accepts auth headers from caller.
    """

    def __init__(self, dry_run: bool = False):
        """Initialize API client.

        Args:
            dry_run: If True, print operations without making HTTP calls
        """
        self.dry_run = dry_run

    def get(
        self,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Make GET request.

        Args:
            url: Full endpoint URL
            headers: Request headers (including Authorization)
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If requests library not installed or request fails
        """
        if self.dry_run:
            print(f"[DRY RUN] GET {url} params={params}")
            return {"data": None}

        if requests is None:
            raise RuntimeError("requests library not installed")

        resp = request_with_retries(
            "GET",
            url,
            headers=headers,
            params=params,
            timeout=timeout,
        )
        return resp.json()

    def post(
        self,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Make POST request.

        Args:
            url: Full endpoint URL
            headers: Request headers (including Authorization)
            json_body: JSON payload (for Content-Type: application/json)
            data: Form data (for Content-Type: application/x-www-form-urlencoded)
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If requests library not installed or request fails
        """
        if self.dry_run:
            print(f"[DRY RUN] POST {url} json={json_body} data={data}")
            return {"data": None}

        if requests is None:
            raise RuntimeError("requests library not installed")

        resp = request_with_retries(
            "POST",
            url,
            headers=headers,
            json_body=json_body,
            data=data,
            timeout=timeout,
        )
        return resp.json()

    def delete(
        self,
        url: str,
        headers: dict[str, str],
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Make DELETE request.

        Args:
            url: Full endpoint URL
            headers: Request headers (including Authorization)
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If requests library not installed or request fails
        """
        if self.dry_run:
            print(f"[DRY RUN] DELETE {url}")
            return {"data": None}

        if requests is None:
            raise RuntimeError("requests library not installed")

        resp = request_with_retries(
            "DELETE",
            url,
            headers=headers,
            timeout=timeout,
        )
        return resp.json()
