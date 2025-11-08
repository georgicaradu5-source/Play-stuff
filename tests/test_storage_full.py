"""
Comprehensive tests for storage.py module.

Tests cover:
- Database initialization and schema
- Actions logging and retrieval
- Metrics tracking
- Monthly usage tracking
- Text deduplication (hash + Jaccard)
- Thompson Sampling bandit operations
- Utility methods
"""

import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.storage import Storage, connect_db, init_db, log_action, normalize_text


class TestStorageInit:
    """Test database initialization and schema creation."""

    def test_storage_creates_db_file(self, tmp_path: Path):
        """DB file is created on first init."""
        db_path = tmp_path / "test.db"
        storage = Storage(db_path=str(db_path))
        assert db_path.exists()
        storage.close()

    def test_storage_creates_tables(self, tmp_path: Path):
        """All required tables are created."""
        db_path = tmp_path / "test.db"
        storage = Storage(db_path=str(db_path))

        # Check all tables exist
        cursor = storage.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        expected = {
            "actions",
            "metrics",
            "usage_monthly",
            "text_hashes",
            "bandit",
            "rate_limits",
            "api_calls",
            "usage_daily",
        }
        assert expected.issubset(tables)
        storage.close()

    def test_storage_creates_indexes(self, tmp_path: Path):
        """Indexes are created for performance."""
        db_path = tmp_path / "test.db"
        storage = Storage(db_path=str(db_path))

        cursor = storage.conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

        expected_indexes = {
            "idx_actions_dt",
            "idx_actions_kind",
            "idx_actions_post_id",
            "idx_text_hashes_dt",
            "idx_api_calls_dt",
        }
        assert expected_indexes.issubset(indexes)
        storage.close()


class TestActionsLog:
    """Test action logging and retrieval."""

    def test_log_action_basic(self, tmp_path: Path):
        """Basic action logging works."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        row_id = storage.log_action(
            kind="post",
            post_id="123",
            text="test post",
            topic="tech",
            slot="morning",
        )
        assert row_id > 0
        storage.close()

    def test_log_action_stores_text_hash(self, tmp_path: Path):
        """Action logging also stores text hash."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.log_action(kind="post", post_id="123", text="test post content")

        # Check text_hashes table
        cursor = storage.conn.execute("SELECT COUNT(*) FROM text_hashes")
        count = cursor.fetchone()[0]
        assert count == 1
        storage.close()

    def test_get_recent_actions_all(self, tmp_path: Path):
        """Get all recent actions."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.log_action(kind="post", post_id="1")
        storage.log_action(kind="like", post_id="2")
        storage.log_action(kind="reply", post_id="3")

        actions = storage.get_recent_actions(limit=10)
        assert len(actions) == 3
        assert actions[0]["kind"] == "reply"  # Most recent first
        storage.close()

    def test_get_recent_actions_filtered(self, tmp_path: Path):
        """Get recent actions filtered by kind."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.log_action(kind="post", post_id="1")
        storage.log_action(kind="like", post_id="2")
        storage.log_action(kind="post", post_id="3")

        actions = storage.get_recent_actions(kind="post", limit=10)
        assert len(actions) == 2
        assert all(a["kind"] == "post" for a in actions)
        storage.close()

    def test_already_acted_true(self, tmp_path: Path):
        """already_acted returns True if action exists."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.log_action(kind="like", post_id="123")

        assert storage.already_acted(post_id="123", kind="like")
        storage.close()

    def test_already_acted_false(self, tmp_path: Path):
        """already_acted returns False if action doesn't exist."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        assert not storage.already_acted(post_id="999", kind="like")
        storage.close()


