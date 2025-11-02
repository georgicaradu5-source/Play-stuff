import os
import sys
import types

# Ensure top-level import resolution so modules that do `from auth import ...`
# (located in src/auth.py) can be imported as top-level modules during tests.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(repo_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from x_client import XClient  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def make_fake_requests(sequence, raise_timeout_first=False):
    state = {"calls": 0, "last_headers": None, "last_timeout": None}

    def request(method, url, headers=None, params=None, json=None, timeout=None):
        state["calls"] += 1
        state["last_headers"] = dict(headers or {})
        state["last_timeout"] = timeout
        item = sequence[min(state["calls"] - 1, len(sequence) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    fake_requests = types.SimpleNamespace(request=request)
    return fake_requests, state


def test_get_user_by_username_uses_retries_and_timeout(monkeypatch):
    # Simulate 500 then 200 for GET
    seq = [FakeResponse(500, {}), FakeResponse(200, {"data": {"id": "42", "username": "alice"}})]
    fake_requests, state = make_fake_requests(seq)

    # Patch the reliability.requests used by the wrapper
    import reliability as rel

    monkeypatch.setattr(rel, "requests", types.SimpleNamespace(request=fake_requests.request), raising=False)

    # Create client with oauth2 mode
    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(auth)

    res = client.get_user_by_username("alice")

    assert state["calls"] >= 2, "Expected at least one retry"
    assert res.get("data", {}).get("username") == "alice"
    # Confirm timeout was passed to the underlying requests call
    assert state["last_timeout"] == rel.DEFAULT_TIMEOUT


def test_create_post_sends_idempotency_key_and_is_stable(monkeypatch):
    # Single success response for POST
    seq = [FakeResponse(200, {"data": {"id": "p1"}})]
    fake_requests, state = make_fake_requests(seq)

    import reliability as rel

    monkeypatch.setattr(rel, "requests", types.SimpleNamespace(request=fake_requests.request), raising=False)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(auth)

    payload_text = "hello"
    res1 = client.create_post(payload_text)
    key1 = state["last_headers"].get("Idempotency-Key")

    # Call again with same payload to ensure stable key
    seq2 = [FakeResponse(200, {"data": {"id": "p2"}})]
    fake_requests2, state2 = make_fake_requests(seq2)
    monkeypatch.setattr(rel, "requests", types.SimpleNamespace(request=fake_requests2.request), raising=False)

    res2 = client.create_post(payload_text)
    key2 = state2["last_headers"].get("Idempotency-Key")

    assert key1 is not None and key2 is not None
    assert key1 == key2, "Idempotency key should be deterministic for same payload"
    assert res1.get("data") and res2.get("data")
