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
