import os
import sys
import types
from typing import Any, cast

import pytest

# Ensure src on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

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
    state = {"calls": 0, "last_headers": None, "last_json": None, "last_method": None, "last_url": None}

    def request(method, url, headers=None, params=None, json=None, timeout=None):
        state["calls"] += 1
        state["last_headers"] = dict(headers or {})
        state["last_json"] = json
        state["last_method"] = method
        state["last_url"] = url
        item = sequence[min(state["calls"] - 1, len(sequence) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    return types.SimpleNamespace(request=request), state


def test_create_post_variants_and_retry_and_4xx(monkeypatch):
    # First a retry case: 500 then 200 for POST
    seq = [FakeResponse(500, {}), FakeResponse(200, {"data": {"id": "t1"}})]
    fake_requests, state = make_fake_requests(seq)

    import reliability as rel

    monkeypatch.setattr(rel, "requests", fake_requests, raising=False)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(cast(Any, auth))

    res = client.create_post("hello world", reply_to="123", media_ids=["m1", "m2"], quote_tweet_id="789")
    assert res["data"]["id"] == "t1"
    # Payload should include reply/media/quote fields
    assert state["last_json"]["reply"]["in_reply_to_tweet_id"] == "123"
    assert state["last_json"]["media"]["media_ids"] == ["m1", "m2"]
    assert state["last_json"]["quote_tweet_id"] == "789"
    # Retries should have been attempted
    assert state["calls"] >= 2

    # Now simulate a 400 non-retryable error and ensure it raises
    seq_err = [FakeResponse(400, {})]
    fake_bad, _ = make_fake_requests(seq_err)
    monkeypatch.setattr(rel, "requests", fake_bad, raising=False)
    with pytest.raises(Exception):
        client.create_post("bad")


def test_upload_media_behavior_oauth2_and_tweepy(monkeypatch):
    # OAuth2 mode should raise NotImplementedError
    oauth_auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client_oauth = XClient(cast(Any, oauth_auth))
    with pytest.raises(NotImplementedError):
        client_oauth.upload_media("/tmp/file.png")

    # Tweepy mode should call API v1.1 media_upload and return id string
    class FakeMedia:
        media_id_string = "mid-123"

    class FakeAPIv1:
        def media_upload(self, filename, chunked=True):
            assert chunked is True
            assert filename.endswith("file.png")
            return FakeMedia()

    class FakeAuth:
        mode = "tweepy"

        def get_tweepy_api(self):
            return FakeAPIv1()

    client_tw = XClient(cast(Any, FakeAuth()))
    mid = client_tw.upload_media("/tmp/file.png")
    assert mid == "mid-123"


def test_search_recent_oauth2_mapping(monkeypatch):
    data = {
        "data": [
            {"id": "1", "author_id": "u1", "public_metrics": {"like_count": 2}},
            {"id": "2", "author_id": "u2", "public_metrics": {"like_count": 3}},
        ],
        "includes": {"users": [{"id": "u1", "username": "alice"}, {"id": "u2", "username": "bob"}]},
    }
    seq = [FakeResponse(200, data)]
    fake_requests, _ = make_fake_requests(seq)

    import reliability as rel

    monkeypatch.setattr(rel, "requests", fake_requests, raising=False)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(cast(Any, auth))
    results = client.search_recent("foo")
    assert len(results) == 2
    assert results[0]["author_username"] == "alice"
    assert results[1]["author_username"] == "bob"


def test_like_unlike_and_delete_paths(monkeypatch):
    # Patch get_me to populate me_id without network
    def fake_get_me(self):
        self.me_id = "me"
        return {"data": {"id": "me"}}

    monkeypatch.setattr(XClient, "get_me", fake_get_me)

    # like -> returns liked True
    seq_like = [FakeResponse(200, {"data": {"liked": True}})]
    # unlike -> returns liked False in response per implementation semantics
    seq_unlike = [FakeResponse(200, {"data": {"liked": False}})]
    # delete -> returns deleted True
    seq_del = [FakeResponse(200, {"data": {"deleted": True}})]

    import reliability as rel

    fake_like, _ = make_fake_requests(seq_like)
    fake_unlike, _ = make_fake_requests(seq_unlike)
    fake_delete, _ = make_fake_requests(seq_del)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(cast(Any, auth))

    # like
    monkeypatch.setattr(rel, "requests", fake_like, raising=False)
    assert client.like_post("t1") is True

    # unlike
    monkeypatch.setattr(rel, "requests", fake_unlike, raising=False)
    assert client.unlike_post("t1") is False

    # delete
    monkeypatch.setattr(rel, "requests", fake_delete, raising=False)
    assert client.delete_post("t1") is True


def test_get_user_by_username_404_raises(monkeypatch):
    seq = [FakeResponse(404, {})]
    fake_requests, _ = make_fake_requests(seq)

    import reliability as rel

    monkeypatch.setattr(rel, "requests", fake_requests, raising=False)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(cast(Any, auth))
    import pytest

    with pytest.raises(Exception):
        client.get_user_by_username("nobody")
