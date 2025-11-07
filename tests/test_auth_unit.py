import json
import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import auth as auth_mod  # noqa: E402
from auth import UnifiedAuth  # noqa: E402


class DummyResp:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    # Prevent using a real token file
    monkeypatch.chdir(tmp_path)
    for k in list(os.environ.keys()):
        if k.startswith("X_"):
            monkeypatch.delenv(k, raising=False)
    yield


def test_from_env_invalid_mode(monkeypatch):
    monkeypatch.setenv("X_AUTH_MODE", "invalid")
    with pytest.raises(ValueError):
        UnifiedAuth.from_env()


def test_from_env_with_mode_override(monkeypatch):
    monkeypatch.setenv("X_AUTH_MODE", "tweepy")
    # Override explicit mode to oauth2
    ua = UnifiedAuth.from_env("oauth2")
    assert ua.mode == "oauth2"


def test_generate_pkce_pair():
    ua = UnifiedAuth(mode="oauth2", client_id="cid")
    verifier, challenge = ua._generate_pkce_pair()
    assert len(verifier) > 10
    # base64 url safe w/o '=' padding
    assert "=" not in verifier
    assert len(challenge) > 10


def test_exchange_code_saves_tokens(monkeypatch, tmp_path):
    ua = UnifiedAuth(mode="oauth2", client_id="cid", token_file=str(tmp_path / "t.json"))

    captured = {}

    def fake_post(url, data=None, headers=None, auth=None):  # noqa: D401
        captured["data"] = data
        return DummyResp(200, {"access_token": "A", "refresh_token": "R"})

    monkeypatch.setattr(auth_mod, "requests", types.SimpleNamespace(post=fake_post))

    token = ua._exchange_code("code123", "verifierXYZ")  # noqa: SLF001
    assert token == "A"
    assert ua.oauth2_refresh_token == "R"
    assert (tmp_path / "t.json").exists()
    saved = json.loads((tmp_path / "t.json").read_text())
    assert saved["access_token"] == "A"
    assert captured["data"]["code"] == "code123"


def test_refresh_oauth2_token(monkeypatch, tmp_path):
    # Prepare existing refresh token via file
    token_file = tmp_path / "tok.json"
    token_file.write_text(json.dumps({"access_token": "OLD", "refresh_token": "REF"}))
    ua = UnifiedAuth(mode="oauth2", client_id="cid", token_file=str(token_file))

    def fake_post(url, data=None, headers=None, auth=None):
        assert data["grant_type"] == "refresh_token"
        return DummyResp(200, {"access_token": "NEW", "refresh_token": "REF2"})

    monkeypatch.setattr(auth_mod, "requests", types.SimpleNamespace(post=fake_post))

    new_token = ua.refresh_oauth2_token()
    assert new_token == "NEW"
    assert ua.oauth2_refresh_token == "REF2"


def test_get_oauth2_access_token_loads_from_file(monkeypatch, tmp_path):
    token_file = tmp_path / "tok.json"
    token_file.write_text(json.dumps({"access_token": "X1", "refresh_token": "Y1"}))
    ua = UnifiedAuth(mode="oauth2", client_id="cid", token_file=str(token_file))
    token = ua.get_oauth2_access_token()
    assert token == "X1"


def test_get_oauth2_access_token_missing_raises():
    ua = UnifiedAuth(mode="oauth2", client_id="cid", token_file="missing.json")
    with pytest.raises(RuntimeError):
        ua.get_oauth2_access_token()


def test_get_me_user_id_oauth2(monkeypatch):
    ua = UnifiedAuth(mode="oauth2", client_id="cid")
    ua.oauth2_access_token = "TOKEN123"

    def fake_get(url, headers=None):
        assert headers["Authorization"].startswith("Bearer ")
        return DummyResp(200, {"data": {"id": "555"}})

    monkeypatch.setattr(auth_mod, "requests", types.SimpleNamespace(get=fake_get))
    uid = ua.get_me_user_id()
    assert uid == "555"
    # cached
    assert ua.get_me_user_id() == "555"


def test_get_tweepy_client_errors_when_not_in_mode():
    ua = UnifiedAuth(mode="oauth2", client_id="cid")
    with pytest.raises(RuntimeError):
        ua.get_tweepy_client()


def test_get_tweepy_client_missing_creds(monkeypatch):
    ua = UnifiedAuth(mode="tweepy")
    # Ensure tweepy placeholder module
    monkeypatch.setattr(auth_mod, "tweepy", types.SimpleNamespace(Client=object), raising=False)
    with pytest.raises(RuntimeError):
        ua.get_tweepy_client()


def test_get_tweepy_client_success(monkeypatch):
    class DummyClient:
        def __init__(self, consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None, wait_on_rate_limit=False):  # noqa: D401,E501
            self.consumer_key = consumer_key
            self.access_token = access_token

    dummy_mod = types.SimpleNamespace(Client=DummyClient)
    monkeypatch.setattr(auth_mod, "tweepy", dummy_mod, raising=False)

    ua = UnifiedAuth(mode="tweepy", api_key="K", api_secret="S", access_token="AT", access_secret="AS")
    client = ua.get_tweepy_client()
    assert isinstance(client, DummyClient)
    # cached
    assert ua.get_tweepy_client() is client


def test_authorize_oauth2_wrong_mode():
    ua = UnifiedAuth(mode="tweepy")
    with pytest.raises(RuntimeError):
        ua.authorize_oauth2(["tweet.read"])  # type: ignore[arg-type]


def test_refresh_oauth2_token_wrong_mode():
    ua = UnifiedAuth(mode="tweepy")
    with pytest.raises(RuntimeError):
        ua.refresh_oauth2_token()


def test_get_oauth2_access_token_wrong_mode():
    ua = UnifiedAuth(mode="tweepy")
    with pytest.raises(RuntimeError):
        ua.get_oauth2_access_token()


def test_get_me_user_id_tweepy_path(monkeypatch):
    # Provide dummy tweepy client that returns object with .data.id
    class DummyData:
        id = 999

    class DummyClient:
        def get_me(self, user_fields=None):  # noqa: D401
            return types.SimpleNamespace(data=DummyData())

    monkeypatch.setattr(auth_mod, "tweepy", types.SimpleNamespace(Client=DummyClient), raising=False)
    ua = UnifiedAuth(mode="tweepy", api_key="K", api_secret="S", access_token="AT", access_secret="AS")
    ua._tweepy_client = DummyClient()  # shortcut
    uid = ua.get_me_user_id()
    assert uid == "999"

