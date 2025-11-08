from datetime import time as dtime


def test_current_slot_basic_inside_window():
    from orchestration.engine import current_slot

    slot = current_slot(["morning"], now=dtime(9, 30))
    assert slot == "morning"


def test_current_slot_cross_midnight():
    from orchestration.engine import current_slot

    # 01:00 should fall into late-night (23:00 -> 02:00)
    slot = current_slot(["late-night"], now=dtime(1, 0))
    assert slot == "late-night"


class FakeClient:
    def __init__(self):
        self.posts = []

    def get_me(self):
        return {"data": {"id": "me"}}

    def create_post(self, text: str):  # pragma: no cover (not used in dry-run)
        self.posts.append(text)
        return {"data": {"id": str(len(self.posts))}}


class FakeStorage:
    def __init__(self, duplicate=False):
        self.duplicate = duplicate
        self.actions = []

    def is_text_duplicate(self, text: str, days: int = 7) -> bool:
        return self.duplicate

    # Minimal bandit choose
    def bandit_choose(self, items):
        return items[0]

    # Minimal API used by run_post_action in non-dry path
    def log_action(self, **kwargs):  # pragma: no cover
        self.actions.append(kwargs)


def test_run_post_action_dry_run_not_duplicate():
    from orchestration.engine import run_post_action

    client = FakeClient()
    storage = FakeStorage(duplicate=False)
    config = {"topics": ["t1"], "schedule": {"windows": ["morning"]}}

    # Should not raise
    run_post_action(client, storage, config, dry_run=True)


def test_run_post_action_duplicate_skips():
    from orchestration.engine import run_post_action

    client = FakeClient()
    storage = FakeStorage(duplicate=True)
    config = {"topics": ["t1"], "schedule": {"windows": ["morning"]}}

    # Should return early without errors
    run_post_action(client, storage, config, dry_run=True)


def test_run_interact_actions_invokes_act_on_search(monkeypatch):
    import orchestration.engine as engine

    client = FakeClient()
    storage = FakeStorage()
    calls = []

    def fake_act_on_search(**kwargs):
        calls.append(kwargs)
        # Return limits unchanged
        return kwargs.get("limits", {})

    monkeypatch.setattr(engine, "act_on_search", fake_act_on_search)

    config = {
        "queries": ["foo", {"query": "bar"}, ""],
        "jitter_seconds": [1, 2],
        "max_per_window": {"reply": 1, "like": 2, "follow": 3, "repost": 4},
        "feature_flags": {"allow_likes": "on", "allow_follows": "off"},
    }

    engine.run_interact_actions(client, storage, config, dry_run=True)

    # Two non-empty queries should trigger two calls
    assert len(calls) == 2
    # Feature flag off should set follows to 0 in passed limits
    assert all(call["limits"]["follow"] == 0 for call in calls)


def test_run_scheduler_calls_children(monkeypatch):
    import orchestration.engine as engine

    client = FakeClient()
    storage = FakeStorage()
    calls = {"post": 0, "interact": 0}

    def fake_post(*args, **kwargs):
        calls["post"] += 1

    def fake_interact(*args, **kwargs):
        calls["interact"] += 1

    monkeypatch.setattr(engine, "run_post_action", fake_post)
    monkeypatch.setattr(engine, "run_interact_actions", fake_interact)

    config = {"cadence": {"weekdays": [1, 2, 3, 4, 5, 6, 7]}}
    engine.run_scheduler(client, storage, config, mode="both", dry_run=True)

    assert calls == {"post": 1, "interact": 1}
