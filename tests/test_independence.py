"""R03 independence tests (audit P0-02).

Each test asserts a value the OLD counting logic (raw issue rows /
evidence_count used as "independent sources") would VIOLATE, so every test
fails on the old logic and passes on the fixed logic:
- old logic would count 3 same-author issues as 3; fixed counts 1.
- old logic would count 19 raw links for ai-agent-api as 19; fixed counts 3.
- old logic had no cross-org concept at all; a one-repo theme with 5
  distinct authors would look corroborated. Fixed: orgs == 1.
"""
import sqlite3

from demand_radar import db as dbmod
from demand_radar.score import (
    count_independent_evidence,
    count_raw_evidence,
    cross_org_corroborated,
    independent_evidence_count,
    independent_organisations,
    score_components,
)


def _db(tmp_path):
    dbp = tmp_path / "t.sqlite"
    dbmod.init_db(dbp)
    return dbp


def _source(conn, sid, platform="github", ext="x#1", url=None, author_hash=None,
            group_repo="acme/widgets"):
    conn.execute(
        "INSERT INTO source_items (source_id, platform, external_id, url, canonical_url,"
        " author_key, title, excerpt, published_at, fetched_at, content_hash,"
        " source_type, domain, status, author_hash)"
        " VALUES (?, ?, ?, ?, ?, NULL, ?, ?, '2026-10-01T00:00:00Z',"
        " '2026-11-05T00:00:00Z', 'h', 'firsthand_issue', 'AI', 'VERIFIED', ?)",
        (sid, platform, ext, url or f"https://github.com/{group_repo}/issues/{sid}",
         url or f"https://github.com/{group_repo}/issues/{sid}", f"issue {sid}",
         f"excerpt {sid}", author_hash),
    )


def _pain(conn, pid, job="drive an API reliably", blocker="API call fails"):
    conn.execute(
        "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done, blocker,"
        " status, created_at, updated_at) VALUES (?, 'AI', 'user', ?, ?, 'VERIFIED',"
        " '2026-11-05T00:00:00Z', '2026-11-05T00:00:00Z')", (pid, job, blocker),
    )


def _link(conn, pid, sid, group="acme/widgets"):
    conn.execute(
        "INSERT INTO evidence_links (pain_id, source_id, is_firsthand,"
        " independence_group, evidence_note) VALUES (?, ?, 1, ?, 'x')", (pid, sid, group),
    )


def test_three_issues_one_author_count_once(tmp_path):
    """Three issues from one author in one repo = 1 independent group."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    for i in (1, 2, 3):
        _source(conn, f"s{i}", ext=f"acme/widgets#{100 + i}", author_hash="author-A")
        _link(conn, "p1", f"s{i}")
    conn.commit()
    assert count_raw_evidence(conn, "p1") == 3  # raw rows still preserved
    assert count_independent_evidence(conn, "p1") == 1  # old logic: 3
    assert independent_evidence_count(conn, "p1") == 1


def test_two_reposts_of_one_issue_count_once(tmp_path):
    """Two reposts of the same issue (same author, same repo, same title) = 1."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    for i, ext in ((1, "acme/widgets#201"), (2, "acme/widgets#202")):
        _source(conn, f"s{i}", ext=ext, author_hash="author-A")
        _link(conn, "p1", f"s{i}")
    conn.commit()
    assert count_raw_evidence(conn, "p1") == 2
    assert count_independent_evidence(conn, "p1") == 1  # old logic: 2


