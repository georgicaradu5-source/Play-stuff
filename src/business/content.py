"""Content generation and template management."""

from __future__ import annotations

import random

# Topic-based post templates
TEMPLATES = {
    "power-platform": [
        "Quick tip for Power Platform builders: keep flows modular and document triggers. Small wins compound.",
        "Power BI + Power Automate = fast insights and faster action. What combo do you use most?",
        "Power Apps component libraries save so much rebuild time. Investing in reusable patterns pays off.",
        "DataverseDataverse relationships enable so much - start with the data model and the rest follows.",
    ],
    "data-viz": [
        "Data viz tip: label directly, minimize legends. Clarity > cleverness.",
        "DAX calculations can be powerful - keep measures tidy and reusable.",
        "Interactive dashboards shine when they answer questions before users ask.",
        "Color choice matters: use contrast intentionally and test for accessibility.",
    ],
    "automation": [
        "Automate the boring parts first. Start with high-frequency, low-risk tasks.",
        "Workflow automation shines when paired with good naming and error alerts.",
        "Build small, test early, then scale. Automation compounds when it's reliable.",
        "Document your flows - future you (or your team) will thank you.",
    ],
    "ai": [
        "AI is a tool, not magic. Frame the problem first, then pick the model.",
        "Prompt engineering matters: be specific, give context, iterate.",
        "Model hallucinations remind us: always validate outputs for critical use cases.",
        "Fine-tuning can beat prompt tricks when you have domain-specific data.",
    ],
}

# Reply templates for engagement
REPLY_TEMPLATES = [
    "Nice point! What's your favorite resource on this?",
    "Interesting! How are you handling edge cases?",
    "Love this - curious how you track success over time.",
    "Great insight! Have you documented this approach anywhere?",
    "This resonates. Any gotchas you hit along the way?",
    "Solid tip! How long did it take to see results?",
]


def choose_template(topic: str) -> str:
    """Choose a random template for the given topic.

    Args:
        topic: Topic key (e.g., "power-platform", "data-viz", "automation", "ai")

    Returns:
        Random template text for the topic, or default message if topic not found
    """
    candidates = TEMPLATES.get(topic, ["Sharing a quick note on automation and data."])
    return random.choice(candidates)


def make_post(topic: str, slot: str, allow_media: bool = False) -> tuple[str, str | None]:
    """Generate post text and optional media path.

    Args:
        topic: Topic key for template selection
        slot: Time slot (currently unused, reserved for future slot-specific content)
        allow_media: Whether to allow media attachment (placeholder for future feature)

    Returns:
        Tuple of (post_text, media_path). media_path is always None currently.
    """
    text = choose_template(topic)
    media_path = None
    # Media support: can be enabled later
    if allow_media:
        # Could select from a media library here
        pass
    return text, media_path


def helpful_reply(base_text: str = "") -> str:
    """Generate a helpful reply text.

    Args:
        base_text: Optional base text (currently unused, reserved for context-aware replies)

    Returns:
        Random reply template text
    """
    return random.choice(REPLY_TEMPLATES)
