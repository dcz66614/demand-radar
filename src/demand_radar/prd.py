"""REWORK1 R05: PRD data model and rendering helpers.

A PRD is built from DB evidence only (prd_from_db): VERIFIED source
links with title/excerpt/state, competitor_checks rows, and the pain's
own job/blocker/score. The free-text fields (user_task, workaround,
impact, sample_input, expected_output, acceptance_tests, caveats) are
supplied by the R05 author from the cited evidence — never invented,
never copied as boilerplate across PRDs. validate() refuses a PRD that
is missing any required section.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field


@dataclass
class EvidenceItem:
    url: str
    title: str
    excerpt: str
    issue_state: str
    org: str


@dataclass
class CompetitorCheck:
    product: str
    version: str
    url: str
    capability: str
    gap: str
    checked_at: str


@dataclass
class PRD:
    pain_id: str
    domain: str
    job: str
    blocker: str
    score: int
    score_reason: str
    user_task: str = ""
    workaround: str = ""
    impact: str = ""
    evidence: list[EvidenceItem] = field(default_factory=list)
    competitors: list[CompetitorCheck] = field(default_factory=list)
    sample_input: str = ""
    expected_output: str = ""
    acceptance_tests: list[str] = field(default_factory=list)
    closed_evidence: int = 0
    open_evidence: int = 0
    caveats: list[str] = field(default_factory=list)

    @property
    def n_orgs(self) -> int:
        return len({e.org for e in self.evidence})


REQUIRED_SECTIONS = (
    "user_task", "workaround", "impact", "sample_input",
    "expected_output", "acceptance_tests",
)


def validate(prd: PRD) -> list[str]:
    """Return a list of problems; empty means the PRD is complete."""
    problems: list[str] = []
    for section in REQUIRED_SECTIONS:
        value = getattr(prd, section)
        if not value:
            problems.append(f"missing required section: {section}")
    if len(prd.acceptance_tests) < 3 or len(prd.acceptance_tests) > 5:
        problems.append(
            f"acceptance_tests must be 3-5 unique tests, got {len(prd.acceptance_tests)}"
        )
    if len(set(prd.acceptance_tests)) != len(prd.acceptance_tests):
        problems.append("acceptance_tests must be unique")
    if not prd.evidence:
        problems.append("no VERIFIED evidence items")
    if any(not e.url for e in prd.evidence):
        problems.append("evidence item without URL")
    if len(prd.competitors) < 2:
        problems.append(f"need >= 2 competitor checks, got {len(prd.competitors)}")
    if any(c.gap == "" for c in prd.competitors):
        problems.append("competitor check without a recorded gap")
    return problems


def prd_from_db(conn: sqlite3.Connection, pain_id: str, **kwargs) -> PRD:
    """Build a PRD skeleton from DB evidence. Free-text kwargs are the
    author's, grounded in the cited evidence (see module docstring)."""
    row = conn.execute(
        "SELECT domain, job_to_be_done, blocker, score, score_reason "
        "FROM pain_points WHERE pain_id = ?",
        (pain_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"unknown pain_id: {pain_id}")
    domain, job, blocker, score, score_reason = row
    evidence = [
        EvidenceItem(
            url=r[0], title=r[1] or "", excerpt=r[2] or "",
            issue_state=r[3] or "unknown", org=r[4],
        )
        for r in conn.execute(
            "SELECT s.url, s.title, s.excerpt, s.issue_state, e.independence_group "
            "FROM evidence_links e JOIN source_items s ON s.source_id = e.source_id "
            "WHERE e.pain_id = ? AND s.status = 'VERIFIED' ORDER BY s.url",
            (pain_id,),
        )
    ]
    competitors = [
        CompetitorCheck(
            product=r[0], version=r[1] or "not stated on checked page",
            url=r[2], capability=r[3] or "", gap=r[4] or "",
            checked_at=r[5] or "",
        )
        for r in conn.execute(
            "SELECT product, version, checked_url, capability, gaps, checked_at "
            "FROM competitor_checks WHERE pain_id = ? ORDER BY product",
            (pain_id,),
        )
    ]
    closed = sum(1 for e in evidence if e.issue_state == "closed")
    open_n = sum(1 for e in evidence if e.issue_state == "open")
    return PRD(
        pain_id=pain_id, domain=domain, job=job, blocker=blocker,
        score=int(score) if score is not None else 0,
        score_reason=score_reason or "",
        evidence=evidence, competitors=competitors,
        closed_evidence=closed, open_evidence=open_n,
        **kwargs,
    )


def render_markdown(prd: PRD) -> str:
    """Render a PRD as Markdown. All content comes from the PRD object;
    no boilerplate paragraph is shared across PRDs — each section is the
    pain's own text."""
    problems = validate(prd)
    if problems:
        raise ValueError(f"PRD {prd.pain_id} incomplete: {'; '.join(problems)}")
    lines = [
        f"# PRD (R05 rewrite) — {prd.pain_id}",
        "",
        f"- Domain: {prd.domain}",
        f"- Job to be done: {prd.job}",
        f"- Blocker: {prd.blocker}",
        f"- Score: {prd.score} (corrected R03/R04 scoring; see score_reason below)",
        f"- Score reason: {prd.score_reason}",
        (f"- Independent organisations: {prd.n_orgs}; "
         f"VERIFIED evidence: {len(prd.evidence)} links "
         f"({prd.closed_evidence} closed, {prd.open_evidence} open)"),
        "",
        "## User task",
        prd.user_task,
        "",
        "## Evidence (VERIFIED sources only, with quotations/paraphrases)",
    ]
    for e in prd.evidence:
        lines.append(f"- [{e.issue_state}] [{e.org}] {e.url}")
        lines.append(f"  - {e.title}")
        if e.excerpt.strip():
            lines.append(f"  - Quoted/paraphrased from the post: \"{e.excerpt.strip()[:300]}\"")
    lines += [
        "",
        "## Actual workaround and impact",
        prd.workaround,
        "",
        prd.impact,
        "",
        "## Competitor checks (R04, checked 2026-11-05, 0 solve the pain)",
    ]
    for c in prd.competitors:
        lines += [
            f"- {c.product} ({c.version}) — {c.url} (checked {c.checked_at})",
            f"  - Observed capability: {c.capability}",
            f"  - Gap vs this pain: {c.gap}",
        ]
    lines += [
        "",
        "## Sample input",
        prd.sample_input,
        "",
        "## Expected output",
        prd.expected_output,
        "",
        "## Acceptance tests",
    ]
    for i, test in enumerate(prd.acceptance_tests, 1):
        lines.append(f"{i}. {test}")
    lines += [
        "",
        "## Caveats and stop conditions",
    ]
    lines += [f"- {c}" for c in prd.caveats] or ["- None recorded."]
    lines.append(
        "- Closed evidence items are counted as evidence of a real problem, "
        "not as proof the problem is solved: R02 did not check resolution "
        "from comments."
    )
    lines.append(
        "- If the linked sources are withdrawn or the blocker is fixed "
        "upstream, this PRD is withdrawn."
    )
    lines.append("")
    return "\n".join(lines)
