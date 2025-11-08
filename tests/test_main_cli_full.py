import builtins
import importlib
import os
import runpy
import subprocess
import sys
import types
from pathlib import Path


def _run_main_with_args(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    python_exe = sys.executable
    main_path = str(Path(__file__).resolve().parents[1] / "src" / "main.py")
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    return subprocess.run([python_exe, main_path, *args], capture_output=True, text=True, env=env_vars)


def test_cli_dry_run_true(monkeypatch, tmp_path):
    import main as main_mod

    # Ensure no config file; default config path used
    monkeypatch.setenv("X_AUTH_MODE", "tweepy")
    monkeypatch.setenv("TELEMETRY_ENABLED", "false")

    # Stub XClient and scheduler
    called = {"scheduler": False}

    class DummyClient:
        pass

    monkeypatch.setattr(main_mod, "attach_tracecontext_to_logs", lambda: None)
    monkeypatch.setattr(main_mod, "init_telemetry", lambda: None)
    monkeypatch.setattr(
        main_mod,
        "get_logger",
        lambda name: types.SimpleNamespace(
            info=lambda *a, **k: None,
            debug=lambda *a, **k: None,
            warning=lambda *a, **k: None,
            error=lambda *a, **k: None,
        ),
    )
    monkeypatch.setattr(main_mod, "configure_logging", lambda *a, **k: None)

    import x_client as x_client_mod

    monkeypatch.setattr(x_client_mod.XClient, "from_env", staticmethod(lambda dry_run=False: DummyClient()))

    def fake_run_scheduler(**kwargs):
        called["scheduler"] = True

    # Inject run_scheduler into main namespace when imported
    monkeypatch.setitem(sys.modules, "scheduler", types.SimpleNamespace(run_scheduler=fake_run_scheduler))

    # Simulate command-line args
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setattr(sys, "argv", ["prog", "--mode", "both", "--dry-run", "true"])

    main_mod.main()

    assert called["scheduler"] is True


def test_cli_authorize_oauth2_success(monkeypatch):
    # Force OAuth2 path
    monkeypatch.setenv("X_AUTH_MODE", "oauth2")
    monkeypatch.setenv("TELEMETRY_ENABLED", "false")

    import main as main_mod

    # Stub UnifiedAuth
    class DummyAuth:
        def authorize_oauth2(self, scopes):
            return True

    import auth as auth_mod

    monkeypatch.setattr(auth_mod.UnifiedAuth, "from_env", classmethod(lambda cls, mode: DummyAuth()))
    # Avoid noisy logging/telemetry
    monkeypatch.setattr(main_mod, "attach_tracecontext_to_logs", lambda: None)
    monkeypatch.setattr(main_mod, "init_telemetry", lambda: None)
    monkeypatch.setattr(main_mod, "configure_logging", lambda *a, **k: None)

    # Capture sys.exit
    exits = {}

    def fake_exit(code=0):
        exits["code"] = code
        raise SystemExit(code)

    monkeypatch.setattr(sys, "argv", ["prog", "--authorize"])
    monkeypatch.setattr(sys, "exit", fake_exit)

    try:
        main_mod.main()
    except SystemExit:
        pass

    assert exits.get("code") == 0


def test_cli_config_validation_import_fallback(monkeypatch, tmp_path):
    # Create a minimal config file so that YAML path is taken if available
    cfg = tmp_path / "config.yaml"
    cfg.write_text("auth_mode: tweepy\n", encoding="utf-8")

    # Reload main with yaml available; we'll only simulate config_schema ImportError during load_config
    import main as main_mod

    # Patch import to raise ImportError only for config_schema.validate path
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "config_schema":
            raise ImportError("simulated missing pydantic")
        return original_import(name, *args, **kwargs)

    monkeypatch.setenv("TELEMETRY_ENABLED", "false")

    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        # Call load_config directly to avoid running the entire app
        config = main_mod.load_config(str(cfg), validate=True)
    finally:
        monkeypatch.setattr(builtins, "__import__", original_import)

    assert config.get("auth_mode") == "tweepy"


def test_cli_yaml_import_fallback_raises(monkeypatch, tmp_path):
    # To exercise yaml import fallback: file must exist and yaml import must fail, causing RuntimeError
    cfg = tmp_path / "config.yaml"
    cfg.write_text("auth_mode: tweepy\n", encoding="utf-8")

    # Reload 'main' module with yaml import failing
    if "main" in sys.modules:
        del sys.modules["main"]

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("simulated missing pyyaml")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        main_mod = importlib.import_module("main")
    finally:
        monkeypatch.setattr(builtins, "__import__", original_import)

    # Now calling load_config should raise because yaml is None and file exists
    try:
        main_mod.load_config(str(cfg), validate=False)
        assert False, "Expected RuntimeError due to missing PyYAML"
    except RuntimeError as e:
        assert "PyYAML not installed" in str(e)


def test_cli_main_guard_subprocess_safety_print(monkeypatch, tmp_path):
    # Provide a minimal config file to reduce validation noise
    cfg = tmp_path / "config.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n", encoding="utf-8")
    env = {"TELEMETRY_ENABLED": "false", "X_AUTH_MODE": "tweepy"}
    result = _run_main_with_args(["--safety", "print-budget", "--config", str(cfg)], env=env)
    assert result.returncode == 0
    # Allow warnings in stderr, but no fatal ERROR lines
    assert "Authorization failed" not in result.stderr
    assert "[ERROR]" not in result.stdout


def test_main_guard_via_runpy(monkeypatch, tmp_path):
    # Run the script as __main__ in-process to cover the guard line
    cfg = tmp_path / "config.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n", encoding="utf-8")
    monkeypatch.setenv("TELEMETRY_ENABLED", "false")
    main_path = str(Path(__file__).resolve().parents[1] / "src" / "main.py")

    # Arrange argv for a fast-exit safety command
    monkeypatch.setattr(sys, "argv", ["prog", "--safety", "print-budget", "--config", str(cfg)])

    try:
        runpy.run_path(main_path, run_name="__main__")
    except SystemExit as e:
        # print-budget path exits with code 0
        assert e.code == 0
