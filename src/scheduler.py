"""Scheduler with time-window support and action orchestration."""

from __future__ import annotations

import random
from datetime import datetime, time as dtime
from typing import Any, Optional

from actions import act_on_search, choose_template
from storage import Storage
from x_client import XClient
from logger import get_logger

logger = get_logger(__name__)


# Time windows for posting
WINDOWS = {
    "morning": (dtime(9, 0), dtime(12, 0)),
    "afternoon": (dtime(13, 0), dtime(17, 0)),
    "evening": (dtime(18, 0), dtime(21, 0)),
}


def current_slot(windows: list[str]) -> Optional[str]:
    """Determine current time window."""
    now = datetime.now().time()
    for name in windows:
        start, end = WINDOWS.get(name, (None, None))
        if start and end and start <= now <= end:
            return name
    # Default to random if outside all windows
    return random.choice(windows) if windows else None


def run_post_action(
    client: XClient,
    storage: Storage,
    config: dict[str, Any],
    dry_run: bool,
) -> None:
    """Execute a post action based on config."""
    # Get time window
    windows = config.get("schedule", {}).get("windows", ["morning", "afternoon", "evening"])
    slot = current_slot(windows) or "morning"
    
    # Get topic (with learning if enabled)
    topics = config.get("topics", ["automation"])
    if config.get("learning", {}).get("enabled", False):
        # Use bandit to choose topic
        topic = storage.bandit_choose(topics)
    else:
        topic = random.choice(topics)
    
    # Generate post
    text, media_path = choose_template(topic), None
    
    # Check for duplicates
    if storage.is_text_duplicate(text, days=7):
        logger.warning("Duplicate text detected, skipping post")
        return
    
    # Create post
    if dry_run:
        logger.debug(f"[DRY RUN] create_post(text='{text[:50]}...', topic={topic}, slot={slot})")
        post_id = "dry-run-post"
    else:
        # Check budget first
        from budget import BudgetManager
        budget_mgr = BudgetManager(storage=storage, plan=config.get("plan", "free"))  # type: ignore
        can_write, msg = budget_mgr.can_write(1)
        if not can_write:
            logger.warning(f"Budget check failed: {msg}")
            print(f"❌ {msg}")
            return
        
        resp = client.create_post(text)
        post_id = resp.get("data", {}).get("id", "unknown")
        
        # Log action
        storage.log_action(
            kind="post",
            post_id=post_id,
            text=text,
            topic=topic,
            slot=slot,
            media=0,
        )
        
        # Update budget
        budget_mgr.add_writes(1)
        
        logger.info(f"Posted: {post_id} (topic={topic}, slot={slot})")
        print(f"✓ Posted: {post_id} (topic={topic}, slot={slot})")


def run_interact_actions(
    client: XClient,
    storage: Storage,
    config: dict[str, Any],
    dry_run: bool,
) -> None:
    """Execute interaction actions (search, like, reply, etc.)."""
    # Get user ID
    me_data = client.get_me()
    me_user_id = me_data.get("data", {}).get("id", "unknown")
    
    # Get queries from config
    queries = config.get("queries", [])
    if not queries:
        logger.warning("No queries configured for interaction mode")
        print("⚠️  No queries configured for interaction mode")
        return
    
    # Get limits
    limits = config.get("max_per_window", {
        "reply": 3,
        "like": 10,
        "follow": 3,
        "repost": 1,
    })
    
    # Feature flags
    feature_flags = config.get("feature_flags", {})
    if str(feature_flags.get("allow_likes", "auto")).lower() == "off":
        limits["like"] = 0
    if str(feature_flags.get("allow_follows", "auto")).lower() == "off":
        limits["follow"] = 0
    
    # Jitter bounds
    jitter_bounds = tuple(config.get("jitter_seconds", [8, 20]))  # type: ignore
    
    # Execute for each query
    for query_item in queries:
        if isinstance(query_item, dict):
            query = query_item.get("query", "")
        else:
            query = str(query_item)
        
        if not query:
            continue
        
        print(f"\n🔍 Searching: {query[:50]}...")
        remaining = act_on_search(
            client=client,
            storage=storage,
            query=query,
            limits=limits.copy(),
            jitter_bounds=jitter_bounds,
            dry_run=dry_run,
            me_user_id=me_user_id,
        )
        print(f"   Remaining limits: {remaining}")


def run_scheduler(
    client: XClient,
    storage: Storage,
    config: dict[str, Any],
    mode: str,
    dry_run: bool,
) -> None:
    """Main scheduler entry point."""
    # Check weekday filter
    weekdays = config.get("cadence", {}).get("weekdays", [1, 2, 3, 4, 5])
    today = datetime.today().isoweekday()
    if today not in weekdays and not dry_run:
        print(f"⏸️  Outside configured weekdays ({weekdays}), exiting")
        return
    
    print(f"\n{'='*60}")
    print(f"🤖 X Agent Unified - {mode.upper()} mode")
    print(f"{'='*60}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dry run: {dry_run}")
    print(f"{'='*60}\n")
    
    # Execute based on mode
    if mode in ("post", "both"):
        run_post_action(client, storage, config, dry_run)
    
    if mode in ("interact", "both"):
        run_interact_actions(client, storage, config, dry_run)
    
    print(f"\n{'='*60}")
    print(f"✓ Scheduler completed")
    print(f"{'='*60}\n")
