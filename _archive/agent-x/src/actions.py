from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Iterable, Optional
import logging

from storage import already_acted, is_duplicate_text, log_action
from util import sleep_with_jitter


TEMPLATES = {
    "power-platform": [
        "Quick tip for Power Platform builders: keep flows modular and document triggers. Small wins compound.",
        "Power BI + Power Automate = fast insights and faster action. What combo do you use most?",
    ],
    "data-viz": [
        "Data viz tip: label directly, minimize legends. Clarity > cleverness.",
        "DAX calculations can be powerful—keep measures tidy and reusable.",
    ],
    "automation": [
        "Automate the boring parts first. Start with high-frequency, low-risk tasks.",
        "Workflow automation shines when paired with good naming and error alerts.",
    ],
}


def choose_template(topic: str) -> str:
    cands = TEMPLATES.get(topic, ["Sharing a quick note on automation and data."])
    return random.choice(cands)


def make_post(topic: str, slot: str, *, allow_media: bool = False) -> tuple[str, Optional[str]]:
    text = choose_template(topic)
    media_path = None
    # Minimal: no media by default; media can be enabled later.
    if allow_media:
        media_path = None
    return text, media_path


def helpful_reply(base_text: str) -> str:
    suffixes = [
        "Nice point! What’s your favorite resource on this?",
        "Interesting! How are you handling edge cases?",
        "Love this—curious how you track success over time.",
    ]
    return f"{random.choice(suffixes)}"


def act_on_search(
    *,
    xapi,
    query: str,
    limits: dict[str, int],
    jitter_bounds: tuple[int, int],
    dry_run: bool,
    me_user_id: str,
) -> dict[str, int]:
    """Perform reply, like, and follow actions up to limits per window.

    Randomizes order of actions and sleeps with jitter between calls.
    """
    remaining = {k: int(v) for k, v in limits.items()}
    logger = logging.getLogger("agent_x")
    posts = xapi.search_recent(query, max_results=20)
    random.shuffle(posts)

    for p in posts:
        if all(v <= 0 for v in remaining.values()):
            break
        pid = p["id"]
        author_id = p.get("author_id")
        # Skip self
        if author_id and str(author_id) == str(me_user_id):
            continue

        actions: list[str] = []
        if remaining.get("reply", 0) > 0:
            actions.append("reply")
        if remaining.get("like", 0) > 0:
            actions.append("like")
        if remaining.get("follow", 0) > 0:
            actions.append("follow")
        if remaining.get("repost", 0) > 0:
            actions.append("repost")
        random.shuffle(actions)

        for a in actions:
            if remaining.get(a, 0) <= 0:
                continue
            if a == "reply":
                if not already_acted(pid, "reply"):
                    reply_text = helpful_reply("")
                    if dry_run:
                        logger.info("[dry-run] reply to %s: %s", pid, reply_text)
                        rid = "dry-run-reply"
                    else:
                        rid = xapi.reply(pid, reply_text)
                    if not dry_run:
                        log_action(post_id=pid, kind="reply", ref_id=rid, text=reply_text)
                    remaining["reply"] -= 1
                    sleep_with_jitter(jitter_bounds)
            elif a == "like":
                if not already_acted(pid, "like"):
                    if dry_run:
                        logger.info("[dry-run] like %s", pid)
                    else:
                        xapi.like(pid)
                    if not dry_run:
                        log_action(post_id=pid, kind="like")
                    remaining["like"] -= 1
                    sleep_with_jitter(jitter_bounds)
            elif a == "follow" and author_id:
                if not already_acted(str(author_id), "follow"):
                    if dry_run:
                        logger.info("[dry-run] follow %s", author_id)
                    else:
                        xapi.follow(str(author_id))
                    if not dry_run:
                        log_action(post_id=str(author_id), kind="follow")
                    remaining["follow"] -= 1
                    sleep_with_jitter(jitter_bounds)
            elif a == "repost":
                if not already_acted(pid, "repost"):
                    if dry_run:
                        logger.info("[dry-run] repost %s", pid)
                    else:
                        xapi.repost(pid)
                    if not dry_run:
                        log_action(post_id=pid, kind="repost")
                    remaining["repost"] -= 1
                    sleep_with_jitter(jitter_bounds)

    return remaining


