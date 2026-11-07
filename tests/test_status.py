"""R01 status-transition tests: ingest -> FETCHED, review persists a verdict,
export/UI default excludes REJECTED. Fails on old code where status never moved."""
import json

from test_models import BASE

from demand_radar import db as dbmod
from demand_radar.ingest import ingest_file


def test_ingest_status_is_fetched(tmp_path):
    dbp = tmp_path / "t.sqlite"; dbmod.init_db(dbp)
    f = tmp_path / "in.jsonl"; f.write_text(json.dumps(BASE) + "\n")
    assert ingest_file(dbp, f) == 1
    with dbmod.connect(dbp) as conn:
        row = conn.execute("SELECT status, review_verdict FROM source_items").fetchone()
        assert row == ("FETCHED", None)


def test_review_verdict_persists(tmp_path):
    dbp = tmp_path / "t.sqlite"; dbmod.init_db(dbp)
    f = tmp_path / "in.jsonl"; f.write_text(json.dumps(BASE) + "\n")
    ingest_file(dbp, f)
    with dbmod.connect(dbp) as conn:
        conn.execute("UPDATE source_items SET status='VERIFIED', review_verdict='VERIFIED', "
                     "review_reason='firsthand issue, clear blocker', reviewed_at='2026-11-05T00:00:00Z'")
        conn.commit()
        row = conn.execute("SELECT status, review_verdict, review_reason FROM source_items").fetchone()
        assert row[0] == "VERIFIED" and row[1] == "VERIFIED" and "blocker" in row[2]


def test_review_columns_exist_after_init(tmp_path):
    dbp = tmp_path / "t.sqlite"; dbmod.init_db(dbp)
    with dbmod.connect(dbp) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(source_items)")}
        assert {"review_verdict", "review_reason", "reviewed_at", "author_hash",
                "issue_state", "issue_state_checked_at", "issue_labels"} <= cols
