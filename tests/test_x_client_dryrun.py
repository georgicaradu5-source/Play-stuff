import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from auth import UnifiedAuth  # noqa: E402
from x_client import XClient  # noqa: E402


class DummyAuth(UnifiedAuth):
    def __init__(self, mode: str = "oauth2"):
        super().__init__(mode="oauth2", client_id="cid")
        # Pretend token is already present
        self.oauth2_access_token = "token"
        self.access_token = "token"


def test_dry_run_endpoints_return_sane_values():
    client = XClient(DummyAuth(), dry_run=True)

    me = client.get_me()
    assert me["data"]["id"] == "dummy_user_id"

    user = client.get_user_by_username("bob")
    assert user["data"]["username"] == "bob"

    tweet = client.get_tweet("123")
    assert tweet["data"]["id"] == "123"

    ok = client.delete_post("123")
    assert ok is True

    results = client.search_recent("hello world")
    assert results == []
