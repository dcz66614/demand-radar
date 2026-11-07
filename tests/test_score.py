from demand_radar.dedupe import suggest_merge
from demand_radar.normalize import canonical_url
from demand_radar.score import evidence_score, total_score


def test_score_max_100():
    assert total_score(30, 25, 20, 15, 10, 5) == (100, False)


def test_cap_59_single_source():
    assert total_score(30, 25, 20, 15, 10, 1) == (59, True)


def test_no_cap_two_sources():
    total, capped = total_score(15, 10, 15, 10, 10, 2)
    assert total == 60 and not capped


def test_evidence_map():
    assert (evidence_score(0), evidence_score(1), evidence_score(2), evidence_score(5)) == (0, 10, 15, 30)


def test_canonical_strips_tracking():
    assert canonical_url("https://github.com/a/b/issues/1?utm_source=x&foo=1") == "https://github.com/a/b/issues/1?foo=1"


def test_dedupe_suggests_only():
    assert suggest_merge("export records", "export fails", "export records", "export fails")
    assert not suggest_merge("export records", "export fails", "unrelated topic", "different blocker")
