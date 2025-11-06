"""Configuration schema validation using Pydantic v2.

This module provides strict type validation for YAML configuration files
used by the X Agent. It ensures configuration integrity at startup and
provides clear error messages for invalid values.

Example:
    >>> is_valid, error, config = validate_config("config.yaml")
    >>> if not is_valid:
    ...     print(f"Config error: {error}")
"""

from enum import Enum
from pathlib import Path
from typing import Any

import yaml

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
    from pydantic import ValidationError as PydanticValidationError

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore[misc,assignment]

    def Field(*args: Any, **kwargs: Any) -> None:  # type: ignore[misc] # noqa: N802
        """Fallback Field when Pydantic not available."""
        return None

    def field_validator(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        """Fallback field_validator when Pydantic not available."""
        def decorator(f: Any) -> Any:
            return f
        return decorator

    def model_validator(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        """Fallback model_validator when Pydantic not available."""
        def decorator(f: Any) -> Any:
            return f
        return decorator

    PydanticValidationError = Exception  # type: ignore[misc,assignment]


class AuthMode(str, Enum):
    """Authentication mode for X API."""

    TWEEPY = "tweepy"
    OAUTH2 = "oauth2"


class PlanTier(str, Enum):
    """X API plan tier."""

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"


class TimeWindow(str, Enum):
    """Time windows for posting."""

    MORNING = "morning"  # 9am-12pm
    AFTERNOON = "afternoon"  # 1pm-5pm
    EVENING = "evening"  # 6pm-9pm
    EARLY_MORNING = "early-morning"  # 5am-8am
    NIGHT = "night"  # 9pm-11pm
    LATE_NIGHT = "late-night"  # 11pm-2am


class FeatureToggle(str, Enum):
    """Feature flag states."""

    AUTO = "auto"
    ON = "on"
    OFF = "off"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class QueryConfig(BaseModel):
    """Search query configuration."""

    query: str = Field(..., min_length=1, description="X search query string")
    actions: list[str] = Field(
        ..., min_length=1, description="Actions to perform: like, reply, follow, repost"
    )

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: list[str]) -> list[str]:
        """Ensure all actions are valid."""
        valid_actions = {"like", "reply", "follow", "repost"}
        for action in v:
            if action not in valid_actions:
                raise ValueError(
                    f"Invalid action '{action}'. Must be one of: {valid_actions}"
                )
        return v


class ScheduleConfig(BaseModel):
    """Scheduling configuration."""

    windows: list[TimeWindow] = Field(
        ..., min_length=1, description="Time windows for posting"
    )


class CadenceConfig(BaseModel):
    """Posting cadence configuration."""

    weekdays: list[int] = Field(
        ..., min_length=1, max_length=7, description="Days of week (1=Monday, 7=Sunday)"
    )

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, v: list[int]) -> list[int]:
        """Ensure weekdays are in valid range."""
        for day in v:
            if not 1 <= day <= 7:
                raise ValueError(f"Weekday {day} out of range. Must be 1-7.")
        return v


class MaxPerWindowConfig(BaseModel):
    """Rate limits per time window."""

    post: int = Field(..., ge=0, description="Max posts per window")
    reply: int = Field(..., ge=0, description="Max replies per window")
    like: int = Field(..., ge=0, description="Max likes per window")
    follow: int = Field(..., ge=0, description="Max follows per window")
    repost: int = Field(..., ge=0, description="Max reposts per window")


class LearningConfig(BaseModel):
    """Thompson Sampling learning configuration."""

    enabled: bool = Field(..., description="Enable Thompson Sampling optimization")


