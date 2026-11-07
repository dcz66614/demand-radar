"""R05 gate runner (reproducible, deterministic).

Usage (from the rework1 root, venv active):
    python -m demand_radar score          # fresh reports/ranking.csv, exit 0
    python reports/rework1/run_gate_r05.py  # gate CSVs + mvp_selection.json

Writes:
- reports/rework1/ranking.csv (verbatim copy of fresh reports/ranking.csv)
- reports/rework1/qualifying_prds.csv / not_qualified.csv
- reports/mvp_selection.json (same shape as the original file)
Prints counts, qualified ids and the gate fingerprint. Exit 0.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from demand_radar import db as dbmod
from demand_radar.selection import (
    build_mvp_selection,
    evaluate_all,
    fingerprint,
    write_gate_csvs,
)

DB = ROOT / "data" / "demand_radar.sqlite"


def main() -> int:
    ranking_src = ROOT / "reports" / "ranking.csv"
    ranking_dst = ROOT / "reports" / "rework1" / "ranking.csv"
    if not ranking_src.exists():
        print("reports/ranking.csv missing — run `python -m demand_radar score` first",
              file=sys.stderr)
        return 2
    shutil.copyfile(ranking_src, ranking_dst)
    with dbmod.connect(DB) as conn:
        results = evaluate_all(conn)
        out = write_gate_csvs(conn, ROOT / "reports" / "rework1")
        selection = build_mvp_selection(results)
    (ROOT / "reports" / "mvp_selection.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ranking copied -> {ranking_dst}")
    print(f"qualified: {out['n_qualified']} {out['qualified_ids']}")
    print(f"not qualified: {out['n_not_qualified']}")
    print(f"fingerprint: {out['fingerprint']}")
    assert fingerprint(results) == out["fingerprint"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
