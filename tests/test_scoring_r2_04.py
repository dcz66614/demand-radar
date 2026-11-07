"""R2-04 evidence-bound scoring tests (review P1-01; brief §R2-04).

Pins the new rule:
- a placeholder workaround ('see linked issues') or NULL earns F=0;
  only a DOCUMENTED workaround earns F=15; a paid-keyword mention alone
  earns nothing;
- L is 0 without documented transfer/reuse evidence (none exists);
- an UNKNOWN competitor trail blocks G (0) and the gate; 2 real checks
  give G=10;
- the 70 gate is NOT lowered;
- E comes from DIRECT_SAME_PAIN orgs for R2-03-assessed pains;
- the old-score diff (reports/rework2/score_diff.csv) is reproducible
  from the live DB.

Three older tests were updated for this rule change, with reasons
recorded in the test itself (tests/test_independence.py::test_cap59...,
tests/test_independence.py::test_migration..., tests/test_cli.py::
test_score_writes_ranking): they asserted the defective F=15/L=5 values.
"""
import csv
from pathlib import Path

from demand_radar import db as dbmod
from demand_radar.evidence_assessment import (
    ADJACENT,
    DIRECT,
    upsert_assessment,
)
from demand_radar.score import score_components
from demand_radar.selection import GATE_MIN_SCORE, gate_check

ROOT = Path(__file__).resolve().parents[1]

CANDIDATES = {
    "0b7adcf63ec0f2075fab": 30,
    "4bb734fac7245033d327": 30,
    "6513d051954cbe1b5027": 45,
    "cd021eac3c93ed0d2de1": 35,
    "e3091fb34139fdf57dbd": 35,
}


def _db(tmp_path):
    dbp = tmp_path / "t.sqlite"
    dbmod.init_db(dbp)
    return dbp


def _source(conn, sid, ext, url, author_hash):
    conn.execute(
        "INSERT INTO source_items (source_id, platform, external_id, url, canonical_url,"
        " author_key, title, excerpt, published_at, fetched_at, content_hash,"
        " source_type, domain, status, author_hash, issue_state)"
        " VALUES (?, 'github', ?, ?, ?, NULL, ?, ?, '2026-10-01T00:00:00Z',"
        " '2026-11-05T00:00:00Z', 'h', 'firsthand_issue', 'AI', 'VERIFIED', ?, 'open')",
        (sid, ext, url, url, f"issue {sid}", f"excerpt {sid}", author_hash),
    )


def _pain(conn, pid, job="drive an API reliably", blocker="API call fails",
          workaround=None, workaround_status=None):
    conn.execute(
        "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done, blocker,"
        " current_workaround, workaround_status, status, created_at, updated_at)"
        " VALUES (?, 'AI', 'user', ?, ?, ?, ?, 'VERIFIED',"
        " '2026-11-05T00:00:00Z', '2026-11-05T00:00:00Z')",
        (pid, job, blocker, workaround, workaround_status),
    )


def _link(conn, pid, sid, group):
    conn.execute(
        "INSERT INTO evidence_links (pain_id, source_id, is_firsthand,"
        " independence_group, evidence_note) VALUES (?, ?, 1, ?, 'x')", (pid, sid, group),
    )


def _check(conn, pid, product, gaps="gap"):
    conn.execute(
        "INSERT INTO competitor_checks (check_id, pain_id, product, checked_url,"
        " does_solve, gaps, checked_at) VALUES (?, ?, ?, ?, 0, ?, '2026-11-06')",
        (f"cc-{pid}-{product}", pid, product, f"https://example.com/{product}", gaps),
    )


def _two_org_pain(conn, pid="p1"):
    """A pain with 2 orgs / 2 authors, no competitor checks yet."""
    _pain(conn, pid)
    for i, (repo, author) in enumerate((("acme/a", "auth-A"), ("acme/b", "auth-B"))):
        sid = f"{pid}-s{i+1}"
        _source(conn, sid, f"{repo}#{pid}-{i}", f"https://github.com/{repo}/issues/{pid}-{i}", author)
        _link(conn, pid, sid, repo)
    conn.commit()


