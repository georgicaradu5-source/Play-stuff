import random

from src import actions


class DummyStorage:
    def __init__(self):
        self.acted = set()
        self.logged = []

    def already_acted(self, post_id, kind):
        return (post_id, kind) in self.acted

    def log_action(self, **kwargs):
        self.logged.append(kwargs)


def test_choose_template_returns_valid():
    for topic in actions.TEMPLATES:
        for _ in range(10):
            t = actions.choose_template(topic)
            assert t in actions.TEMPLATES[topic]
    # Unknown topic returns fallback
    assert actions.choose_template("not-a-topic") == "Sharing a quick note on automation and data."


def test_make_post_and_reply():
    text, media = actions.make_post("ai", "morning")
    assert text in actions.TEMPLATES["ai"]
    assert media is None
    reply = actions.helpful_reply()
    assert reply in actions.REPLY_TEMPLATES


def test_act_on_search_dedup_and_limits(monkeypatch):
    class DummyClient:
        def search_recent(self, query, max_results):
            return [
                {"id": "1", "author_id": "a"},
                {"id": "2", "author_id": "b"},
                {"id": "3", "author_id": "me"},
            ]

        def create_post(self, text, reply_to=None):
            return {"data": {"id": "r1"}}

        def like_post(self, pid):
            pass

        def follow_user(self, uid):
            pass

        def retweet(self, pid):
            pass

    storage = DummyStorage()
    storage.acted.add(("1", "reply"))  # Already replied
    storage.acted.add(("2", "like"))  # Already liked
    limits = {"reply": 1, "like": 1, "follow": 1, "repost": 1}
    monkeypatch.setattr(random, "shuffle", lambda x: None)  # Deterministic
    remaining = actions.act_on_search(DummyClient(), storage, "query", limits, (0, 0), dry_run=True, me_user_id="me")
    # Only reply to 2, like 1, follow a, repost 2 (since 3 is self)
    assert remaining["reply"] == 0
    assert remaining["like"] == 0  # like performed on 1, 2 already liked
    assert remaining["follow"] == 0
    assert remaining["repost"] == 0
