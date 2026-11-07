"""Deterministic 0-100 scoring (Execution Plan §5). Pure function, unit-tested.

REWORK1 changes (audit P0-02, R03):
- E is computed from DISTINCT independence groups via count_independent_evidence(),
  never from raw issue-row counts. evidence_count stays the raw unique-URL
  count and is labelled as such everywhere; it must never masquerade as
  independence.
- G is UNKNOWN (0) when a pain has no competitor_checks rows. A missing
  competitor check must block the gate, never default to a positive 10.
- S/F/L reasons are case-specific: each score_reason quotes the pain's own
  job/blocker text and the keywords/signals actually matched. Where a
  component cannot be validated from the record it is capped conservatively
  and the reason says so. No single default reason is shared per thematic
  label (verified: no two pains share an identical score_reason unless their
  inputs are identical).

Independence-group semantics (documented, R03; corrected by parent 2026-11-05
after author hashes landed — see decision log):
- The audit (P0-02) prescribes E from DISTINCT existing independence groups,
  i.e. distinct organisation/repo keys in evidence_links.independence_group.
  That is what count_independent_evidence() returns, and it is the ONLY
  number used for E, cap-59, PRD and MVP gates.
- WHY NOT (author, repo): the first R03 implementation counted distinct
  (author_hash, repo) pairs. Once author hashes landed that re-inflated E to
  30 for pains with many authors inside few repos (AI 19 raw -> 14 pairs ->
  total 80 again; a pandas-only theme with 7 authors in 1 repo reached 80).
  That is the same inflation the audit flagged, at a finer granularity, and
  it admits single-repo themes the audit said were wrongly admitted.
- Author hashes are still used and recorded: count_distinct_authors() reports
  them, and the PRD gate (R05) additionally requires >= 2 distinct authors,
  so a single author filing the same demand in two repos cannot qualify
  alone. Same-author duplicates inside one repo already collapse at org
  level (e.g. LangChain #41708/#41709/#41710 = 1 group).
- Two unrelated issues in the same repo are NOT automatically the same
  demand: grouping is by shared job+blocker (the pain), never by repo
  alone. count_independent_evidence() only counts links attached to that
  pain_id.

REWORK2 R2-04 — evidence-bound scoring (review P1-01; brief §R2-04).
The R05 scores were all exactly 70 = E20 + S20 + F15 + G10 + L5, and the
F and L parts were unproven by the record's own admission:
- F=15 was awarded whenever a current_workaround string existed, including
  the placeholder 'see linked issues' on all 5 qualifying themes, while the
  R05 PRDs state "No workaround is documented in the record". A placeholder
  is not feasibility evidence. The old rule also awarded F=15 when NO
  workaround and NO paid signal existed at all ("feasibility NOT validated
  — F capped at 15"). Both branches are removed.
- L=5 was awarded with the reason "no transfer/reuse evidence in record".
  A component with no evidence behind it is 0, never a positive minimum.
- G=10 was awarded for >=2 competitor_checks rows even when a row was an
  UNKNOWN trail. An UNKNOWN trail now blocks G (G=0) and the gate.

The R2-04 rule (this module's score_components):
- E: from DIRECT_SAME_PAIN evidence only, for pains R2-03 assessed
  (direct_only_counts); unassessed pains keep the R03 org-group count.
  Adjacent / duplicate / out-of-scope links contribute nothing.
- S: UNCHANGED in R2-04 (keyword-derived severity; P1-01's S concern is
  recorded as a residual limitation in reports/rework2/r2_04.md, not
  silently fixed here). Keeping S is conservative in the direction of
  the review: even with S=20 retained, no theme reaches 70.
- F: 15 ONLY when pain_points.workaround_status = 'DOCUMENTED' (a real,
  verifiable workaround recorded — none exists in this dataset); otherwise
  0 / UNKNOWN. A paid/rate-limit keyword mention is NOT feasibility
  evidence (F=0). Placeholder values ('see linked issues') and NULL are
  UNKNOWN by migration; the raw current_workaround text is preserved
  untouched in the DB for the score diff.
- G: 0 if any competitor check does_solve=1; 0 if any UNKNOWN trail
  exists; 10 if >=2 REAL (non-UNKNOWN) checks and none solves; 5 if
  exactly 1 real check; 0 if no real check.
- L: 0 always in this dataset — no documented transfer/reuse evidence
  exists. L>0 requires a documented reuse_evidence record; the schema
  for one does not exist yet, so no L point can be awarded honestly.
- The 70 gate is NOT lowered (selection.GATE_MIN_SCORE stays 70).
"""
import sqlite3

