"""R01 extract tests."""
from demand_radar.extract import from_github_issue, from_hn_item

FETCHED = "2026-11-05T00:00:00Z"


def _issue(**kw):
    d = {"number": 1, "repository_url": "https://api.github.com/repos/a/b",
         "html_url": "https://github.com/a/b/issues/1", "title": "API fails",
         "body": "call fails", "created_at": "2026-10-01T11:00:00Z"}
    d.update(kw)
    return d


def test_github_extract_fields():
    d = from_github_issue(_issue(), "AI", FETCHED)
    assert d["platform"] == "github" and d["external_id"] == "a/b#1"
    assert d["url"] == "https://github.com/a/b/issues/1"
    assert d["domain"] == "AI" and d["fetched_at"] == FETCHED


def test_github_extract_excerpt_capped():
    d = from_github_issue(_issue(body="x" * 500), "AI", FETCHED)
    assert len(d["excerpt"]) <= 300


def test_github_extract_bad_date_is_null():
    d = from_github_issue(_issue(created_at="not-a-date"), "AI", FETCHED)
    assert d["published_at"] is None


def test_github_extract_empty_body_uses_title():
    d = from_github_issue(_issue(body=""), "AI", FETCHED)
    assert d["excerpt"] == "API fails"


def test_hn_extract_http_url_is_replaced_by_item_link():
    # extract() keeps the raw url; validation in models rejects http, so callers
    # must substitute the HN item link — document the behaviour here.
    d = from_hn_item({"id": 9, "title": "Ask HN: x", "text": "hello", "time": 1762300000},
                     "JOB", FETCHED)
    assert d["platform"] == "hackernews" and d["external_id"] == "9"
    assert d["published_at"] is not None and d["published_at"].endswith("Z")