def test_two_unrelated_issues_same_repo_not_same_demand(tmp_path):
    """Two unrelated issues in the same repo are NOT automatically one demand:
    each pain counts only its own links, and neither is cross-org corroborated."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "pA", job="export records", blocker="export fails on large files")
    _pain(conn, "pB", job="import records", blocker="import drops rows silently")
    _source(conn, "s1", ext="acme/widgets#301", author_hash="author-A")
    _source(conn, "s2", ext="acme/widgets#302", author_hash="author-B")
    _link(conn, "pA", "s1")
    _link(conn, "pB", "s2")
    conn.commit()
    assert count_independent_evidence(conn, "pA") == 1
    assert count_independent_evidence(conn, "pB") == 1
    # Same repo for both, but different pains stay distinct demands.
    assert independent_organisations(conn, "pA") == 1
    assert not cross_org_corroborated(conn, "pA")
    assert not cross_org_corroborated(conn, "pB")
    comp = score_components(conn, "pA", "export records", "export fails on large files")
    assert "NOT cross-org corroborated" in comp["reason"]


def test_one_repo_theme_not_corroborated_across_orgs(tmp_path):
    """Five distinct authors, one repo: 1 org group (audit method), 5 authors,
    0 cross-org corroboration. Author count must never masquerade as org
    corroboration — and must not inflate E either."""
    from demand_radar.score import count_distinct_authors

    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    for i in range(1, 6):
        _source(conn, f"s{i}", ext=f"acme/widgets#{400 + i}", author_hash=f"author-{i}")
        _link(conn, "p1", f"s{i}")
    conn.commit()
    assert count_independent_evidence(conn, "p1") == 1  # audit: org groups
    assert count_distinct_authors(conn, "p1") == 5
    assert independent_organisations(conn, "p1") == 1
    assert cross_org_corroborated(conn, "p1") is False


def test_same_author_two_repos_counts_twice_documented_rule(tmp_path):
    """Org-level rule: same author in two repos = 2 org groups (different
    project contexts). But the person-level figure is 1 author, so the R05
    gate (>= 2 distinct authors) must still block this from qualifying
    alone — org count is not person corroboration."""
    from demand_radar.score import count_distinct_authors

    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    _source(conn, "s1", ext="acme/widgets#501", author_hash="author-A")
    _link(conn, "p1", "s1", group="acme/widgets")
    _source(conn, "s2", ext="other/gadgets#9", author_hash="author-A")
    _link(conn, "p1", "s2", group="other/gadgets")
    _source(conn, "s3", ext="other/gadgets#10", author_hash="author-A")
    _link(conn, "p1", "s3", group="other/gadgets")
    conn.commit()
    assert count_independent_evidence(conn, "p1") == 2
    assert count_distinct_authors(conn, "p1") == 1
    assert independent_organisations(conn, "p1") == 2
    assert cross_org_corroborated(conn, "p1") is True


def test_ai_agent_api_19_raw_links_are_3_groups(tmp_path):
    """Audit P0-02 fixture: 19 raw links, 3 existing groups (AgentLab,
    LangChain, HN). Old logic scored E=30 on 19; fixed E=20 on 3."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "ai", job="drive an AI agent / API reliably",
          blocker="API calls fail, return wrong results, or silently substitute defaults")
    groups = [("ServiceNow/AgentLab", 11), ("langchain-ai/langchain", 7), ("hn", 1)]
    n = 0
    for group, k in groups:
        for _ in range(k):
            n += 1
            _source(conn, f"s{n}", ext=f"{group}#{n}", author_hash=None)
            _link(conn, "ai", f"s{n}", group=group)
    conn.commit()
    assert count_raw_evidence(conn, "ai") == 19
    assert count_independent_evidence(conn, "ai") == 3
    assert independent_organisations(conn, "ai") == 3
    comp = score_components(conn, "ai", "drive an AI agent / API reliably",
                            "API calls fail, return wrong results, or silently substitute defaults")
    assert comp["n_independent"] == 3 and comp["e"] == 20 and comp["n_raw"] == 19
    assert "cross-org corroborated" in comp["reason"]


def test_fin_data_9_raw_links_are_2_groups(tmp_path):
    """Audit P0-02 fixture: 9 raw links, 2 groups (EdgarTools, OpenBB)."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "fin", job="read SEC filings accurately",
          blocker="filing data is misclassified, mislabelled or dropped in extraction")
    n = 0
    for group, k in (("dgunning/edgartools", 5), ("openbq-org/OpenBB", 4)):
        for _ in range(k):
            n += 1
            _source(conn, f"s{n}", ext=f"{group}#{n}")
            _link(conn, "fin", f"s{n}", group=group)
    conn.commit()
    assert count_raw_evidence(conn, "fin") == 9
    assert count_independent_evidence(conn, "fin") == 2
    comp = score_components(conn, "fin", "read SEC filings accurately",
                            "filing data is misclassified, mislabelled or dropped in extraction")
    assert comp["n_independent"] == 2 and comp["e"] == 15


def test_cap59_uses_independent_count_not_raw(tmp_path):
    """One group with many raw links: E comes from 1 org, not 9 raw links.

    R2-04 change, reason recorded: the old assertion (total 59, capped)
    rested on the defective F=15 + L=5 awards. Under the evidence-bound
    rule F=0/L=0, the total is E10+S20+F0+G10+L0 = 40 and the cap does
    not bite. The cap-59 guard itself is unchanged and still covered by
    the total_score unit tests in test_score.py; at 1 org the maximum
    reachable total is now 55 (even with a DOCUMENTED workaround, F=15),
    so the cap is a safety net, not a live constraint. What this test
    pins is the counting: 9 raw links in 1 repo = 1 independent source,
    never 9 — raw-count scoring would have given E=30 and total 60.
    """
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    for i in range(1, 10):
        _source(conn, f"s{i}", ext=f"acme/widgets#{600 + i}", author_hash=f"author-{i}")
        _link(conn, "p1", f"s{i}")
    conn.commit()
    # 9 distinct authors in ONE repo: n_indep=1 by org (audit method);
    # author count (9) is reported, never used for E.
    conn2 = dbmod.connect(_db(tmp_path / "x"))
    _pain(conn2, "p2")
    for i in range(1, 10):
        _source(conn2, f"s{i}", ext=f"acme/widgets#{700 + i}", author_hash="author-A")
        _link(conn2, "p2", f"s{i}")
    conn2.commit()
    assert count_independent_evidence(conn2, "p2") == 1  # old logic: 9
    # 2 competitor checks so G=10; the <2-independent cap is not reached
    # under the R2-04 rule (see docstring).
    for i in (1, 2):
        conn2.execute(
            "INSERT INTO competitor_checks (check_id, pain_id, product, checked_url,"
            " does_solve, gaps, checked_at) VALUES (?, 'p2', ?, 'https://example.com',"
            " 0, 'gap', '2026-11-05T00:00:00Z')", (f"c{i}", f"product-{i}"),
        )
    conn2.commit()
    comp = score_components(conn2, "p2", "drive an API reliably", "API call fails")
    assert comp["n_independent"] == 1
    assert comp["total"] == 40 and comp["capped"] is False
    assert comp["e"] == 10 and comp["f"] == 0 and comp["l"] == 0
    assert "CAP59" not in comp["reason"]


def test_score_reason_is_case_specific(tmp_path):
    """No single default reason per thematic label: reasons quote the pain's
    own blocker text, so two pains with different blockers differ."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "pA", job="export records", blocker="export fails on large files")
    _pain(conn, "pB", job="import records", blocker="import drops rows silently")
    _source(conn, "s1", ext="acme/widgets#801", author_hash="author-A")
    _source(conn, "s2", ext="acme/widgets#802", author_hash="author-B")
    _link(conn, "pA", "s1")
    _link(conn, "pB", "s2")
    conn.commit()
    ra = score_components(conn, "pA", "export records", "export fails on large files")["reason"]
    rb = score_components(conn, "pB", "import records", "import drops rows silently")["reason"]
    assert ra != rb
    assert "export fails on large files" in ra
    assert "import drops rows silently" in rb


