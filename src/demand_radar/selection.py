"""REWORK1 R05: deterministic PRD qualification gate and selection.

Gate (fixed, must NOT be lowered): a pain qualifies for a rewritten PRD
only if ALL of the following hold, verified from the DB each run:

- total score >= 70 (from score.score_components, E from distinct org groups)
- cross-org corroborated: >= 2 distinct independence_group orgs
- >= 2 distinct authors (count_distinct_authors, author_hash)
- >= 2 competitor_checks rows with 0 does_solve=1 and 0 UNKNOWN trails
- counted evidence is VERIFIED-only (scoring already excludes REJECTED
  sources; see the note on rejected_links_excluded below)

Evidence-VERIFIED reading (explicit, R03 addendum): the gate applies to the
evidence actually counted. A pain may have REJECTED sources attached in
evidence_links; those rows are excluded from every count (raw, orgs,
authors, ranking URLs) and are reported in `rejected_links_excluded`, not
silently counted. Pain 0b7adcf63ec0f2075fab has 2 such attached REJECTED
links (OpenBB #7640/#7641, vendor promotion); its counted evidence is
4 VERIFIED links from 3 orgs. If a stricter reading is ever required
("no REJECTED link may be attached at all"), that pain drops out and the
qualifier count falls from 5 to 4 — the field is recorded so the decision
is auditable either way.

R2-04 DIRECT-aware gate: for pains R2-03 assessed, orgs / authors /
evidence counts and the closed/open split are computed from
DIRECT_SAME_PAIN links only (evidence_assessment.direct_only_counts);
unassessed pains keep the R03 VERIFIED-only counts. The 70 score gate
is NOT lowered. A pain whose DIRECT evidence fails the org/author
thresholds fails the gate even if its raw VERIFIED counts would pass.

Closed-issue caveat: closed state does NOT mean solved (R02 did not check
resolution from comments). Closed/open counts of VERIFIED evidence are
reported per pain (`closed_evidence`, `open_evidence`); a mostly-closed
pain is flagged in `notes`, never silently dropped.

Determinism: same DB in -> same selection out. evaluate_all() returns
rows sorted by (score desc, pain_id asc); fingerprint() hashes the
canonical JSON of the result list. Tests prove re-running reproduces the
same fingerprint.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path

from .competitors import count_checks, unknown_check_count
from .evidence_assessment import DIRECT, direct_only_counts
from .score import (
    count_distinct_authors,
    count_raw_evidence,
    has_assessment,
    independent_organisations,
)

GATE_MIN_SCORE = 70
GATE_MIN_ORGS = 2
GATE_MIN_AUTHORS = 2
GATE_MIN_COMPETITOR_CHECKS = 2


def rejected_links_excluded(conn: sqlite3.Connection, pain_id: str) -> int:
    """Evidence links attached to a pain whose source is REJECTED.

    These rows exist in evidence_links but are excluded from every
    counted figure. Reported, never counted.
    """
    row = conn.execute(
        "SELECT COUNT(*) FROM evidence_links e JOIN source_items s "
        "ON s.source_id = e.source_id "
        "WHERE e.pain_id = ? AND s.status = 'REJECTED'",
        (pain_id,),
    ).fetchone()
    return int(row[0]) if row else 0


def evidence_state_counts(conn: sqlite3.Connection, pain_id: str) -> dict:
    """Closed/open split of a pain's VERIFIED evidence (R02 issue_state).

    Closed does not mean solved; the split is reported so R05/R06 can
    weigh it. States other than open/closed are counted as 'other'.
    """
    rows = conn.execute(
        "SELECT s.issue_state, COUNT(*) FROM evidence_links e "
        "JOIN source_items s ON s.source_id = e.source_id "
        "WHERE e.pain_id = ? AND s.status = 'VERIFIED' GROUP BY s.issue_state",
        (pain_id,),
    ).fetchall()
    counts = {str(state): int(n) for state, n in rows}
    return {
        "closed": counts.get("closed", 0),
        "open": counts.get("open", 0),
        "other": sum(n for k, n in counts.items() if k not in ("closed", "open")),
    }


def evidence_state_counts_direct(conn: sqlite3.Connection, pain_id: str) -> dict:
    """Closed/open split of a pain's DIRECT_SAME_PAIN evidence only.

    Same shape as evidence_state_counts. Closed does not mean solved.
    """
    rows = conn.execute(
        """SELECT s.issue_state, COUNT(*) FROM evidence_assessment ea
        JOIN evidence_links el ON el.pain_id = ea.pain_id
          AND el.source_id = (
              SELECT source_id FROM source_items WHERE url = ea.source_url)
        JOIN source_items s ON s.source_id = el.source_id
        WHERE ea.pain_id = ? AND ea.classification = ?
        GROUP BY s.issue_state""",
        (pain_id, DIRECT),
    ).fetchall()
    counts = {str(state): int(n) for state, n in rows}
    return {
        "closed": counts.get("closed", 0),
        "open": counts.get("open", 0),
        "other": sum(n for k, n in counts.items() if k not in ("closed", "open")),
    }


def gate_check(conn: sqlite3.Connection, pain_id: str) -> dict:
    """Evaluate the R05 gate for one pain, from the DB. Pure read.

    R2-04: for R2-03-assessed pains the org/author/evidence figures are
    DIRECT-only; unassessed pains keep the R03 VERIFIED-only figures.
    """
    row = conn.execute(
        "SELECT domain, job_to_be_done, blocker, score FROM pain_points "
        "WHERE pain_id = ?",
        (pain_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"unknown pain_id: {pain_id}")
    domain, job, blocker, score = row
    score = int(score) if score is not None else 0
    if has_assessment(conn, pain_id):
        direct = direct_only_counts(conn, pain_id)
        n_orgs = direct["n_orgs"]
        n_authors = direct["n_authors"]
        n_raw = direct["n_direct"]
        states = evidence_state_counts_direct(conn, pain_id)
    else:
        n_orgs = independent_organisations(conn, pain_id)
        n_authors = count_distinct_authors(conn, pain_id)
        n_raw = count_raw_evidence(conn, pain_id)
        states = evidence_state_counts(conn, pain_id)
    n_rejected = rejected_links_excluded(conn, pain_id)
    n_checks = count_checks(conn, pain_id)
    n_solves = int(
        conn.execute(
            "SELECT COUNT(*) FROM competitor_checks "
            "WHERE pain_id = ? AND does_solve = 1",
            (pain_id,),
        ).fetchone()[0]
    )
    n_unknown = unknown_check_count(conn, pain_id)
    failures: list[str] = []
    if score < GATE_MIN_SCORE:
        failures.append(f"score {score} < {GATE_MIN_SCORE}")
    if n_orgs < GATE_MIN_ORGS:
        failures.append(f"only {n_orgs} independent org(s), need >= {GATE_MIN_ORGS}")
    if n_authors < GATE_MIN_AUTHORS:
        failures.append(f"only {n_authors} distinct author(s), need >= {GATE_MIN_AUTHORS}")
    if n_checks < GATE_MIN_COMPETITOR_CHECKS:
        failures.append(
            f"only {n_checks} competitor check(s), need >= {GATE_MIN_COMPETITOR_CHECKS}"
        )
    if n_solves > 0:
        failures.append(f"{n_solves} competitor check(s) fully solve the pain")
    if n_unknown > 0:
        failures.append(f"{n_unknown} UNKNOWN competitor trail(s) block the gate")
    notes: list[str] = []
    if n_rejected:
        notes.append(
            f"{n_rejected} attached evidence link(s) are REJECTED and excluded "
            "from all counts (counted evidence is VERIFIED-only)"
        )
    total_verified = states["closed"] + states["open"] + states["other"]
    if total_verified and states["closed"] * 2 > total_verified:
        notes.append(
            f"closed-evidence majority: {states['closed']} of {total_verified} "
            "VERIFIED evidence items are CLOSED — closed does not mean solved, "
            "resolution was not checked from comments (R02 limitation)"
        )
    return {
        "pain_id": pain_id,
        "domain": domain,
        "job": job,
        "blocker": blocker,
        "score": score,
        "n_orgs": n_orgs,
        "cross_org": n_orgs >= 2,
        "n_authors": n_authors,
        "n_raw_verified": n_raw,
        "rejected_links_excluded": n_rejected,
        "n_checks": n_checks,
        "n_solves": n_solves,
        "n_unknown_checks": n_unknown,
        "closed_evidence": states["closed"],
        "open_evidence": states["open"],
        "qualified": not failures,
        "failures": failures,
        "failure_reason": "; ".join(failures) if failures else "",
        "notes": notes,
    }


def evaluate_all(conn: sqlite3.Connection) -> list[dict]:
    """Gate-check every VERIFIED pain. Deterministic order:
    score desc, then pain_id asc."""
    pain_ids = [
        r[0]
        for r in conn.execute(
            "SELECT pain_id FROM pain_points WHERE status = 'VERIFIED' ORDER BY pain_id"
        )
    ]
    results = [gate_check(conn, pid) for pid in pain_ids]
    results.sort(key=lambda r: (-r["score"], r["pain_id"]))
    return results


def fingerprint(results: list[dict]) -> str:
    """SHA-256 of the canonical JSON of gate results (determinism check)."""
    canonical = json.dumps(results, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def write_gate_csvs(conn: sqlite3.Connection, outdir: str | Path) -> dict:
    """Write ranking copy, qualifying_prds.csv and not_qualified.csv.

    ranking.csv is the fresh CLI output (reports/ranking.csv) copied
    verbatim; the two gate files are derived from evaluate_all().
    Returns paths and counts.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    results = evaluate_all(conn)
    qualified = [r for r in results if r["qualified"]]
    not_qualified = [r for r in results if not r["qualified"]]
    fields = [
        "pain_id", "domain", "job", "score", "n_orgs", "n_authors",
        "n_raw_verified", "rejected_links_excluded", "n_checks", "n_solves",
        "n_unknown_checks", "closed_evidence", "open_evidence",
        "qualified", "failure_reason",
    ]
    for name, rows in (("qualifying_prds.csv", qualified),
                       ("not_qualified.csv", not_qualified)):
        with open(outdir / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    return {
        "qualifying": outdir / "qualifying_prds.csv",
        "not_qualified": outdir / "not_qualified.csv",
        "n_qualified": len(qualified),
        "n_not_qualified": len(not_qualified),
        "qualified_ids": [r["pain_id"] for r in qualified],
        "fingerprint": fingerprint(results),
    }


MVP_BUILT = [
    {
        "id": "R1-A",
        "path": "mvps/r1_a",
        "pain_id": "6513d051954cbe1b5027",
        "domain": "AI",
        "name": "AI fault-injection validator",
        "positioning": "PARTIALLY_REAL_WORLD_VALIDATED",
        "real_validated": (
            "recorded-event replay of LangChain #41708/#41710 through the real "
            "StreamingHandler; content-based factual check (no factual=False flag); "
            "real tiktoken 0.14.0 substitution detection for OpenAI models"
        ),
        "not_real_world_validated": (
            "#340 Qwen substitution (approximation only, no Qwen tokenizer); "
            "English/code OpenAI substitution (real tokenizers indistinguishable); "
            "no live API call ever made"
        ),
        "source": "reports/rework2/r2_05.md §1/§3; mvps/r1_a/README.md (Positioning)",
    },
    {
        "id": "R1-B",
        "path": "mvps/r1_b",
        "pain_id": "4bb734fac7245033d327",
        "domain": "BIO",
        "name": "BIO signal validator",
        "positioning": "PARTIALLY_REAL_WORLD_VALIDATED",
        "real_validated": (
            "real neurokit2 0.3.0 / wfdb 4.3.1 calls (rsp_process, hrv_rsa, "
            "fractal_dfa, signal_filter, signal_power, ecg_process, rdrecord/rdann) "
            "including a vendored MIT-BIH record 100 10 s excerpt"
        ),
        "not_real_world_validated": (
            "fixture-based checks remain synthetic signals generated from issue "
            "parameters, not original recordings"
        ),
        "source": "reports/rework2/r2_05.md §2/§3; mvps/r1_b/README.md (Positioning)",
    },
]


def build_mvp_selection(results: list[dict], superseded: list[dict] | None = None) -> dict:
    """mvp_selection.json content (REWORK2 shape).

    "prd_eligible" is the pool that passes the CURRENT gate (R2-04
    evidence-bound scoring, gate 70) — it is a PRD-eligibility list,
    NOT a list of built MVPs. "mvp_built" is the separate, static list
    of prototypes that actually exist in mvps/ (MVP_BUILT); a pain
    being PRD-eligible does not mean an MVP was built for it, and a
    built prototype does not make its pain PRD-eligible — the two
    lists are independent by design (R2-06). "superseded" carries the
    REWORK1-eligible entries that the R2-04 re-score removed, with
    their old scores preserved for the diff; pass them in explicitly,
    never recomputed.
    """
    eligible = []
    not_selected = []
    for r in results:
        entry = {
            "pain_id": r["pain_id"],
            "domain": r["domain"],
            "job": r["job"],
            "score": r["score"],
            "evidence_count": r["n_raw_verified"],
            "independent_organisations": r["n_orgs"],
            "distinct_authors": r["n_authors"],
            "competitor_checks": r["n_checks"],
            "closed_evidence": r["closed_evidence"],
            "open_evidence": r["open_evidence"],
        }
        if r["qualified"]:
            entry["reason"] = (
                f"gate PASS: score {r['score']} >= 70, {r['n_orgs']} orgs, "
                f"{r['n_authors']} authors, {r['n_checks']} competitor checks, "
                "0 does_solve — PRD-eligible under the R2-04 evidence-bound gate"
            )
            eligible.append(entry)
        else:
            entry["reason"] = f"not selected: {r['failure_reason']}"
            not_selected.append(entry)
    return {
        "prd_eligible": eligible,
        "mvp_built": [dict(m) for m in MVP_BUILT],
        "not_selected": not_selected,
        "superseded_rework1_prd_eligible": list(superseded) if superseded else [],
    }
