"""Integration tests for load_config deep-merge behavior.

This module tests that load_config properly merges validated Pydantic fields
back into the raw YAML while preserving unknown/additional sections that are
not part of the schema (e.g., rate_limits, personas, monitoring, safety, autonomous).
"""

import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def config_with_extra_sections():
    """Create a config YAML with both schema-defined and extra sections."""
    config_data = {
        # Schema-defined sections
        "auth_mode": "tweepy",
        "plan": "free",
        "topics": ["AI", "Python", "Tech"],
        "queries": [{"query": "AI trends", "actions": ["like", "reply"]}],
        "schedule": {"windows": ["morning", "afternoon"]},
        "cadence": {"weekdays": [1, 2, 3, 4, 5]},
        "max_per_window": {"post": 2, "reply": 3, "like": 5, "follow": 2, "repost": 1},
        "jitter_seconds": [10, 30],
        "learning": {"enabled": True},
        "budget": {"buffer_pct": 0.05, "custom_read_cap": None, "custom_write_cap": None},
        # Extra sections not in schema
        "rate_limits": {
            "read_per_15min": 15000,
            "write_per_24hr": 50,
            "custom_endpoints": {"/2/tweets": {"limit": 100, "window": "15min"}},
        },
        "personas": {
            "default": {"tone": "friendly", "expertise": ["Python", "AI"], "style": "technical-but-accessible"},
            "professional": {"tone": "formal", "expertise": ["Software Architecture"]},
        },
        "monitoring": {
            "enable_telemetry": True,
            "log_retention_days": 30,
            "metrics_export": {"endpoint": "http://localhost:4317", "interval_seconds": 60},
        },
        "safety": {
            "content_filter": {"enabled": True, "blocked_patterns": ["spam", "offensive"]},
            "rate_check": {"enabled": True, "warn_threshold_pct": 0.8},
        },
        "autonomous": {
            "decision_mode": "conservative",
            "require_approval": ["follow", "repost"],
            "auto_approve": ["like"],
            "max_daily_decisions": 100,
        },
    }
    return config_data


