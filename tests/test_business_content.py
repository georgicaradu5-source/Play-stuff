"""Tests for business logic content generation."""

import random

from business.content import REPLY_TEMPLATES, TEMPLATES, choose_template, helpful_reply, make_post


def test_templates_structure():
    """Test that TEMPLATES dict has expected structure."""
    assert isinstance(TEMPLATES, dict)
    assert "power-platform" in TEMPLATES
    assert "data-viz" in TEMPLATES
    assert "automation" in TEMPLATES
    assert "ai" in TEMPLATES

    # Each topic should have a list of templates
    for topic, templates in TEMPLATES.items():
        assert isinstance(templates, list)
        assert len(templates) > 0
        for template in templates:
            assert isinstance(template, str)
            assert len(template) > 0


def test_reply_templates_structure():
    """Test that REPLY_TEMPLATES list has expected structure."""
    assert isinstance(REPLY_TEMPLATES, list)
    assert len(REPLY_TEMPLATES) > 0
    for template in REPLY_TEMPLATES:
        assert isinstance(template, str)
        assert len(template) > 0


def test_choose_template_known_topic():
    """Test choose_template with known topic."""
    topic = "power-platform"
    result = choose_template(topic)

    assert isinstance(result, str)
    assert result in TEMPLATES[topic]


def test_choose_template_unknown_topic():
    """Test choose_template with unknown topic returns default."""
    topic = "unknown-topic-xyz"
    result = choose_template(topic)

    assert isinstance(result, str)
    assert result == "Sharing a quick note on automation and data."


def test_choose_template_randomness(monkeypatch):
    """Test that choose_template uses random.choice."""
    topic = "ai"
    expected = "AI is a tool, not magic. Frame the problem first, then pick the model."

    # Mock random.choice to return first item
    def mock_choice(seq):
        return seq[0]

    monkeypatch.setattr(random, "choice", mock_choice)
    result = choose_template(topic)
    assert result == expected


def test_make_post_basic():
    """Test make_post returns text and None media_path."""
    topic = "automation"
    slot = "morning"

    text, media_path = make_post(topic, slot)

    assert isinstance(text, str)
    assert text in TEMPLATES[topic]
    assert media_path is None


def test_make_post_with_media_flag():
    """Test make_post with allow_media=True (currently no-op)."""
    topic = "data-viz"
    slot = "afternoon"

    text, media_path = make_post(topic, slot, allow_media=True)

    assert isinstance(text, str)
    assert text in TEMPLATES[topic]
    assert media_path is None  # Media not yet implemented


def test_helpful_reply_basic():
    """Test helpful_reply returns a reply template."""
    result = helpful_reply()

    assert isinstance(result, str)
    assert result in REPLY_TEMPLATES


def test_helpful_reply_with_base_text():
    """Test helpful_reply with base_text (currently unused)."""
    result = helpful_reply(base_text="Some context")

    assert isinstance(result, str)
    assert result in REPLY_TEMPLATES


def test_helpful_reply_randomness(monkeypatch):
    """Test that helpful_reply uses random.choice."""
    expected = REPLY_TEMPLATES[0]

    # Mock random.choice to return first item
    def mock_choice(seq):
        return seq[0]

    monkeypatch.setattr(random, "choice", mock_choice)
    result = helpful_reply()
    assert result == expected


def test_all_topics_have_content():
    """Test all topics have at least 3 templates for variety."""
    for topic, templates in TEMPLATES.items():
        assert len(templates) >= 3, f"Topic '{topic}' should have at least 3 templates"


def test_reply_templates_have_variety():
    """Test reply templates have at least 5 options."""
    assert len(REPLY_TEMPLATES) >= 5


def test_template_lengths_reasonable():
    """Test templates are not too long (Twitter limit aware)."""
    max_length = 280  # Twitter character limit

    for topic, templates in TEMPLATES.items():
        for template in templates:
            assert len(template) < max_length, f"Template in '{topic}' exceeds {max_length} chars"

    for template in REPLY_TEMPLATES:
        assert len(template) < max_length, f"Reply template exceeds {max_length} chars"
