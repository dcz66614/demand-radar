"""R2-04 score diff builder (idempotent).

Reads the pre-R2-04 snapshot (reports/rework2/score_old_snapshot.csv,
taken before any R2-04 code ran) and the live DB after the R2-04 score
re-run, and writes reports/rework2/score_diff.csv: old score + E/S/F/G/L
breakdown (parsed from the old score_reason), new score + breakdown
(recomputed live via score_components and asserted equal to the stored
pain_points.score), DIRECT-only counts, cross-org/author counts, real
vs UNKNOWN competitor checks, and the excluded adjacent evidence per
candidate (with a per-classification breakdown).

Usage (from the rework2 root, venv active; AFTER `python -m demand_radar
score` with the R2-04 rule):
    python reports/rework2/build_score_diff_r2_04.py
Exit 0. Idempotent: re-running rewrites identical rows.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from demand_radar import db as dbmod
from demand_radar.competitors import real_check_count, unknown_check_count
from demand_radar.evidence_assessment import assessment_counts, direct_only_counts
from demand_radar.score import count_raw_evidence, score_components

DB = ROOT / "data" / "demand_radar.sqlite"
CANDIDATES = [
    "0b7adcf63ec0f2075fab",
    "4bb734fac7245033d327",
    "6513d051954cbe1b5027",
    "cd021eac3c93ed0d2de1",
    "e3091fb34139fdf57dbd",
]

FIELDS = [
    "pain_id", "domain",
    "old_score", "old_e", "old_s", "old_f", "old_g", "old_l",
    "new_score", "new_e", "new_s", "new_f", "new_g", "new_l",
    "direct_count", "direct_orgs", "direct_authors", "raw_verified_urls",
    "real_competitor_checks", "unknown_competitor_checks",
    "excluded_adjacent_evidence", "excluded_detail",
]


def _parse_old(reason: str) -> dict:
    found = dict(re.findall(r"([ESFGL])=(\d+)", reason))
    assert set(found) == {"E", "S", "F", "G", "L"}, f"unparsable old reason: {reason[:120]}"
    return {k.lower(): int(v) for k, v in found.items()}


def main() -> int:
    old_rows = {
        r["pain_id"]: r
        for r in csv.DictReader(
            (ROOT / "reports" / "rework2" / "score_old_snapshot.csv").read_text().splitlines()
        )
    }
    out = []
    with dbmod.connect(DB) as conn:
        for pid in CANDIDATES:
            old = old_rows[pid]
            ob = _parse_old(old["old_score_reason"])
            domain, job, blocker, stored = conn.execute(
                "SELECT domain, job_to_be_done, blocker, score FROM pain_points "
                "WHERE pain_id = ?",
                (pid,),
            ).fetchone()
            comp = score_components(conn, pid, job, blocker)
            assert comp["total"] == stored, f"{pid}: live {comp['total']} != stored {stored}"
            direct = direct_only_counts(conn, pid)
            counts = assessment_counts(conn, pid)
            excluded = sum(
                v for k, v in counts.items() if k != "DIRECT_SAME_PAIN"
            )
            detail = "; ".join(
                f"{k}={v}" for k, v in sorted(counts.items()) if k != "DIRECT_SAME_PAIN"
            )
            out.append({
                "pain_id": pid, "domain": domain,
                "old_score": old["old_score"],
                "old_e": ob["e"], "old_s": ob["s"], "old_f": ob["f"],
                "old_g": ob["g"], "old_l": ob["l"],
                "new_score": comp["total"],
                "new_e": comp["e"], "new_s": comp["s"], "new_f": comp["f"],
                "new_g": comp["g"], "new_l": comp["l"],
                "direct_count": direct["n_direct"],
                "direct_orgs": direct["n_orgs"],
                "direct_authors": direct["n_authors"],
                "raw_verified_urls": count_raw_evidence(conn, pid),
                "real_competitor_checks": real_check_count(conn, pid),
                "unknown_competitor_checks": unknown_check_count(conn, pid),
                "excluded_adjacent_evidence": excluded,
                "excluded_detail": detail,
            })
            print(f"{pid[:6]} {domain}: old {old['old_score']} "
                  f"(E{ob['e']} S{ob['s']} F{ob['f']} G{ob['g']} L{ob['l']}) -> "
                  f"new {comp['total']} "
                  f"(E{comp['e']} S{comp['s']} F{comp['f']} G{comp['g']} L{comp['l']}), "
                  f"DIRECT {direct['n_direct']}/{direct['n_orgs']} orgs/"
                  f"{direct['n_authors']} authors, excluded {excluded} ({detail})")
    with open(ROOT / "reports" / "rework2" / "score_diff.csv", "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print(f"wrote reports/rework2/score_diff.csv ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
