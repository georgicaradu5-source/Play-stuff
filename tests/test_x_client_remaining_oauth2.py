"""Remaining coverage tests for src/x_client.py OAuth2 paths.
Targets previously uncovered: early error paths and span attribute sets.
"""

import builtins
from types import SimpleNamespace
from typing import Any

import pytest

from src.auth import UnifiedAuth
from src.x_client import XClient


class DummyAuth(UnifiedAuth):  # type: ignore[misc]
    """Minimal UnifiedAuth stub for OAuth2 mode."""

    def __init__(self):
        self.mode = "oauth2"
        self.access_token = "tok123"

    # Tweepy paths unused; provide dummies.
    def get_tweepy_client(self):  # pragma: no cover - not used here
        return None

    def get_tweepy_api(self):  # pragma: no cover
        return None


class FakeResponse:
    def __init__(self, status: int, payload: dict[str, Any]):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture()
def oauth2_client():
    return XClient(DummyAuth(), dry_run=False)


@pytest.fixture()
def patch_requests(monkeypatch):
    # Ensure requests import path is considered present
    monkeypatch.setitem(builtins.__dict__, "requests", SimpleNamespace())


@pytest.fixture()
def fake_request(monkeypatch):
    calls = []

    def _fake(method, url, headers=None, params=None, json_body=None, timeout=None):
        calls.append((method, url))
        # Return minimal payload based on URL pattern.
        if url.endswith("/users/me"):
            return FakeResponse(200, {"data": {"id": "me123", "username": "agent"}})
        if "/users/by/username/" in url:
            return FakeResponse(200, {"data": {"id": "u55", "username": url.split("/")[-1], "public_metrics": {}}})
        if "/tweets/search/recent" in url:
            return FakeResponse(
                200,
                {
                    "data": [{"id": "t1", "author_id": "u55", "public_metrics": {}}],
                    "includes": {"users": [{"id": "u55", "username": "agent"}]},
                    "meta": {},
                },
            )
        if url.endswith("/tweets") and method == "POST":
            return FakeResponse(201, {"data": {"id": "new123"}})
        if "/tweets/" in url and method == "GET":
            return FakeResponse(200, {"data": {"id": url.split("/")[-1], "text": "hello"}})
        if method == "DELETE" and "/tweets/" in url:
            return FakeResponse(200, {"data": {"deleted": True}})
        if url.endswith("/likes") and method == "POST":
            return FakeResponse(200, {"data": {"liked": True}})
        if "/likes/" in url and method == "DELETE":
            return FakeResponse(200, {"data": {"liked": False}})
        if url.endswith("/retweets") and method == "POST":
            return FakeResponse(200, {"data": {"retweeted": True}})
        if "/retweets/" in url and method == "DELETE":
            return FakeResponse(200, {})
        if url.endswith("/following") and method == "POST":
            return FakeResponse(200, {"data": {"following": True}})
        return FakeResponse(200, {})

    monkeypatch.setattr("src.x_client.request_with_retries", _fake)
    return calls


def test_oauth2_get_me(oauth2_client, fake_request):
    data = oauth2_client.get_me()
    assert data["data"]["id"] == "me123"
    assert oauth2_client.me_id == "me123"


@pytest.mark.parametrize("username", ["alice", "bob"])
def test_oauth2_get_user_by_username(oauth2_client, fake_request, username):
    data = oauth2_client.get_user_by_username(username)
    assert data["data"]["username"] == username


def test_oauth2_get_tweet(oauth2_client, fake_request):
    t = oauth2_client.get_tweet("t42")
    assert t["data"]["id"] == "t42"


def test_oauth2_create_post(oauth2_client, fake_request):
    resp = oauth2_client.create_post("Hello world", reply_to="t1", media_ids=["m1"], quote_tweet_id="q2")
    assert resp["data"]["id"] == "new123"


def test_oauth2_search_recent_single_page(oauth2_client, fake_request):
    res = oauth2_client.search_recent("python", max_results=5)
    assert len(res) == 1
    assert res[0]["author_username"] == "agent"


@pytest.mark.parametrize(
    "method_name, arg",
    [
        ("delete_post", "del123"),
        ("like_post", "l5"),
        ("unlike_post", "l5"),
        ("retweet", "r7"),
        ("unretweet", "r7"),
        ("follow_user", "u99"),
    ],
)
def test_oauth2_engagement_methods(oauth2_client, fake_request, method_name, arg):
    oauth2_client.me_id = "me123"  # ensure populated
    fn = getattr(oauth2_client, method_name)
    assert fn(arg) is True or fn(arg) is False  # boolean return


def test_oauth2_requests_missing(monkeypatch):
    # Simulate requests import missing for error branch coverage
    from src import x_client as xc

    monkeypatch.setattr(xc, "requests", None)
    client = XClient(DummyAuth(), dry_run=False)
    with pytest.raises(RuntimeError) as ei:
        client.get_me()
    assert "requests library not installed" in str(ei.value)