class TestMetrics:
    """Test metrics tracking."""

    def test_update_metrics_basic(self, tmp_path: Path):
        """Basic metrics update."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.update_metrics(
            post_id="123",
            like_count=5,
            reply_count=2,
            retweet_count=1,
            quote_count=0,
            impression_count=100,
        )

        metrics = storage.get_metrics(post_id="123")
        assert metrics is not None
        assert metrics["like_count"] == 5
        assert metrics["reply_count"] == 2
        storage.close()

    def test_update_metrics_auto_reward(self, tmp_path: Path):
        """Metrics auto-calculates reward if not provided."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.update_metrics(
            post_id="123",
            like_count=10,
            reply_count=5,
            retweet_count=2,
        )

        metrics = storage.get_metrics(post_id="123")
        # Reward = (10*1.0 + 5*2.0 + 2*3.0) / 100 = 0.26
        assert metrics is not None
        assert metrics["reward"] == pytest.approx(0.26, abs=0.01)
        storage.close()

    def test_update_metrics_custom_reward(self, tmp_path: Path):
        """Metrics accepts custom reward value."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.update_metrics(post_id="123", reward=0.75)

        metrics = storage.get_metrics(post_id="123")
        assert metrics is not None
        assert metrics["reward"] == 0.75
        storage.close()

    def test_get_metrics_none(self, tmp_path: Path):
        """get_metrics returns None for unknown post."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        metrics = storage.get_metrics(post_id="unknown")
        assert metrics is None
        storage.close()

    def test_upsert_metrics(self, tmp_path: Path):
        """upsert_metrics updates existing metrics."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.update_metrics(post_id="123", like_count=5)
        storage.upsert_metrics(
            post_id="123",
            like_count=10,
            reply_count=2,
            retweet_count=1,
            quote_count=0,
            impression_count=200,
            reward=0.5,
        )

        metrics = storage.get_metrics(post_id="123")
        assert metrics is not None
        assert metrics["like_count"] == 10
        assert metrics["reward"] == 0.5
        storage.close()


class TestMonthlyUsage:
    """Test monthly usage tracking."""

    def test_get_monthly_usage_new_period(self, tmp_path: Path):
        """get_monthly_usage returns zeros for new period."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        usage = storage.get_monthly_usage(period="2025-01")
        assert usage["period"] == "2025-01"
        assert usage["create_count"] == 0
        assert usage["read_count"] == 0
        storage.close()

    def test_update_monthly_usage_new_period(self, tmp_path: Path):
        """update_monthly_usage creates new period."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.update_monthly_usage(period="2025-01", create_count=5, read_count=10)

        usage = storage.get_monthly_usage(period="2025-01")
        assert usage["create_count"] == 5
        assert usage["read_count"] == 10
        storage.close()

    def test_update_monthly_usage_incremental(self, tmp_path: Path):
        """update_monthly_usage increments existing counts."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.update_monthly_usage(period="2025-01", create_count=5, read_count=10)
        storage.update_monthly_usage(period="2025-01", create_count=3, read_count=7)

        usage = storage.get_monthly_usage(period="2025-01")
        assert usage["create_count"] == 8
        assert usage["read_count"] == 17
        storage.close()


