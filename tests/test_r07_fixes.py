"""R07 fix tests: prd_cards and evidence review_status must agree with the
gate verdicts and the R02 source verdicts. These FAIL on the pre-fix DB
(stale DRAFT/TBD cards, 13 VERIFIED links to REJECTED sources)."""
import csv
from pathlib import Path

from demand_radar import db as dbmod

ROOT = Path(__file__).resolve().parents[1]


def test_prd_cards_agree_with_gate():
    """R2-06 update: the gate is now the R2-04 evidence-bound gate
    (reports/rework2/qualifying_prds_r2_04.csv, 0 rows), not the R05 file
    (reports/rework1/qualifying_prds.csv, 5 rows). The R05 file is kept
    as history; the cards must agree with the CURRENT gate, so all 17
    are SUPERSEDED with md_path under reports/prds/superseded/.
    FAILS on the pre-R2-06 DB (5 rows still QUALIFIED)."""
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        qual = {r["pain_id"] for r in csv.DictReader(
            (ROOT / "reports/rework2/qualifying_prds_r2_04.csv")
            .read_text().splitlines())}
        assert qual == set()
        cards = conn.execute(
            "SELECT pain_id, status, md_path FROM prd_cards").fetchall()
        assert len(cards) == 17
        for pain_id, status, md_path in cards:
            assert (ROOT / md_path).exists(), f"prd_cards md_path missing: {md_path}"
            assert status == "SUPERSEDED"
            assert md_path.startswith("reports/prds/superseded/")


def test_evidence_review_status_agrees_with_source():
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        stale = conn.execute(
            "SELECT COUNT(*) FROM evidence_links e JOIN source_items s "
            "ON s.source_id=e.source_id WHERE "
            "(s.status='REJECTED' AND e.review_status!='REJECTED') OR "
            "(s.status='VERIFIED' AND e.review_status!='VERIFIED')").fetchone()[0]
        assert stale == 0
        counts = dict(conn.execute(
            "SELECT review_status, COUNT(*) FROM evidence_links "
            "GROUP BY review_status").fetchall())
        assert counts == {"REJECTED": 13, "VERIFIED": 356}


def test_run_events_populated():
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        n = conn.execute("SELECT COUNT(*) FROM run_events").fetchone()[0]
        assert n > 0


def test_export_columns_contain_no_author_identity():
    """T12 automation branch: exports must not leak author_key/author_hash."""
    import json as _json

    from demand_radar.__main__ import main

    assert main(["export", "--format", "json"]) == 0  # regenerate, don't trust a stale file
    rows = _json.loads((ROOT / "data" / "exports" / "source_items.json").read_text())
    assert rows, "export is empty"
    for row in rows:
        assert "author_key" not in row and "author_hash" not in row


def test_cross_platform_same_author_counts_once():
    """T06 automation branch: the same author reposting on GitHub and HN
    counts as one person (count_distinct_authors), even across platforms."""
    import tempfile

    from demand_radar.score import count_distinct_authors, count_independent_evidence

    dbp = Path(tempfile.mkdtemp()) / "t.sqlite"
    dbmod.init_db(dbp)
    with dbmod.connect(dbp) as conn:
        conn.execute(
            "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done, blocker,"
            " status, created_at, updated_at) VALUES ('p1','AI','user','j','b',"
            " 'VERIFIED','2026-11-05T00:00:00Z','2026-11-05T00:00:00Z')")
        for sid, platform, ext, group in (
                ("s1", "github", "acme/widgets#1", "acme/widgets"),
                ("s2", "hackernews", "99", "hn")):
            conn.execute(
                "INSERT INTO source_items (source_id, platform, external_id, url,"
                " canonical_url, title, excerpt, published_at, fetched_at, content_hash,"
                " source_type, domain, status, author_hash) VALUES (?, ?, ?, ?, ?, ?, ?,"
                " '2026-10-01T00:00:00Z', '2026-11-05T00:00:00Z', 'h', 'firsthand_issue',"
                " 'AI', 'VERIFIED', 'author-A')",
                (sid, platform, ext, f"https://example.com/{sid}",
                 f"https://example.com/{sid}", f"issue {sid}", f"excerpt {sid}"))
            conn.execute(
                "INSERT INTO evidence_links (pain_id, source_id, is_firsthand,"
                " independence_group, evidence_note) VALUES ('p1', ?, 1, ?, 'x')",
                (sid, group))
        conn.commit()
        assert count_distinct_authors(conn, "p1") == 1
        assert count_independent_evidence(conn, "p1") == 2  # 2 orgs, 1 person


def test_apps_make_no_network_calls():
    """T13 automation branch: the three Streamlit apps are pure-local
    (no requests/urllib/socket imports)."""
    import ast

    for app in (ROOT / "app" / "streamlit_app.py",
                ROOT / "mvps" / "r1_a" / "app.py",
                ROOT / "mvps" / "r1_b" / "app.py"):
        tree = ast.parse(app.read_text())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        assert not (mods & {"requests", "urllib", "socket", "http"}), f"{app}: {mods}"
