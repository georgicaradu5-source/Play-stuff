"""Filtering logic for post and action eligibility."""

from __future__ import annotations


def should_act_on_post(
    post_id: str,
    author_id: str | None,
    me_user_id: str,
) -> bool:
    """Determine if we should act on a post.

    Filters out:
    - Posts by the authenticated user (no self-interaction)

    Args:
        post_id: ID of the post to evaluate
        author_id: Author's user ID (may be None)
        me_user_id: Authenticated user's ID

    Returns:
        True if we should consider acting on this post, False otherwise
    """
    # Skip self-posts
    if author_id and str(author_id) == str(me_user_id):
        return False

    return True


def filter_eligible_actions(
    post_id: str,
    available_actions: list[str],
    remaining_quotas: dict[str, int],
) -> list[str]:
    """Filter actions to those that are both available and have quota remaining.

    Args:
        post_id: ID of the post (currently unused, reserved for post-specific rules)
        available_actions: List of action types that could be performed
        remaining_quotas: Dict mapping action type to remaining count

    Returns:
        List of action types that have quota remaining
    """
    eligible = []
    for action in available_actions:
        if remaining_quotas.get(action, 0) > 0:
            eligible.append(action)
    return eligible
