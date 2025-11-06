"""Tests for configuration schema validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from config_schema import ConfigSettings, validate_config


@pytest.fixture
def example_config_path():
    """Path to example config file."""
    return Path("config.example.yaml")


@pytest.fixture
def minimal_valid_config():
    """Minimal valid configuration dictionary."""
    return {
        "auth_mode": "tweepy",
        "plan": "free",
        "topics": ["test-topic"],
        "queries": [{"query": "test query", "actions": ["like"]}],
        "schedule": {"windows": ["morning"]},
        "cadence": {"weekdays": [1, 2, 3]},
        "max_per_window": {
            "post": 1,
            "reply": 3,
            "like": 10,
            "follow": 3,
            "repost": 1,
        },
        "jitter_seconds": [8, 20],
        "learning": {"enabled": True},
        "budget": {"buffer_pct": 0.05},
    }


@pytest.fixture
def temp_config_file(minimal_valid_config):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        return Path(f.name)


def test_load_example_config(example_config_path):
    """Test loading the example configuration file."""
    if not example_config_path.exists():
        pytest.skip("config.example.yaml not found")

    is_valid, error, config = validate_config(example_config_path)

    assert is_valid, f"Example config should be valid. Error: {error}"
    assert error is None
    assert config is not None
    assert config.auth_mode.value == "tweepy"
    assert config.plan.value == "free"
    assert len(config.topics) > 0
    assert len(config.queries) > 0


def test_minimal_valid_config(temp_config_file):
    """Test loading a minimal valid configuration."""
    is_valid, error, config = validate_config(temp_config_file)

    assert is_valid, f"Minimal config should be valid. Error: {error}"
    assert error is None
    assert config is not None
    assert config.auth_mode.value == "tweepy"
    assert config.plan.value == "free"

    # Clean up
    temp_config_file.unlink()


def test_missing_required_field(minimal_valid_config):
    """Test that missing required fields cause validation failure."""
    # Remove required field
    del minimal_valid_config["plan"]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "plan" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_invalid_auth_mode(minimal_valid_config):
    """Test that invalid auth_mode values are rejected."""
    minimal_valid_config["auth_mode"] = "invalid_mode"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "auth_mode" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_invalid_plan(minimal_valid_config):
    """Test that invalid plan values are rejected."""
    minimal_valid_config["plan"] = "enterprise"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "plan" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_extra_field_allowed(minimal_valid_config):
    """Test that extra fields are allowed (Pydantic default behavior)."""
    minimal_valid_config["extra_field"] = "should_be_ignored"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    # Pydantic v2 allows extra fields by default
    assert is_valid, f"Config with extra field should be valid. Error: {error}"
    assert error is None
    assert config is not None

    # Clean up
    temp_path.unlink()


def test_invalid_jitter_range(minimal_valid_config):
    """Test that jitter_seconds with min >= max is rejected."""
    minimal_valid_config["jitter_seconds"] = [20, 8]  # min > max

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "jitter" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_invalid_weekday(minimal_valid_config):
    """Test that weekdays out of range are rejected."""
    minimal_valid_config["cadence"]["weekdays"] = [0, 8]  # Invalid: must be 1-7

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "weekday" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_invalid_action(minimal_valid_config):
    """Test that invalid query actions are rejected."""
    minimal_valid_config["queries"][0]["actions"] = ["like", "invalid_action"]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "action" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_empty_topics(minimal_valid_config):
    """Test that empty topics list is rejected."""
    minimal_valid_config["topics"] = []

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "topics" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_negative_rate_limit(minimal_valid_config):
    """Test that negative rate limits are rejected."""
    minimal_valid_config["max_per_window"]["post"] = -1

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert config is None

    # Clean up
    temp_path.unlink()


def test_buffer_pct_out_of_range(minimal_valid_config):
    """Test that buffer_pct outside [0, 1] is rejected."""
    minimal_valid_config["budget"]["buffer_pct"] = 1.5

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "buffer_pct" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_config_to_dict(minimal_valid_config):
    """Test that ConfigSettings can be converted to dict."""
    config_obj = ConfigSettings(**minimal_valid_config)
    config_dict = config_obj.to_dict()

    assert isinstance(config_dict, dict)
    assert config_dict["auth_mode"] == "tweepy"
    assert config_dict["plan"] == "free"
    assert "topics" in config_dict


def test_extended_time_windows(minimal_valid_config):
    """Test that extended schedule windows are accepted by the schema."""
    minimal_valid_config["schedule"]["windows"] = [
        "early-morning",
        "night",
        "late-night",
    ]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert is_valid, f"Extended windows should be valid. Error: {error}"
    assert error is None
    assert config is not None
    assert [w.value for w in config.schedule.windows] == [
        "early-morning",
        "night",
        "late-night",
    ]

    temp_path.unlink()


def test_file_not_found():
    """Test validation of non-existent config file."""
    is_valid, error, config = validate_config("nonexistent.yaml")

    assert not is_valid
    assert error is not None
    assert "not found" in error.lower()
    assert config is None


def test_invalid_yaml():
    """Test validation of malformed YAML file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write("invalid: yaml: content: [unclosed")
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "yaml" in error.lower() or "parsing" in error.lower()
    assert config is None

    # Clean up
    temp_path.unlink()


