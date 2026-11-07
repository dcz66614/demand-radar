import pytest
from pydantic import ValidationError

from demand_radar.models import SourceItem

BASE = {
    "platform": "github", "external_id": "a/b#1",
    "url": "https://github.com/a/b/issues/1", "title": "x",
    "excerpt": "short excerpt", "published_at": "2026-10-01T11:00:00Z",
    "fetched_at": "2026-11-05T00:00:00Z", "domain": "AI", "source_type": "firsthand_issue",
}


def test_valid_item():
    assert SourceItem.model_validate(BASE).source_id


def test_http_url_rejected():
    with pytest.raises(ValidationError):
        SourceItem.model_validate({**BASE, "url": "http://example.com/x"})


def test_long_excerpt_rejected():
    with pytest.raises(ValidationError):
        SourceItem.model_validate({**BASE, "excerpt": "x" * 301})


def test_bad_domain_rejected():
    with pytest.raises(ValidationError):
        SourceItem.model_validate({**BASE, "domain": "XX"})


def test_missing_url_rejected():
    d = dict(BASE); del d["url"]
    with pytest.raises(ValidationError):
        SourceItem.model_validate(d)
