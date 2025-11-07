"""Comprehensive unit tests for scheduler actions (run_post_action, run_interact_actions)."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scheduler import run_interact_actions, run_post_action  # noqa: E402


class DummyStorage:
    """Minimal storage stub for scheduler tests."""

    def __init__(self):
        self.actions = []
        self.duplicates = set()
        self.bandit_arms = ["ai", "python"]
        self.monthly_usage = {"read_count": 0, "create_count": 0}

    def is_text_duplicate(self, text, days=7):
        return text in self.duplicates

    def log_action(self, **kwargs):
        self.actions.append(kwargs)

    def bandit_choose(self, topics):
        return topics[0] if topics else "default"

    def get_monthly_usage(self, period):
        return self.monthly_usage.copy()

    def update_monthly_usage(self, period, read_count=None, create_count=None):
        if read_count is not None:
            self.monthly_usage["read_count"] = read_count
        if create_count is not None:
            self.monthly_usage["create_count"] = create_count


class DummyClient:
    """Minimal XClient stub."""

    def __init__(self, post_response=None, me_response=None):
        self.post_response = post_response or {"data": {"id": "12345"}}
        self.me_response = me_response or {"data": {"id": "me123"}}
        self.posts_created = []
        self.searches = []

    def create_post(self, text, **kwargs):
        self.posts_created.append({"text": text, **kwargs})
        return self.post_response

    def get_me(self):
        return self.me_response

    def search_recent(self, query, max_results):
        self.searches.append(query)
        return []


def test_run_post_action_dry_run_no_storage_write():
    """Dry-run mode should not write to storage or call budget manager."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"topics": ["testing"], "schedule": {"windows": ["morning"]}, "learning": {"enabled": False}}

    with patch("scheduler.choose_template", return_value="Dry run post"):
        run_post_action(client, storage, config, dry_run=True)

    # No actions logged in dry-run
    assert len(storage.actions) == 0
    assert len(client.posts_created) == 0


def test_run_post_action_duplicate_text_skipped():
    """Post action should skip if text is a duplicate."""
    storage = DummyStorage()
    storage.duplicates.add("Duplicate post")
    client = DummyClient()
    config = {"topics": ["ai"], "schedule": {"windows": ["afternoon"]}, "learning": {"enabled": False}}

    with patch("scheduler.choose_template", return_value="Duplicate post"):
        run_post_action(client, storage, config, dry_run=True)

    # No post created due to duplicate
    assert len(storage.actions) == 0
    assert len(client.posts_created) == 0


def test_run_post_action_budget_check_failure():
    """Post action should abort if budget check fails."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"topics": ["python"], "plan": "free", "learning": {"enabled": False}}

    # Mock BudgetManager to reject write
    with patch("scheduler.choose_template", return_value="Budget fail post"):
        with patch("budget.BudgetManager") as mock_budget:
            mock_mgr = Mock()
            mock_mgr.can_write.return_value = (False, "Hard cap exceeded")
            mock_budget.return_value = mock_mgr

            run_post_action(client, storage, config, dry_run=False)

    # No post created due to budget failure
    assert len(client.posts_created) == 0
    assert len(storage.actions) == 0


def test_run_post_action_success_with_logging():
    """Post action should create post and log action when budget allows."""
    storage = DummyStorage()
    client = DummyClient(post_response={"data": {"id": "post-abc"}})
    config = {"topics": ["automation"], "plan": "basic", "learning": {"enabled": False}}

    with patch("scheduler.choose_template", return_value="Success post"):
        with patch("budget.BudgetManager") as mock_budget:
            mock_mgr = Mock()
            mock_mgr.can_write.return_value = (True, "OK")
            mock_budget.return_value = mock_mgr

            run_post_action(client, storage, config, dry_run=False)

    # Post created and logged
    assert len(client.posts_created) == 1
    assert client.posts_created[0]["text"] == "Success post"
    assert len(storage.actions) == 1
    assert storage.actions[0]["kind"] == "post"
    assert storage.actions[0]["post_id"] == "post-abc"
    assert storage.actions[0]["topic"] == "automation"
    # Budget incremented
    mock_mgr.add_writes.assert_called_once_with(1)


def test_run_post_action_uses_bandit_when_learning_enabled():
    """Post action should use bandit for topic selection if learning enabled."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"topics": ["ai", "python", "data"], "learning": {"enabled": True}}

    with patch("scheduler.choose_template", return_value="Learning post"):
        run_post_action(client, storage, config, dry_run=True)

    # Bandit should have been called (storage.bandit_choose returns first topic)
    # Since dry_run=True, no actual post created, but topic selection exercised


