"""Reliability utilities: retries, timeouts, and idempotency helpers.

Small, dependency-free helpers to add robustness to HTTP calls when using
raw requests in OAuth2 mode. Tweepy mode already handles retries internally.

Design goals:
- Explicit timeout on every request (default 10s)
- Bounded retries with exponential backoff + jitter on retryable status codes
- Respect rate limit headers when present (sleep until reset, capped)
- Optional Idempotency-Key header generation for safe POST retries
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from collections.abc import Callable, Mapping
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


DEFAULT_TIMEOUT = 10.0  # seconds
DEFAULT_RETRIES = 3
RETRYABLE_STATUSES: set[int] = {429, 500, 502, 503, 504}


def _compute_idempotency_key(payload: Any) -> str:
    """Compute a stable idempotency key from the JSON payload."""
    try:
        data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(data).hexdigest()
    except Exception:
        # Fallback to a random key if payload is not JSON-serializable
        return hashlib.sha256(str(payload).encode()).hexdigest()


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, Any] | None = None,
    json_body: Any | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff_base: float = 0.5,
    backoff_cap: float = 8.0,
    status_forcelist: set[int] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Any:
    """Perform an HTTP request with retries and backoff.

    Returns requests.Response on success, raises on permanent failure.
    """
    if requests is None:  # pragma: no cover
        raise RuntimeError("requests library not installed")

    sfl = status_forcelist or RETRYABLE_STATUSES
    attempt = 0
    hdrs: dict[str, str] = dict(headers or {})

    # Add idempotency key for POST to allow safe retries
    if method.upper() == "POST" and "Idempotency-Key" not in hdrs:
        hdrs["Idempotency-Key"] = _compute_idempotency_key(json_body)

    while True:
        try:
            resp = requests.request(
                method=method.upper(),
                url=url,
                headers=hdrs,
                params=params,
                json=json_body,
                timeout=timeout,
            )
        except requests.Timeout:
            if attempt >= retries:
                raise
            # Exponential backoff with jitter for timeouts
            delay = min(backoff_cap, backoff_base * (2**attempt)) + random.uniform(0, 0.5)
            sleep_fn(delay)
            attempt += 1
            continue

        # Success fast path
        if resp.status_code < 400:
            return resp

        # Non-retryable
        if resp.status_code not in sfl or attempt >= retries:
            resp.raise_for_status()
            return resp

        # If rate limited and headers indicate reset time, try to honor it
        rl_reset = resp.headers.get("x-rate-limit-reset") or resp.headers.get("X-Rate-Limit-Reset")
        if rl_reset and rl_reset.isdigit():
            now = int(time.time())
            reset_at = int(rl_reset)
            wait = max(0.0, min(backoff_cap, float(reset_at - now)))
        else:
            # Exponential backoff with jitter
            wait = min(backoff_cap, backoff_base * (2**attempt)) + random.uniform(0, 0.5)

        sleep_fn(wait)
        attempt += 1
