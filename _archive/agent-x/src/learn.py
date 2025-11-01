from __future__ import annotations

from typing import Iterable, Optional

from storage import bandit_update, connect_db, upsert_metrics


def compute_reward(like: int, reply: int, rt: int, quote: int, impressions: Optional[int]) -> float:
    numer = like + 2 * reply + 2 * rt + quote
    denom = impressions if impressions and impressions > 0 else max(1, like + reply + rt + quote)
    r = numer / denom
    return max(0.0, min(1.0, float(r)))


def settle(xapi, post_id: str, arm: str) -> None:
    m = xapi.fetch_metrics(post_id)
    reward = compute_reward(
        like=m.get("like_count", 0),
        reply=m.get("reply_count", 0),
        rt=m.get("retweet_count", 0),
        quote=m.get("quote_count", 0),
        impressions=None,
    )
    upsert_metrics(
        post_id=post_id,
        like_count=m.get("like_count", 0),
        reply_count=m.get("reply_count", 0),
        retweet_count=m.get("retweet_count", 0),
        quote_count=m.get("quote_count", 0),
        impression_count=None,
        reward=reward,
    )
    bandit_update(arm, reward)


def settle_all(xapi, default_arm_for_post: Optional[str] = None) -> int:
    """Fetch metrics for owned posts and update bandit entries.

    If an action row lacks a saved topic/slot, use default_arm_for_post if provided.
    """
    count = 0
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT post_id, topic, slot, media FROM actions WHERE kind='post'")
        rows = cur.fetchall()
        for post_id, topic, slot, media in rows:
            if not topic or not slot:
                if default_arm_for_post is None:
                    continue
                arm = default_arm_for_post
            else:
                arm = f"{topic}|{slot}|{int(media) > 0}"
            try:
                settle(xapi, str(post_id), arm)
                count += 1
            except Exception:
                # Skip failures; could add logging
                continue
    return count
