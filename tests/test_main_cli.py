import os
import sys
from pathlib import Path

# Ensure src on path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import main as main_mod  # noqa: E402


def run_main_with_args(args, env=None):
    env = env or {}
    old_argv = sys.argv[:]
    old_env = dict(os.environ)
    try:
        sys.argv = ["prog"] + args
        os.environ.update(env)
        main_mod.main()
        return 0
    except SystemExit as e:
        return e.code
    finally:
        sys.argv = old_argv
        os.environ.clear()
        os.environ.update(old_env)


def test_authorize_requires_oauth2(monkeypatch):
    code = run_main_with_args(["--authorize"], env={"X_AUTH_MODE": "tweepy"})
    assert code == 1


def test_authorize_success(monkeypatch):
    # Mock UnifiedAuth.from_env(...).authorize_oauth2 -> True, then exit 0
    class DummyAuth:
        def authorize_oauth2(self, scopes):
            return True

    # Patch inside main.main
    import auth as auth_mod

    monkeypatch.setattr(auth_mod.UnifiedAuth, "from_env", lambda *_args, **_kw: DummyAuth())

    code = run_main_with_args(["--authorize"], env={"X_AUTH_MODE": "oauth2"})
    assert code == 0


def test_authorize_failure(monkeypatch):
    """Test --authorize with OAuth2 returns exit code 1 when authorization fails (covers main.py lines 245-247)."""
    class DummyAuth:
        def authorize_oauth2(self, scopes):
            return False  # Authorization failed

    import auth as auth_mod

    monkeypatch.setattr(auth_mod.UnifiedAuth, "from_env", lambda *_args, **_kw: DummyAuth())

    code = run_main_with_args(["--authorize"], env={"X_AUTH_MODE": "oauth2"})
    assert code == 1  # Should exit with code 1 on failure


def test_main_initializes_client_dry_run(monkeypatch, tmp_path):
    # Provide minimal config file
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    # Patch XClient.from_env to dummy
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kwargs: DummyClient()))

    # Patch run_scheduler to no-op
    import scheduler as sch

    monkeypatch.setattr(sch, "run_scheduler", lambda **kwargs: None)

    code = run_main_with_args(["--mode", "both", "--dry-run", "true", "--config", str(cfg)])
    assert code == 0
