"""Enhanced retry and error coverage tests for reliability.py and x_client.py."""

import time
from types import SimpleNamespace

import pytest

from reliability import _compute_idempotency_key, request_with_retries


def test_idempotency_key_stable():
    """Test idempotency key is stable for same payload."""
    payload = {"text": "Hello", "reply_to": "123"}
    key1 = _compute_idempotency_key(payload)
    key2 = _compute_idempotency_key(payload)
    assert key1 == key2
    assert len(key1) == 64  # SHA256 hex


def test_idempotency_key_different_payloads():
    """Test different payloads produce different keys."""
    key1 = _compute_idempotency_key({"text": "A"})
    key2 = _compute_idempotency_key({"text": "B"})
    assert key1 != key2


def test_idempotency_key_fallback_non_json():
    """Test idempotency key fallback for non-JSON-serializable payload."""

    # Object with circular reference
    class Circular:
        def __init__(self):
            self.ref = self

    obj = Circular()
    key = _compute_idempotency_key(obj)
    assert len(key) == 64  # Should still produce a key


def test_request_success_no_retry(monkeypatch):
    """Test successful request doesn't retry."""
    import requests as req

    class MockResponse:
        status_code = 200
        text = "OK"

        def json(self):
            return {"id": "123"}

    call_count = 0

    def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return MockResponse()

    monkeypatch.setattr(req, "request", mock_request)

    resp = request_with_retries("GET", "https://api.example.com/test")
    assert resp.status_code == 200
    assert call_count == 1