class TestTextDeduplication:
    """Test text deduplication via hash + Jaccard."""

    def test_normalize_text_basic(self):
        """normalize_text lowercases and collapses whitespace."""
        result = normalize_text("Hello, World! @user #hashtag")
        # normalize_text only lowercases and collapses whitespace
        assert result == "hello, world! @user #hashtag"

    def test_normalize_text_collapses_whitespace(self):
        """normalize_text collapses multiple spaces."""
        result = normalize_text("Multiple   spaces    here")
        assert result == "multiple spaces here"

    def test_store_text_hash(self, tmp_path: Path):
        """store_text_hash stores hash and normalized text."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.store_text_hash(text="Test post!", post_id="123")

        cursor = storage.conn.execute("SELECT text_hash, text_norm FROM text_hashes")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == hashlib.sha256(b"Test post!").hexdigest()
        assert row[1] == "test post!"
        storage.close()

    def test_is_text_duplicate_exact_hash(self, tmp_path: Path):
        """is_text_duplicate detects exact hash match."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.store_text_hash(text="Duplicate content", post_id="1")

        assert storage.is_text_duplicate("Duplicate content")
        storage.close()

    def test_is_text_duplicate_no_match(self, tmp_path: Path):
        """is_text_duplicate returns False for unique text."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.store_text_hash(text="Original content", post_id="1")

        assert not storage.is_text_duplicate("Completely different text")
        storage.close()

    def test_is_text_duplicate_jaccard_similar(self, tmp_path: Path):
        """is_text_duplicate detects Jaccard similarity."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.store_text_hash(text="The quick brown fox jumps", post_id="1")

        # High overlap: "the quick brown fox" common, only "jumps" vs "leaps" differ
        # Tokens in first: {the, quick, brown, fox, jumps} = 5
        # Tokens in second: {the, quick, brown, fox, leaps} = 5
        # Intersection: {the, quick, brown, fox} = 4
        # Union: {the, quick, brown, fox, jumps, leaps} = 6
        # Jaccard = 4/6 = 0.667, which is < 0.7
        similar = "The quick brown fox leaps"
        # Adjust threshold to capture this case
        assert storage.is_text_duplicate(similar, jaccard_threshold=0.6)
        storage.close()

    def test_is_text_duplicate_jaccard_dissimilar(self, tmp_path: Path):
        """is_text_duplicate allows low Jaccard similarity."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.store_text_hash(text="The quick brown fox", post_id="1")

        dissimilar = "A slow red turtle"
        assert not storage.is_text_duplicate(dissimilar, jaccard_threshold=0.7)
        storage.close()

    def test_is_text_duplicate_days_cutoff(self, tmp_path: Path):
        """is_text_duplicate respects days cutoff."""
        from datetime import UTC

        storage = Storage(db_path=str(tmp_path / "test.db"))
        old_dt = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        storage.store_text_hash(text="Old content", post_id="1", dt=old_dt)

        # Not duplicate because older than 7 days
        assert not storage.is_text_duplicate("Old content", days=7)
        storage.close()

    def test_get_recent_texts(self, tmp_path: Path):
        """get_recent_texts returns normalized texts within cutoff."""
        from datetime import UTC

        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.store_text_hash(text="Recent post", post_id="1")
        old_dt = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        storage.store_text_hash(text="Old post", post_id="2", dt=old_dt)

        texts = storage.get_recent_texts(days=7)
        assert len(texts) == 1
        assert texts[0] == "recent post"
        storage.close()


class TestThompsonSamplingBandit:
    """Test Thompson Sampling bandit operations."""

    def test_bandit_choose_default_params(self, tmp_path: Path):
        """bandit_choose samples with default alpha/beta=1.0."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        arms = ["topic:tech", "topic:ai", "topic:devops"]

        chosen = storage.bandit_choose(arms)
        assert chosen in arms
        storage.close()

    def test_bandit_choose_deterministic_with_seed(self, tmp_path: Path, monkeypatch):
        """bandit_choose is deterministic with seeded random."""
        import random

        storage = Storage(db_path=str(tmp_path / "test.db"))
        arms = ["topic:tech", "topic:ai"]

        random.seed(42)
        choice1 = storage.bandit_choose(arms)

        random.seed(42)
        choice2 = storage.bandit_choose(arms)

        assert choice1 == choice2
        storage.close()

    def test_bandit_update_new_arm(self, tmp_path: Path):
        """bandit_update creates new arm with updated params."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.bandit_update(arm="topic:tech", reward=0.8)

        cursor = storage.conn.execute("SELECT alpha, beta FROM bandit WHERE arm='topic:tech'")
        row = cursor.fetchone()
        assert row is not None
        # alpha = 1.0 + 0.8 = 1.8, beta = 1.0 + (1.0 - 0.8) = 1.2
        assert row[0] == pytest.approx(1.8)
        assert row[1] == pytest.approx(1.2)
        storage.close()

    def test_bandit_update_existing_arm(self, tmp_path: Path):
        """bandit_update increments existing arm params."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.bandit_update(arm="topic:tech", reward=0.5)
        storage.bandit_update(arm="topic:tech", reward=0.7)

        cursor = storage.conn.execute("SELECT alpha, beta FROM bandit WHERE arm='topic:tech'")
        row = cursor.fetchone()
        assert row is not None
        # After 1st: alpha=1.5, beta=1.5
        # After 2nd: alpha=2.2, beta=1.8
        assert row[0] == pytest.approx(2.2)
        assert row[1] == pytest.approx(1.8)
        storage.close()

    def test_bandit_update_clamps_reward(self, tmp_path: Path):
        """bandit_update clamps reward to [0, 1]."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.bandit_update(arm="topic:tech", reward=2.5)

        cursor = storage.conn.execute("SELECT alpha, beta FROM bandit WHERE arm='topic:tech'")
        row = cursor.fetchone()
        # Reward clamped to 1.0: alpha = 2.0, beta = 1.0
        assert row[0] == pytest.approx(2.0)
        assert row[1] == pytest.approx(1.0)
        storage.close()

    def test_get_bandit_arms_empty(self, tmp_path: Path):
        """get_bandit_arms returns empty list when no arms."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        arms = storage.get_bandit_arms()
        assert arms == []
        storage.close()

    def test_get_bandit_arms_populated(self, tmp_path: Path):
        """get_bandit_arms returns all arms sorted."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.bandit_update(arm="topic:ai", reward=0.5)
        storage.bandit_update(arm="topic:devops", reward=0.3)
        storage.bandit_update(arm="topic:tech", reward=0.7)

        arms = storage.get_bandit_arms()
        assert len(arms) == 3
        assert arms[0]["arm"] == "topic:ai"
        assert arms[1]["arm"] == "topic:devops"
        assert arms[2]["arm"] == "topic:tech"
        storage.close()


class TestUtility:
    """Test utility functions and backward compatibility."""

    def test_connect_db_context_manager(self, tmp_path: Path):
        """connect_db works as context manager."""
        db_path = tmp_path / "test.db"
        with connect_db(str(db_path)) as conn:
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

    def test_init_db_creates_database(self):
        """init_db creates database at default path."""
        # init_db uses module-level DB_PATH, so test it creates and closes
        init_db()
        # Verify DB_PATH exists
        from src.storage import DB_PATH

        assert Path(DB_PATH).exists()

    def test_log_action_backward_compat(self):
        """log_action backward compat function works."""
        # log_action uses module-level DB_PATH
        log_action(kind="post", post_id="backward123", text="backward test")

        from src.storage import DB_PATH

        storage = Storage(db_path=DB_PATH)
        actions = storage.get_recent_actions(kind="post", limit=10)
        # Find our action
        found = any(a["post_id"] == "backward123" for a in actions)
        assert found
        storage.close()

    def test_storage_close(self, tmp_path: Path):
        """close() properly closes connection."""
        storage = Storage(db_path=str(tmp_path / "test.db"))
        storage.close()

        # Verify connection is closed by attempting query (should fail)
        with pytest.raises(sqlite3.ProgrammingError):
            storage.conn.execute("SELECT 1")
