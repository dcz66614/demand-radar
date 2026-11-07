"""R2-06: mvp_selection.json must distinguish PRD eligibility from built MVPs.

The old file's "selected" (5 entries) was the REWORK1 PRD-eligible pool,
not built MVPs — and under the R2-04 re-score all 5 fail the gate. The new
shape has explicit "prd_eligible" (current gate, 0 entries), "mvp_built"
(the 2 prototypes that actually exist, PARTIALLY_REAL_WORLD_VALIDATED),
"not_selected" (221, current gate) and "superseded_rework1_prd_eligible"
(the old 5, preserved with their old scores). These tests fail on the old
file (no prd_eligible/mvp_built keys, 5 "selected").
"""
import json
from pathlib import Path

from demand_radar import db as dbmod
from demand_radar.selection import MVP_BUILT, build_mvp_selection, evaluate_all

ROOT = Path(__file__).resolve().parents[1]
OLD_FIVE = {
    "0b7adcf63ec0f2075fab",
    "4bb734fac7245033d327",
    "6513d051954cbe1b5027",
    "cd021eac3c93ed0d2de1",
    "e3091fb34139fdf57dbd",
}


def _live_selection():
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        return build_mvp_selection(evaluate_all(conn))


def test_prd_eligible_is_empty_under_r2_04_gate():
    sel = _live_selection()
    assert sel["prd_eligible"] == []
    assert len(sel["not_selected"]) == 221


def test_mvp_built_is_two_prototypes_not_products():
    sel = _live_selection()
    assert [m["id"] for m in sel["mvp_built"]] == ["R1-A", "R1-B"]
    for m in sel["mvp_built"]:
        assert m["positioning"] == "PARTIALLY_REAL_WORLD_VALIDATED"
        assert (ROOT / m["path"]).is_dir()
        assert m["not_real_world_validated"], "must state what is NOT validated"
    assert sel["mvp_built"] == [dict(m) for m in MVP_BUILT]


def test_built_prototypes_do_not_make_their_pains_eligible():
    sel = _live_selection()
    built_pains = {m["pain_id"] for m in sel["mvp_built"]}
    eligible_pains = {e["pain_id"] for e in sel["prd_eligible"]}
    assert built_pains == {"6513d051954cbe1b5027", "4bb734fac7245033d327"}
    assert eligible_pains == set()
    assert built_pains.isdisjoint(eligible_pains)
    # Both built pains are in not_selected with a score failure reason.
    by_id = {e["pain_id"]: e for e in sel["not_selected"]}
    for pid in built_pains:
        assert "score" in by_id[pid]["reason"] and "< 70" in by_id[pid]["reason"]


def test_file_agrees_with_live_gate_and_records_superseded_five():
    doc = json.loads((ROOT / "reports" / "mvp_selection.json").read_text())
    assert doc["prd_eligible"] == []
    assert len(doc["not_selected"]) == 221
    assert [m["id"] for m in doc["mvp_built"]] == ["R1-A", "R1-B"]
    sup = doc["superseded_rework1_prd_eligible"]
    assert {e["pain_id"] for e in sup} == OLD_FIVE
    assert all(e["score"] == 70 for e in sup), "old REWORK1 scores preserved"
    assert all("R2-04" in e["reason"] and "superseded" in e["reason"].lower()
               for e in sup)
    # The preserved snapshot of the pre-R2-06 file must still exist.
    snap = json.loads(
        (ROOT / "reports" / "rework2" / "mvp_selection_before_r2_06.json").read_text())
    assert {e["pain_id"] for e in snap["selected"]} == OLD_FIVE
