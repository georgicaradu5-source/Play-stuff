import builtins
from unittest.mock import patch

import scheduler
from orchestration import engine as eng


class DummyClient:  # minimal stub matching required XClient interface for tests
    def __init__(self):
        self.me_user_id = "me123"

    def get_me(self):
        return {"data": {"id": self.me_user_id}}


class DummyStorage:  # minimal stub matching required Storage interface for tests
    def __init__(self, duplicate=False):
        self._duplicate = duplicate

    def is_text_duplicate(self, text: str, days: int = 7) -> bool:
        return self._duplicate

    # Stubs used by act_on_search if ever called (shouldn't in these tests)
    def already_acted(self, *_args, **_kwargs):
        return False

    def log_action(self, **_kwargs):
        pass

    def bandit_choose(self, topics):
        return topics[0] if topics else "automation"


def test_engine_run_post_action_duplicate_dry_run():
    storage = DummyStorage(duplicate=True)
    client = DummyClient()
    config = {"topics": ["testing"], "schedule": {"windows": ["morning"]}}

    # Directly call engine; this covers duplicate attribute path in engine
    eng.run_post_action(client, storage, config, dry_run=True)


def test_engine_run_interact_actions_no_queries_prints_info():
    storage = DummyStorage()
    client = DummyClient()
    config = {"queries": []}

    with patch.object(builtins, "print") as mock_print:
        eng.run_interact_actions(client, storage, config, dry_run=True)
    # Ensure informational messages were printed
    printed = "".join(str(c) for c in mock_print.call_args_list)
    assert "No search queries configured" in printed


def test_engine_run_interact_actions_feature_flags_and_query_extraction():
    storage = DummyStorage()
    client = DummyClient()
    config = {
        "queries": [{"query": "python tips"}, "ai news", {"query": ""}],
        "feature_flags": {"allow_likes": "off", "allow_follows": "off"},
        "max_per_window": {"reply": 3, "like": 10, "follow": 3, "repost": 1},
        "jitter_seconds": [5, 15],
    }

    calls = []

    def _fake_act_on_search(**kwargs):
        calls.append(kwargs)
        # Return remaining limits to simulate progress
        return kwargs.get("limits", {})

    with patch.object(eng, "act_on_search", _fake_act_on_search):
        eng.run_interact_actions(client, storage, config, dry_run=True)

    # Should have been called for non-empty queries (2 calls)
    assert len(calls) == 2
    # Query strings extracted properly
    assert calls[0]["query"] == "python tips"
    assert calls[1]["query"] == "ai news"
    # Feature flags applied: likes and follows disabled
    assert calls[0]["limits"]["like"] == 0
    assert calls[0]["limits"]["follow"] == 0


def test_scheduler_run_interact_actions_delegates_when_not_dry_run():
    storage = DummyStorage()
    client = DummyClient()
    config = {"queries": []}

    # When not dry-run, shim should delegate to engine implementation
    # (exercise the non-dry path return in scheduler shim)
    scheduler.run_interact_actions(client, storage, config, dry_run=False)


def test_engine_run_post_action_with_learning_enabled():
    """Test bandit topic selection path when learning is enabled (covers line 172)."""
    storage = DummyStorage()
    storage.bandit_choose = lambda topics: topics[0]  # stub bandit
    client = DummyClient()
    config = {
        "topics": ["ai", "python"],
        "learning": {"enabled": True},
        "schedule": {"windows": ["morning"]},
    }

    eng.run_post_action(client, storage, config, dry_run=True)


def test_engine_run_post_action_span_exception_handling():
    """Test span.set_attribute exception handling in run_post_action (lines 176-181)."""

    class BrokenSpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, key: str, value):
            raise RuntimeError("Span error")

    def broken_start_span(name: str):
        return BrokenSpan()

    storage = DummyStorage()
    client = DummyClient()
    config = {"topics": ["testing"], "schedule": {"windows": ["morning"]}}

    # Temporarily inject broken span to trigger exception path
    with patch.object(eng, "start_span", broken_start_span):
        # Should not raise; exceptions are caught
        eng.run_post_action(client, storage, config, dry_run=True)


