"""REWORK2 R2-03: problem-signature evidence assessment.

A theme is only a demand if its evidence reports the SAME fine-grained
problem.  Each qualifying theme gets one ``problem_signature`` (actor,
input_artifact, operation, observed_failure, expected_output,
affected_product, version_or_environment); every evidence link of the
theme is classified against that signature:

- ``DIRECT_SAME_PAIN`` — the link reports the signature's problem.
- ``ADJACENT_CONTEXT`` — same workflow/domain, different operation,
  product or failure; background only, never counted.
- ``DUPLICATE`` — the same report filed more than once; the later
  filing(s) add no demand however the first filing is classified.
- ``OUT_OF_SCOPE`` — a different problem (packaging, docs CI, feature
  request, deployment question, CVE tracking, vendor promotion, ...).
- ``UNKNOWN`` — the link could not be read; never guessed.

Only ``DIRECT_SAME_PAIN`` links enter an independence count.  A
cross-org count requires the same problem_signature, not the same
broad domain.  This module never touches ``score.py`` / ``selection.py``
(R2-04 owns scoring); it only produces the assessment data R2-04 will
consume.
"""
from __future__ import annotations

import sqlite3

DIRECT = "DIRECT_SAME_PAIN"
ADJACENT = "ADJACENT_CONTEXT"
DUPLICATE = "DUPLICATE"
OUT_OF_SCOPE = "OUT_OF_SCOPE"
UNKNOWN = "UNKNOWN"

CLASSIFICATIONS = frozenset({DIRECT, ADJACENT, DUPLICATE, OUT_OF_SCOPE, UNKNOWN})

SIGNATURE_FIELDS = (
    "actor",
    "input_artifact",
    "operation",
    "observed_failure",
    "expected_output",
    "affected_product",
    "version_or_environment",
)


def upsert_problem_signature(
    conn: sqlite3.Connection, pain_id: str, signature: dict, assessed_at: str
) -> None:
    """Store one theme's problem_signature (idempotent upsert)."""
    missing = [f for f in SIGNATURE_FIELDS if not signature.get(f)]
    if missing:
        raise ValueError(f"problem_signature for {pain_id} lacks: {missing}")
    conn.execute(
        """INSERT INTO problem_signatures
        (pain_id, actor, input_artifact, operation, observed_failure,
         expected_output, affected_product, version_or_environment, assessed_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(pain_id) DO UPDATE SET
            actor=excluded.actor, input_artifact=excluded.input_artifact,
            operation=excluded.operation,
            observed_failure=excluded.observed_failure,
            expected_output=excluded.expected_output,
            affected_product=excluded.affected_product,
            version_or_environment=excluded.version_or_environment,
            assessed_at=excluded.assessed_at""",
        (pain_id, *(signature[f] for f in SIGNATURE_FIELDS), assessed_at),
    )


def upsert_assessment(
    conn: sqlite3.Connection,
    pain_id: str,
    source_url: str,
    classification: str,
    reason: str,
    assessed_at: str,
) -> None:
    """Store one per-link assessment (idempotent upsert)."""
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"unknown classification: {classification!r}")
    if not reason.strip():
        raise ValueError("assessment reason must not be empty")
    conn.execute(
        """INSERT INTO evidence_assessment
        (pain_id, source_url, classification, reason, assessed_at)
        VALUES (?,?,?,?,?)
        ON CONFLICT(pain_id, source_url) DO UPDATE SET
            classification=excluded.classification,
            reason=excluded.reason, assessed_at=excluded.assessed_at""",
        (pain_id, source_url, classification, reason, assessed_at),
    )


def direct_only_counts(conn: sqlite3.Connection, pain_id: str) -> dict:
    """Recompute a theme's evidence from DIRECT_SAME_PAIN links only.

    Returns n_direct, the set of independence groups (orgs), n_orgs, the
    set of distinct author hashes and n_authors — all restricted to
    DIRECT_SAME_PAIN assessments.  Adjacent, duplicate, out-of-scope and
    unknown links contribute nothing.
    """
    rows = conn.execute(
        """SELECT el.independence_group, s.author_hash
        FROM evidence_assessment ea
        JOIN evidence_links el
          ON el.pain_id = ea.pain_id
         AND el.source_id = (
             SELECT source_id FROM source_items WHERE url = ea.source_url)
        JOIN source_items s ON s.source_id = el.source_id
        WHERE ea.pain_id = ? AND ea.classification = ?""",
        (pain_id, DIRECT),
    ).fetchall()
    orgs = {r[0] for r in rows}
    authors = {r[1] for r in rows if r[1]}
    return {
        "n_direct": len(rows),
        "orgs": sorted(orgs),
        "n_orgs": len(orgs),
        "authors": sorted(authors),
        "n_authors": len(authors),
    }


def assessment_counts(conn: sqlite3.Connection, pain_id: str) -> dict:
    """How many links of a theme carry each classification."""
    rows = conn.execute(
        "SELECT classification, COUNT(*) FROM evidence_assessment "
        "WHERE pain_id = ? GROUP BY classification",
        (pain_id,),
    ).fetchall()
    out = {c: 0 for c in sorted(CLASSIFICATIONS)}
    out.update(dict(rows))
    return out
