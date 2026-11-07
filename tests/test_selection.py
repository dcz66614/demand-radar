"""R05 gate tests (selection.py).

Each test pins one gate condition, so lowering any threshold or dropping
a check makes a test fail. Fixtures mirror tests/test_independence.py.
"""
from demand_radar import db as dbmod
from demand_radar.score import score_components, store_score
from demand_radar.selection import (
    build_mvp_selection,
    evaluate_all,
    fingerprint,
    gate_check,
)


def _db(tmp_path):
    dbp = tmp_path / "t.sqlite"
    dbmod.init_db(dbp)
    return dbp


def _source(conn, sid, ext, url, author_hash, state="open"):
    conn.execute(
        "INSERT INTO source_items (source_id, platform, external_id, url, canonical_url,"
        " author_key, title, excerpt, published_at, fetched_at, content_hash,"
        " source_type, domain, status, author_hash, issue_state)"
        " VALUES (?, 'github', ?, ?, ?, NULL, ?, ?, '2026-10-01T00:00:00Z',"
        " '2026-11-05T00:00:00Z', 'h', 'firsthand_issue', 'AI', 'VERIFIED', ?, ?)",
        (sid, ext, url, url, f"issue {sid}", f"excerpt {sid}", author_hash, state),
    )


def _pain(conn, pid, job="drive an API reliably", blocker="API call fails"):
    conn.execute(
        "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done, blocker,"
        " status, created_at, updated_at) VALUES (?, 'AI', 'user', ?, ?, 'VERIFIED',"
        " '2026-11-05T00:00:00Z', '2026-11-05T00:00:00Z')", (pid, job, blocker),
    )


def _link(conn, pid, sid, group):
    conn.execute(
        "INSERT INTO evidence_links (pain_id, source_id, is_firsthand,"
        " independence_group, evidence_note) VALUES (?, ?, 1, ?, 'x')", (pid, sid, group),
    )


def _check(conn, pid, product, does_solve=0):
    conn.execute(
        "INSERT INTO competitor_checks (check_id, pain_id, product, checked_url,"
        " does_solve, gaps, checked_at) VALUES (?, ?, ?, ?, ?, 'gap', '2026-11-05')",
        (f"cc-{pid}-{product}", pid, product, f"https://example.com/{product}", does_solve),
    )


def _qualifying(conn, pid="p1"):
    """A pain meeting every gate condition; score is set to 70 directly
    (score_components is tested separately in test_score/test_independence)."""
    _pain(conn, pid)
    for i, (repo, author) in enumerate((("acme/a", "auth-A"), ("acme/b", "auth-B"))):
        sid = f"{pid}-s{i+1}"
        _source(conn, sid, f"{repo}#{pid}-{i}", f"https://github.com/{repo}/issues/{pid}-{i}", author)
        _link(conn, pid, sid, repo)
    _check(conn, pid, "alt-one")
    _check(conn, pid, "alt-two")
    conn.execute("UPDATE pain_points SET score=70 WHERE pain_id=?", (pid,))
    conn.commit()


def test_gate_passes_for_qualifying_pain(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn)
    r = gate_check(conn, "p1")
    assert r["qualified"] is True
    assert r["failure_reason"] == ""
    assert r["n_orgs"] == 2 and r["n_authors"] == 2 and r["n_checks"] == 2
    assert r["n_solves"] == 0 and r["n_unknown_checks"] == 0


def test_gate_fails_when_score_below_70(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn)
    conn.execute("UPDATE pain_points SET score=65 WHERE pain_id='p1'")
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "score 65 < 70" in r["failure_reason"]


