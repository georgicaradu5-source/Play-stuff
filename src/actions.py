"""Template-based content generation and interaction actions."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from business.content import REPLY_TEMPLATES, TEMPLATES, choose_template, helpful_reply, make_post
from business.filters import should_act_on_post
from storage import Storage

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from x_client import XClient

# Re-export from business layer for backward compatibility
__all__ = ["TEMPLATES", "REPLY_TEMPLATES", "choose_template", "make_post", "helpful_reply", "act_on_search"]


def act_on_search(
    client: XClient,
    storage: Storage,
    query: str,
    limits: dict[str, int],
    jitter_bounds: tuple[int, int],
    dry_run: bool,
    me_user_id: str,
) -> dict[str, int]:
    """Perform reply, like, follow actions up to limits."""
    import time

    remaining = {k: int(v) for k, v in limits.items()}
    posts = client.search_recent(query, max_results=20)
    random.shuffle(posts)

    for p in posts:
        if all(v <= 0 for v in remaining.values()):
            break

        pid = p["id"]
        author_id = p.get("author_id")

        # Use business layer filter
        if not should_act_on_post(pid, author_id, me_user_id):
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
                if not storage.already_acted(pid, "reply"):
                    reply_text = helpful_reply()
                    if dry_run:
                        print(f"[DRY RUN] reply to {pid}: {reply_text}")
                    else:
                        resp = client.create_post(reply_text, reply_to=pid)
                        rid = resp.get("data", {}).get("id", "unknown")
                        storage.log_action(kind="reply", post_id=pid, ref_id=rid, text=reply_text)
                    remaining["reply"] -= 1
                    time.sleep(random.uniform(*jitter_bounds))

            elif a == "like":
                if not storage.already_acted(pid, "like"):
                    if dry_run:
                        print(f"[DRY RUN] like {pid}")
                    else:
                        client.like_post(pid)
                        storage.log_action(kind="like", post_id=pid)
                    remaining["like"] -= 1
                    time.sleep(random.uniform(*jitter_bounds))

            elif a == "follow" and author_id:
                if not storage.already_acted(str(author_id), "follow"):
                    if dry_run:
                        print(f"[DRY RUN] follow {author_id}")
                    else:
                        client.follow_user(str(author_id))
                        storage.log_action(kind="follow", post_id=str(author_id))
                    remaining["follow"] -= 1
                    time.sleep(random.uniform(*jitter_bounds))

            elif a == "repost":
                if not storage.already_acted(pid, "repost"):
                    if dry_run:
                        print(f"[DRY RUN] repost {pid}")
                    else:
                        client.retweet(pid)
                        storage.log_action(kind="repost", post_id=pid)
                    remaining["repost"] -= 1
                    time.sleep(random.uniform(*jitter_bounds))

    return remaining
