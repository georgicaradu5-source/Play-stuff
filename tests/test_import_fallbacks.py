import builtins
import importlib
import sys


def _reload_with_missing(module_name: str, missing: str):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == missing:
            raise ImportError(f"simulated missing {missing}")
        return original_import(name, *args, **kwargs)

    # Remove target module so import triggers again
    if module_name in sys.modules:
        del sys.modules[module_name]
    builtins.__import__ = fake_import  # type: ignore
    try:
        mod = importlib.import_module(module_name)
    finally:
        builtins.__import__ = original_import  # restore immediately
    return mod


def test_auth_tweepy_fallback():
    mod = _reload_with_missing("auth", "tweepy")
    assert getattr(mod, "tweepy") is None  # fallback path executed

    # reload normally to restore for other tests
    importlib.reload(mod)


def test_auth_dotenv_fallback():
    # Simulate missing dotenv; ensure load_dotenv not executed
    mod = _reload_with_missing("auth", "dotenv")
    # Presence: we don't expose dotenv symbol; just ensure module imported fine
    assert hasattr(mod, "UnifiedAuth")
    importlib.reload(mod)


def test_config_schema_pydantic_fallback():
    mod = _reload_with_missing("config_schema", "pydantic")
    # PYDANTIC_AVAILABLE flag should be False
    assert getattr(mod, "PYDANTIC_AVAILABLE") is False
    # Field returns None placeholder
    assert mod.Field("x") is None  # type: ignore[attr-defined]
    importlib.reload(mod)


def test_budget_storage_fallback():
    mod = _reload_with_missing("budget", "storage")
    # Storage symbol should exist (None placeholder assigned)
    assert getattr(mod, "Storage") is None
    importlib.reload(mod)