def test_scheduler_shim_non_dry_post_action_delegates():
    """Test scheduler shim non-dry-run path for run_post_action (covers lines 75-76)."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"topics": ["automation"], "schedule": {"windows": ["morning"]}}

    # Non-dry path delegates to original engine implementation
    with patch("scheduler._ORIGINAL_RUN_POST_ACTION") as mock_orig:
        scheduler.run_post_action(client, storage, config, dry_run=False)
        assert mock_orig.called


def test_act_on_search_jitter_sleep():
    """Test that act_on_search sleeps with jitter after actions (covers jitter branches)."""
    storage = DummyStorage()
    client = DummyClient()
    # Mock search_recent to return a post
    client.search_recent = lambda q, max_results: [{"id": "p1", "author_id": "a1"}]  # type: ignore[method-assign]

    calls = []

    def mock_sleep(duration):
        calls.append(duration)

    import time

    with patch.object(time, "sleep", mock_sleep):
        # Call with limits allowing one action
        eng.act_on_search(
            client=client,
            storage=storage,
            query="test",
            limits={"reply": 1, "like": 0, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=True,
            me_user_id="me123",
        )

    # Should have slept once with jitter value in bounds
    assert len(calls) == 1
    assert 1 <= calls[0] <= 2


def test_engine_run_interact_actions_span_exception_paths():
    """Test span exception handling in run_interact_actions (lines 276-277, 292-293)."""

    class BrokenSpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, key: str, value):
            raise RuntimeError("Span error")

    def broken_start_span(name: str):
        return BrokenSpan()

    storage = DummyStorage()
    client = DummyClient()
    config = {"queries": ["python"], "max_per_window": {"reply": 0, "like": 0, "follow": 0, "repost": 0}}

    # Temporarily inject broken span to trigger exception paths
    with patch.object(eng, "start_span", broken_start_span):
        with patch.object(eng, "act_on_search", lambda **kw: {}):
            # Should not raise; exceptions are caught at lines 276-277, 292-293
            eng.run_interact_actions(client, storage, config, dry_run=True)


def test_scheduler_shim_non_dry_interact_actions():
    """Test scheduler shim non-dry-run interact path (covers lines 75-76 when queries present)."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"queries": ["test"]}

    with patch("scheduler._ORIGINAL_RUN_INTERACT_ACTIONS") as mock_orig:
        scheduler.run_interact_actions(client, storage, config, dry_run=False)
        assert mock_orig.called


def test_engine_run_post_action_exception_in_duplicate_span():
    """Test span exception handling in duplicate detection path (lines 192-193)."""

    class BrokenSpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, key: str, value):
            if key == "duplicate":
                raise RuntimeError("Span error on duplicate")

    def broken_start_span(name: str):
        return BrokenSpan()

    storage = DummyStorage(duplicate=True)
    client = DummyClient()
    config = {"topics": ["testing"], "schedule": {"windows": ["morning"]}}

    with patch.object(eng, "start_span", broken_start_span):
        # Should not raise; exception is caught at lines 192-193
        eng.run_post_action(client, storage, config, dry_run=True)


def test_engine_run_post_action_random_topic_fallback():
    """Test random topic selection when learning is disabled (covers line 69 exception path)."""

    class BrokenSpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, key: str, value):
            raise RuntimeError("Span error")

    def broken_start_span(name: str):
        return BrokenSpan()

    storage = DummyStorage()
    client = DummyClient()
    config = {"topics": ["ai"], "learning": {"enabled": False}, "schedule": {"windows": ["morning"]}}

    with patch.object(eng, "start_span", broken_start_span):
        # Should not raise; span exception caught (line 69 is exception path for span.set_attribute)
        eng.run_post_action(client, storage, config, dry_run=True)