def act_on_posts(
    *,
    xapi,
    posts: list[dict[str, Any]],
    limits: dict[str, int],
    jitter_bounds: tuple[int, int],
    dry_run: bool,
    me_user_id: str,
) -> dict[str, int]:
    logger = logging.getLogger("agent_x")
    remaining = {k: int(v) for k, v in limits.items()}
    random.shuffle(posts)
    for p in posts:
        if all(v <= 0 for v in remaining.values()):
            break
        pid = p["id"]
        author_id = p.get("author_id")
        if author_id and str(author_id) == str(me_user_id):
            continue
        actions = []
        if remaining.get("reply", 0) > 0:
            actions.append("reply")
        if remaining.get("like", 0) > 0:
            actions.append("like")
        if remaining.get("follow", 0) > 0:
            actions.append("follow")
        if remaining.get("repost", 0) > 0:
            actions.append("repost")
        random.shuffle(actions)
        for a in actions:
            if remaining.get(a, 0) <= 0:
                continue
            if a == "reply":
                if not already_acted(pid, "reply"):
                    reply_text = helpful_reply("")
                    if dry_run:
                        logger.info("[dry-run] reply to %s: %s", pid, reply_text)
                        rid = "dry-run-reply"
                    else:
                        rid = xapi.reply(pid, reply_text)
                    if not dry_run:
                        log_action(post_id=pid, kind="reply", ref_id=rid, text=reply_text)
                    remaining["reply"] -= 1
                    sleep_with_jitter(jitter_bounds)
            elif a == "like":
                if not already_acted(pid, "like"):
                    if dry_run:
                        logger.info("[dry-run] like %s", pid)
                    else:
                        xapi.like(pid)
                    if not dry_run:
                        log_action(post_id=pid, kind="like")
                    remaining["like"] -= 1
                    sleep_with_jitter(jitter_bounds)
            elif a == "follow" and author_id:
                if not already_acted(str(author_id), "follow"):
                    if dry_run:
                        logger.info("[dry-run] follow %s", author_id)
                    else:
                        xapi.follow(str(author_id))
                    if not dry_run:
                        log_action(post_id=str(author_id), kind="follow")
                    remaining["follow"] -= 1
                    sleep_with_jitter(jitter_bounds)
            elif a == "repost":
                if not already_acted(pid, "repost"):
                    if dry_run:
                        logger.info("[dry-run] repost %s", pid)
                    else:
                        xapi.repost(pid)
                    if not dry_run:
                        log_action(post_id=pid, kind="repost")
                    remaining["repost"] -= 1
                    sleep_with_jitter(jitter_bounds)
    return remaining


def post_once(
    *,
    xapi,
    topic: str,
    slot: str,
    jitter_bounds: tuple[int, int],
    dry_run: bool,
) -> Optional[str]:
    logger = logging.getLogger("agent_x")
    text, media_path = make_post(topic, slot, allow_media=False)
    # In dry-run, skip duplicate checks and DB writes to avoid filesystem needs
    if not dry_run and is_duplicate_text(text):
        return None
    if dry_run:
        logger.info("[dry-run] post (%s/%s): %s", topic, slot, text)
        post_id = "dry-run-post"
    else:
        media_ids = None
        if media_path:
            media_id = xapi.upload_media(media_path)
            media_ids = [media_id]
        post_id = xapi.create_post(text, media_ids)
    if not dry_run:
        log_action(post_id=post_id, kind="post", text=text, topic=topic, slot=slot, media=1 if media_path else 0)
        sleep_with_jitter(jitter_bounds)
    return post_id