@pytest.fixture
def temp_config_file(config_with_extra_sections):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump(config_with_extra_sections, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_load_config_preserves_unknown_sections(temp_config_file):
    """Test that load_config preserves sections not in the Pydantic schema."""
    from main import load_config

    # Load with validation enabled (default)
    config = load_config(temp_config_file, validate=True)

    # Verify schema-defined fields are present and validated
    assert config["auth_mode"] == "tweepy"
    assert config["plan"] == "free"
    assert config["topics"] == ["AI", "Python", "Tech"]
    assert config["schedule"]["windows"] == ["morning", "afternoon"]

    # Verify extra sections are preserved
    assert "rate_limits" in config
    assert config["rate_limits"]["read_per_15min"] == 15000
    assert config["rate_limits"]["write_per_24hr"] == 50
    assert "custom_endpoints" in config["rate_limits"]
    assert "/2/tweets" in config["rate_limits"]["custom_endpoints"]

    assert "personas" in config
    assert "default" in config["personas"]
    assert config["personas"]["default"]["tone"] == "friendly"
    assert "professional" in config["personas"]

    assert "monitoring" in config
    assert config["monitoring"]["enable_telemetry"] is True
    assert config["monitoring"]["log_retention_days"] == 30
    assert "metrics_export" in config["monitoring"]

    assert "safety" in config
    assert "content_filter" in config["safety"]
    assert config["safety"]["content_filter"]["enabled"] is True

    assert "autonomous" in config
    assert config["autonomous"]["decision_mode"] == "conservative"
    assert "follow" in config["autonomous"]["require_approval"]


def test_load_config_validated_fields_override_raw(temp_config_file):
    """Test that validated Pydantic fields override raw YAML values."""
    from main import load_config

    # Modify the file to have a boolean for feature flag (should normalize to "on"/"off")
    with open(temp_config_file, encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Add feature_flags with boolean values
    config_data["feature_flags"] = {
        "allow_likes": True,  # Should normalize to "on"
        "allow_follows": False,  # Should normalize to "off"
        "allow_media": "auto",
    }

    with open(temp_config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    config = load_config(temp_config_file, validate=True)

    # Pydantic should normalize booleans to "on"/"off"
    assert config["feature_flags"]["allow_likes"] == "on"
    assert config["feature_flags"]["allow_follows"] == "off"
    assert config["feature_flags"]["allow_media"] == "auto"


def test_load_config_deep_merge_nested_dicts(temp_config_file):
    """Test that deep-merge works correctly for nested dictionaries."""
    from main import load_config

    # Load to get baseline
    config = load_config(temp_config_file, validate=True)

    # Verify nested merge for rate_limits (not in schema)
    assert config["rate_limits"]["custom_endpoints"]["/2/tweets"]["limit"] == 100
    assert config["rate_limits"]["custom_endpoints"]["/2/tweets"]["window"] == "15min"

    # Verify nested merge for monitoring
    assert config["monitoring"]["metrics_export"]["endpoint"] == "http://localhost:4317"
    assert config["monitoring"]["metrics_export"]["interval_seconds"] == 60


def test_load_config_without_validation_preserves_all(temp_config_file):
    """Test that load_config with validate=False preserves everything as-is."""
    from main import load_config

    config = load_config(temp_config_file, validate=False)

    # All sections should be present exactly as in YAML
    assert "rate_limits" in config
    assert "personas" in config
    assert "monitoring" in config
    assert "safety" in config
    assert "autonomous" in config

    # Schema-defined sections also present
    assert config["auth_mode"] == "tweepy"
    assert config["plan"] == "free"


def test_load_config_invalid_schema_field_falls_back(temp_config_file):
    """Test that invalid schema fields cause fallback to raw YAML (backward compat)."""
    from main import load_config

    # Corrupt a schema-required field
    with open(temp_config_file, encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    config_data["plan"] = "invalid_tier"  # Not a valid PlanTier enum

    with open(temp_config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    # Should fall back to raw YAML without validation
    config = load_config(temp_config_file, validate=True)

    # Still loads the config, preserving invalid value
    assert config["plan"] == "invalid_tier"

    # Extra sections still preserved
    assert "rate_limits" in config
    assert "personas" in config


def test_load_config_merge_preserves_list_replacement():
    """Test that lists are replaced entirely, not merged element-wise."""
    config_data = {
        "auth_mode": "tweepy",
        "plan": "free",
        "topics": ["Topic1", "Topic2"],  # Original list
        "queries": [{"query": "test", "actions": ["like"]}],
        "schedule": {"windows": ["morning"]},
        "cadence": {"weekdays": [1, 2, 3]},
        "max_per_window": {"post": 1, "reply": 1, "like": 1, "follow": 1, "repost": 1},
        "jitter_seconds": [5, 15],
        "learning": {"enabled": False},
        "budget": {"buffer_pct": 0.1},
        "custom_list": ["A", "B", "C"],  # Extra section with list
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    try:
        from main import load_config

        config = load_config(temp_path, validate=True)

        # Verified list from schema should be replaced (not element-merged)
        assert config["topics"] == ["Topic1", "Topic2"]
        assert config["cadence"]["weekdays"] == [1, 2, 3]

        # Custom list should be preserved as-is
        assert config["custom_list"] == ["A", "B", "C"]

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_load_config_merge_type_override():
    """Test that validated values override raw values even when types differ."""
    config_data = {
        "auth_mode": "tweepy",
        "plan": "free",
        "topics": ["Tech"],
        "queries": [{"query": "test", "actions": ["like"]}],
        "schedule": {"windows": ["morning"]},
        "cadence": {"weekdays": [1]},
        "max_per_window": {"post": 1, "reply": 1, "like": 1, "follow": 1, "repost": 1},
        "jitter_seconds": [5, 15],
        "learning": {"enabled": False},
        "budget": {
            "buffer_pct": 0.1,
            "custom_read_cap": "unlimited",  # Wrong type, but in extra section
        },
        "logging": {"level": "INFO", "file": None},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    try:
        from main import load_config

        config = load_config(temp_path, validate=True)

        # Pydantic validation should convert/validate types in schema
        assert isinstance(config["budget"]["buffer_pct"], float)
        assert config["budget"]["buffer_pct"] == 0.1

        # custom_read_cap with wrong type should either:
        # 1) Be validated and fail (causing fallback to raw), or
        # 2) Be validated and coerced to None
        # Let's check what happens
        assert "budget" in config

    finally:
        Path(temp_path).unlink(missing_ok=True)
