"""Template-based content generation and interaction actions."""

from __future__ import annotations

import random

from storage import Storage

TEMPLATES = {
    "power-platform": [
        "Quick tip for Power Platform builders: keep flows modular and document triggers. Small wins compound.",
        "Power BI + Power Automate = fast insights and faster action. What combo do you use most?",
        "Power Apps component libraries save so much rebuild time. Investing in reusable patterns pays off.",
        "DataverseDataverse relationships enable so much—start with the data model and the rest follows.",
    ],
    "data-viz": [
        "Data viz tip: label directly, minimize legends. Clarity > cleverness.",
        "DAX calculations can be powerful—keep measures tidy and reusable.",
        "Interactive dashboards shine when they answer questions before users ask.",
        "Color choice matters: use contrast intentionally and test for accessibility.",
    ],
    "automation": [
        "Automate the boring parts first. Start with high-frequency, low-risk tasks.",
        "Workflow automation shines when paired with good naming and error alerts.",
        "Build small, test early, then scale. Automation compounds when it's reliable.",
        "Document your flows—future you (or your team) will thank you.",
    ],
    "ai": [
        "AI is a tool, not magic. Frame the problem first, then pick the model.",
        "Prompt engineering matters: be specific, give context, iterate.",
        "Model hallucinations remind us: always validate outputs for critical use cases.",
        "Fine-tuning can beat prompt tricks when you have domain-specific data.",
    ],
}


REPLY_TEMPLATES = [
    "Nice point! What's your favorite resource on this?",
    "Interesting! How are you handling edge cases?",
    "Love this—curious how you track success over time.",
    "Great insight! Have you documented this approach anywhere?",
    "This resonates. Any gotchas you hit along the way?",
    "Solid tip! How long did it take to see results?",
]


def choose_template(topic: str) -> str:
    """Choose a random template for the given topic."""
    candidates = TEMPLATES.get(topic, ["Sharing a quick note on automation and data."])
    return random.choice(candidates)


def make_post(topic: str, slot: str, allow_media: bool = False) -> tuple[str, str | None]:
    """Generate post text and optional media path."""
    text = choose_template(topic)
    media_path = None
    # Media support: can be enabled later
    if allow_media:
        # Could select from a media library here
        pass
    return text, media_path


def helpful_reply(base_text: str = "") -> str:
    """Generate a helpful reply text."""
    return random.choice(REPLY_TEMPLATES)


def act_on_search(
    client,
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

        # Skip self
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
