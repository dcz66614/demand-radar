"""REWORK1 R04: competitor gate tests.

Gate rule: >=2 real checks and zero UNKNOWN trails.
These tests fail on the old code (no competitors module, competitor_checks
has 0 rows so the gate is not met).
"""
import sqlite3

import pytest

from demand_radar.competitors import (
    count_checks,
    gate_met,
    insert_competitor_check,
    list_checks,
    unknown_check_count,
)
from demand_radar.db import init_db

PAIN = "6513d051954cbe1b5027"


@pytest.fixture()
def conn(tmp_path):
    db_path = tmp_path / "test.sqlite"
    init_db(db_path)
    c = sqlite3.connect(str(db_path))
    c.execute("PRAGMA foreign_keys = ON")
    c.execute(
        "INSERT INTO pain_points (pain_id, domain, who, job_to_be_done, blocker,"
        " created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
        (PAIN, "AI", "user", "drive an AI agent / API reliably", "API calls fail",
         "2026-11-05", "2026-11-05"),
    )
    c.commit()
    yield c
    c.close()


def _check(conn, product="LiteLLM", url="https://docs.litellm.ai/"):
    return insert_competitor_check(
        conn, pain_id=PAIN, product=product, version="1.65.0",
        url=url, capability="Retries and fallbacks across LLM providers",
        gap="Retries do not fix wrong results or silent default substitution",
        reviewer_reason="Official docs describe retry/fallback; no result-validation feature found",
    )


def test_gate_fails_with_zero_checks(conn):
    assert count_checks(conn, PAIN) == 0
    assert not gate_met(conn, PAIN)


def test_gate_fails_with_one_check(conn):
    _check(conn)
    assert count_checks(conn, PAIN) == 1
    assert not gate_met(conn, PAIN)


def test_gate_passes_with_two_real_checks(conn):
    _check(conn)
    _check(conn, product="LangSmith", url="https://docs.smith.langchain.com/")
    assert count_checks(conn, PAIN) == 2
    assert gate_met(conn, PAIN)


def test_unknown_trail_blocks_gate_even_with_two_rows(conn):
    _check(conn)
    insert_competitor_check(
        conn, pain_id=PAIN, product="UNKNOWN", version="n/a",
        url="https://example.com/not-found",
        capability="UNKNOWN: bounded search found no real alternative",
        gap="UNKNOWN: no product found after documented search; gap cannot be assessed",
        reviewer_reason="Failed-search trail, not a real alternative",
    )
    assert count_checks(conn, PAIN) == 2
    assert unknown_check_count(conn, PAIN) == 1
    assert not gate_met(conn, PAIN)


def test_unknown_gap_prefix_also_blocks(conn):
    _check(conn)
    _check(conn, product="LangSmith", url="https://docs.smith.langchain.com/")
    insert_competitor_check(
        conn, pain_id=PAIN, product="SomeTool", version="n/a",
        url="https://example.com/sometool",
        capability="Claims to solve the pain",
        gap="UNKNOWN: capability page could not be verified (HTTP error)",
        reviewer_reason="URL did not return a verifiable capability page",
    )
    assert not gate_met(conn, PAIN)


def test_insert_rejects_empty_fields(conn):
    with pytest.raises(ValueError):
        insert_competitor_check(
            conn, pain_id=PAIN, product="", version="1.0",
            url="https://example.com", capability="x", gap="y",
            reviewer_reason="z",
        )
    with pytest.raises(ValueError):
        insert_competitor_check(
            conn, pain_id=PAIN, product="X", version="1.0",
            url="https://example.com", capability="x", gap="",
            reviewer_reason="z",
        )


def test_insert_is_idempotent_and_lists_checks(conn):
    cid1 = _check(conn)
    cid2 = _check(conn)
    assert cid1 == cid2
    assert count_checks(conn, PAIN) == 1
    rows = list_checks(conn, PAIN)
    assert len(rows) == 1
    assert rows[0]["product"] == "LiteLLM"
    assert rows[0]["version"] == "1.65.0"
    assert rows[0]["checked_url"] == "https://docs.litellm.ai/"
    assert rows[0]["does_solve"] == 0