from .competitors import count_checks, unknown_check_count
from .evidence_assessment import direct_only_counts

E_MAP = {0: 0, 1: 10, 2: 15, 3: 20, 4: 25}

# Placeholder workaround texts: a pointer to "the linked issues" is not a
# workaround and never evidences feasibility. Compared case-insensitively
# after stripping. Any other recorded text is treated as DOCUMENTED only
# when workaround_status says so (migration backfills it); see
# workaround_status() below.
PLACEHOLDER_WORKAROUNDS = frozenset({"see linked issues"})


def evidence_score(n_independent: int) -> int:
    if n_independent >= 5:
        return 30
    return E_MAP.get(max(n_independent, 0), 0)


def total_score(e: int, s: int, f: int, g: int, l: int, n_independent: int) -> tuple[int, bool]:
    """Returns (total, cap_applied). <2 independent firsthand sources caps at 59."""
    total = e + s + f + g + l
    total = max(0, min(100, total))
    if n_independent < 2 and total > 59:
        return 59, True
    return total, False


def count_independent_evidence(conn, pain_id: str) -> int:
    """Count DISTINCT organisation/repo independence groups for a pain.

    Audit-faithful (P0-02): the unit is the independence_group key
    (repo/context), never raw issue rows and never distinct (author, repo)
    pairs — the latter re-inflates single-repo themes. Same-author
    duplicates inside one repo collapse to 1 group (e.g. LangChain
    #41708/#41709/#41710). See count_distinct_authors() for the
    person-level figure, reported alongside but NOT used for E.
    """
    # REJECTED sources never count as evidence (R02 verdicts).
    row = conn.execute(
        "SELECT COUNT(DISTINCT e.independence_group) FROM evidence_links e "
        "JOIN source_items s ON s.source_id = e.source_id "
        "WHERE e.pain_id = ? AND s.status = 'VERIFIED'",
        (pain_id,),
    ).fetchone()
    return int(row[0]) if row else 0


def count_distinct_authors(conn, pain_id: str) -> int:
    """Distinct author hashes behind a pain (person-level figure).

    Reported alongside the org count; used by the R05 gate (>= 2 distinct
    authors required) so one author filing in two repos cannot qualify
    alone. NOT used for E.
    """
    row = conn.execute(
        "SELECT COUNT(DISTINCT s.author_hash) FROM evidence_links e "
        "JOIN source_items s ON s.source_id = e.source_id "
        "WHERE e.pain_id = ? AND s.status = 'VERIFIED' AND s.author_hash IS NOT NULL",
        (pain_id,),
    ).fetchone()
    return int(row[0]) if row else 0


def independent_evidence_count(conn, pain_id: str) -> int:
    """Back-compat alias for count_independent_evidence()."""
    return count_independent_evidence(conn, pain_id)


def count_raw_evidence(conn, pain_id: str) -> int:
    """Raw unique evidence URLs linked to a pain (evidence_count semantics).

    Kept as a separate, clearly labelled field. Must never be used as the
    independence count for E, cap-59, PRD or MVP gates.
    """
    row = conn.execute(
        "SELECT COUNT(*) FROM evidence_links e JOIN source_items s "
        "ON s.source_id = e.source_id WHERE e.pain_id = ? AND s.status = 'VERIFIED'",
        (pain_id,),
    ).fetchone()
    return int(row[0]) if row else 0


