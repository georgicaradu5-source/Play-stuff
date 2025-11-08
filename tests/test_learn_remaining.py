"""
Tests for remaining uncovered lines in src/learn.py.

Coverage targets:
- Line 95: default_arm is None path in settle_all
- Lines 103-105: Exception handling in settle_all
- Lines 115-116: print_bandit_stats with no bandit data
"""

from src import learn


class MockStorage:
    """Mock storage for testing."""

    def __init__(self, bandit_arms=None, actions=None):
        self.bandit_arms = bandit_arms or []
        self.actions = actions or []
        self.metrics_updated = []
        self.bandit_updated = []

    def get_recent_actions(self, kind, limit):
        return self.actions

    def get_bandit_arms(self):
        return self.bandit_arms

    def update_metrics(self, **kwargs):
        self.metrics_updated.append(kwargs)

    def bandit_update(self, arm, reward):
        self.bandit_updated.append((arm, reward))


class MockClient:
    """Mock client for testing."""

    def __init__(self, tweet_data=None, raise_error=False):
        self.tweet_data = tweet_data
        self.raise_error = raise_error
        self.get_tweet_calls = []

    def get_tweet(self, post_id):
        self.get_tweet_calls.append(post_id)
        if self.raise_error:
            raise RuntimeError("Mock API error")
        return self.tweet_data or {}


def test_settle_all_default_arm_none_skips_invalid_entries():
    """
    Test settle_all when default_arm=None and entries have missing topic/slot.

    Covers line 95: if default_arm is None: continue
    """
    storage = MockStorage(
        actions=[
            {"post_id": None, "topic": "tech", "slot": "morning", "media": 1},  # Skip: no post_id (line 90)
            {"post_id": "1", "topic": None, "slot": None, "media": 0},  # Skip: no topic/slot + no default (line 95-96)
            {"post_id": "2", "topic": "tech", "slot": "morning", "media": 1},  # Process
        ]
    )

    client = MockClient(
        tweet_data={
            "data": {
                "public_metrics": {
                    "like_count": 1,
                    "reply_count": 0,
                    "retweet_count": 0,
                    "quote_count": 0,
                    "impression_count": 10,
                }
            }
        }
    )

    # Call with default_arm=None
    count = learn.settle_all(client, storage, default_arm=None)

    # Only post_id "2" should be processed
    assert count == 1
    assert len(client.get_tweet_calls) == 1
    assert client.get_tweet_calls[0] == "2"


def test_settle_all_handles_settle_exceptions():
    """
    Test settle_all continues when settle() raises an exception.

    Covers lines 103-105: except Exception as e: print(...); continue
    """
    storage = MockStorage(
        actions=[
            {"post_id": "1", "topic": "tech", "slot": "morning", "media": 1},  # Will fail
            {"post_id": "2", "topic": "tech", "slot": "afternoon", "media": 0},  # Will fail
            {"post_id": "3", "topic": "tech", "slot": "evening", "media": 1},  # Will fail
        ]
    )

    # Client that raises errors
    client = MockClient(raise_error=True)

    # Should continue despite exceptions
    count = learn.settle_all(client, storage, default_arm="default|slot|0")

    # No posts successfully settled
    assert count == 0
    # But all 3 were attempted
    assert len(client.get_tweet_calls) == 3


def test_settle_no_data_returns_early(capsys):
    """
    Test settle() returns early when get_tweet returns no data.

    Covers lines 31-32: print warning and return when no data
    """
    storage = MockStorage()
    client = MockClient(tweet_data={"error": "not found"})  # No "data" key

    learn.settle(client, storage, "999", "tech|morning|1")

    # Should not update anything
    assert len(storage.metrics_updated) == 0
    assert len(storage.bandit_updated) == 0

    # Should print warning
    captured = capsys.readouterr()
    assert "Could not fetch metrics for 999" in captured.out


def test_print_bandit_stats_no_data(capsys):
    """
    Test print_bandit_stats when there are no bandit arms.

    Covers lines 115-116: if not arms: print(...); return
    """
    storage = MockStorage(bandit_arms=[])  # Empty arms list

    learn.print_bandit_stats(storage)

    captured = capsys.readouterr()
    assert "No bandit data yet." in captured.out
    # Should not print the header or arm details
    assert "Learning Stats" not in captured.out


def test_print_bandit_stats_with_data_shows_header(capsys):
    """
    Verify print_bandit_stats shows proper output when data exists.

    This confirms the no-data path is distinct from the normal path.
    """
    storage = MockStorage(
        bandit_arms=[
            {"arm": "tech|morning|1", "alpha": 5.0, "beta": 2.0},
        ]
    )

    learn.print_bandit_stats(storage)

    captured = capsys.readouterr()
    assert "Learning Stats" in captured.out
    assert "No bandit data yet." not in captured.out
