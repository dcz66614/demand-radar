"""SQLite access. Single writer, explicit transactions, UPSERT by (platform, external_id)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import SourceItem

SCHEMA = Path(__file__).with_name("schema.sql").read_text()


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        # REWORK1 R04 competitor columns (idempotent migration).
        for ddl in (
            "ALTER TABLE competitor_checks ADD COLUMN version TEXT",
            "ALTER TABLE competitor_checks ADD COLUMN capability TEXT",
            "ALTER TABLE competitor_checks ADD COLUMN reviewer_reason TEXT",
        ):
            try:
                conn.execute(ddl)
            except Exception:  # noqa: S110 - column may already exist (idempotent migration)
                pass
        # REWORK1 R03 independence column (idempotent migration).
        for ddl in (
            "ALTER TABLE pain_points ADD COLUMN independent_evidence_count INTEGER NOT NULL DEFAULT 0",
        ):
            try:
                conn.execute(ddl)
            except Exception:  # noqa: S110 - column may already exist (idempotent migration)
                pass
        conn.commit()
        # REWORK2 R2-04 evidence-bound scoring (idempotent).
        # - pain_points.workaround_status: UNKNOWN / DOCUMENTED. The raw
        #   current_workaround text is NEVER overwritten (history preserved
        #   for the score diff); the status is what scoring reads.
        #   Backfill: NULL / empty / known placeholder values -> UNKNOWN;
        #   any other recorded text -> DOCUMENTED.
        # - competitor_checks gains executable_function / acceptance_case /
        #   evidence_level so a re-verified check records the function
        #   actually judged, the R2-03 sample it was judged against, and
        #   how the verdict was reached (SCOPE_DOCUMENTED / UNKNOWN /
        #   NOT_REEXAMINED). Old columns are untouched.
        for ddl in (
            "ALTER TABLE pain_points ADD COLUMN workaround_status TEXT",
            "ALTER TABLE competitor_checks ADD COLUMN executable_function TEXT",
            "ALTER TABLE competitor_checks ADD COLUMN acceptance_case TEXT",
            "ALTER TABLE competitor_checks ADD COLUMN evidence_level TEXT",
        ):
            try:
                conn.execute(ddl)
            except Exception:  # noqa: S110 - column may already exist (idempotent migration)
                pass
        conn.execute(
            """UPDATE pain_points SET workaround_status = 'UNKNOWN'
            WHERE workaround_status IS NULL AND (
                current_workaround IS NULL
                OR TRIM(current_workaround) = ''
                OR LOWER(TRIM(current_workaround)) IN ('see linked issues'))"""
        )
        conn.execute(
            """UPDATE pain_points SET workaround_status = 'DOCUMENTED'
            WHERE workaround_status IS NULL"""
        )
        conn.commit()
        # REWORK1 R02 review fields (idempotent migration).
        for ddl in (
            "ALTER TABLE source_items ADD COLUMN review_verdict TEXT",
            "ALTER TABLE source_items ADD COLUMN review_reason TEXT",
            "ALTER TABLE source_items ADD COLUMN reviewed_at TEXT",
            "ALTER TABLE source_items ADD COLUMN author_hash TEXT",
            "ALTER TABLE source_items ADD COLUMN issue_state TEXT",
            "ALTER TABLE source_items ADD COLUMN issue_state_checked_at TEXT",
            "ALTER TABLE source_items ADD COLUMN issue_labels TEXT",
        ):
            try:
                conn.execute(ddl)
            except Exception:  # noqa: S110 - column may already exist (idempotent migration)
                pass
        conn.commit()
        # REWORK2 R2-03 problem-signature evidence assessment (idempotent).
        # Old data is never overwritten: assessments live in their own tables.
        conn.execute(
            """CREATE TABLE IF NOT EXISTS problem_signatures (
            pain_id TEXT PRIMARY KEY REFERENCES pain_points(pain_id),
            actor TEXT NOT NULL,
            input_artifact TEXT NOT NULL,
            operation TEXT NOT NULL,
            observed_failure TEXT NOT NULL,
            expected_output TEXT NOT NULL,
            affected_product TEXT NOT NULL,
            version_or_environment TEXT NOT NULL,
            assessed_at TEXT NOT NULL
        )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS evidence_assessment (
            pain_id TEXT NOT NULL REFERENCES pain_points(pain_id),
            source_url TEXT NOT NULL,
            classification TEXT NOT NULL CHECK(classification IN (
                'DIRECT_SAME_PAIN', 'ADJACENT_CONTEXT', 'DUPLICATE',
                'OUT_OF_SCOPE', 'UNKNOWN')),
            reason TEXT NOT NULL,
            assessed_at TEXT NOT NULL,
            PRIMARY KEY (pain_id, source_url)
        )"""
        )
        conn.commit()


def upsert_source_item(conn: sqlite3.Connection, item: SourceItem) -> bool:
    """Insert or ignore on (platform, external_id). Returns True if inserted."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO source_items
        (source_id, platform, external_id, url, canonical_url, author_key, title,
         excerpt, published_at, fetched_at, content_hash, source_type, domain, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?, 'FETCHED')""",
        (
            item.source_id, item.platform, item.external_id, item.url,
            item.canonical_url, None, item.title, item.excerpt,
            item.published_at, item.fetched_at, item.content_hash,
            item.source_type, item.domain,
        ),
    )
    conn.commit()
    return cur.rowcount == 1


def counts(conn: sqlite3.Connection) -> dict:
    out = {}
    for table in ("source_items", "pain_points", "evidence_links"):
        out[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    out["by_domain"] = dict(
        conn.execute("SELECT domain, COUNT(*) FROM source_items GROUP BY domain").fetchall()
    )
    return out
