"""Unified storage combining both agent schemas with learning support."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agent_unified.db")


@contextmanager
def connect_db(path: str = DB_PATH):
    """Context manager for database connections."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def normalize_text(text: str) -> str:
    """Normalize text for deduplication."""
    return " ".join(text.lower().split())


class Storage:
    """Unified storage with full schema support."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize complete database schema."""
        with self.conn:
            # Actions log (merged schema from both agents)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    kind TEXT NOT NULL,
                    dt TEXT NOT NULL,
                    ref_id TEXT,
                    text TEXT,
                    topic TEXT,
                    slot TEXT,
                    media INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    rate_limit_remaining INTEGER,
                    rate_limit_reset INTEGER
                )
            """)

            # Metrics tracking
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    post_id TEXT PRIMARY KEY,
                    like_count INTEGER DEFAULT 0,
                    reply_count INTEGER DEFAULT 0,
                    retweet_count INTEGER DEFAULT 0,
                    quote_count INTEGER DEFAULT 0,
                    impression_count INTEGER DEFAULT 0,
                    reward REAL DEFAULT 0.0,
                    last_updated TEXT
                )
            """)

            # Monthly usage tracking
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_monthly (
                    period TEXT PRIMARY KEY,
                    create_count INTEGER DEFAULT 0,
                    read_count INTEGER DEFAULT 0,
                    last_updated TEXT
                )
            """)

            # Text deduplication (combined approach)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS text_hashes (
                    text_hash TEXT PRIMARY KEY,
                    post_id TEXT,
                    dt TEXT,
                    text TEXT,
                    text_norm TEXT,
                    created_at TEXT
                )
            """)

            # Thompson Sampling bandit (from agent-x)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS bandit (
                    arm TEXT PRIMARY KEY,
                    alpha REAL DEFAULT 1.0,
                    beta REAL DEFAULT 1.0,
                    last_updated TEXT
                )
            """)

            # Rate limits tracking
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    endpoint TEXT PRIMARY KEY,
                    limit_total INTEGER,
                    remaining INTEGER,
                    reset_epoch INTEGER,
                    dt TEXT
                )
            """)

            # API calls log
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dt TEXT,
                    endpoint TEXT,
                    method TEXT,
                    status INTEGER,
                    params TEXT,
                    limit_total INTEGER,
                    remaining INTEGER,
                    reset_epoch INTEGER
                )
            """)

            # Daily usage tracking (from agent-x)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_daily (
                    dt TEXT PRIMARY KEY,
                    likes INTEGER DEFAULT 0,
                    follows INTEGER DEFAULT 0,
                    posts INTEGER DEFAULT 0,
                    reposts INTEGER DEFAULT 0
                )
            """)

            # Create indexes
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_dt ON actions(dt)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_kind ON actions(kind)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_post_id ON actions(post_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_text_hashes_dt ON text_hashes(dt)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_api_calls_dt ON api_calls(dt)")

    # ============================================================================
    # ACTIONS
    # ============================================================================

    def log_action(
        self,
        kind: str,
        post_id: str | None = None,
        ref_id: str | None = None,
        text: str | None = None,
        topic: str | None = None,
        slot: str | None = None,
        media: int = 0,
        status: str = "success",
        rate_limit_remaining: int | None = None,
        rate_limit_reset: int | None = None,
        dt: str | None = None,
    ) -> int:
        """Log an action to the database."""
        if dt is None:
            dt = datetime.utcnow().isoformat()

        cursor = self.conn.execute(
            """
            INSERT INTO actions (post_id, kind, dt, ref_id, text, topic, slot, media, status, rate_limit_remaining, rate_limit_reset)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (post_id, kind, dt, ref_id, text, topic, slot, media, status, rate_limit_remaining, rate_limit_reset),
        )
        self.conn.commit()

        # Also store text hash if text provided
        if text:
            self.store_text_hash(text, post_id, dt)

        return int(cursor.lastrowid or 0)

    def get_recent_actions(self, kind: str | None = None, limit: int = 100) -> list[dict]:
        """Get recent actions."""
        if kind:
            cursor = self.conn.execute(
                "SELECT * FROM actions WHERE kind = ? ORDER BY dt DESC LIMIT ?",
                (kind, limit),
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM actions ORDER BY dt DESC LIMIT ?",
                (limit,),
            )
        return [dict(row) for row in cursor.fetchall()]

    def already_acted(self, post_id: str, kind: str) -> bool:
        """Check if action already performed on post."""
        cursor = self.conn.execute(
            "SELECT 1 FROM actions WHERE post_id=? AND kind=?",
            (post_id, kind),
        )
        return cursor.fetchone() is not None

    # ============================================================================
    # METRICS
    # ============================================================================

    def update_metrics(
        self,
        post_id: str,
        like_count: int = 0,
        reply_count: int = 0,
        retweet_count: int = 0,
        quote_count: int = 0,
        impression_count: int = 0,
        reward: float | None = None,
    ) -> None:
        """Update metrics for a post."""
        last_updated = datetime.utcnow().isoformat()

        if reward is None:
            # Calculate reward if not provided
            reward = (like_count * 1.0 + reply_count * 2.0 + retweet_count * 3.0 + quote_count * 2.5) / 100.0

        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO metrics
                (post_id, like_count, reply_count, retweet_count, quote_count, impression_count, reward, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (post_id, like_count, reply_count, retweet_count, quote_count, impression_count, reward, last_updated),
            )

    def get_metrics(self, post_id: str) -> dict | None:
        """Get metrics for a post."""
        cursor = self.conn.execute(
            "SELECT * FROM metrics WHERE post_id = ?",
            (post_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def upsert_metrics(
        self,
        post_id: str,
        like_count: int,
        reply_count: int,
        retweet_count: int,
        quote_count: int,
        impression_count: int | None,
        reward: float,
    ) -> None:
        """Upsert metrics (agent-x compatibility)."""
        self.update_metrics(
            post_id=post_id,
            like_count=like_count,
            reply_count=reply_count,
            retweet_count=retweet_count,
            quote_count=quote_count,
            impression_count=impression_count or 0,
            reward=reward,
        )

    # ============================================================================
    # MONTHLY USAGE
    # ============================================================================

    def get_monthly_usage(self, period: str) -> dict:
        """Get usage for a specific month (format: YYYY-MM)."""
        cursor = self.conn.execute(
            "SELECT * FROM usage_monthly WHERE period = ?",
            (period,),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"period": period, "create_count": 0, "read_count": 0}

    def update_monthly_usage(self, period: str, create_count: int = 0, read_count: int = 0) -> None:
        """Update monthly usage counts."""
        last_updated = datetime.utcnow().isoformat()

        with self.conn:
            cursor = self.conn.execute(
                "SELECT create_count, read_count FROM usage_monthly WHERE period = ?",
                (period,),
            )
            row = cursor.fetchone()

            if row:
                new_creates = row[0] + create_count
                new_reads = row[1] + read_count
                self.conn.execute(
                    "UPDATE usage_monthly SET create_count = ?, read_count = ?, last_updated = ? WHERE period = ?",
                    (new_creates, new_reads, last_updated, period),
                )
            else:
                self.conn.execute(
                    "INSERT INTO usage_monthly (period, create_count, read_count, last_updated) VALUES (?, ?, ?, ?)",
                    (period, create_count, read_count, last_updated),
                )

    # ============================================================================
    # TEXT DEDUPLICATION
    # ============================================================================

    def store_text_hash(self, text: str, post_id: str | None = None, dt: str | None = None) -> None:
        """Store text hash for deduplication."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        text_norm = normalize_text(text)
        created_at = dt or datetime.utcnow().isoformat()

        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO text_hashes (text_hash, post_id, dt, text, text_norm, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (text_hash, post_id, created_at, text, text_norm, created_at),
            )

    def is_text_duplicate(self, text: str, days: int = 7, jaccard_threshold: float = 0.9) -> bool:
        """Check if text has been used recently (combined approach)."""
        # Hash-based check
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        cursor = self.conn.execute(
            "SELECT 1 FROM text_hashes WHERE text_hash = ? AND created_at > ?",
            (text_hash, cutoff),
        )
        if cursor.fetchone():
            return True

        # Jaccard similarity check (agent-x approach)
        text_norm = normalize_text(text)
        tokens = set(text_norm.split())

        cursor = self.conn.execute(
            "SELECT text_norm FROM text_hashes WHERE created_at > ? ORDER BY created_at DESC LIMIT 200",
            (cutoff,),
        )
        recent_texts = [row[0] for row in cursor.fetchall()]

        for recent in recent_texts:
            rtokens = set(recent.split())
            if not rtokens:
                continue
            j = len(tokens & rtokens) / max(1, len(tokens | rtokens))
            if j >= jaccard_threshold:
                return True

        return False

    def get_recent_texts(self, days: int = 7) -> list[str]:
        """Get recent text norms."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor = self.conn.execute(
            "SELECT text_norm FROM text_hashes WHERE created_at >= ? ORDER BY created_at DESC",
            (cutoff,),
        )
        return [row[0] for row in cursor.fetchall()]

    # ============================================================================
    # THOMPSON SAMPLING BANDIT
    # ============================================================================

    def bandit_choose(self, arms: Sequence[str]) -> str:
        """Sample with Thompson Sampling from alpha/beta."""
        import random

        results = {}
        for arm in arms:
            cursor = self.conn.execute("SELECT alpha, beta FROM bandit WHERE arm=?", (arm,))
            row = cursor.fetchone()
            alpha, beta = (float(row[0]), float(row[1])) if row else (1.0, 1.0)

            # Beta distribution sampling via gamma variates
            a = random.gammavariate(alpha, 1.0)
            b = random.gammavariate(beta, 1.0)
            results[arm] = a / (a + b) if (a + b) > 0 else 0.5

        # Return arm with max sampled value
        return max(results, key=results.get)  # type: ignore

    def bandit_update(self, arm: str, reward: float) -> None:
        """Update bandit arm with reward."""
        reward = max(0.0, min(1.0, reward))
        last_updated = datetime.utcnow().isoformat()

        with self.conn:
            cursor = self.conn.execute("SELECT alpha, beta FROM bandit WHERE arm=?", (arm,))
            row = cursor.fetchone()
            alpha, beta = (float(row[0]), float(row[1])) if row else (1.0, 1.0)

            alpha += reward
            beta += 1.0 - reward

            self.conn.execute(
                """
                INSERT INTO bandit(arm, alpha, beta, last_updated) VALUES(?,?,?,?)
                ON CONFLICT(arm) DO UPDATE SET alpha=?, beta=?, last_updated=?
                """,
                (arm, alpha, beta, last_updated, alpha, beta, last_updated),
            )

    def get_bandit_arms(self) -> list[dict]:
        """Get all bandit arms with their stats."""
        cursor = self.conn.execute("SELECT * FROM bandit ORDER BY arm")
        return [dict(row) for row in cursor.fetchall()]

    # ============================================================================
    # UTILITY
    # ============================================================================

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


# Backward compatibility functions for agent-x
def init_db() -> None:
    """Initialize database (agent-x compatibility)."""
    storage = Storage()
    storage.close()


def log_action(**kwargs) -> None:
    """Log action (agent-x compatibility)."""
    storage = Storage()
    storage.log_action(**kwargs)
    storage.close()
