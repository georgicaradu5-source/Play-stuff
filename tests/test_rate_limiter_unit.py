import os
import sys

# Ensure src on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import rate_limiter as rl  # noqa: E402


def test_update_from_headers_and_can_call_threshold():
    r = rl.RateLimiter()
    headers = {
        "x-rate-limit-limit": "100",
        "x-rate-limit-remaining": "3",
        "x-rate-limit-reset": str(int(__import__("time").time()) + 1),
    }
    r.update_from_headers("/tweets", headers)
    can, wait = r.can_call("/tweets", min_remaining=5)
    assert can is False and wait is not None


def test_wait_if_needed_uses_sleep(monkeypatch):
    r = rl.RateLimiter()
    # Set up limits to force wait
    now = int(__import__("time").time())
    # Use a reset sufficiently in the future to avoid race to zero wait
    r.limits["/x"] = {"limit": 10, "remaining": 0, "reset": now + 3}

    calls = {"slept": 0, "dur": 0}

    def fake_sleep(d):
        calls["slept"] += 1
        calls["dur"] = d

    monkeypatch.setattr(rl.time, "sleep", fake_sleep)
    r.wait_if_needed("/x", min_remaining=5)
    assert calls["slept"] == 1
    assert calls["dur"] >= 1  # includes +1s buffer


def test_add_jitter_range(monkeypatch):
    r = rl.RateLimiter()
    # Force randint to return fixed value
    monkeypatch.setattr(rl.random, "randint", lambda a, b: 1500)
    calls = {"dur": None}

    def fake_sleep(d):
        calls["dur"] = d

    monkeypatch.setattr(rl.time, "sleep", fake_sleep)
    r.add_jitter(1000, 2000)
    assert calls["dur"] is not None
    assert abs(calls["dur"] - 1.5) < 0.001


def test_backoff_and_retry_success_after_rate_limit(monkeypatch):
    r = rl.RateLimiter()
    delays = []

    def fake_sleep(d):
        delays.append(d)

    monkeypatch.setattr(rl.time, "sleep", fake_sleep)
    # Make random.uniform deterministic
    monkeypatch.setattr(rl.random, "uniform", lambda a, b: 0.0)

    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise Exception("429 rate limit")
        return "ok"

    out = r.backoff_and_retry(flaky, max_retries=3)
    assert out == "ok"
    # Should have slept twice with exponential backoff: 1st=1, 2nd=2 (base^attempt where base=2 default)
    assert len(delays) == 2
    assert delays[0] == 1 and delays[1] == 2


def test_backoff_and_retry_non_rate_error(monkeypatch):
    r = rl.RateLimiter()

    def boom():
        raise Exception("500 other")

    try:
        r.backoff_and_retry(boom)
    except Exception as e:
        assert "500" in str(e)
    else:
        raise AssertionError("Expected exception to propagate")


def test_backoff_and_retry_exhaustion(monkeypatch):
    r = rl.RateLimiter()
    monkeypatch.setattr(rl.random, "uniform", lambda a, b: 0.0)

    def always_rl():
        raise Exception("429 too many")

    try:
        r.backoff_and_retry(always_rl, max_retries=2)
    except Exception as e:
        assert "too many" in str(e)
    else:
        raise AssertionError("Expected exhaustion raising last error")