def test_request_retryable_429_with_backoff(monkeypatch):
    """Test 429 status triggers retries with backoff."""
    import requests as req

    attempt = 0

    class MockResponse:
        def __init__(self, status):
            self.status_code = status
            self.headers = {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    def mock_request(*args, **kwargs):
        nonlocal attempt
        attempt += 1
        if attempt <= 2:
            return MockResponse(429)
        return MockResponse(200)

    sleep_calls = []

    def mock_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr(req, "request", mock_request)

    resp = request_with_retries("POST", "https://api.example.com/test", sleep_fn=mock_sleep)
    assert resp.status_code == 200
    assert attempt == 3
    assert len(sleep_calls) == 2  # Two retries = two sleeps


def test_request_retryable_500_exhausts_retries(monkeypatch):
    """Test 500 status exhausts retries and raises."""
    import requests as req

    class MockResponse:
        status_code = 500
        headers = {}
        text = "Internal Server Error"

        def raise_for_status(self):
            raise Exception("HTTP 500")

    monkeypatch.setattr(req, "request", lambda *a, **kw: MockResponse())

    sleep_calls = []

    def mock_sleep(delay):
        sleep_calls.append(delay)

    with pytest.raises(Exception, match="HTTP 500"):
        request_with_retries("GET", "https://api.example.com/test", retries=2, sleep_fn=mock_sleep)
    assert len(sleep_calls) == 2  # Exhausted 2 retries


def test_request_timeout_retry(monkeypatch):
    """Test timeout triggers retry with exponential backoff."""
    import requests as req

    attempt = 0

    def mock_request(*args, **kwargs):
        nonlocal attempt
        attempt += 1
        if attempt <= 1:
            raise req.Timeout("Connection timeout")
        # Succeed on second attempt
        resp = SimpleNamespace()
        resp.status_code = 200
        resp.text = "OK"
        return resp

    sleep_calls = []

    def mock_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr(req, "request", mock_request)

    resp = request_with_retries("GET", "https://api.example.com/test", sleep_fn=mock_sleep)
    assert resp.status_code == 200
    assert attempt == 2
    assert len(sleep_calls) == 1


def test_request_timeout_exhausts_retries(monkeypatch):
    """Test repeated timeouts exhaust retries and raise."""
    import requests as req

    def mock_request(*args, **kwargs):
        raise req.Timeout("Connection timeout")

    monkeypatch.setattr(req, "request", mock_request)

    with pytest.raises(req.Timeout):
        request_with_retries("GET", "https://api.example.com/test", retries=1, sleep_fn=lambda d: None)


def test_request_rate_limit_reset_header(monkeypatch):
    """Test rate limit reset header is honored."""
    import requests as req

    attempt = 0

    class MockResponse:
        def __init__(self, status, reset_time=None):
            self.status_code = status
            self.headers = {}
            if reset_time:
                self.headers["x-rate-limit-reset"] = str(reset_time)

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    def mock_request(*args, **kwargs):
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            # Return 429 with reset time 2 seconds in future
            return MockResponse(429, reset_time=int(time.time()) + 2)
        return MockResponse(200)

    sleep_calls = []

    def mock_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr(req, "request", mock_request)

    resp = request_with_retries("GET", "https://api.example.com/test", sleep_fn=mock_sleep)
    assert resp.status_code == 200
    assert len(sleep_calls) == 1
    # Should have slept for ~2 seconds (capped at backoff_cap if needed)
    assert 0 < sleep_calls[0] <= 8.0


def test_request_idempotency_key_added_for_post(monkeypatch):
    """Test Idempotency-Key header is added for POST requests."""
    import requests as req

    captured_headers = {}

    def mock_request(method, url, headers, **kwargs):
        captured_headers.update(headers or {})
        resp = SimpleNamespace()
        resp.status_code = 200
        return resp

    monkeypatch.setattr(req, "request", mock_request)

    request_with_retries("POST", "https://api.example.com/test", json_body={"text": "Hi"})
    assert "Idempotency-Key" in captured_headers


def test_request_preserves_existing_idempotency_key(monkeypatch):
    """Test existing Idempotency-Key header is preserved."""
    import requests as req

    captured_headers = {}

    def mock_request(method, url, headers, **kwargs):
        captured_headers.update(headers or {})
        resp = SimpleNamespace()
        resp.status_code = 200
        return resp

    monkeypatch.setattr(req, "request", mock_request)

    custom_key = "my-custom-key"
    request_with_retries(
        "POST",
        "https://api.example.com/test",
        headers={"Idempotency-Key": custom_key},
        json_body={"text": "Hi"},
    )
    assert captured_headers["Idempotency-Key"] == custom_key


def test_request_non_retryable_status(monkeypatch):
    """Test non-retryable status (e.g., 400) raises immediately."""
    import requests as req

    class MockResponse:
        status_code = 400
        headers = {}
        text = "Bad Request"

        def raise_for_status(self):
            raise Exception("HTTP 400")

    call_count = 0

    def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return MockResponse()

    monkeypatch.setattr(req, "request", mock_request)

    with pytest.raises(Exception, match="HTTP 400"):
        request_with_retries("GET", "https://api.example.com/test")
    assert call_count == 1  # No retries for 400


def test_request_custom_status_forcelist(monkeypatch):
    """Test custom status_forcelist for retries."""
    import requests as req

    attempt = 0

    class MockResponse:
        def __init__(self, status):
            self.status_code = status
            self.headers = {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    def mock_request(*args, **kwargs):
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            return MockResponse(418)  # I'm a teapot
        return MockResponse(200)

    monkeypatch.setattr(req, "request", mock_request)

    # 418 is not in default RETRYABLE_STATUSES, so should fail immediately
    with pytest.raises(Exception, match="HTTP 418"):
        request_with_retries("GET", "https://api.example.com/test", sleep_fn=lambda d: None)
    assert attempt == 1

    # Now retry with custom forcelist including 418
    attempt = 0
    resp = request_with_retries(
        "GET",
        "https://api.example.com/test",
        status_forcelist={418},
        sleep_fn=lambda d: None,
    )
    assert resp.status_code == 200
    assert attempt == 2


def test_request_backoff_cap_enforced(monkeypatch):
    """Test backoff delay is capped at backoff_cap."""
    import requests as req

    attempt = 0

    class MockResponse:
        status_code = 503
        headers = {}

        def raise_for_status(self):
            raise Exception("HTTP 503")

    def mock_request(*args, **kwargs):
        nonlocal attempt
        attempt += 1
        return MockResponse()

    sleep_calls = []

    def mock_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr(req, "request", mock_request)

    with pytest.raises(Exception):
        request_with_retries(
            "GET",
            "https://api.example.com/test",
            retries=5,
            backoff_base=2.0,
            backoff_cap=3.0,
            sleep_fn=mock_sleep,
        )
    # All sleep delays should be <= backoff_cap + jitter (3.0 + 0.5)
    for delay in sleep_calls:
        assert delay <= 3.5
