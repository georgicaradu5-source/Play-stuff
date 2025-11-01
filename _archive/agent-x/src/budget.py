from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Tuple

from storage import DB_PATH


# Default Free caps; can be overridden via configure_caps()
_CREATE_CAP = 500
_READ_CAP = 100


def configure_caps(posts_create_cap: int | None, posts_read_cap: int | None) -> None:
    global _CREATE_CAP, _READ_CAP
    if posts_create_cap:
        _CREATE_CAP = int(posts_create_cap)
    if posts_read_cap:
        _READ_CAP = int(posts_read_cap)


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_budget() -> None:
    con = _conn()
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS usage_monthly(
              period TEXT PRIMARY KEY,
              create_count INT,
              read_count INT
            );
            CREATE TABLE IF NOT EXISTS usage_daily(
              dt TEXT PRIMARY KEY,
              likes INT,
              follows INT,
              posts INT,
              reposts INT
            );
            """
        )
        con.commit()
    finally:
        con.close()


def _ym() -> str:
    d = datetime.utcnow()
    return f"{d.year:04d}-{d.month:02d}"


def _ymd() -> str:
    d = datetime.utcnow()
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"


def add_create(n: int = 1, cap: int | None = None) -> None:
    cap = int(cap if cap is not None else _CREATE_CAP)
    init_budget()
    con = _conn()
    try:
        p = _ym()
        row = con.execute("SELECT create_count FROM usage_monthly WHERE period=?", (p,)).fetchone()
        cur = 0 if row is None else (row[0] or 0)
        if cur + n > cap:
            raise RuntimeError("X API create cap reached for current month")
        # Preserve read_count if exists
        con.execute(
            "INSERT OR REPLACE INTO usage_monthly(period, create_count, read_count) VALUES(?,?,COALESCE((SELECT read_count FROM usage_monthly WHERE period=?),0))",
            (p, cur + n, p),
        )
        con.commit()
    finally:
        con.close()


def add_reads(posts_returned: int, cap: int | None = None) -> None:
    cap = int(cap if cap is not None else _READ_CAP)
    init_budget()
    con = _conn()
    try:
        p = _ym()
        row = con.execute("SELECT read_count FROM usage_monthly WHERE period=?", (p,)).fetchone()
        cur = 0 if row is None else (row[0] or 0)
        if cur + posts_returned > cap:
            raise RuntimeError("X API read cap reached for current month")
        con.execute(
            "INSERT OR REPLACE INTO usage_monthly(period, create_count, read_count) VALUES( COALESCE(?,period), COALESCE((SELECT create_count FROM usage_monthly WHERE period=?),0), ? )",
            (p, p, cur + posts_returned),
        )
        con.commit()
    finally:
        con.close()


def monthly_counts() -> Tuple[int, int]:
    init_budget()
    con = _conn()
    try:
        p = _ym()
        row = con.execute("SELECT create_count, read_count FROM usage_monthly WHERE period=?", (p,)).fetchone()
        if row is None:
            return (0, 0)
        return (row[0] or 0, row[1] or 0)
    finally:
        con.close()

