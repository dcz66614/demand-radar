"""R01 CLI tests. The score/export/stage tests FAIL on the old code:
old `score` printed a message and wrote no ranking.csv; old `report --stage`
accepted any string; old `export` included REJECTED rows."""
import csv

import pytest

from demand_radar import db as dbmod
from demand_radar.__main__ import main, run_score
from demand_radar.models import SourceItem

BASE = {
    "platform": "github", "external_id": "a/b#1",
    "url": "https://github.com/a/b/issues/1", "title": "API crashes",
    "excerpt": "the API call fails with a crash", "published_at": "2026-10-01T11:00:00Z",
    "fetched_at": "2026-11-05T00:00:00Z", "domain": "AI", "source_type": "firsthand_issue",
}


def _seed(tmp_path, monkeypatch):
    import demand_radar.__main__ as cli
    dbp = tmp_path / "t.sqlite"
    dbmod.init_db(dbp)
    monkeypatch.setattr(cli, "DB", dbp)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    with dbmod.connect(dbp) as conn:
        item = SourceItem.model_validate(BASE)
        dbmod.upsert_source_item(conn, item)
        # Evidence only counts when the source is VERIFIED (R02 verdicts).
        conn.execute("UPDATE source_items SET status='VERIFIED'")
        conn.execute(
            "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done, blocker, status, created_at, updated_at) "
            "VALUES ('p1','AI','user','drive an API reliably','API call fails', 'VERIFIED','2026-11-05T00:00:00Z','2026-11-05T00:00:00Z')")
        conn.execute(
            "INSERT INTO evidence_links (pain_id, source_id, is_firsthand, independence_group, evidence_note) "
            "VALUES ('p1', ?, 1, 'a/b', 'x')", (item.source_id,))
        conn.commit()
    return dbp


def test_score_writes_ranking(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    assert main(["score"]) == 0
    ranking = tmp_path / "reports" / "ranking.csv"
    assert ranking.exists()
    rows = list(csv.DictReader(ranking.read_text().splitlines()))
    assert len(rows) == 1 and rows[0]["pain_id"] == "p1"
    assert rows[0]["independent_evidence_count"] == "1"
    assert rows[0]["total"] == "30"  # R2-04: E10 + S20 + F0 + G0 + L0, 1 indep group
    # (was 50 under the defective F15+L5; F/L now need evidence, none exists)


def test_score_is_deterministic(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    assert main(["score"]) == 0
    first = (tmp_path / "reports" / "ranking.csv").read_bytes()
    assert main(["score"]) == 0
    assert (tmp_path / "reports" / "ranking.csv").read_bytes() == first


def test_score_unknown_g_when_no_competitor_checks(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    assert main(["score"]) == 0
    rows = list(csv.DictReader((tmp_path / "reports" / "ranking.csv").read_text().splitlines()))
    assert "UNKNOWN" in rows[0]["score_reason"] and "G=0" in rows[0]["score_reason"]


def test_report_unknown_stage_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        main(["report", "--stage", "bogus"])
    assert exc.value.code == 2


def test_report_known_stage_ok(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    assert main(["report", "--stage", "final"]) == 0


def test_export_excludes_rejected_by_default(tmp_path, monkeypatch):
    dbp = _seed(tmp_path, monkeypatch)
    with dbmod.connect(dbp) as conn:
        conn.execute("UPDATE source_items SET status='REJECTED'")
        conn.commit()
    assert main(["export", "--format", "csv"]) == 0
    rows = list(csv.DictReader((tmp_path / "data" / "exports" / "source_items.csv").read_text().splitlines()))
    assert rows == []
    assert main(["export", "--format", "csv", "--all"]) == 0
    rows = list(csv.DictReader((tmp_path / "data" / "exports" / "source_items.csv").read_text().splitlines()))
    assert len(rows) == 1


def test_score_missing_db_returns_2(tmp_path, monkeypatch):
    import demand_radar.__main__ as cli
    monkeypatch.setattr(cli, "DB", tmp_path / "nope.sqlite")
    assert run_score(db_path=tmp_path / "nope.sqlite", root=tmp_path) == 2
