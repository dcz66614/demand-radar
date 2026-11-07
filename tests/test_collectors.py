import requests

from demand_radar.collectors.github_issues import fetch_issues


class FakeResp:
    def __init__(self, status=200, data=None, headers=None):
        self.status_code = status; self._data = data or []; self.headers = headers or {}
    def json(self): return self._data
    def raise_for_status(self):
        if self.status_code >= 400: raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, responses): self.responses = list(responses); self.calls = 0
    def get(self, *a, **k):
        self.calls += 1; return self.responses.pop(0)


def test_pr_excluded():
    data = [{"number": 1, "html_url": "https://github.com/a/b/issues/1"},
            {"number": 2, "html_url": "https://github.com/a/b/pull/2", "pull_request": {}}]
    items, _ = fetch_issues("a/b", session=FakeSession([FakeResp(200, data)]))
    assert len(items) == 1 and items[0]["number"] == 1


def test_empty_list():
    items, _ = fetch_issues("a/b", session=FakeSession([FakeResp(200, [])]))
    assert items == []


def test_429_retries_once(monkeypatch):
    monkeypatch.setattr("demand_radar.collectors.github_issues.time.sleep", lambda s: None)
    data = [{"number": 1}]
    s = FakeSession([FakeResp(429, [], {"Retry-After": "0"}), FakeResp(200, data, {"X-RateLimit-Remaining": "59"})])
    items, rate = fetch_issues("a/b", session=s)
    assert len(items) == 1 and rate["remaining"] == "59" and s.calls == 2
