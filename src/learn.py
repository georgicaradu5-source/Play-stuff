"""Thompson Sampling learning loop for optimizing agent behavior."""

from __future__ import annotations

from typing import Optional

from storage import Storage
from x_client import XClient


def compute_reward(
    like: int,
    reply: int,
    rt: int,
    quote: int,
    impressions: Optional[int] = None,
) -> float:
    """Compute reward from engagement metrics.
    
    Formula: weighted engagement divided by reach (or baseline).
    """
    numer = like + 2 * reply + 2 * rt + quote
    denom = impressions if impressions and impressions > 0 else max(1, like + reply + rt + quote)
    r = numer / denom
    return max(0.0, min(1.0, float(r)))


def settle(client: XClient, storage: Storage, post_id: str, arm: str) -> None:
    """Fetch metrics for a post and update bandit arm."""
    # Get tweet metrics
    tweet_data = client.get_tweet(post_id)
    if not tweet_data.get("data"):
        print(f"⚠️  Could not fetch metrics for {post_id}")
        return
    
    metrics = tweet_data["data"].get("public_metrics", {})
    
    like_count = metrics.get("like_count", 0)
    reply_count = metrics.get("reply_count", 0)
    retweet_count = metrics.get("retweet_count", 0)
    quote_count = metrics.get("quote_count", 0)
    impression_count = metrics.get("impression_count")
    
    # Compute reward
    reward = compute_reward(
        like=like_count,
        reply=reply_count,
        rt=retweet_count,
        quote=quote_count,
        impressions=impression_count,
    )
    
    # Update storage
    storage.update_metrics(
        post_id=post_id,
        like_count=like_count,
        reply_count=reply_count,
        retweet_count=retweet_count,
        quote_count=quote_count,
        impression_count=impression_count or 0,
        reward=reward,
    )
    
    # Update bandit arm
    storage.bandit_update(arm, reward)
    
    print(f"✓ Settled {post_id}: reward={reward:.3f} (likes={like_count}, replies={reply_count}, RT={retweet_count})")


def settle_all(
    client: XClient,
    storage: Storage,
    default_arm: Optional[str] = None,
) -> int:
    """Fetch metrics for all owned posts and update bandit entries.
    
    Returns:
        Number of posts settled
    """
    count = 0
    actions = storage.get_recent_actions(kind="post", limit=1000)
    
    for action in actions:
        post_id = action.get("post_id")
        topic = action.get("topic")
        slot = action.get("slot")
        media = action.get("media", 0)
        
        if not post_id:
            continue
        
        # Construct arm identifier
        if not topic or not slot:
            if default_arm is None:
                continue
            arm = default_arm
        else:
            arm = f"{topic}|{slot}|{int(media) > 0}"
        
        try:
            settle(client, storage, str(post_id), arm)
            count += 1
        except Exception as e:
            print(f"⚠️  Failed to settle {post_id}: {e}")
            continue
    
    return count


def print_bandit_stats(storage: Storage) -> None:
    """Print bandit arm statistics."""
    arms = storage.get_bandit_arms()
    
    if not arms:
        print("\nNo bandit data yet.")
        return
    
    print("\n=== Learning Stats (Thompson Sampling) ===")
    for arm_data in sorted(arms, key=lambda x: x.get("alpha", 0) / (x.get("alpha", 1) + x.get("beta", 1)), reverse=True):
        arm = arm_data["arm"]
        alpha = arm_data.get("alpha", 1.0)
        beta = arm_data.get("beta", 1.0)
        
        # Estimated success rate
        est_reward = alpha / (alpha + beta)
        pulls = alpha + beta - 2  # Subtract prior (1,1)
        
        print(f"\n{arm}")
        print(f"  Est. reward: {est_reward:.3f}")
        print(f"  Pulls: {int(pulls)}")
        print(f"  Alpha: {alpha:.2f}, Beta: {beta:.2f}")
