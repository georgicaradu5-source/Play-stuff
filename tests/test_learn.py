import pytest
from src import learn

class DummyStorage:
    def __init__(self):
        self.metrics = {}
        self.bandit = []
        self.actions = []
    def update_metrics(self, **kwargs):
        self.metrics = kwargs
    def bandit_update(self, arm, reward):
        self.bandit.append((arm, reward))
    def get_bandit_arms(self):
        return [
            {"arm": "topic|slot|1", "alpha": 3.0, "beta": 2.0},
            {"arm": "topic|slot|0", "alpha": 2.0, "beta": 3.0},
        ]
    def get_recent_actions(self, kind, limit):
        return self.actions

class DummyClient:
    def __init__(self, tweet_data):
        self.tweet_data = tweet_data
    def get_tweet(self, post_id):
        return self.tweet_data

def test_compute_reward_basic():
    # Like=1, reply=1, rt=1, quote=1, impressions=10
    r = learn.compute_reward(1, 1, 1, 1, 10)
    assert 0 < r < 1
    # No impressions, fallback to sum
    r2 = learn.compute_reward(1, 1, 1, 1, None)
    assert 0 < r2 <= 1
    # Zero engagement
    assert learn.compute_reward(0, 0, 0, 0, 0) == 0.0
    # Capped at 1.0
    assert learn.compute_reward(10, 10, 10, 10, 1) == 1.0

def test_settle_success():
    storage = DummyStorage()
    client = DummyClient({"data": {"public_metrics": {"like_count": 2, "reply_count": 1, "retweet_count": 1, "quote_count": 0, "impression_count": 10}}})
    learn.settle(client, storage, "123", "topic|slot|1")
    assert storage.metrics["like_count"] == 2
    assert storage.bandit[0][0] == "topic|slot|1"
    assert 0 < storage.bandit[0][1] < 1

def test_settle_handles_missing_data():
    storage = DummyStorage()
    client = DummyClient({})
    learn.settle(client, storage, "123", "topic|slot|1")
    assert storage.metrics == {}
    assert storage.bandit == []

def test_settle_all_and_print_bandit_stats(capsys):
    storage = DummyStorage()
    storage.actions = [
        {"post_id": "1", "topic": "topic", "slot": "slot", "media": 1},
        {"post_id": "2", "topic": None, "slot": None, "media": 0},
        {"post_id": None, "topic": "topic", "slot": "slot", "media": 1},
    ]
    client = DummyClient({"data": {"public_metrics": {"like_count": 1, "reply_count": 1, "retweet_count": 1, "quote_count": 1, "impression_count": 10}}})
    count = learn.settle_all(client, storage, default_arm="default|slot|0")
    assert count == 2
    # Print bandit stats
    learn.print_bandit_stats(storage)
    out = capsys.readouterr().out
    assert "Learning Stats" in out
    assert "Est. reward" in out