def test_rate_limits_optional_section(minimal_valid_config):
    """Test that rate_limits section is optional and validates correctly."""
    minimal_valid_config["rate_limits"] = {
        "read_per_15min": 15000,
        "write_per_24hr": 50,
        "custom_endpoints": {
            "/2/tweets": {"limit": 100, "window": "15min"},
            "/2/users/by": {"limit": 300, "window": "15min"},
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert is_valid, f"rate_limits should validate. Error: {error}"
    assert config is not None
    assert config.rate_limits is not None
    assert config.rate_limits.read_per_15min == 15000
    assert config.rate_limits.write_per_24hr == 50
    assert "/2/tweets" in config.rate_limits.custom_endpoints
    assert config.rate_limits.custom_endpoints["/2/tweets"].limit == 100
    assert config.rate_limits.custom_endpoints["/2/tweets"].window == "15min"

    temp_path.unlink()


def test_personas_optional_section(minimal_valid_config):
    """Test that personas section is optional and validates correctly."""
    minimal_valid_config["personas"] = {
        "default": {"tone": "friendly", "expertise": ["Python", "AI"], "style": "casual"},
        "professional": {"tone": "formal", "expertise": ["Enterprise Software"]},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert is_valid, f"personas should validate. Error: {error}"
    assert config is not None
    assert config.personas is not None
    assert "default" in config.personas
    assert config.personas["default"].tone == "friendly"
    assert "Python" in config.personas["default"].expertise
    assert config.personas["default"].style == "casual"
    assert "professional" in config.personas
    assert config.personas["professional"].tone == "formal"

    temp_path.unlink()


def test_monitoring_optional_section(minimal_valid_config):
    """Test that monitoring section is optional and validates correctly."""
    minimal_valid_config["monitoring"] = {
        "enable_telemetry": True,
        "log_retention_days": 90,
        "metrics_export": {"endpoint": "http://localhost:4317", "interval_seconds": 60},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert is_valid, f"monitoring should validate. Error: {error}"
    assert config is not None
    assert config.monitoring is not None
    assert config.monitoring.enable_telemetry is True
    assert config.monitoring.log_retention_days == 90
    assert config.monitoring.metrics_export is not None
    assert config.monitoring.metrics_export.endpoint == "http://localhost:4317"
    assert config.monitoring.metrics_export.interval_seconds == 60

    temp_path.unlink()


def test_safety_optional_section(minimal_valid_config):
    """Test that safety section is optional and validates correctly."""
    minimal_valid_config["safety"] = {
        "content_filter": {"enabled": True, "blocked_patterns": ["spam", "offensive"]},
        "rate_check": {"enabled": True, "warn_threshold_pct": 0.85},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert is_valid, f"safety should validate. Error: {error}"
    assert config is not None
    assert config.safety is not None
    assert config.safety.content_filter.enabled is True
    assert "spam" in config.safety.content_filter.blocked_patterns
    assert config.safety.rate_check.enabled is True
    assert config.safety.rate_check.warn_threshold_pct == 0.85

    temp_path.unlink()


def test_autonomous_optional_section(minimal_valid_config):
    """Test that autonomous section is optional and validates correctly."""
    minimal_valid_config["autonomous"] = {
        "decision_mode": "moderate",
        "require_approval": ["follow", "repost"],
        "auto_approve": ["like"],
        "max_daily_decisions": 150,
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert is_valid, f"autonomous should validate. Error: {error}"
    assert config is not None
    assert config.autonomous is not None
    assert config.autonomous.decision_mode.value == "moderate"
    assert "follow" in config.autonomous.require_approval
    assert "like" in config.autonomous.auto_approve
    assert config.autonomous.max_daily_decisions == 150

    temp_path.unlink()


def test_autonomous_invalid_action(minimal_valid_config):
    """Test that autonomous section rejects invalid actions."""
    minimal_valid_config["autonomous"] = {
        "decision_mode": "conservative",
        "require_approval": ["invalid_action"],
        "auto_approve": ["like"],
        "max_daily_decisions": 100,
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert not is_valid
    assert error is not None
    assert "invalid_action" in error.lower()

    temp_path.unlink()


def test_all_optional_sections_together(minimal_valid_config):
    """Test that all optional sections can be used together."""
    minimal_valid_config.update({
        "rate_limits": {
            "read_per_15min": 10000,
            "write_per_24hr": 40,
            "custom_endpoints": {},
        },
        "personas": {"default": {"tone": "friendly", "expertise": ["AI"]}},
        "monitoring": {"enable_telemetry": False, "log_retention_days": 30},
        "safety": {
            "content_filter": {"enabled": True, "blocked_patterns": []},
            "rate_check": {"enabled": True, "warn_threshold_pct": 0.8},
        },
        "autonomous": {
            "decision_mode": "conservative",
            "require_approval": ["follow"],
            "auto_approve": ["like"],
            "max_daily_decisions": 100,
        },
    })

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    assert is_valid, f"All optional sections together should validate. Error: {error}"
    assert config is not None
    assert config.rate_limits is not None
    assert config.personas is not None
    assert config.monitoring is not None
    assert config.safety is not None
    assert config.autonomous is not None

    temp_path.unlink()


def test_pydantic_unavailable_fallback(minimal_valid_config, monkeypatch):
    """Test graceful fallback when Pydantic is not available."""
    import config_schema

    # Simulate Pydantic being unavailable
    monkeypatch.setattr(config_schema, "PYDANTIC_AVAILABLE", False)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(minimal_valid_config, f)
        temp_path = Path(f.name)

    is_valid, error, config = validate_config(temp_path)

    # Should fail gracefully with helpful error message
    assert not is_valid
    assert error is not None
    assert "pydantic" in error.lower()
    assert "install" in error.lower()
    assert config is None

    temp_path.unlink()
