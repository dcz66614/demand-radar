"""R2-04 gate runner (reproducible, deterministic).

Same gate as reports/rework1/run_gate_r05.py (R05), but with the R2-04
rule: DIRECT-only evidence counts for R2-03-assessed pains, evidence-bound
F/L, UNKNOWN competitor trails blocking G and the gate. The 70 gate is
NOT lowered.

Writes ONLY under reports/rework2/ — the R05 originals in
reports/rework1/ and reports/mvp_selection.json are untouched:
- reports/rework2/ranking_r2_04.csv (verbatim copy of fresh reports/ranking.csv)
- reports/rework2/qualifying_prds_r2_04.csv / not_qualified_r2_04.csv
- reports/rework2/mvp_selection_r2_04.json

Usage (from the rework2 root, venv active; AFTER `python -m demand_radar score`):
    python reports/rework2/run_gate_r2_04.py
Prints counts, qualified ids and the gate fingerprint. Exit 0.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from demand_radar import db as dbmod
from demand_radar.selection import build_mvp_selection, evaluate_all, fingerprint

DB = ROOT / "data" / "demand_radar.sqlite"
OUTDIR = ROOT / "reports" / "rework2"

FIELDS = [
    "pain_id", "domain", "job", "score", "n_orgs", "n_authors",
    "n_raw_verified", "rejected_links_excluded", "n_checks", "n_solves",
    "n_unknown_checks", "closed_evidence", "open_evidence",
    "qualified", "failure_reason",
]


def main() -> int:
    ranking_src = ROOT / "reports" / "ranking.csv"
    ranking_dst = OUTDIR / "ranking_r2_04.csv"
    if not ranking_src.exists():
        print("reports/ranking.csv missing — run `python -m demand_radar score` first",
              file=sys.stderr)
        return 2
    shutil.copyfile(ranking_src, ranking_dst)
    with dbmod.connect(DB) as conn:
        results = evaluate_all(conn)
        qualified = [r for r in results if r["qualified"]]
        not_qualified = [r for r in results if not r["qualified"]]
        for name, rows in (("qualifying_prds_r2_04.csv", qualified),
                           ("not_qualified_r2_04.csv", not_qualified)):
            with open(OUTDIR / name, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
        selection = build_mvp_selection(results)
    (OUTDIR / "mvp_selection_r2_04.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ranking copied -> {ranking_dst}")
    print(f"qualified: {len(qualified)} {[r['pain_id'] for r in qualified]}")
    print(f"not qualified: {len(not_qualified)}")
    print(f"fingerprint: {fingerprint(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
