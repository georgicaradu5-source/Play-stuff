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


def test_safety_print_budget(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    # Fake BudgetManager
    class DummyBudget:
        def print_budget(self):
            self.called = True

    import budget as budget_mod

    monkeypatch.setattr(budget_mod.BudgetManager, "from_config", staticmethod(lambda *a, **k: DummyBudget()))
    code = run_main_with_args(["--safety", "print-budget", "--config", str(cfg)])
    assert code == 0


def test_safety_print_limits(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import rate_limiter as rl

    called = {"yes": False}

    class DummyRL(rl.RateLimiter):
        def print_limits(self):
            called["yes"] = True

    monkeypatch.setattr(rl, "RateLimiter", DummyRL)
    code = run_main_with_args(["--safety", "print-limits", "--config", str(cfg)])
    assert code == 0 and called["yes"] is True


def test_safety_print_learning(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    import learn as learn_mod

    called = {"yes": False}

    def fake_print_bandit(storage):
        called["yes"] = True

    monkeypatch.setattr(learn_mod, "print_bandit_stats", fake_print_bandit)
    code = run_main_with_args(["--safety", "print-learning", "--config", str(cfg)])
    assert code == 0 and called["yes"] is True


def test_settle_single_and_all(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("auth_mode: tweepy\nplan: free\n")

    # Patch XClient.from_env to dummy to avoid real client init
    import x_client as xc

    class DummyClient:
        pass

    monkeypatch.setattr(xc.XClient, "from_env", staticmethod(lambda **kwargs: DummyClient()))

    # Patch Storage to control get_recent_actions
    import storage as storage_mod

    class DummyStorage:
        def __init__(self):
            pass

        def get_recent_actions(self, kind: str, limit: int = 1):
            return [{"post_id": "P123", "topic": "t", "slot": "afternoon", "media": 1}]

        def close(self):
            pass

    monkeypatch.setattr(storage_mod, "Storage", DummyStorage)

    # Patch learn.settle and learn.settle_all
    import learn as learn_mod

    captured = {"settle": None, "settle_all": None}

    def fake_settle(client, storage, post_id, arm):
        captured["settle"] = (post_id, arm)

    def fake_settle_all(client, storage, default_arm):
        captured["settle_all"] = default_arm
        return 5

    monkeypatch.setattr(learn_mod, "settle", fake_settle)
    monkeypatch.setattr(learn_mod, "settle_all", fake_settle_all)

    # --settle
    code1 = run_main_with_args(["--settle", "P123", "--config", str(cfg)])
    assert code1 == 0
    assert captured["settle"] == ("P123", "t|afternoon|True")

    # --settle-all
    code2 = run_main_with_args(["--settle-all", "--config", str(cfg)])
    assert code2 == 0
    assert captured["settle_all"] == "default|morning|False"
