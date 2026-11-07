"""R2-04 independent re-derivation of the 5 new scores.

Deliberately does NOT import demand_radar.score: it recomputes each
candidate's score from the raw inputs — reports/rework2/
evidence_assessment.csv (R2-03 classifications), the DB's evidence_links
/ source_items tables (for independence groups and authors), the DB's
pain_points (job/blocker/workaround_status), and reports/rework2/
competitor_checks_r2_04.jsonl — using a plain re-implementation of the
documented R2-04 rule. It then compares the result with the stored
pain_points.score (written by `python -m demand_radar score`) and with
reports/rework2/score_diff.csv.

Rule re-implemented here (must match src/demand_radar/score.py):
- E: 0/10/15/20/25/30 for 0/1/2/3/4/5+ DISTINCT orgs among DIRECT links.
- S: 20 if the blocker matches a failure keyword, 10 for time-cost or
  missing-capability wording, else 5.
- F: 15 only if workaround_status = 'DOCUMENTED', else 0.
- G: 0 if any check does_solve=1; 0 if any UNKNOWN trail (gaps starting
  'UNKNOWN:'); 10 if >=2 real checks; 5 if exactly 1; else 0.
- L: 0 (no documented reuse evidence exists).
- Cap at 59 if DIRECT orgs < 2 and total > 59.

Usage (from the rework2 root): python reports/rework2/rederive_scores_r2_04.py
Exit 0 iff all 5 re-derived scores match the stored scores and the diff CSV.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "demand_radar.sqlite"

CANDIDATES = [
    "0b7adcf63ec0f2075fab",
    "4bb734fac7245033d327",
    "6513d051954cbe1b5027",
    "cd021eac3c93ed0d2de1",
    "e3091fb34139fdf57dbd",
]

SEV_WORDS = ("crash", "fails", "cannot", "broken", "wrong", "misclass",
             "incorrect", "dropped", "loses", "lost", "silently")
TIME_WORDS = ("slow", "takes hours", "manual", "every time")


def e_map(n: int) -> int:
    return {0: 0, 1: 10, 2: 15, 3: 20, 4: 25}.get(n, 30) if n < 5 else 30


def main() -> int:
    direct_urls = {}
    for row in csv.DictReader(
            (ROOT / "reports" / "rework2" / "evidence_assessment.csv").read_text().splitlines()):
        if row["classification"] == "DIRECT_SAME_PAIN":
            direct_urls.setdefault(row["pain_id"], set()).add(row["source_url"])
    checks = {}
    for line in (ROOT / "reports" / "rework2" / "competitor_checks_r2_04.jsonl").read_text().splitlines():
        c = json.loads(line)
        checks.setdefault(c["pain_id"], []).append(c)
    diff = {
        r["pain_id"]: r
        for r in csv.DictReader(
            (ROOT / "reports" / "rework2" / "score_diff.csv").read_text().splitlines())
    }
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    ok = True
    for pid in CANDIDATES:
        job, blocker, status, stored = con.execute(
            "SELECT job_to_be_done, blocker, workaround_status, score "
            "FROM pain_points WHERE pain_id = ?", (pid,)
        ).fetchone()
        orgs, authors = set(), set()
        for (url,) in [(u,) for u in sorted(direct_urls.get(pid, ()))]:
            row = con.execute(
                "SELECT el.independence_group, s.author_hash FROM evidence_links el "
                "JOIN source_items s ON s.source_id = el.source_id "
                "WHERE s.url = ? AND el.pain_id = ?", (url, pid),
            ).fetchone()
            assert row is not None, f"{pid}: DIRECT url not in evidence_links: {url}"
            orgs.add(row[0])
            if row[1]:
                authors.add(row[1])
        e = e_map(len(orgs))
        text = f"{job} {blocker}".lower()
        if any(w in text for w in SEV_WORDS):
            s = 20
        elif any(w in text for w in TIME_WORDS) or "feature request" in text or "missing" in text:
            s = 10
        else:
            s = 5
        f = 15 if status == "DOCUMENTED" else 0
        rows = checks.get(pid, [])
        unknown = sum(1 for c in rows if (c.get("gaps") or "").startswith("UNKNOWN:"))
        real = len(rows) - unknown
        solves = sum(1 for c in rows if c.get("does_solve") == 1)
        if solves or unknown:
            g = 0
        elif real >= 2:
            g = 10
        elif real == 1:
            g = 5
        else:
            g = 0
        total = e + s + f + g + 0
        if len(orgs) < 2 and total > 59:
            total = 59
        match_stored = total == stored
        match_diff = int(diff[pid]["new_score"]) == total
        match_parts = (int(diff[pid]["new_e"]) == e and int(diff[pid]["new_s"]) == s
                       and int(diff[pid]["new_f"]) == f and int(diff[pid]["new_g"]) == g
                       and int(diff[pid]["new_l"]) == 0
                       and int(diff[pid]["direct_count"]) == len(direct_urls.get(pid, ()))
                       and int(diff[pid]["direct_orgs"]) == len(orgs)
                       and int(diff[pid]["direct_authors"]) == len(authors))
        status_line = "PASS" if (match_stored and match_diff and match_parts) else "FAIL"
        if status_line == "FAIL":
            ok = False
        print(f"{pid[:6]}: re-derived E{e} S{s} F{f} G{g} L0 = {total} "
              f"(DIRECT {len(direct_urls.get(pid, ()))} links, {len(orgs)} orgs, "
              f"{len(authors)} authors, {real} real / {unknown} UNKNOWN checks) "
              f"| stored {stored} | diff {diff[pid]['new_score']} -> {status_line}")
    print("RE-DERIVATION:", "ALL 5 MATCH" if ok else "MISMATCH — see FAIL lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
