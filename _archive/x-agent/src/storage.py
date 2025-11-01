"""SQLite storage for actions, metrics, and budget tracking."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class Storage:
    """SQLite storage manager."""

    def __init__(self, db_path: str = "data/x_agent.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.conn:
            # Actions log
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    kind TEXT NOT NULL,
                    dt TEXT NOT NULL,
                    ref_id TEXT,
                    text TEXT,
                    topic TEXT,
                    media INTEGER DEFAULT 0,
                    status TEXT,
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

            # Text deduplication
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS text_hashes (
                    text_hash TEXT PRIMARY KEY,
                    text TEXT,
                    created_at TEXT
                )
            """)

            # Create indexes
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_dt ON actions(dt)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_kind ON actions(kind)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_post_id ON actions(post_id)")

    def log_action(
        self,
        kind: str,
        post_id: Optional[str] = None,
        ref_id: Optional[str] = None,
        text: Optional[str] = None,
        topic: Optional[str] = None,
        media: int = 0,
        status: str = "success",
        rate_limit_remaining: Optional[int] = None,
        rate_limit_reset: Optional[int] = None,
    ) -> int:
        """Log an action to the database."""
        dt = datetime.utcnow().isoformat()
        cursor = self.conn.execute(
            """
            INSERT INTO actions (post_id, kind, dt, ref_id, text, topic, media, status, rate_limit_remaining, rate_limit_reset)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (post_id, kind, dt, ref_id, text, topic, media, status, rate_limit_remaining, rate_limit_reset),
        )
        self.conn.commit()
        return cursor.lastrowid

    def is_text_duplicate(self, text: str, days: int = 7) -> bool:
        """Check if text has been used recently."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = (cutoff - timedelta(days=days)).isoformat()

        cursor = self.conn.execute(
            "SELECT 1 FROM text_hashes WHERE text_hash = ? AND created_at > ?",
            (text_hash, cutoff),
        )
        return cursor.fetchone() is not None

    def store_text_hash(self, text: str) -> None:
        """Store text hash for deduplication."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        created_at = datetime.utcnow().isoformat()
        
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO text_hashes (text_hash, text, created_at) VALUES (?, ?, ?)",
                (text_hash, text, created_at),
            )

    def update_metrics(
        self,
        post_id: str,
        like_count: int = 0,
        reply_count: int = 0,
        retweet_count: int = 0,
        quote_count: int = 0,
        impression_count: int = 0,
    ) -> None:
        """Update metrics for a post."""
        last_updated = datetime.utcnow().isoformat()
        
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO metrics 
                (post_id, like_count, reply_count, retweet_count, quote_count, impression_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (post_id, like_count, reply_count, retweet_count, quote_count, impression_count, last_updated),
            )

    def get_metrics(self, post_id: str) -> Optional[dict]:
        """Get metrics for a post."""
        cursor = self.conn.execute(
            "SELECT * FROM metrics WHERE post_id = ?",
            (post_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_recent_actions(self, kind: Optional[str] = None, limit: int = 100) -> list[dict]:
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

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


# Import timedelta for date calculations
from datetime import timedelta
