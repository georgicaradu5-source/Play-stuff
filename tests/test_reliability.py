import time
from types import SimpleNamespace

from src import reliability as rel


class FakeHTTPError(Exception):
    pass


class FakeTimeoutError(Exception):
    pass


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise FakeHTTPError(f"HTTP {self.status_code}")


def make_fake_requests(sequence, raise_timeout_first=False):
    state = {
        "calls": 0,
        "last_headers": None,
    }

    def request(method, url, headers=None, params=None, json=None, timeout=None):
        state["calls"] += 1
        state["last_headers"] = headers or {}
        if raise_timeout_first and state["calls"] == 1:
            raise FakeTimeoutError("timeout")
        item = sequence[min(state["calls"] - 1, len(sequence) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    fake_requests = SimpleNamespace(
        request=request,
    Timeout=FakeTimeoutError,
        HTTPError=FakeHTTPError,
    )
    return fake_requests, state


def test_retries_on_500_then_success(monkeypatch):
    # First 500, then 200
    seq = [FakeResponse(500), FakeResponse(200, {"ok": True})]
    fake_requests, state = make_fake_requests(seq)
    monkeypatch.setattr(rel, "requests", fake_requests, raising=False)

    waits = []
    def sleep_fn(s):
        waits.append(s)

    resp = rel.request_with_retries(
        "GET",
        "https://example.test",
        retries=2,
        sleep_fn=sleep_fn,
        backoff_base=0.01,
        backoff_cap=0.05,
    )
    assert resp.status_code == 200
    assert state["calls"] == 2
    assert len(waits) >= 1


def test_respects_rate_limit_reset_header(monkeypatch):
    reset_at = int(time.time()) + 1
    seq = [FakeResponse(429, headers={"x-rate-limit-reset": str(reset_at)}), FakeResponse(200)]
    fake_requests, state = make_fake_requests(seq)
    monkeypatch.setattr(rel, "requests", fake_requests, raising=False)

    waits = []
    def sleep_fn(s):
        waits.append(s)

    resp = rel.request_with_retries(
        "GET",
        "https://example.test",
        retries=2,
        sleep_fn=sleep_fn,
        backoff_cap=2.0,
    )
    assert resp.status_code == 200
    assert state["calls"] == 2
    # We should have waited approximately <= 2 seconds
    assert waits and waits[0] <= 2.0


def test_timeout_then_retry_success(monkeypatch):
    seq = [FakeResponse(200, {"ok": True})]
    fake_requests, state = make_fake_requests(seq, raise_timeout_first=True)
    monkeypatch.setattr(rel, "requests", fake_requests, raising=False)

    waits = []
    def sleep_fn(s):
        waits.append(s)

    resp = rel.request_with_retries(
        "GET",
        "https://example.test",
        retries=2,
        sleep_fn=sleep_fn,
        backoff_base=0.01,
        backoff_cap=0.05,
    )
    assert resp.status_code == 200
    assert state["calls"] == 2  # one timeout + one success
    assert len(waits) == 1


def test_idempotency_key_added_for_post(monkeypatch):
    seq = [FakeResponse(200, {"ok": True})]
    fake_requests, state = make_fake_requests(seq)
    monkeypatch.setattr(rel, "requests", fake_requests, raising=False)

    payload = {"a": 1, "b": 2}
    resp = rel.request_with_retries(
        "POST",
        "https://example.test",
        json_body=payload,
        retries=0,
    )
    assert resp.status_code == 200
    key1 = state["last_headers"].get("Idempotency-Key")
    assert key1 and isinstance(key1, str)

    # Second call with same payload should generate the same key
    resp = rel.request_with_retries(
        "POST",
        "https://example.test",
        json_body=payload,
        retries=0,
    )
    key2 = state["last_headers"].get("Idempotency-Key")
    assert key2 == key1
