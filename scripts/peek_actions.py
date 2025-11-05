"""Peek recent actions logged by the X Agent.

Usage:
    python scripts/peek_actions.py                # Show last 10 actions
    python scripts/peek_actions.py --limit 25     # Show last 25 actions
    python scripts/peek_actions.py --kind post    # Filter by kind (post, like, reply, etc.)
    python scripts/peek_actions.py --json         # Output JSON instead of table

Reads from the unified SQLite DB at data/agent_unified.db.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agent_unified.db")


def human_ts(iso_ts: str) -> str:
    try:
        return datetime.fromisoformat(iso_ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_ts


def fetch_actions(kind: str | None, limit: int) -> list[dict[str, Any]]:
    # Local import to avoid heavy dependencies if unused elsewhere
    from src.storage import Storage

    storage = Storage(DB_PATH)
    try:
        return storage.get_recent_actions(kind=kind, limit=limit)
    finally:
        storage.close()


def format_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "(no actions found)"

    # Columns to display
    cols = ["id", "dt", "kind", "post_id", "status", "topic", "slot", "media", "rate_limit_remaining"]
    widths = {c: len(c) for c in cols}
    for r in rows:
        for c in cols:
            val = r.get(c)
            if c == "dt" and isinstance(val, str):
                val = human_ts(val)
            widths[c] = max(widths[c], len(str(val)) if val is not None else 4)

    def fmt_row(r: dict[str, Any]) -> str:
        parts = []
        for c in cols:
            val = r.get(c)
            if c == "dt" and isinstance(val, str):
                val = human_ts(val)
            parts.append(str(val)[: widths[c]].ljust(widths[c]))
        return " | ".join(parts)

    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    body = "\n" + "\n".join(fmt_row(r) for r in rows)
    return header + "\n" + sep + body


def main() -> int:
    parser = argparse.ArgumentParser(description="Peek recent actions from the agent database.")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent actions to show (default: 10)")
    parser.add_argument("--kind", type=str, default=None, help="Filter by action kind (post, like, reply, etc.)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of table")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run a dry-run or post action first.", file=sys.stderr)
        return 1

    rows = fetch_actions(kind=args.kind, limit=args.limit)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(format_table(rows))
        print(f"\nShown {len(rows)} action(s). Use --json for raw output.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
