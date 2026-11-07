"""R05 PRD tests (prd.py).

A PRD must be complete, grounded in DB evidence, and unique: two PRDs
for different pains must not share acceptance tests or boilerplate
paragraphs. validate() refuses incomplete PRDs before rendering.
"""
from demand_radar import db as dbmod
from demand_radar.prd import PRD, prd_from_db, render_markdown, validate


def _db(tmp_path):
    dbp = tmp_path / "t.sqlite"
    dbmod.init_db(dbp)
    return dbp


def _seed(conn, pid, job, blocker):
    conn.execute(
        "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done, blocker,"
        " status, score, score_reason, created_at, updated_at)"
        " VALUES (?, 'AI', 'user', ?, ?, 'VERIFIED', 70, 'E=20 S=20 F=15 G=10 L=5',"
        " '2026-11-05T00:00:00Z', '2026-11-05T00:00:00Z')", (pid, job, blocker),
    )
    for i, (repo, author) in enumerate((("acme/a", "auth-A"), ("acme/b", "auth-B"))):
        sid = f"{pid}-s{i+1}"
        conn.execute(
            "INSERT INTO source_items (source_id, platform, external_id, url,"
            " canonical_url, author_key, title, excerpt, published_at, fetched_at,"
            " content_hash, source_type, domain, status, author_hash, issue_state)"
            " VALUES (?, 'github', ?, ?, ?, NULL, ?, ?, '2026-10-01T00:00:00Z',"
            " '2026-11-05T00:00:00Z', 'h', 'firsthand_issue', 'AI', 'VERIFIED', ?, 'open')",
            (sid, f"{repo}#{pid}-{i}", f"https://github.com/{repo}/issues/{pid}-{i}",
             f"https://github.com/{repo}/issues/{pid}-{i}", f"issue {sid}", f"excerpt {sid}", author),
        )
        conn.execute(
            "INSERT INTO evidence_links (pain_id, source_id, is_firsthand,"
            " independence_group, evidence_note) VALUES (?, ?, 1, ?, 'x')", (pid, sid, repo),
        )
    for product in ("alt-one", "alt-two"):
        conn.execute(
            "INSERT INTO competitor_checks (check_id, pain_id, product, checked_url,"
            " does_solve, gaps, checked_at) VALUES (?, ?, ?, ?, 0, ?, '2026-11-05')",
            (f"cc-{pid}-{product}", pid, product, f"https://example.com/{product}",
             f"gap for {product}"),
        )
    conn.commit()


def _kwargs(tag):
    return {
        "user_task": f"user task {tag}",
        "workaround": f"workaround {tag}",
        "impact": f"impact {tag}",
        "sample_input": f"sample input {tag}",
        "expected_output": f"expected output {tag}",
        "acceptance_tests": [f"acceptance test {tag}-{i}" for i in range(1, 4)],
        "caveats": [f"caveat {tag}"],
    }


def test_prd_from_db_loads_verified_evidence_only(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _seed(conn, "p1", "drive an API reliably", "API call fails")
    prd = prd_from_db(conn, "p1", **_kwargs("one"))
    assert len(prd.evidence) == 2
    assert all(e.url.startswith("https://github.com/") for e in prd.evidence)
    assert len(prd.competitors) == 2
    assert prd.score == 70 and prd.n_orgs == 2
    assert validate(prd) == []


def test_render_contains_all_required_sections(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _seed(conn, "p1", "drive an API reliably", "API call fails")
    prd = prd_from_db(conn, "p1", **_kwargs("one"))
    md = render_markdown(prd)
    for section in ("## User task", "## Evidence", "## Actual workaround and impact",
                    "## Competitor checks", "## Sample input", "## Expected output",
                    "## Acceptance tests", "## Caveats"):
        assert section in md
    assert "https://github.com/acme/a/issues/p1-0" in md
    assert "acceptance test one-1" in md


def test_validate_rejects_missing_acceptance_tests(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _seed(conn, "p1", "drive an API reliably", "API call fails")
    kw = _kwargs("one")
    kw["acceptance_tests"] = ["only one", "only two"]
    prd = prd_from_db(conn, "p1", **kw)
    problems = validate(prd)
    assert any("3-5 unique tests" in p for p in problems)


def test_validate_rejects_duplicate_acceptance_tests(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _seed(conn, "p1", "drive an API reliably", "API call fails")
    kw = _kwargs("one")
    kw["acceptance_tests"] = ["same test"] * 3
    prd = prd_from_db(conn, "p1", **kw)
    assert any("unique" in p for p in validate(prd))


def test_validate_rejects_prd_with_fewer_than_two_competitors(tmp_path):
    conn = dbmod.connect(_db(tmp_path))
    _seed(conn, "p1", "drive an API reliably", "API call fails")
    conn.execute("DELETE FROM competitor_checks WHERE product='alt-two'")
    conn.commit()
    prd = prd_from_db(conn, "p1", **_kwargs("one"))
    assert any(">= 2 competitor checks" in p for p in validate(prd))


def test_two_prds_do_not_share_acceptance_tests(tmp_path):
    """No copied boilerplate: acceptance tests and sample inputs differ
    per pain, and rendering two PRDs gives different acceptance sections."""
    conn = dbmod.connect(_db(tmp_path))
    _seed(conn, "p1", "drive an API reliably", "API call fails")
    _seed(conn, "p2", "read biosignal files", "file reading fails")
    md1 = render_markdown(prd_from_db(conn, "p1", **_kwargs("one")))
    md2 = render_markdown(prd_from_db(conn, "p2", **_kwargs("two")))
    assert "acceptance test one-1" in md1 and "acceptance test one-1" not in md2
    assert "acceptance test two-1" in md2 and "acceptance test two-1" not in md1
    assert "sample input one" in md1 and "sample input two" in md2


def test_render_refuses_incomplete_prd():
    prd = PRD(pain_id="px", domain="AI", job="j", blocker="b", score=70,
              score_reason="r")
    try:
        render_markdown(prd)
    except ValueError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("render_markdown should refuse an incomplete PRD")