def independent_organisations(conn, pain_id: str) -> int:
    """Distinct repo/context (organisation) keys behind a pain's evidence."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT e.independence_group) FROM evidence_links e "
        "JOIN source_items s ON s.source_id = e.source_id "
        "WHERE e.pain_id = ? AND s.status = 'VERIFIED'",
        (pain_id,),
    ).fetchone()
    return int(row[0]) if row else 0


def has_assessment(conn, pain_id: str) -> bool:
    """True if R2-03 assessed any evidence link of this pain.

    Missing evidence_assessment table (a DB built before R2-03) is treated
    as "not assessed" rather than an error, so old fixtures keep working.
    """
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM evidence_assessment WHERE pain_id = ?",
            (pain_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return False
    return bool(row and row[0])


def workaround_status(conn, pain_id: str) -> str:
    """Feasibility-evidence status of a pain's recorded workaround.

    'DOCUMENTED' only when the migration set it so (a real workaround text
    recorded). Anything else — NULL, empty, or a placeholder such as
    'see linked issues' — is 'UNKNOWN' and earns no F points. The raw
    current_workaround text is never rewritten; this reads the status
    column and falls back to deriving it from the raw text if the column
    is absent (a DB built before the R2-04 migration).
    """
    try:
        row = conn.execute(
            "SELECT current_workaround, workaround_status FROM pain_points "
            "WHERE pain_id = ?",
            (pain_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        row = conn.execute(
            "SELECT current_workaround FROM pain_points WHERE pain_id = ?",
            (pain_id,),
        ).fetchone()
        if not row:
            return "UNKNOWN"
        raw = (row[0] or "").strip()
        return "UNKNOWN" if not raw or raw.lower() in PLACEHOLDER_WORKAROUNDS else "DOCUMENTED"
    if not row:
        return "UNKNOWN"
    raw, status = row
    if status:
        return str(status)
    raw = (raw or "").strip()
    return "UNKNOWN" if not raw or raw.lower() in PLACEHOLDER_WORKAROUNDS else "DOCUMENTED"
    """Distinct repo/context (organisation) keys behind a pain's evidence."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT e.independence_group) FROM evidence_links e "
        "JOIN source_items s ON s.source_id = e.source_id "
        "WHERE e.pain_id = ? AND s.status = 'VERIFIED'",
        (pain_id,),
    ).fetchone()
    return int(row[0]) if row else 0


def cross_org_corroborated(conn, pain_id: str) -> bool:
    """True only if evidence comes from >= 2 distinct organisations/repos.

    One-repository evidence is never cross-org corroborated, however many
    authors or raw links it has.
    """
    return independent_organisations(conn, pain_id) >= 2


def _keywords(text: str, words: tuple[str, ...]) -> list[str]:
    return [w for w in words if w in text]


