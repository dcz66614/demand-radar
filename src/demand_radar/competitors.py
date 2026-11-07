"""REWORK1 R04: real competitor evidence.

Competitor checks live in the ``competitor_checks`` table (schema.sql).
The original table only had product/checked_url/does_solve/gaps/checked_at;
R04 adds version / capability / reviewer_reason columns via an idempotent
migration (see ensure_competitor_columns), because the audit requires exactly
grounded product names, versions, official URLs, observed capabilities,
gaps, check date and reviewer reasoning.

Gate rule (see score.py, R03 owns scoring):
- gate met iff >= 2 checks AND none of them is an UNKNOWN trail.
- An UNKNOWN trail is a check whose product is "UNKNOWN" or whose gap
  starts with "UNKNOWN:" — a bounded, reproducible failed search.
  It blocks the qualifying gate; it never awards G=10.
- does_solve=1 means the checked alternative fully solves the pain.
  Scoring currently still awards G=10 for >=2 checks regardless of
  does_solve; that is a scoring-code limitation flagged for R05, not
  hidden here — see reports/rework1/competitors.md.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import date

UNKNOWN_PRODUCT = "UNKNOWN"


def ensure_competitor_columns(conn: sqlite3.Connection) -> None:
    """Idempotent migration: add version/capability/reviewer_reason columns.

    R2-04 adds executable_function / acceptance_case / evidence_level so a
    re-verified check records the function actually judged, the R2-03
    sample it was judged against, and how the verdict was reached
    (SCOPE_DOCUMENTED = documented function/scope tied to the sample,
    not execution-tested; UNKNOWN = marketing copy / broken library /
    no sample link; NOT_REEXAMINED = row untouched by R2-04).
    """
    existing = {r[1] for r in conn.execute("PRAGMA table_info(competitor_checks)")}
    for ddl in (
        "ALTER TABLE competitor_checks ADD COLUMN version TEXT",
        "ALTER TABLE competitor_checks ADD COLUMN capability TEXT",
        "ALTER TABLE competitor_checks ADD COLUMN reviewer_reason TEXT",
        "ALTER TABLE competitor_checks ADD COLUMN executable_function TEXT",
        "ALTER TABLE competitor_checks ADD COLUMN acceptance_case TEXT",
        "ALTER TABLE competitor_checks ADD COLUMN evidence_level TEXT",
    ):
        col = ddl.split("ADD COLUMN ")[1].split(" ")[0]
        if col not in existing:
            conn.execute(ddl)
    conn.commit()


def check_id_for(pain_id: str, product: str, url: str) -> str:
    """Deterministic check id so re-running the loader is idempotent."""
    digest = hashlib.sha256(f"{pain_id}|{product}|{url}".encode()).hexdigest()
    return f"cc-{digest[:16]}"


def insert_competitor_check(
    conn: sqlite3.Connection,
    *,
    pain_id: str,
    product: str,
    version: str,
    url: str,
    capability: str,
    gap: str,
    reviewer_reason: str,
    does_solve: int = 0,
    checked_at: str | None = None,
    executable_function: str | None = None,
    acceptance_case: str | None = None,
    evidence_level: str | None = None,
) -> str:
    """Insert one competitor check. Returns the check_id.

    Raises ValueError on empty product/url/capability/gap/reviewer_reason —
    a check without a grounded record is not a check.
    R2-04: executable_function / acceptance_case / evidence_level record
    what was actually judged and how; an UNKNOWN verdict is recorded by
    prefixing gap with 'UNKNOWN: ' (the existing convention — see
    unknown_check_count), keeping the product name so history is kept.
    """
    for name, value in (
        ("product", product),
        ("url", url),
        ("capability", capability),
        ("gap", gap),
        ("reviewer_reason", reviewer_reason),
    ):
        if not value or not str(value).strip():
            raise ValueError(f"competitor check requires non-empty {name}")
    if does_solve not in (0, 1):
        raise ValueError("does_solve must be 0 or 1")
    ensure_competitor_columns(conn)
    check_id = check_id_for(pain_id, product, url)
    checked_at = checked_at or date.today().isoformat()
    conn.execute(
        """INSERT OR REPLACE INTO competitor_checks
        (check_id, pain_id, product, version, checked_url, capability,
         does_solve, gaps, reviewer_reason, checked_at,
         executable_function, acceptance_case, evidence_level)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (check_id, pain_id, product, version, url, capability,
         does_solve, gap, reviewer_reason, checked_at,
         executable_function, acceptance_case, evidence_level),
    )
    conn.commit()
    return check_id


def real_check_count(conn: sqlite3.Connection, pain_id: str) -> int:
    """Competitor checks that are real alternatives, not UNKNOWN trails."""
    return count_checks(conn, pain_id) - unknown_check_count(conn, pain_id)


def count_checks(conn: sqlite3.Connection, pain_id: str) -> int:
    """Total competitor_checks rows for a pain (including UNKNOWN trails)."""
    row = conn.execute(
        "SELECT COUNT(*) FROM competitor_checks WHERE pain_id=?", (pain_id,)
    ).fetchone()
    return int(row[0]) if row else 0


def unknown_check_count(conn: sqlite3.Connection, pain_id: str) -> int:
    """Rows that are failed-search trails, not real alternatives."""
    row = conn.execute(
        "SELECT COUNT(*) FROM competitor_checks WHERE pain_id=? "
        "AND (product=? OR gaps LIKE 'UNKNOWN:%')",
        (pain_id, UNKNOWN_PRODUCT),
    ).fetchone()
    return int(row[0]) if row else 0


def gate_met(conn: sqlite3.Connection, pain_id: str) -> bool:
    """Qualifying gate: >=2 real checks and zero UNKNOWN trails."""
    return count_checks(conn, pain_id) >= 2 and unknown_check_count(conn, pain_id) == 0


def list_checks(conn: sqlite3.Connection, pain_id: str) -> list[dict]:
    """All checks for a pain, in deterministic order."""
    ensure_competitor_columns(conn)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(competitor_checks)")]
    rows = conn.execute(
        "SELECT * FROM competitor_checks WHERE pain_id=? ORDER BY product, checked_url",
        (pain_id,),
    ).fetchall()
    return [dict(zip(cols, r)) for r in rows]
