import random
from typing import Any, cast

from actions import act_on_search


class DummyClient:
    def __init__(self, posts: list[dict[str, Any]]):
        self._posts = posts

    def search_recent(self, query: str, max_results: int = 10):  # noqa: D401 - simple dummy
        return self._posts[:max_results]

    # The following methods emulate x_client behavior but are no-ops for dry-run.
    def create_post(self, text: str, reply_to: str | None = None):
        return {"data": {"id": "reply123"}}

    def like_post(self, post_id: str):  # pragma: no cover - not hit in dry-run
        pass

    def follow_user(self, user_id: str):  # pragma: no cover - not hit in dry-run
        pass

    def retweet(self, post_id: str):  # pragma: no cover - not hit in dry-run
        pass


class DummyStorage:
    def __init__(self):
        self.logged = []

    def already_acted(self, post_id: str, kind: str) -> bool:
        return False

    def log_action(self, **kwargs):  # pragma: no cover - not hit in dry-run
        self.logged.append(kwargs)


def test_act_on_search_dry_run_all_action_types(monkeypatch):
    # Deterministic randomness: keep order stable and uniform jitter
    monkeypatch.setattr(random, "shuffle", lambda x: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)

    posts = [
        {"id": "p1", "author_id": "authorA"},
        {"id": "p2", "author_id": "authorB"},
    ]
    client = DummyClient(posts)
    storage = DummyStorage()

    limits = {"reply": 1, "like": 1, "follow": 1, "repost": 1}
    jitter_bounds = (0, 0)
    remaining = act_on_search(
        client=cast(Any, client),
        storage=cast(Any, storage),
        query="test",
        limits=limits,
        jitter_bounds=jitter_bounds,
        dry_run=True,
        me_user_id="selfUser",
    )

    # All counts should drop to zero in dry-run path
    assert remaining == {"reply": 0, "like": 0, "follow": 0, "repost": 0}


def test_act_on_search_skips_self(monkeypatch):
    monkeypatch.setattr(random, "shuffle", lambda x: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    posts = [
        {"id": "p1", "author_id": "selfUser"},  # should be skipped entirely
        {"id": "p2", "author_id": "other"},
    ]
    client = DummyClient(posts)
    storage = DummyStorage()
    limits = {"reply": 1}
    remaining = act_on_search(
        client=cast(Any, client),
        storage=cast(Any, storage),
        query="test",
        limits=limits,
        jitter_bounds=(0, 0),
        dry_run=True,
        me_user_id="selfUser",
    )
    # reply should decrement to zero after acting on second post only
    assert remaining == {"reply": 0}


def test_act_on_search_live_paths(monkeypatch):
    # Deterministic execution and no actual waiting
    monkeypatch.setattr(random, "shuffle", lambda x: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)

    posts = [
        {"id": "p1", "author_id": "authorA"},
    ]

    class LiveClient(DummyClient):
        def __init__(self, posts):
            super().__init__(posts)
            self.calls: list[tuple[str, str]] = []

        def create_post(self, text: str, reply_to: str | None = None):
            self.calls.append(("reply", reply_to or ""))
            return {"data": {"id": "r1"}}

        def like_post(self, post_id: str):
            self.calls.append(("like", post_id))

        def follow_user(self, user_id: str):
            self.calls.append(("follow", user_id))

        def retweet(self, post_id: str):
            self.calls.append(("repost", post_id))

    class LiveStorage(DummyStorage):
        def log_action(self, **kwargs):
            self.logged.append(kwargs)

    client = LiveClient(posts)
    storage = LiveStorage()
    limits = {"reply": 1, "like": 1, "follow": 1, "repost": 1}
    remaining = act_on_search(
        client=cast(Any, client),
        storage=cast(Any, storage),
        query="q",
        limits=limits,
        jitter_bounds=(0, 0),
        dry_run=False,
        me_user_id="selfUser",
    )

    # All decremented to zero
    assert remaining == {"reply": 0, "like": 0, "follow": 0, "repost": 0}
    # Verify side effects recorded
    kinds = {k for k, _ in client.calls}
    assert kinds == {"reply", "like", "follow", "repost"}
    logged_kinds = {e["kind"] for e in storage.logged}
    assert logged_kinds == {"reply", "like", "follow", "repost"}


def test_act_on_search_quota_exhaustion_breaks(monkeypatch):
    # Make ordering deterministic and avoid sleeping
    monkeypatch.setattr(random, "shuffle", lambda x: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: 0)

    posts = [{"id": f"p{i}", "author_id": f"u{i}"} for i in range(10)]
    client = DummyClient(posts)
    storage = DummyStorage()

    limits = {"reply": 2, "like": 0, "follow": 0, "repost": 0}
    remaining = act_on_search(
        client=cast(Any, client),
        storage=cast(Any, storage),
        query="q",
        limits=limits,
        jitter_bounds=(0, 0),
        dry_run=True,
        me_user_id="selfUser",
    )

    # Should early-break once reply quota is exhausted (hits the all<=0 branch)
    assert remaining == {"reply": 0, "like": 0, "follow": 0, "repost": 0}