class BudgetConfig(BaseModel):
    """Budget and rate limit configuration."""

    buffer_pct: float = Field(
        ..., ge=0.0, le=1.0, description="Safety buffer percentage (0.05 = 5%)"
    )
    custom_read_cap: int | None = Field(
        None, ge=0, description="Optional custom read cap"
    )
    custom_write_cap: int | None = Field(
        None, ge=0, description="Optional custom write cap"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    file: str | None = Field(None, description="Optional log file path")
    format: str | None = Field(None, description="Optional log format string")


class FeatureFlagsConfig(BaseModel):
    """Feature flags configuration."""

    allow_likes: FeatureToggle = Field(
        default=FeatureToggle.AUTO, description="Enable likes"
    )
    allow_follows: FeatureToggle = Field(
        default=FeatureToggle.AUTO, description="Enable follows"
    )
    allow_media: FeatureToggle = Field(
        default=FeatureToggle.OFF, description="Enable media uploads"
    )

    @field_validator("allow_likes", "allow_follows", "allow_media", mode="before")
    @classmethod
    def normalize_feature_toggle(cls, v):
        """Normalize boolean values to FeatureToggle enum."""
        if isinstance(v, bool):
            return "on" if v else "off"
        return v


class ConfigSettings(BaseModel):
    """Complete configuration schema for X Agent."""

    auth_mode: AuthMode = Field(..., description="Authentication mode")
    plan: PlanTier = Field(..., description="X API plan tier")
    topics: list[str] = Field(
        ..., min_length=1, description="Topics for content generation"
    )
    queries: list[QueryConfig] = Field(
        ..., min_length=1, description="Search queries for interaction"
    )
    schedule: ScheduleConfig = Field(..., description="Posting schedule")
    cadence: CadenceConfig = Field(..., description="Posting cadence")
    max_per_window: MaxPerWindowConfig = Field(..., description="Rate limits per window")
    jitter_seconds: tuple[int, int] = Field(
        ..., description="Jitter bounds [min, max] in seconds"
    )
    learning: LearningConfig = Field(..., description="Learning configuration")
    budget: BudgetConfig = Field(..., description="Budget configuration")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    feature_flags: FeatureFlagsConfig = Field(
        default_factory=FeatureFlagsConfig, description="Feature flags"
    )

    @field_validator("jitter_seconds")
    @classmethod
    def validate_jitter(cls, v: tuple[int, int]) -> tuple[int, int]:
        """Ensure jitter min < max."""
        if len(v) != 2:
            raise ValueError("jitter_seconds must be [min, max]")
        min_jitter, max_jitter = v
        if min_jitter >= max_jitter:
            raise ValueError(
                f"jitter_seconds min ({min_jitter}) must be < max ({max_jitter})"
            )
        if min_jitter < 0:
            raise ValueError(f"jitter_seconds min ({min_jitter}) must be >= 0")
        return v

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, v: list[str]) -> list[str]:
        """Ensure topics are non-empty strings."""
        for topic in v:
            if not topic.strip():
                raise ValueError("Topic strings cannot be empty")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for backward compatibility."""
        return self.model_dump(mode="python")


def validate_config(
    path: str | Path,
) -> tuple[bool, str | None, ConfigSettings | None]:
    """Validate a YAML configuration file against the schema.

    Args:
        path: Path to YAML configuration file

    Returns:
        Tuple of (is_valid, error_message, config_object)
        - is_valid: True if validation passed
        - error_message: Error description if validation failed, None otherwise
        - config_object: Validated ConfigSettings instance if successful, None otherwise

    Example:
        >>> is_valid, error, config = validate_config("config.yaml")
        >>> if is_valid:
        ...     print(f"Config loaded: {config.plan}")
        ... else:
        ...     print(f"Validation failed: {error}")
    """
    if not PYDANTIC_AVAILABLE:
        return (
            False,
            "Pydantic is not installed. Install with: pip install pydantic>=2.0",
            None,
        )

    try:
        # Load YAML
        config_path = Path(path)
        if not config_path.exists():
            return False, f"Config file not found: {path}", None

        with open(config_path, encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        if not isinstance(raw_config, dict):
            return False, "Config file must contain a YAML dictionary", None

        # Validate with Pydantic
        config_obj = ConfigSettings(**raw_config)
        return True, None, config_obj

    except PydanticValidationError as e:
        # Collect all validation errors
        errors = []
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append(f"  {location}: {message}")

        error_msg = "Configuration validation failed:\n" + "\n".join(errors)
        return False, error_msg, None

    except yaml.YAMLError as e:
        return False, f"YAML parsing error: {e}", None

    except Exception as e:
        return False, f"Unexpected error during validation: {e}", None
