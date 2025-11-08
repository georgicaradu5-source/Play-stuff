import tempfile
from pathlib import Path

import yaml

import config_schema as cs


def test_validate_config_unexpected_exception(monkeypatch):
    # Prepare minimal valid YAML content
    minimal = {
        "auth_mode": "tweepy",
        "plan": "free",
        "topics": ["t"],
        "queries": [{"query": "q", "actions": ["like"]}],
        "schedule": {"windows": ["morning"]},
        "cadence": {"weekdays": [1]},
        "max_per_window": {"post": 1, "reply": 1, "like": 1, "follow": 1, "repost": 1},
        "jitter_seconds": [1, 2],
        "learning": {"enabled": True},
        "budget": {"buffer_pct": 0.05},
    }

    class RaisingConfig:
        def __init__(self, **kwargs):  # noqa: D401 - simulate construction failure
            raise RuntimeError("boom")

    # Force the generic Exception branch inside validate_config
    monkeypatch.setattr(cs, "ConfigSettings", RaisingConfig)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump(minimal, f)
        path = Path(f.name)

    ok, err, cfg = cs.validate_config(path)
    assert ok is False
    assert err is not None and "Unexpected error" in err
    assert cfg is None

    path.unlink()