def test_gate_fails_when_single_org(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    for i, author in enumerate(("auth-A", "auth-B")):
        sid = f"s{i+1}"
        _source(conn, sid, f"acme/a#1{i}", f"https://github.com/acme/a/issues/1{i}", author)
        _link(conn, "p1", sid, "acme/a")
    _check(conn, "p1", "alt-one")
    _check(conn, "p1", "alt-two")
    conn.execute("UPDATE pain_points SET score=70 WHERE pain_id='p1'")
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "only 1 independent org" in r["failure_reason"]


def test_gate_fails_when_single_author(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    for i, repo in enumerate(("acme/a", "acme/b")):
        sid = f"s{i+1}"
        _source(conn, sid, f"{repo}#1{i}", f"https://github.com/{repo}/issues/1{i}", "auth-A")
        _link(conn, "p1", sid, repo)
    _check(conn, "p1", "alt-one")
    _check(conn, "p1", "alt-two")
    conn.execute("UPDATE pain_points SET score=70 WHERE pain_id='p1'")
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "only 1 distinct author" in r["failure_reason"]


def test_gate_fails_when_competitor_solves_pain(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn)
    _check(conn, "p1", "alt-solver", does_solve=1)
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "fully solve" in r["failure_reason"]


def test_gate_fails_with_fewer_than_two_checks(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1")
    for i, (repo, author) in enumerate((("acme/a", "auth-A"), ("acme/b", "auth-B"))):
        sid = f"s{i+1}"
        _source(conn, sid, f"{repo}#1{i}", f"https://github.com/{repo}/issues/1{i}", author)
        _link(conn, "p1", sid, repo)
    _check(conn, "p1", "alt-one")
    conn.execute("UPDATE pain_points SET score=70 WHERE pain_id='p1'")
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "only 1 competitor check" in r["failure_reason"]


def test_gate_fails_on_unknown_competitor_trail(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn)
    conn.execute(
        "INSERT INTO competitor_checks (check_id, pain_id, product, checked_url,"
        " does_solve, gaps, checked_at) VALUES ('cc-p1-unk', 'p1', 'UNKNOWN',"
        " 'https://example.com/search', 0, 'UNKNOWN: no alternative found', '2026-11-05')"
    )
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
    assert "UNKNOWN" in r["failure_reason"]


def test_rejected_sources_never_count_as_evidence(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn)
    # Attach a REJECTED source to the same pain: counts must not move.
    _source(conn, "s9", "acme/c#99", "https://github.com/acme/c/issues/99", "auth-C")
    conn.execute("UPDATE source_items SET status='REJECTED' WHERE source_id='s9'")
    _link(conn, "p1", "s9", "acme/c")
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["n_raw_verified"] == 2
    assert r["n_orgs"] == 2
    assert r["rejected_links_excluded"] == 1
    assert r["qualified"] is True


def test_closed_majority_is_flagged_not_dropped(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn)
    conn.execute("UPDATE source_items SET issue_state='closed' WHERE source_id IN ('p1-s1','p1-s2')")
    conn.commit()
    r = gate_check(conn, "p1")
    assert r["closed_evidence"] == 2 and r["open_evidence"] == 0
    assert r["qualified"] is True  # flagged in notes, not dropped
    assert any("closed-evidence majority" in n for n in r["notes"])


def test_selection_is_deterministic_same_db_same_result(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn, "p1")
    _qualifying(conn, "p2")
    conn.execute("UPDATE pain_points SET score=65 WHERE pain_id='p2'")
    conn.commit()
    first = evaluate_all(conn)
    second = evaluate_all(conn)
    assert fingerprint(first) == fingerprint(second)
    assert [r["pain_id"] for r in first if r["qualified"]] == ["p1"]


def test_mvp_selection_carries_explicit_reasons(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _qualifying(conn, "p1")
    _qualifying(conn, "p2")
    conn.execute("UPDATE pain_points SET score=65 WHERE pain_id='p2'")
    conn.commit()
    sel = build_mvp_selection(evaluate_all(conn))
    # R2-06 shape: "prd_eligible" is the gate-passing pool (NOT built MVPs);
    # "mvp_built" is the separate static list of prototypes that exist.
    assert [s["pain_id"] for s in sel["prd_eligible"]] == ["p1"]
    assert len(sel["not_selected"]) == 1
    assert "score 65 < 70" in sel["not_selected"][0]["reason"]
    assert "not selected:" in sel["not_selected"][0]["reason"]
    assert [m["id"] for m in sel["mvp_built"]] == ["R1-A", "R1-B"]
    assert all(m["positioning"] == "PARTIALLY_REAL_WORLD_VALIDATED"
               for m in sel["mvp_built"])
    assert sel["superseded_rework1_prd_eligible"] == []


def test_score_from_real_scorer_feeds_gate(tmp_path):
    """End-to-end: score_components (E from org groups) drives the gate,
    so a 1-org pain can never reach 70 even with a raw count of 19."""
    conn = dbmod.connect(_db(tmp_path))
    _pain(conn, "p1", job="process signals", blocker="signal functions crash")
    for i in range(19):
        sid = f"s{i}"
        _source(conn, sid, f"acme/a#{i}", f"https://github.com/acme/a/issues/{i}", f"auth-{i}")
        _link(conn, "p1", sid, "acme/a")
    _check(conn, "p1", "alt-one")
    _check(conn, "p1", "alt-two")
    conn.commit()
    comp = score_components(conn, "p1", "process signals", "signal functions crash")
    store_score(conn, "p1", comp)
    conn.commit()
    assert comp["n_independent"] == 1
    assert comp["total"] <= 59  # cap-59: <2 independent sources
    r = gate_check(conn, "p1")
    assert r["qualified"] is False
