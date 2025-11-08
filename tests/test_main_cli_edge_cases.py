"""Edge case tests for main.py CLI to push coverage from 75% toward 85%+."""

import os
import sys
from pathlib import Path

# Ensure src on path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import main as main_mod  # noqa: E402


def run_main_with_args(args, env=None):
    """Helper to run main with args and capture exit code."""
    env = env or {}
    old_argv = sys.argv[:]
    old_env = dict(os.environ)
    try:
        sys.argv = ["prog"] + args
        os.environ.update(env)
        main_mod.main()
        return 0
    except SystemExit as e:
        return e.code if e.code is not None else 0
    finally:
        sys.argv = old_argv
        os.environ.clear()
        os.environ.update(old_env)


def test_missing_config_file_uses_defaults(monkeypatch, capsys):
    """When config file doesn't exist, should use default config."""
    # Patch XClient and scheduler to no-op
    import scheduler as sch
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(sch, "run_scheduler", lambda **kw: None)

    code = run_main_with_args(["--config", "/nonexistent/config.yaml", "--mode", "post", "--dry-run", "true"])
    assert code == 0


def test_config_load_yaml_not_installed(monkeypatch, tmp_path):
    """Test error when yaml module is not available."""
    # Create a config file
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\n")

    # Mock yaml to None
    import main as m

    monkeypatch.setattr(m, "yaml", None)

    code = run_main_with_args(["--config", str(cfg)])
    assert code == 1


def test_config_validation_failure_falls_back(monkeypatch, tmp_path, capsys):
    """When validation fails, should fall back to raw config loading."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: invalid_mode\nplan: free\n")

    # Patch validation to fail
    import config_schema as cs

    monkeypatch.setattr(cs, "validate_config", lambda _path: (False, "Invalid auth_mode", None))

    # Patch XClient and scheduler to allow completion
    import scheduler as sch
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(sch, "run_scheduler", lambda **kw: None)

    code = run_main_with_args(["--config", str(cfg), "--dry-run", "true"])
    # Should succeed with fallback
    assert code == 0


def test_plan_override_from_args(monkeypatch, tmp_path):
    """Test --plan argument overrides config."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    captured_config = {}

    def capture_scheduler(**kwargs):
        captured_config.update(kwargs.get("config", {}))

    import scheduler as sch
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(sch, "run_scheduler", capture_scheduler)

    code = run_main_with_args(["--config", str(cfg), "--plan", "pro", "--dry-run", "true"])
    assert code == 0
    assert captured_config.get("plan") == "pro"


def test_client_initialization_failure(monkeypatch, tmp_path, capsys):
    """Test client init failure exits with error."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import x_client as xc

    def raise_error(**kw):
        raise RuntimeError("Auth credentials missing")

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(raise_error))

    code = run_main_with_args(["--config", str(cfg), "--dry-run", "true"])
    assert code == 1
    captured = capsys.readouterr()
    assert "Failed to initialize client" in captured.out


def test_client_init_failure_oauth2_hint(monkeypatch, tmp_path, capsys):
    """Test OAuth2 failure shows --authorize hint."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: oauth2\nplan: free\n")

    import x_client as xc

    def raise_error(**kw):
        raise RuntimeError("Token not found")

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(raise_error))

    code = run_main_with_args(["--config", str(cfg), "--dry-run", "true"], env={"X_AUTH_MODE": "oauth2"})
    assert code == 1
    captured = capsys.readouterr()
    assert "--authorize" in captured.out


def test_safety_print_budget(monkeypatch, tmp_path):
    """Test --safety print-budget."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import budget as bg
    import x_client as xc

    class DummyClient:
        pass

    class DummyBudget:
        def print_budget(self):
            print("BUDGET_INFO")

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(bg.BudgetManager, "from_config", staticmethod(lambda *a, **kw: DummyBudget()))

    code = run_main_with_args(["--config", str(cfg), "--safety", "print-budget"])
    assert code == 0


def test_safety_print_limits(monkeypatch, tmp_path):
    """Test --safety print-limits."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import rate_limiter as rl
    import x_client as xc

    class DummyClient:
        pass

    class DummyLimiter:
        def print_limits(self):
            print("RATE_LIMITS")

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(rl, "RateLimiter", DummyLimiter)

    code = run_main_with_args(["--config", str(cfg), "--safety", "print-limits"])
    assert code == 0


