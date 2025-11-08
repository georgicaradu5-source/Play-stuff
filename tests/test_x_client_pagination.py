
from src.x_client import XClient


def test_search_recent_pagination(monkeypatch):
    """Test that search_recent paginates and aggregates results up to max_results."""
    class DummyAuth:
        mode = "tweepy"
        def get_tweepy_client(self):
            class DummyClient:
                def __init__(self):
                    self.calls = 0
                def search_recent_tweets(self, query, max_results, expansions, tweet_fields, user_fields, next_token=None):
                    self.calls += 1
                    # Simulate two pages: first returns 3 tweets, second returns 2 tweets, then done
                    if self.calls == 1:
                        class DummyResp1:
                            data = [type("T", (), {"id": i, "author_id": f"a{i}", "public_metrics": {"retweet_count": i}}) for i in range(3)]
                            includes = type("Inc", (), {"get": lambda self, k, default=None: []})()
                            meta = type("Meta", (), {"next_token": "token2"})()
                        return DummyResp1()
                    elif self.calls == 2:
                        class DummyResp2:
                            data = [type("T", (), {"id": i+3, "author_id": f"a{i+3}", "public_metrics": {"retweet_count": i+3}}) for i in range(2)]
                            includes = type("Inc", (), {"get": lambda self, k, default=None: []})()
                            meta = type("Meta", (), {"next_token": None})()
                        return DummyResp2()
                    else:
                        class DummyResp3:
                            data = []
                            includes = type("Inc", (), {"get": lambda self, k, default=None: []})()
                            meta = type("Meta", (), {"next_token": None})()
                        return DummyResp3()
            return DummyClient()

    client = XClient(DummyAuth(), dry_run=False)  # type: ignore[arg-type]
    results = client.search_recent("foo", max_results=5)
    # Should aggregate 3 from first page, 2 from second, stop at 5
    assert len(results) == 5
    assert all("id" in r and "author_id" in r for r in results)
    # IDs should be 0,1,2,3,4 (as str or int)
    ids = [str(r["id"]) for r in results]
    assert ids == ["0", "1", "2", "3", "4"]
