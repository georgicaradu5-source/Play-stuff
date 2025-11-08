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
    state = {"calls": 0, "last_headers": None, "last_timeout": None, "last_json": None, "last_data": None}

    def request(method, url, headers=None, params=None, json=None, data=None, timeout=None):  # noqa: A002 - shadow builtins ok in test
        state["calls"] += 1
        state["last_headers"] = dict(headers or {})
        state["last_timeout"] = timeout
        state["last_json"] = json
        state["last_data"] = data
        item = sequence[min(state["calls"] - 1, len(sequence) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    fake_requests = types.SimpleNamespace(request=request, Timeout=TimeoutError, HTTPError=Exception)
    return fake_requests, state


def test_upload_media_tweepy_success():
    class DummyAPI:
        def media_upload(self, filename, chunked=True):
            return types.SimpleNamespace(media_id_string="mid123")

    class DummyAuth:
        mode = "tweepy"

        def get_tweepy_api(self):
            return DummyAPI()

    client = XClient(DummyAuth())  # type: ignore[arg-type]
    media_id = client.upload_media("/tmp/foo.png")
    assert media_id == "mid123"


def test_upload_media_oauth2_not_implemented():
    auth = types.SimpleNamespace(mode="oauth2", access_token="tok")
    client = XClient(auth)
    try:
        client.upload_media("/tmp/foo.png")
        assert False, "Expected NotImplementedError"
    except NotImplementedError:
        pass


def test_create_post_oauth2_payload_fields(monkeypatch):
    seq = [FakeResponse(200, {"data": {"id": "p1"}})]
    fake_requests, state = make_fake_requests(seq)

    import reliability as rel

    monkeypatch.setattr(rel, "requests", types.SimpleNamespace(request=fake_requests.request), raising=False)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(auth)

    res = client.create_post(
        "hello",
        reply_to="123",
        media_ids=["m1", "m2"],
        quote_tweet_id="789",
    )
    assert res.get("data")
    assert state["last_json"].get("reply", {}).get("in_reply_to_tweet_id") == "123"
    assert state["last_json"].get("media", {}).get("media_ids") == ["m1", "m2"]
    assert state["last_json"].get("quote_tweet_id") == "789"


def test_create_post_tweepy_kwargs_mapping():
    captured = {}

    class DummyClient:
        def create_tweet(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(data={"id": "tw1"})

    class DummyAuth:
        mode = "tweepy"

        def get_tweepy_client(self):
            return DummyClient()

    client = XClient(DummyAuth())  # type: ignore[arg-type]
    res = client.create_post("hi", reply_to="t1", media_ids=["m1"], quote_tweet_id="q1")
    assert res["data"]["id"] == "tw1"
    assert captured["in_reply_to_tweet_id"] == "t1"
    assert captured["media_ids"] == ["m1"]
    assert captured["quote_tweet_id"] == "q1"


def test_engagement_oauth2_like_unlike_retweet_follow(monkeypatch):
    # Sequence of responses for like, unlike, retweet, unretweet, follow
    seq = [
        FakeResponse(200, {"data": {"liked": True}}),
        FakeResponse(200, {"data": {"liked": False}}),
        FakeResponse(200, {"data": {"retweeted": True}}),
        FakeResponse(200, {}),  # unretweet DELETE returns 200
        FakeResponse(200, {"data": {"following": True}}),
    ]
    fake_requests, state = make_fake_requests(seq)

    import reliability as rel

    monkeypatch.setattr(rel, "requests", types.SimpleNamespace(request=fake_requests.request), raising=False)

    auth = types.SimpleNamespace(mode="oauth2", access_token="token")
    client = XClient(auth)
    client.me_id = "me"

    assert client.like_post("t1") is True
    assert client.unlike_post("t1") is False
    assert client.retweet("t2") is True
    assert client.unretweet("t2") is True


def test_tweepy_engagements_basic():
    class DummyClient:
        def __init__(self):
            self.calls = []

        def like(self, tweet_id):
            self.calls.append(("like", tweet_id))
            return types.SimpleNamespace(data={"liked": True})

        def unlike(self, tweet_id):
            self.calls.append(("unlike", tweet_id))
            return types.SimpleNamespace(data={"liked": False})

        def retweet(self, tweet_id):
            self.calls.append(("retweet", tweet_id))
            return types.SimpleNamespace(data={"retweeted": True})

        def unretweet(self, tweet_id):
            self.calls.append(("unretweet", tweet_id))
            return types.SimpleNamespace(data={"retweeted": False})

        def follow_user(self, user_id):
            self.calls.append(("follow_user", user_id))
            return types.SimpleNamespace(data={"following": True})

    class DummyAuth:
        mode = "tweepy"

        def get_tweepy_client(self):
            return DummyClient()

    client = XClient(DummyAuth())  # type: ignore[arg-type]
    assert client.like_post("t1") is True
    # Unlike returns the 'liked' flag from API; current implementation returns False here
    assert client.unlike_post("t1") is False
    assert client.retweet("t2") is True
    assert client.unretweet("t2") is True
    assert client.follow_user("u1") is True
