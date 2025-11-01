from __future__ import annotations

from datetime import datetime
from typing import Optional

from storage import connect_db


def record_api_call(endpoint: str, method: str, status: Optional[int], params: str | None, headers: dict | None) -> None:
    dt = datetime.utcnow().isoformat()
    limit = remaining = reset = None
    if headers:
        limit = _to_int(headers.get("x-rate-limit-limit"))
        remaining = _to_int(headers.get("x-rate-limit-remaining"))
        reset = _to_int(headers.get("x-rate-limit-reset"))
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO api_calls(dt, endpoint, method, status, params, limit, remaining, reset) VALUES(?,?,?,?,?,?,?,?)",
            (dt, endpoint, method, status or 0, params or "", limit, remaining, reset),
        )
        if limit is not None:
            cur.execute(
                "INSERT OR REPLACE INTO rate_limits(endpoint, limit, remaining, reset, dt) VALUES(?,?,?,?,?)",
                (endpoint, limit, remaining, reset, dt),
            )


def _to_int(val) -> Optional[int]:
    try:
        return int(val)
    except Exception:
        return None


def get_limits() -> list[dict]:
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT endpoint, limit, remaining, reset, dt FROM rate_limits ORDER BY endpoint")
        rows = cur.fetchall()
        result = []
        for endpoint, limit, remaining, reset, dt in rows:
            result.append(
                {
                    "endpoint": endpoint,
                    "limit": limit,
                    "remaining": remaining,
                    "reset": reset,
                    "seen_at": dt,
                }
            )
        return result

