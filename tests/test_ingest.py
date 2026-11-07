import json

from test_models import BASE

from demand_radar import db as dbmod
from demand_radar.ingest import ingest_file


def test_idempotent_ingest(tmp_path):
    dbp = tmp_path / "t.sqlite"; dbmod.init_db(dbp)
    f = tmp_path / "in.jsonl"
    f.write_text(json.dumps(BASE) + "\n" + json.dumps(BASE) + "\n")
    assert ingest_file(dbp, f) == 1
    assert ingest_file(dbp, f) == 0
    with dbmod.connect(dbp) as conn:
        assert dbmod.counts(conn)["source_items"] == 1


def test_init_creates_tables(tmp_path):
    dbp = tmp_path / "t.sqlite"; dbmod.init_db(dbp)
    with dbmod.connect(dbp) as conn:
        assert dbmod.counts(conn)["source_items"] == 0
