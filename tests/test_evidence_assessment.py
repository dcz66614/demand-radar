"""R2-03 tests: only DIRECT_SAME_PAIN counts toward independence.

Rules under test (from the R2-03 brief / review P0-02):
- only DIRECT_SAME_PAIN links enter an independence count;
- a DUPLICATE of the same report does not increase the count;
- cross-org counting requires the SAME problem_signature, not the same
  broad domain (an ADJACENT/OUT_OF_SCOPE link from a second org adds
  no org, and a DIRECT link under a different signature belongs to that
  signature's theme, not this one).
"""
import csv
import sqlite3
import tempfile
from pathlib import Path

import pytest

from demand_radar import db as dbmod
from demand_radar.evidence_assessment import (
    ADJACENT,
    DIRECT,
    DUPLICATE,
    OUT_OF_SCOPE,
    SIGNATURE_FIELDS,
    assessment_counts,
    direct_only_counts,
    upsert_assessment,
    upsert_problem_signature,
)

ROOT = Path(__file__).resolve().parents[1]
AT = "2026-11-06T00:30:00Z"

SIG_A = {f: f"a-{f}" for f in SIGNATURE_FIELDS}
SIG_B = {f: f"b-{f}" for f in SIGNATURE_FIELDS}

# Expected DIRECT-only recount of the real assessment (r2_03.md §3).
# pain_id -> (n_direct, n_orgs, n_authors, survives >=2 orgs and >=2 authors)
EXPECTED = {
    "0b7adcf63ec0f2075fab": (1, 1, 1, False),
    "4bb734fac7245033d327": (12, 1, 8, False),
    "6513d051954cbe1b5027": (2, 2, 2, True),
    "cd021eac3c93ed0d2de1": (10, 2, 9, True),
    "e3091fb34139fdf57dbd": (13, 2, 11, True),
}


def _seed(conn: sqlite3.Connection) -> None:
    """Minimal fixture: two pains (different signatures), three orgs."""
    for pain_id, sig in (("pain-a", SIG_A), ("pain-b", SIG_B)):
        conn.execute(
            "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done,"
            " blocker, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (pain_id, "AI", "user", "job", "blocker", AT, AT),
        )
        upsert_problem_signature(conn, pain_id, sig, AT)
    sources = [
        ("s1", "https://github.com/org-a/repo/issues/1", "org-a/repo", "auth-1"),
        ("s2", "https://github.com/org-a/repo/issues/2", "org-a/repo", "auth-1"),
        ("s3", "https://github.com/org-b/repo/issues/1", "org-b/repo", "auth-2"),
        ("s4", "https://github.com/org-c/repo/issues/1", "org-c/repo", "auth-3"),
    ]
    for sid, url, _grp, author in sources:
        conn.execute(
            "INSERT INTO source_items (source_id, platform, external_id, url,"
            " canonical_url, title, excerpt, fetched_at, content_hash,"
            " source_type, domain, author_hash)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, "github", sid, url, url, "t", "excerpt", AT, "h",
             "issue", "AI", author),
        )
    # pain-a: s1 DIRECT (org-a), s2 DUPLICATE of s1 (same author),
    # s3 ADJACENT (org-b), s4 OUT_OF_SCOPE (org-c).
    for sid, grp in (("s1", "org-a/repo"), ("s2", "org-a/repo"),
                     ("s3", "org-b/repo"), ("s4", "org-c/repo")):
        conn.execute(
            "INSERT INTO evidence_links (pain_id, source_id,"
            " independence_group, evidence_note) VALUES (?,?,?,?)",
            ("pain-a", sid, grp, "note"),
        )
    # pain-b (different signature): s3 DIRECT (org-b) — must not leak
    # into pain-a's count even though it is the same source/org.
    conn.execute(
        "INSERT INTO evidence_links (pain_id, source_id,"
        " independence_group, evidence_note) VALUES (?,?,?,?)",
        ("pain-b", "s3", "org-b/repo", "note"),
    )
    conn.commit()


@pytest.fixture()
def conn():
    dbp = Path(tempfile.mkdtemp()) / "t.sqlite"
    dbmod.init_db(dbp)
    with dbmod.connect(dbp) as c:
        _seed(c)
        yield c


def test_only_direct_counts_toward_independence(conn):
    upsert_assessment(conn, "pain-a", "https://github.com/org-a/repo/issues/1",
                      DIRECT, "same problem", AT)
    upsert_assessment(conn, "pain-a", "https://github.com/org-a/repo/issues/2",
                      DUPLICATE, "same report reposted", AT)
    upsert_assessment(conn, "pain-a", "https://github.com/org-b/repo/issues/1",
                      ADJACENT, "same workflow, different operation", AT)
    upsert_assessment(conn, "pain-a", "https://github.com/org-c/repo/issues/1",
                      OUT_OF_SCOPE, "different problem entirely", AT)
    conn.commit()
    counts = direct_only_counts(conn, "pain-a")
    assert counts["n_direct"] == 1
    assert counts["n_orgs"] == 1
    assert counts["orgs"] == ["org-a/repo"]
    assert counts["n_authors"] == 1
    assert assessment_counts(conn, "pain-a") == {
        "ADJACENT_CONTEXT": 1, "DIRECT_SAME_PAIN": 1, "DUPLICATE": 1,
        "OUT_OF_SCOPE": 1, "UNKNOWN": 0,
    }