def score_components(conn, pain_id: str, job: str, blocker: str) -> dict:
    """Score one VERIFIED pain from the DB. Returns components + reasons.

    R2-04 evidence-bound rule (see module docstring):
    - E from DIRECT_SAME_PAIN orgs when the pain was R2-03-assessed,
      else from R03 org groups. G comes from competitor_checks rows:
      any UNKNOWN trail blocks G (0); >=2 real checks with 0 solves
      gives 10; exactly 1 real check gives 5.
    - F is 15 ONLY with a DOCUMENTED workaround; placeholder/NULL
      workarounds and paid-keyword mentions earn 0.
    - L is 0 without documented transfer/reuse evidence (none exists
      in this dataset). S is unchanged (keyword severity; residual
      limitation, see r2_04.md).
    Every S/F/L reason quotes this pain's own recorded text and the signals
    actually matched; unvalidated components are 0 and say so.
    """
    assessed = has_assessment(conn, pain_id)
    n_raw = count_raw_evidence(conn, pain_id)
    if assessed:
        direct = direct_only_counts(conn, pain_id)
        n_indep = direct["n_orgs"]
        n_authors = direct["n_authors"]
        n_direct = direct["n_direct"]
        n_orgs = direct["n_orgs"]
    else:
        n_indep = count_independent_evidence(conn, pain_id)
        n_authors = count_distinct_authors(conn, pain_id)
        n_direct = None
        n_orgs = independent_organisations(conn, pain_id)
    cross_org = n_orgs >= 2
    e = evidence_score(n_indep)
    text = f"{job} {blocker}".lower()
    blocker_quote = blocker[:80].replace("\n", " ")
    job_quote = job[:80].replace("\n", " ")
    sev_words = ("crash", "fails", "cannot", "broken", "wrong", "misclass",
                 "incorrect", "dropped", "loses", "lost", "silently")
    time_words = ("slow", "takes hours", "manual", "every time")
    matched_sev = _keywords(text, sev_words)
    matched_time = _keywords(text, time_words)
    if matched_sev:
        s, s_r = 20, f"blocker '{blocker_quote}' matches failure keywords {matched_sev}"
    elif matched_time:
        s, s_r = 10, f"blocker '{blocker_quote}' matches time-cost keywords {matched_time}"
    elif "feature request" in text or "missing" in text:
        s, s_r = 10, f"blocker '{blocker_quote}' is a missing capability, workaround may exist"
    else:
        s, s_r = 5, (f"no failure/time-cost keyword in recorded blocker "
                      f"'{blocker_quote}'; severity unproven — S capped at 5")
    w_status = workaround_status(conn, pain_id)
    row = conn.execute(
        "SELECT current_workaround FROM pain_points WHERE pain_id = ?", (pain_id,)
    ).fetchone()
    workaround = (row[0] or "").strip() if row else ""
    if w_status == "DOCUMENTED":
        f, f_r = 15, (f"documented workaround recorded ('{workaround[:60]}'); "
                      "feasibility evidenced by an existing workaround")
    elif workaround.lower() in PLACEHOLDER_WORKAROUNDS:
        f, f_r = 0, (f"recorded workaround is a placeholder ('{workaround[:60]}'), "
                      "not a workaround — feasibility UNKNOWN, F=0 (R2-04)")
    elif workaround:
        f, f_r = 0, ("workaround text present but status is UNKNOWN (not "
                      "verified as a real workaround) — feasibility UNKNOWN, F=0 (R2-04)")
    else:
        f, f_r = 0, ("no workaround recorded — feasibility UNKNOWN, F=0 (R2-04); "
                      "a paid/rate-limit keyword mention, if any, is not "
                      "feasibility evidence")
    n_checks = count_checks(conn, pain_id)
    n_unknown = unknown_check_count(conn, pain_id)
    n_real = n_checks - n_unknown
    solves = conn.execute(
        "SELECT COUNT(*) FROM competitor_checks WHERE pain_id=? AND does_solve=1",
        (pain_id,),
    ).fetchone()[0]
    if solves:
        g, g_r = 0, f"an alternative fully solves this pain ({solves} check(s) does_solve=1) — no gap"
    elif n_unknown > 0:
        g, g_r = 0, (f"{n_unknown} UNKNOWN competitor trail(s) block G — no positive "
                      f"points (R2-04); {n_real} real check(s) recorded")
    elif n_real >= 2:
        g, g_r = 10, f"checked {n_real} real alternatives, none fully solves (see competitor_checks)"
    elif n_real == 1:
        g, g_r = 5, "only 1 real competitor check recorded — partial, gate not met"
    else:
        g, g_r = 0, "UNKNOWN: no real competitor_checks rows (R04 pending)"
    l, l_r = 0, ("no transfer/reuse evidence in record — L=0 (UNKNOWN), never "
                 "a positive minimum without evidence (R2-04)")
    total, capped = total_score(e, s, f, g, l, n_indep)
    gate = ("cross-org corroborated" if cross_org
            else f"NOT cross-org corroborated ({n_orgs} org{'s' if n_orgs != 1 else ''})")
    if assessed:
        e_part = (f"E={e} ({n_indep} DIRECT orgs, {n_authors} DIRECT authors, "
                  f"{n_direct} DIRECT links; {n_raw} raw VERIFIED URLs)")
    else:
        e_part = (f"E={e} ({n_indep} indep orgs, {n_authors} distinct authors, "
                  f"{n_raw} raw URLs)")
    reason = (
        f"{e_part} "
        f"job='{job_quote}' "
        f"S={s} ({s_r}) F={f} ({f_r}) G={g} ({g_r}) L={l} ({l_r}) | {gate}"
        + (" CAP59" if capped else "")
    )
    return {
        "pain_id": pain_id, "n_independent": n_indep, "n_raw": n_raw,
        "n_direct": n_direct, "assessed": assessed,
        "n_authors": n_authors,
        "n_orgs": n_orgs, "cross_org": cross_org, "e": e, "s": s, "f": f,
        "g": g, "l": l, "total": total, "capped": capped, "reason": reason,
        "n_real_checks": n_real, "n_unknown_checks": n_unknown,
    }


def store_score(conn, pain_id: str, comp: dict) -> None:
    """Persist a computed score, retrying briefly on a locked DB (R02 may
    hold the writer). Raises the last error after retries."""
    last = None
    for _ in range(5):
        try:
            conn.execute(
                "UPDATE pain_points SET score=?, score_reason=?, "
                "independent_evidence_count=? WHERE pain_id=?",
                (comp["total"], comp["reason"], comp["n_independent"], pain_id),
            )
            return
        except sqlite3.OperationalError as exc:
            last = exc
            if "locked" not in str(exc).lower():
                raise
            import time

            time.sleep(5)
    raise last
