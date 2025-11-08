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


def make_fake_requests(sequence):
    state = {"calls": 0, "last_headers": None, "last_timeout": None, "last_data": None}

    def request(method, url, headers=None, params=None, json=None, data=None, timeout=None):
        state["calls"] += 1
        state["last_headers"] = dict(headers or {})
        state["last_timeout"] = timeout
        state["last_data"] = data
        item = sequence[min(state["calls"] - 1, len(sequence) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    fake_requests = types.SimpleNamespace(request=request, Timeout=TimeoutError, HTTPError=Exception)
    return fake_requests, state


def test_get_tweet_uses_retries_and_timeout(monkeypatch):
    # Simulate 500 then 200 for GET
    seq = [FakeResponse(500, {}), FakeResponse(200, {"data": {"id": "42", "text": "hi"}})]
    fake_requests, state = make_fake_requests(seq)

    # Patch the reliability.requests used by the wrapper
    import reliability as rel

    monkeypatch.setattr(rel, "requests", types.SimpleNamespace(request=fake_requests.request), raising=False)

    # Create client with oauth2 mode
    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(auth)

    res = client.get_tweet("42")

    assert state["calls"] >= 2, "Expected at least one retry"
    assert res.get("data", {}).get("id") == "42"
    # Confirm timeout was passed to the underlying requests call
    assert state["last_timeout"] == rel.DEFAULT_TIMEOUT