def test_safety_print_learning(monkeypatch, tmp_path):
    """Test --safety print-learning."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import learn as ln
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(ln, "print_bandit_stats", lambda storage: print("BANDIT_STATS"))

    code = run_main_with_args(["--config", str(cfg), "--safety", "print-learning"])
    assert code == 0


def test_settle_single_post(monkeypatch, tmp_path):
    """Test --settle POST_ID."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import learn as ln
    import storage as st
    import x_client as xc

    class DummyClient:
        pass

    class DummyStorage:
        def get_recent_actions(self, kind, limit):
            return [{"post_id": "12345", "topic": "test", "slot": "afternoon", "media": 1}]

        def close(self):
            pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(st, "Storage", DummyStorage)
    monkeypatch.setattr(ln, "settle", lambda client, storage, post_id, arm: None)

    code = run_main_with_args(["--config", str(cfg), "--settle", "12345"])
    assert code == 0


def test_settle_failure(monkeypatch, tmp_path, capsys):
    """Test --settle failure handling."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import learn as ln
    import storage as st
    import x_client as xc

    class DummyClient:
        pass

    class DummyStorage:
        def get_recent_actions(self, kind, limit):
            return []

        def close(self):
            pass

    def raise_error(client, storage, post_id, arm):
        raise RuntimeError("API error")

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(st, "Storage", DummyStorage)
    monkeypatch.setattr(ln, "settle", raise_error)

    code = run_main_with_args(["--config", str(cfg), "--settle", "99999"])
    assert code == 1
    captured = capsys.readouterr()
    assert "Failed to settle" in captured.out


def test_settle_all(monkeypatch, tmp_path):
    """Test --settle-all."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import learn as ln
    import storage as st
    import x_client as xc

    class DummyClient:
        pass

    class DummyStorage:
        def close(self):
            pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(st, "Storage", DummyStorage)
    monkeypatch.setattr(ln, "settle_all", lambda client, storage, default_arm: 5)

    code = run_main_with_args(["--config", str(cfg), "--settle-all"])
    assert code == 0


def test_scheduler_keyboard_interrupt(monkeypatch, tmp_path, capsys):
    """Test scheduler KeyboardInterrupt handling."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import scheduler as sch
    import storage as st
    import x_client as xc

    class DummyClient:
        pass

    class DummyStorage:
        def close(self):
            pass

    def raise_interrupt(**kw):
        raise KeyboardInterrupt()

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(st, "Storage", DummyStorage)
    monkeypatch.setattr(sch, "run_scheduler", raise_interrupt)

    code = run_main_with_args(["--config", str(cfg), "--dry-run", "true"])
    assert code == 1
    captured = capsys.readouterr()
    assert "Interrupted" in captured.out


def test_scheduler_exception(monkeypatch, tmp_path, capsys):
    """Test scheduler exception handling."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import scheduler as sch
    import storage as st
    import x_client as xc

    class DummyClient:
        pass

    class DummyStorage:
        def close(self):
            pass

    def raise_error(**kw):
        raise RuntimeError("Scheduler crashed")

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(st, "Storage", DummyStorage)
    monkeypatch.setattr(sch, "run_scheduler", raise_error)

    code = run_main_with_args(["--config", str(cfg), "--dry-run", "true"])
    assert code == 1
    captured = capsys.readouterr()
    assert "ERROR" in captured.out


def test_default_config_structure(monkeypatch):
    """Test get_default_config returns expected structure."""
    from main import get_default_config

    config = get_default_config()
    assert config["auth_mode"] == "tweepy"
    assert config["plan"] == "free"
    assert "topics" in config
    assert "queries" in config
    assert "schedule" in config
    assert "cadence" in config


def test_config_validation_import_error(monkeypatch, tmp_path):
    """Test config validation when config_schema import fails."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    # Simulate ImportError
    import builtins

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "config_schema":
            raise ImportError("config_schema not found")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    # Patch XClient and scheduler
    import scheduler as sch
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(sch, "run_scheduler", lambda **kw: None)

    code = run_main_with_args(["--config", str(cfg), "--dry-run", "true"])
    # Should succeed with fallback
    assert code == 0


def test_config_validation_generic_exception(monkeypatch, tmp_path):
    """Test config validation with generic exception handling."""
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import config_schema as cs

    def raise_error(path):
        raise ValueError("Unexpected validation error")

    monkeypatch.setattr(cs, "validate_config", raise_error)

    # Patch XClient and scheduler
    import scheduler as sch
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kw: DummyClient()))
    monkeypatch.setattr(sch, "run_scheduler", lambda **kw: None)

    code = run_main_with_args(["--config", str(cfg), "--dry-run", "true"])
    assert code == 0
