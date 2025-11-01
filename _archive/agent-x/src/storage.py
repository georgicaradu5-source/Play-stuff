from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional, Sequence, Tuple

from util import normalize_text


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agent.db")


@contextmanager
def connect_db(path: str = DB_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS actions (
              post_id TEXT PRIMARY KEY,
              kind TEXT,
              dt TEXT,
              ref_id TEXT,
              text TEXT,
              topic TEXT,
              slot TEXT,
              media INT DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
              post_id TEXT PRIMARY KEY,
              like_count INT,
              reply_count INT,
              retweet_count INT,
              quote_count INT,
              impression_count INT,
              reward REAL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS bandit (
              arm TEXT PRIMARY KEY,
              alpha REAL,
              beta REAL
            )
            """
        )
        # Optional FTS for text dedup hints (not required)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS post_texts (
              post_id TEXT PRIMARY KEY,
              dt TEXT,
              text_norm TEXT
            )
            """
        )
        # Rate limits and API call logs
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limits (
              endpoint TEXT PRIMARY KEY,
              limit INT,
              remaining INT,
              reset INT,
              dt TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS api_calls (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              dt TEXT,
              endpoint TEXT,
              method TEXT,
              status INT,
              params TEXT,
              limit INT,
              remaining INT,
              reset INT
            )
            """
        )


def log_action(
    *,
    post_id: str,
    kind: str,
    text: Optional[str] = None,
    topic: Optional[str] = None,
    slot: Optional[str] = None,
    media: int = 0,
    ref_id: Optional[str] = None,
    dt: Optional[str] = None,
) -> None:
    if dt is None:
        dt = datetime.utcnow().isoformat()
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO actions(post_id, kind, dt, ref_id, text, topic, slot, media)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (post_id, kind, dt, ref_id, text, topic, slot, media),
        )
        if text:
            cur.execute(
                "INSERT OR REPLACE INTO post_texts(post_id, dt, text_norm) VALUES(?,?,?)",
                (post_id, dt, normalize_text(text)),
            )


def get_recent_texts(days: int = 7) -> list[str]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT text_norm FROM post_texts WHERE dt >= ? ORDER BY dt DESC",
            (cutoff,),
        )
        rows = cur.fetchall()
    return [r[0] for r in rows]


def is_duplicate_text(text: str, days: int = 7, jaccard_threshold: float = 0.9) -> bool:
    """Detect duplicates by normalized equality and simple Jaccard similarity.

    This avoids repeated templated content; not a full vector store.
    """
    text_norm = normalize_text(text)
    recent = get_recent_texts(days)
    if text_norm in recent:
        return True
    tokens = set(text_norm.split())
    for t in recent[:200]:
        rtokens = set(t.split())
        if not rtokens:
            continue
        j = len(tokens & rtokens) / max(1, len(tokens | rtokens))
        if j >= jaccard_threshold:
            return True
    return False


def upsert_metrics(
    *,
    post_id: str,
    like_count: int,
    reply_count: int,
    retweet_count: int,
    quote_count: int,
    impression_count: Optional[int],
    reward: float,
) -> None:
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO metrics(post_id, like_count, reply_count, retweet_count, quote_count, impression_count, reward)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(post_id) DO UPDATE SET
              like_count=excluded.like_count,
              reply_count=excluded.reply_count,
              retweet_count=excluded.retweet_count,
              quote_count=excluded.quote_count,
              impression_count=excluded.impression_count,
              reward=excluded.reward
            """,
            (
                post_id,
                like_count,
                reply_count,
                retweet_count,
                quote_count,
                impression_count,
                reward,
            ),
        )


def bandit_choose(arms: Sequence[str]) -> str:
    """Sample with Thompson Sampling from alpha/beta, defaulting to 1,1."""
    import random

    with connect_db() as conn:
        cur = conn.cursor()
        results = {}
        for arm in arms:
            cur.execute("SELECT alpha, beta FROM bandit WHERE arm=?", (arm,))
            row = cur.fetchone()
            alpha, beta = (row if row else (1.0, 1.0))
            # Beta distribution sampling via random.gammavariate
            a = random.gammavariate(alpha, 1.0)
            b = random.gammavariate(beta, 1.0)
            results[arm] = a / (a + b)
    # Return arm with max sampled value
    return max(results, key=results.get)


def bandit_update(arm: str, reward: float) -> None:
    reward = max(0.0, min(1.0, reward))
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT alpha, beta FROM bandit WHERE arm=?", (arm,))
        row = cur.fetchone()
        alpha, beta = (row if row else (1.0, 1.0))
        alpha += reward
        beta += (1.0 - reward)
        cur.execute(
            "INSERT INTO bandit(arm, alpha, beta) VALUES(?,?,?) ON CONFLICT(arm) DO UPDATE SET alpha=?, beta=?",
            (arm, alpha, beta, alpha, beta),
        )


def already_acted(post_id: str, kind: str) -> bool:
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM actions WHERE post_id=? AND kind=?", (post_id, kind))
        return cur.fetchone() is not None
