from __future__ import annotations

import random
from datetime import datetime, time as dtime
from typing import Any, Dict, Optional

from actions import act_on_search, act_on_posts, post_once
from storage import init_db
from util import setup_logger


WINDOWS = {
    "morning": (dtime(9, 0), dtime(12, 0)),
    "afternoon": (dtime(13, 0), dtime(17, 0)),
    "evening": (dtime(18, 0), dtime(21, 0)),
}


def load_config(path: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        # Fallback minimal config for dry-run or missing deps
        return {
            "topics": ["power-platform", "data-viz", "automation"],
            "queries": [
                '(Power BI OR "Power Platform") lang:en -is:retweet -is:reply',
                '("Power Apps" OR "Power Automate") lang:en -is:retweet -is:reply',
                '("data visualization" OR "Power BI" OR DAX) lang:en -is:retweet -is:reply',
            ],
            "cadence": {"weekdays": [1, 2, 3, 4, 5], "windows": ["morning", "afternoon", "evening"]},
            "max_per_window": {"post": 1, "reply": 3, "like": 10, "follow": 3, "repost": 1},
            "jitter_seconds": [8, 20],
        }


def current_slot(windows: list[str]) -> Optional[str]:
    now = datetime.now().time()
    for name in windows:
        start, end = WINDOWS.get(name, (None, None))
        if start and end and start <= now <= end:
            return name
    return random.choice(windows) if windows else None


def run_once(
    *,
    xapi,
    cfg: dict[str, Any],
    mode: str,
    dry_run: bool,
) -> None:
    logger = setup_logger()
    if not dry_run:
        init_db()

    weekdays = cfg.get("cadence", {}).get("weekdays", [1, 2, 3, 4, 5])
    if not dry_run and datetime.today().isoweekday() not in weekdays:
        logger.info("Outside configured weekdays; exiting.")
        return

    win_names = cfg.get("cadence", {}).get("windows", cfg.get("schedule", {}).get("windows", ["morning", "afternoon", "evening"]))
    slot = current_slot(win_names) or "morning"
    jitter = tuple(cfg.get("jitter_seconds", [8, 20]))  # type: ignore[assignment]
    topics = cfg.get("topics", ["automation"]) or ["automation"]
    topic = random.choice(topics)

    # Configure Free-tier caps if present
    try:
        import budget  # type: ignore

        caps = cfg.get("tiers", {}).get("free", {}).get("monthly_caps", {})
        budget.configure_caps(caps.get("posts_create"), caps.get("posts_read"))
    except Exception:
        pass

    if mode in ("post", "both"):
        post_once(xapi=xapi, topic=topic, slot=slot, jitter_bounds=jitter, dry_run=dry_run)

    if mode in ("interact", "both"):
        limits = cfg.get("max_per_window", {"reply": 3, "like": 10, "follow": 3, "repost": 1})
        # Feature flags: allow_likes/follows gating on Free
        ff = cfg.get("feature_flags", {})
        if str(ff.get("allow_likes", "auto")).lower() == "off":
            limits["like"] = 0
        if str(ff.get("allow_follows", "auto")).lower() == "off":
            limits["follow"] = 0

        # Watchlist: interact with latest post(s) from specific users (cheap reads)
        watchlist = cfg.get("watchlist_user_ids", [])
        for uid in watchlist:
            try:
                posts = xapi.get_user_tweets(str(uid), max_results=1)
                if posts:
                    act_on_posts(
                        xapi=xapi,
                        posts=posts,
                        limits={k: int(limits.get(k, 0)) for k in ("reply", "like", "follow", "repost")},
                        jitter_bounds=jitter,
                        dry_run=dry_run,
                        me_user_id=xapi.me_user_id,
                    )
            except Exception:
                continue
        for q in cfg.get("queries", []):
            act_on_search(
                xapi=xapi,
                query=q,
                limits={k: int(limits.get(k, 0)) for k in ("reply", "like", "follow", "repost")},
                jitter_bounds=jitter,
                dry_run=dry_run,
                me_user_id=xapi.me_user_id,
            )


def run_loop(*, xapi, cfg: dict[str, Any], mode: str, dry_run: bool) -> None:
    """Run the agent on a simple schedule within configured windows.

    Posts once per active slot and interacts every ~30 minutes.
    """
    logger = setup_logger()
    import schedule  # type: ignore
    import time
    weekdays = cfg.get("cadence", {}).get("weekdays", [1, 2, 3, 4, 5])

    def job():
        if datetime.today().isoweekday() not in weekdays:
            return
        run_once(xapi=xapi, cfg=cfg, mode=mode, dry_run=dry_run)

    # Interact more frequently; post less
    if mode in ("post", "both"):
        schedule.every().hour.at(":05").do(job)
    if mode in ("interact", "both"):
        schedule.every(30).minutes.do(job)

    logger.info("Scheduler started. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")