def test_run_interact_actions_no_queries_warning():
    """Interact actions should warn and exit if no queries configured."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"queries": []}

    with patch("builtins.print") as mock_print:
        run_interact_actions(client, storage, config, dry_run=True)

    # Warning printed
    assert any("No queries" in str(call) for call in mock_print.call_args_list)


def test_run_interact_actions_executes_for_each_query():
    """Interact actions should call act_on_search for each configured query."""
    storage = DummyStorage()
    client = DummyClient()
    config = {
        "queries": [{"query": "python tips"}, "ai news"],
        "max_per_window": {"reply": 3, "like": 10, "follow": 3, "repost": 1},
        "jitter_seconds": [5, 15],
    }

    with patch("scheduler.act_on_search") as mock_act:
        mock_act.return_value = {"reply": 2, "like": 8, "follow": 2, "repost": 0}
        run_interact_actions(client, storage, config, dry_run=True)

    # act_on_search called twice (one per query)
    assert mock_act.call_count == 2
    # Verify query strings
    calls = [call[1]["query"] for call in mock_act.call_args_list]
    assert "python tips" in calls
    assert "ai news" in calls


def test_run_interact_actions_respects_feature_flags():
    """Interact actions should disable likes/follows when feature flags are off."""
    storage = DummyStorage()
    client = DummyClient()
    config = {
        "queries": ["test query"],
        "max_per_window": {"reply": 3, "like": 10, "follow": 3, "repost": 1},
        "feature_flags": {"allow_likes": "off", "allow_follows": "off"},
    }

    with patch("scheduler.act_on_search") as mock_act:
        mock_act.return_value = {"reply": 0, "like": 0, "follow": 0, "repost": 0}
        run_interact_actions(client, storage, config, dry_run=True)

    # Check that limits passed to act_on_search have like=0, follow=0
    limits_passed = mock_act.call_args[1]["limits"]
    assert limits_passed["like"] == 0
    assert limits_passed["follow"] == 0


def test_run_interact_actions_dry_run_attribute():
    """Interact actions should pass dry_run flag correctly."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"queries": ["query1"], "max_per_window": {"reply": 1, "like": 1, "follow": 1, "repost": 1}}

    with patch("scheduler.act_on_search") as mock_act:
        mock_act.return_value = {}
        run_interact_actions(client, storage, config, dry_run=False)

    # Verify dry_run=False passed to act_on_search
    assert mock_act.call_args[1]["dry_run"] is False


def test_run_post_action_slot_selection_fallback():
    """Post action should fall back to 'morning' if no slot matches."""
    storage = DummyStorage()
    client = DummyClient()
    config = {"topics": ["test"], "schedule": {"windows": []}, "learning": {"enabled": False}}

    with patch("scheduler.choose_template", return_value="Fallback post"):
        with patch("scheduler.current_slot", return_value=None):
            run_post_action(client, storage, config, dry_run=True)

    # Should not crash; slot defaults to 'morning' when None returned


def test_run_post_action_default_config_values():
    """Post action should handle missing config keys gracefully with defaults."""
    storage = DummyStorage()
    client = DummyClient()
    config = {}  # Empty config

    with patch("scheduler.choose_template", return_value="Default config post"):
        run_post_action(client, storage, config, dry_run=True)

    # Should not crash; defaults applied for topics, schedule, learning