def test_duplicate_of_same_report_does_not_increase_count(conn):
    # s1 and s2 are the same author/report; s2 marked DUPLICATE.
    upsert_assessment(conn, "pain-a", "https://github.com/org-a/repo/issues/1",
                      DIRECT, "same problem", AT)
    upsert_assessment(conn, "pain-a", "https://github.com/org-a/repo/issues/2",
                      DUPLICATE, "same report, second filing", AT)
    conn.commit()
    counts = direct_only_counts(conn, "pain-a")
    assert counts["n_direct"] == 1
    assert counts["n_authors"] == 1  # same author either way


def test_cross_org_requires_same_problem_signature(conn):
    # org-b has a DIRECT link, but under pain-b's DIFFERENT signature.
    upsert_assessment(conn, "pain-a", "https://github.com/org-a/repo/issues/1",
                      DIRECT, "same problem", AT)
    upsert_assessment(conn, "pain-b", "https://github.com/org-b/repo/issues/1",
                      DIRECT, "same problem under signature B", AT)
    # org-b is ADJACENT under pain-a: it must not add an org to pain-a.
    upsert_assessment(conn, "pain-a", "https://github.com/org-b/repo/issues/1",
                      ADJACENT, "different operation", AT)
    conn.commit()
    counts_a = direct_only_counts(conn, "pain-a")
    counts_b = direct_only_counts(conn, "pain-b")
    assert counts_a["n_orgs"] == 1 and counts_a["orgs"] == ["org-a/repo"]
    assert counts_b["n_orgs"] == 1 and counts_b["orgs"] == ["org-b/repo"]
    # The same source counted under two signatures stays separate.
    assert counts_a["n_direct"] == 1 and counts_b["n_direct"] == 1


def test_same_author_across_two_direct_links_counts_once(conn):
    # s1 and s2 share author auth-1; if both were DIRECT they are still
    # one author. (Here s2 is DIRECT too, to test the author rule.)
    upsert_assessment(conn, "pain-a", "https://github.com/org-a/repo/issues/1",
                      DIRECT, "same problem", AT)
    upsert_assessment(conn, "pain-a", "https://github.com/org-a/repo/issues/2",
                      DIRECT, "same problem, second report, same author", AT)
    conn.commit()
    counts = direct_only_counts(conn, "pain-a")
    assert counts["n_direct"] == 2
    assert counts["n_authors"] == 1


def test_assessment_validation(conn):
    with pytest.raises(ValueError):
        upsert_assessment(conn, "pain-a", "https://example.invalid/1",
                          "MAYBE", "not a classification", AT)
    with pytest.raises(ValueError):
        upsert_assessment(conn, "pain-a", "https://example.invalid/1",
                          DIRECT, "   ", AT)
    with pytest.raises(ValueError):
        upsert_problem_signature(conn, "pain-a", {"actor": "x"}, AT)


def test_migration_is_idempotent():
    dbp = Path(tempfile.mkdtemp()) / "t.sqlite"
    dbmod.init_db(dbp)
    dbmod.init_db(dbp)  # second run must not raise or duplicate
    with dbmod.connect(dbp) as c:
        tables = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "evidence_assessment" in tables
    assert "problem_signatures" in tables


def test_real_assessment_csv_agrees_with_db_and_expected_counts():
    csv_path = ROOT / "reports" / "rework2" / "evidence_assessment.csv"
    rows = list(csv.DictReader(csv_path.read_text().splitlines()))
    assert len(rows) == 76
    assert {r["classification"] for r in rows} <= {
        "DIRECT_SAME_PAIN", "ADJACENT_CONTEXT", "DUPLICATE",
        "OUT_OF_SCOPE", "UNKNOWN",
    }
    assert all(r["reason"].strip() for r in rows)
    assert sum(1 for r in rows if r["classification"] == "UNKNOWN") == 0
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as c:
        # Every evidence link of the 5 themes assessed exactly once.
        for pain_id, (n_direct, n_orgs, n_authors, survives) in EXPECTED.items():
            n_links = c.execute(
                "SELECT COUNT(*) FROM evidence_links WHERE pain_id = ?",
                (pain_id,),
            ).fetchone()[0]
            n_assessed = c.execute(
                "SELECT COUNT(*) FROM evidence_assessment WHERE pain_id = ?",
                (pain_id,),
            ).fetchone()[0]
            assert n_links == n_assessed, pain_id
            counts = direct_only_counts(c, pain_id)
            assert counts["n_direct"] == n_direct, pain_id
            assert counts["n_orgs"] == n_orgs, pain_id
            assert counts["n_authors"] == n_authors, pain_id
            assert (n_orgs >= 2 and n_authors >= 2) == survives, pain_id
        # CSV rows match the DB rows exactly.
        db_rows = c.execute(
            "SELECT pain_id, source_url, classification FROM evidence_assessment"
        ).fetchall()
        csv_keys = {(r["pain_id"], r["source_url"], r["classification"])
                    for r in rows}
        assert set(db_rows) == csv_keys
