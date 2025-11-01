"""Rate limiter with header tracking and exponential backoff."""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar


T = TypeVar("T")


class RateLimiter:
    """Track rate limits per endpoint and implement backoff."""

    def __init__(self):
        # Store rate limit info per endpoint: {endpoint: {limit, remaining, reset}}
        self.limits: dict[str, dict] = {}
        self.last_call: dict[str, float] = {}
        
        # Backoff settings
        self.min_jitter_ms = 100
        self.max_jitter_ms = 2000
        self.backoff_base = 2
        self.max_retries = 3

    def update_from_headers(self, endpoint: str, headers: dict) -> None:
        """Update rate limit info from response headers."""
        # Handle both dict and requests.structures.CaseInsensitiveDict
        limit = headers.get("x-rate-limit-limit") or headers.get("X-Rate-Limit-Limit")
        remaining = headers.get("x-rate-limit-remaining") or headers.get("X-Rate-Limit-Remaining")
        reset = headers.get("x-rate-limit-reset") or headers.get("X-Rate-Limit-Reset")
        
        if limit and remaining and reset:
            self.limits[endpoint] = {
                "limit": int(limit),
                "remaining": int(remaining),
                "reset": int(reset),
                "updated_at": time.time(),
            }

    def can_call(self, endpoint: str, min_remaining: int = 5) -> tuple[bool, Optional[int]]:
        """Check if endpoint can be called safely.
        
        Returns:
            (can_call, seconds_to_wait)
        """
        if endpoint not in self.limits:
            return True, None
        
        info = self.limits[endpoint]
        remaining = info["remaining"]
        reset = info["reset"]
        
        # Check if we're below safety threshold
        if remaining < min_remaining:
            now = time.time()
            wait_seconds = max(0, reset - now)
            return False, int(wait_seconds)
        
        return True, None

    def add_jitter(self, min_ms: Optional[int] = None, max_ms: Optional[int] = None) -> None:
        """Add random jitter delay."""
        min_ms = min_ms or self.min_jitter_ms
        max_ms = max_ms or self.max_jitter_ms
        delay = random.randint(min_ms, max_ms) / 1000.0
        time.sleep(delay)

    def wait_if_needed(self, endpoint: str, min_remaining: int = 5) -> None:
        """Wait if rate limit is close to exhaustion."""
        can_call, wait_seconds = self.can_call(endpoint, min_remaining)
        
        if not can_call and wait_seconds:
            print(f"⏳ Rate limit low for {endpoint}. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds + 1)  # Add 1s buffer

    def backoff_and_retry(
        self,
        func: Callable[..., T],
        *args: Any,
        max_retries: Optional[int] = None,
        **kwargs: Any
    ) -> T:
        """Execute function with exponential backoff on rate limit errors."""
        max_retries = max_retries or self.max_retries
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                
                # Check for rate limit errors
                if "429" in error_str or "rate limit" in error_str:
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        base_delay = self.backoff_base ** attempt
                        jitter = random.uniform(0, 1)
                        delay = base_delay + jitter
                        
                        print(f"⚠️  Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        print(f"❌ Max retries reached for rate limit")
                        raise
                else:
                    # Non-rate-limit error, propagate immediately
                    raise
        
        raise RuntimeError("Backoff retry failed")

    def get_limit_info(self, endpoint: str) -> Optional[dict]:
        """Get current rate limit info for endpoint."""
        return self.limits.get(endpoint)

    def print_limits(self) -> None:
        """Print rate limit status for all tracked endpoints."""
        if not self.limits:
            print("No rate limit data available yet.")
            return
        
        print("\n=== Rate Limit Status ===")
        for endpoint, info in sorted(self.limits.items()):
            remaining = info["remaining"]
            limit = info["limit"]
            reset = info["reset"]
            reset_dt = datetime.fromtimestamp(reset).strftime("%Y-%m-%d %H:%M:%S")
            pct = (remaining / limit) * 100 if limit > 0 else 0
            
            status = "✓" if pct > 50 else "⚠️" if pct > 10 else "❌"
            print(f"\n{status} {endpoint}")
            print(f"   {remaining}/{limit} remaining ({pct:.1f}%)")
            print(f"   Resets: {reset_dt}")