def test_placeholder_workaround_yields_no_f_points(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1", workaround="see linked issues")
    _two_org_pain(conn, "p2")
    conn.execute("UPDATE pain_points SET current_workaround='see linked issues' WHERE pain_id='p2'")
    conn.commit()
    comp = score_components(conn, "p2", "drive an API reliably", "API call fails")
    assert comp["f"] == 0
    assert "placeholder" in comp["reason"] and "F=0" in comp["reason"]


def test_null_workaround_yields_no_f_points(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _two_org_pain(conn, "p1")
    comp = score_components(conn, "p1", "drive an API reliably", "API call fails")
    assert comp["f"] == 0
    assert "no workaround recorded" in comp["reason"]


def test_documented_workaround_yields_f_points(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _two_org_pain(conn, "p1")
    conn.execute(
        "UPDATE pain_points SET current_workaround='restart the kernel, then re-import',"
        " workaround_status='DOCUMENTED' WHERE pain_id='p1'"
    )
    conn.commit()
    comp = score_components(conn, "p1", "drive an API reliably", "API call fails")
    assert comp["f"] == 15
    assert "documented workaround" in comp["reason"]


def test_paid_mention_alone_yields_no_f_points(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _two_org_pain(conn, "p1")
    comp = score_components(
        conn, "p1", "drive an API reliably",
        "API call fails behind a paid subscription with a rate limit")
    assert comp["f"] == 0
    assert "not feasibility evidence" in comp["reason"]


def test_unproven_l_yields_no_points(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _two_org_pain(conn, "p1")
    _check(conn, "p1", "alt-one")
    _check(conn, "p1", "alt-two")
    comp = score_components(conn, "p1", "drive an API reliably", "API call fails")
    assert comp["l"] == 0
    assert "no transfer/reuse evidence" in comp["reason"]
    assert comp["g"] == 10  # 2 real checks, 0 solves, 0 UNKNOWN


def test_unknown_competitor_check_blocks_g_and_gate(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _two_org_pain(conn, "p1")
    _check(conn, "p1", "alt-one")
    _check(conn, "p1", "alt-two", gaps="UNKNOWN: no alternative found")
    conn.execute("UPDATE pain_points SET score=70 WHERE pain_id='p1'")
    conn.commit()
    comp = score_components(conn, "p1", "drive an API reliably", "API call fails")
    assert comp["g"] == 0
    assert "UNKNOWN" in comp["reason"]
    assert comp["n_unknown_checks"] == 1 and comp["n_real_checks"] == 1
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "UNKNOWN" in r["failure_reason"]


def test_gate_still_70(tmp_path):
    assert GATE_MIN_SCORE == 70
    conn = dbmod.connect(_db(tmp_path))
    _two_org_pain(conn, "p1")
    _check(conn, "p1", "alt-one")
    _check(conn, "p1", "alt-two")
    conn.execute("UPDATE pain_points SET score=69 WHERE pain_id='p1'")
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "score 69 < 70" in r["failure_reason"]


def test_direct_only_e_for_assessed_pain(tmp_path):
    """3 raw orgs but only 1 DIRECT: E comes from the 1 DIRECT org."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1", job="process signals", blocker="signal functions crash")
    urls = []
    for i, (repo, author) in enumerate(
            (("acme/a", "auth-A"), ("acme/b", "auth-B"), ("acme/c", "auth-C"))):
        sid = f"s{i+1}"
        url = f"https://github.com/{repo}/issues/{i}"
        urls.append(url)
        _source(conn, sid, f"{repo}#{i}", url, author)
        _link(conn, "p1", sid, repo)
    conn.commit()
    upsert_assessment(conn, "p1", urls[0], DIRECT, "reports the signature problem", "2026-11-06")
    upsert_assessment(conn, "p1", urls[1], ADJACENT, "same workflow, different operation", "2026-11-06")
    upsert_assessment(conn, "p1", urls[2], ADJACENT, "same workflow, different operation", "2026-11-06")
    conn.commit()
    comp = score_components(conn, "p1", "process signals", "signal functions crash")
    assert comp["assessed"] is True
    assert comp["n_direct"] == 1 and comp["n_orgs"] == 1 and comp["n_authors"] == 1
    assert comp["e"] == 10  # 1 DIRECT org, not 3 raw orgs (which would be E=20)
    assert "DIRECT" in comp["reason"]
    r = gate_check(conn, "p1")
    assert r["n_orgs"] == 1 and r["n_authors"] == 1
    assert r["qualified"] is False
    assert "only 1 independent org" in r["failure_reason"]


def test_real_db_five_candidates_new_scores():
    """The 5 R05 candidates under the R2-04 rule, recomputed live from the DB."""
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        for pid, expected_total in CANDIDATES.items():
            row = conn.execute(
                "SELECT job_to_be_done, blocker FROM pain_points WHERE pain_id = ?",
                (pid,),
            ).fetchone()
            comp = score_components(conn, pid, row[0], row[1])
            assert comp["f"] == 0 and comp["l"] == 0, pid
            assert comp["total"] == expected_total, (pid, comp)
    assert CANDIDATES == {
        "0b7adcf63ec0f2075fab": 30,  # E10 (1 DIRECT org) + S20 + F0 + G0 + L0
        "4bb734fac7245033d327": 30,  # E10 (1 DIRECT org) + S20 + F0 + G0 + L0
        "6513d051954cbe1b5027": 45,  # E15 (2 DIRECT orgs) + S20 + F0 + G10 + L0
        "cd021eac3c93ed0d2de1": 35,  # E15 + S20 + F0 + G0 + L0
        "e3091fb34139fdf57dbd": 35,  # E15 + S20 + F0 + G0 + L0
    }


def test_score_diff_csv_reproducible():
    """score_diff.csv old scores are the R05 70s; new scores match a live
    recomputation from the DB (same rule, same data)."""
    path = ROOT / "reports" / "rework2" / "score_diff.csv"
    rows = {r["pain_id"]: r for r in csv.DictReader(path.read_text().splitlines())}
    assert set(rows) == set(CANDIDATES)
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        for pid, row in rows.items():
            assert int(row["old_score"]) == 70, pid
            assert (row["old_e"], row["old_s"], row["old_f"], row["old_g"], row["old_l"]) == (
                "20", "20", "15", "10", "5"), pid
            assert int(row["new_score"]) == CANDIDATES[pid], pid
            db_row = conn.execute(
                "SELECT job_to_be_done, blocker FROM pain_points WHERE pain_id = ?",
                (pid,),
            ).fetchone()
            comp = score_components(conn, pid, db_row[0], db_row[1])
            assert int(row["new_score"]) == comp["total"], pid
            assert int(row["new_e"]) == comp["e"], pid
            assert int(row["direct_count"]) == comp["n_direct"], pid
            assert int(row["direct_orgs"]) == comp["n_orgs"], pid
            assert int(row["direct_authors"]) == comp["n_authors"], pid
            assert int(row["real_competitor_checks"]) == comp["n_real_checks"], pid
            assert int(row["unknown_competitor_checks"]) == comp["n_unknown_checks"], pid
