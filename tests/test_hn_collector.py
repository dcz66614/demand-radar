"""R01 HN collector tests (mocked session). Old code built its own Session,
so it could not be tested without the network."""
from demand_radar.collectors.hackernews import fetch_items


class FakeResp:
    def __init__(self, data):
        self._data = data
    def json(self):
        return self._data


class FakeSession:
    def __init__(self, by_url):
        self.by_url = by_url
    def get(self, url, **k):
        return FakeResp(self.by_url[url])


def test_fetch_filters_by_keyword():
    ids_url = "https://hacker-news.firebaseio.com/v0/askstories.json"
    s = FakeSession({
        ids_url: [1, 2],
        "https://hacker-news.firebaseio.com/v0/item/1.json": {"id": 1, "title": "Ask HN: job search is broken", "text": "hiring"},
        "https://hacker-news.firebaseio.com/v0/item/2.json": {"id": 2, "title": "Ask HN: my cat", "text": "meow"},
    })
    out = fetch_items("askstories", limit=10, keywords=("job",), session=s)
    assert [i["id"] for i in out] == [1]


def test_fetch_skips_deleted_and_dead():
    ids_url = "https://hacker-news.firebaseio.com/v0/askstories.json"
    s = FakeSession({
        ids_url: [1, 2, 3],
        "https://hacker-news.firebaseio.com/v0/item/1.json": {"id": 1, "deleted": True, "title": "x"},
        "https://hacker-news.firebaseio.com/v0/item/2.json": {"id": 2, "dead": True, "title": "x"},
        "https://hacker-news.firebaseio.com/v0/item/3.json": {"id": 3, "title": "Ask HN: job tips"},
    })
    assert [i["id"] for i in fetch_items("askstories", limit=10, session=s)] == [3]


def test_fetch_empty_list():
    s = FakeSession({"https://hacker-news.firebaseio.com/v0/askstories.json": []})
    assert fetch_items("askstories", limit=10, session=s) == []
