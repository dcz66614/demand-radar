"""R2-06: rebuild reports/mvp_selection.json in the REWORK2 shape.

Reads the live DB gate (evaluate_all, R2-04 evidence-bound scoring, gate
70 unchanged) and the preserved REWORK1 snapshot
(reports/rework2/mvp_selection_before_r2_06.json). Writes
reports/mvp_selection.json with explicit keys:

  prd_eligible                    — pains passing the CURRENT gate (0)
  mvp_built                       — the 2 prototypes that actually exist
  not_selected                    — pains failing the current gate (221)
  superseded_rework1_prd_eligible — the old 5, old scores preserved,
                                    with the R2-04 supersession reason

Idempotent: re-running on the new file reproduces it byte-identically
(the snapshot is the preserved source of the old 5, not the live file).
Does NOT touch reports/rework2/mvp_selection_r2_04.json or the R05
originals in reports/rework1/.

Usage: python reports/rework2/build_mvp_selection_r2_06.py
Exit 0 on success; asserts prd_eligible == [] and not_selected == 221.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from demand_radar import db as dbmod
from demand_radar.selection import build_mvp_selection, evaluate_all

SNAPSHOT = ROOT / "reports" / "rework2" / "mvp_selection_before_r2_06.json"
OUT = ROOT / "reports" / "mvp_selection.json"


def main() -> int:
    snap = json.loads(SNAPSHOT.read_text())
    old_five = snap["selected"]
    assert len(old_five) == 5, f"snapshot must hold the old 5, got {len(old_five)}"
    superseded = []
    for e in old_five:
        entry = dict(e)
        entry["reason"] = (
            "SUPERSEDED by R2-04 re-score: REWORK1 score was 70 under the old "
            "rule (F=15/L=5 unproven); under the R2-04 evidence-bound rule this "
            "pain scores below 70 — see reports/rework2/not_qualified_r2_04.csv "
            "and score_diff.csv. PRD file moved to reports/prds/superseded/."
        )
        superseded.append(entry)
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        results = evaluate_all(conn)
    doc = build_mvp_selection(results, superseded=superseded)
    doc["version"] = "REWORK2"
    doc["gate"] = (
        "R2-04 evidence-bound scoring; GATE_MIN_SCORE=70 unchanged; "
        "prd_eligible is PRD eligibility, NOT built MVPs; "
        "mvp_built prototypes do not offset eliminated PRDs (r2_05.md)"
    )
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    assert doc["prd_eligible"] == []
    assert len(doc["not_selected"]) == 221
    assert len(doc["superseded_rework1_prd_eligible"]) == 5
    assert [m["id"] for m in doc["mvp_built"]] == ["R1-A", "R1-B"]
    print(f"wrote {OUT}: prd_eligible 0, mvp_built 2, "
          f"not_selected 221, superseded_rework1_prd_eligible 5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