def test_template_prefixed_blockers_still_distinguished_by_job(tmp_path):
    """Blockers that start with the same pasted issue template must still get
    distinct reasons: the job text is quoted in the reason."""
    conn = dbmod.connect(_db(tmp_path))
    template = "### Submission checklist - [x] This is a bug, not a usage question. "
    _pain(conn, "pA", job="export records", blocker=template + "export fails")
    _pain(conn, "pB", job="import records", blocker=template + "import drops rows")
    _source(conn, "s1", ext="acme/widgets#901", author_hash="author-A")
    _source(conn, "s2", ext="acme/widgets#902", author_hash="author-B")
    _link(conn, "pA", "s1")
    _link(conn, "pB", "s2")
    conn.commit()
    ra = score_components(conn, "pA", "export records", template + "export fails")["reason"]
    rb = score_components(conn, "pB", "import records", template + "import drops rows")["reason"]
    assert ra != rb
    assert "job='export records'" in ra and "job='import records'" in rb


def test_migration_idempotent_and_score_persists_independent_count(tmp_path, monkeypatch):
    """init_db twice keeps one column; run_score stores independent count."""
    import demand_radar.__main__ as cli
    from demand_radar.__main__ import main

    dbp = _db(tmp_path)
    dbmod.init_db(dbp)  # second run must not raise / duplicate
    cols = [r[1] for r in sqlite3.connect(dbp).execute("PRAGMA table_info(pain_points)")]
    assert cols.count("independent_evidence_count") == 1
    monkeypatch.setattr(cli, "DB", dbp)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    with dbmod.connect(dbp) as conn:
        _pain(conn, "p1")
        _source(conn, "s1", ext="acme/widgets#901", author_hash="author-A")
        _source(conn, "s2", ext="acme/widgets#902", author_hash="author-A")
        _link(conn, "p1", "s1")
        _link(conn, "p1", "s2")
        conn.commit()
    assert main(["score"]) == 0
    with dbmod.connect(dbp) as conn:
        row = conn.execute(
            "SELECT independent_evidence_count, score FROM pain_points WHERE pain_id='p1'"
        ).fetchone()
    assert row == (1, 30)  # R2-04: 2 raw links, 1 group -> E10+S20+F0+G0+L0=30
    # (was 50 under the defective F15+L5; F/L now need evidence, none exists)


def test_rejected_sources_do_not_count_as_evidence(tmp_path):
    """R02 verdicts are honoured: a REJECTED link in a second org does not
    add an independence group, an author, or a raw URL."""
    from demand_radar.score import count_distinct_authors

    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    _source(conn, "s1", ext="acme/widgets#1", author_hash="author-A")
    _link(conn, "p1", "s1", group="acme/widgets")
    _source(conn, "s2", ext="other/gadgets#1", author_hash="author-B")
    _link(conn, "p1", "s2", group="other/gadgets")
    conn.execute("UPDATE source_items SET status='REJECTED' WHERE source_id='s2'")
    conn.commit()
    assert count_independent_evidence(conn, "p1") == 1
    assert count_distinct_authors(conn, "p1") == 1
    assert count_raw_evidence(conn, "p1") == 1
    assert independent_organisations(conn, "p1") == 1
