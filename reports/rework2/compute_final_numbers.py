"""R2-06: compute every number in reports/final_report_rework2.md from the
live DB / scripts — nothing hand-copied. Writes
reports/rework2/final_numbers_r2_06.json (the report cites it) and prints
a human-readable summary. Exit 0 on success.

Checks asserted here (fail loudly instead of writing a wrong report):
  - source_items 218 = 200 VERIFIED + 18 REJECTED
  - pain_points 221, max score 45, 0 pains >= 70
  - evidence_assessment 76 rows: 38 DIRECT / 10 ADJACENT / 5 DUPLICATE /
    23 OUT_OF_SCOPE / 0 UNKNOWN
  - competitor_checks 34 rows, 0 does_solve, 6 UNKNOWN trails
  - prd_cards 17 SUPERSEDED / 0 QUALIFIED, all md_paths exist
  - gate fingerprint equals the R2-04 fingerprint
  - the 5 R2-04 new scores in score_diff.csv equal the live DB scores
Usage: python reports/rework2/compute_final_numbers.py
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from demand_radar import db as dbmod
from demand_radar.selection import evaluate_all, fingerprint

OUT = ROOT / "reports" / "rework2" / "final_numbers_r2_06.json"
R204_FINGERPRINT = "3d26137fd5e36e53ed08db7fea14c65d823c31dac3870b0e1386d8fe262fafe6"


def main() -> int:
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        n = {}
        n["source_items_total"] = conn.execute(
            "SELECT COUNT(*) FROM source_items").fetchone()[0]
        n["source_verified"] = conn.execute(
            "SELECT COUNT(*) FROM source_items WHERE status='VERIFIED'").fetchone()[0]
        n["source_rejected"] = conn.execute(
            "SELECT COUNT(*) FROM source_items WHERE status='REJECTED'").fetchone()[0]
        n["source_by_domain"] = {
            f"{d}/{s}": c for d, s, c in conn.execute(
                "SELECT domain, status, COUNT(*) FROM source_items "
                "GROUP BY domain, status ORDER BY domain, status").fetchall()
        }
        n["pain_points_total"] = conn.execute(
            "SELECT COUNT(*) FROM pain_points").fetchone()[0]
        n["pain_by_domain"] = {
            d: c for d, c in conn.execute(
                "SELECT domain, COUNT(*) FROM pain_points GROUP BY domain "
                "ORDER BY domain").fetchall()
        }
        n["evidence_links_total"] = conn.execute(
            "SELECT COUNT(*) FROM evidence_links").fetchone()[0]
        n["evidence_review_status"] = {
            s: c for s, c in conn.execute(
                "SELECT review_status, COUNT(*) FROM evidence_links "
                "GROUP BY review_status").fetchall()
        }
        n["evidence_links_to_rejected_sources"] = conn.execute(
            "SELECT COUNT(*) FROM evidence_links e JOIN source_items s "
            "ON s.source_id=e.source_id WHERE s.status='REJECTED'").fetchone()[0]
        n["competitor_checks_total"] = conn.execute(
            "SELECT COUNT(*) FROM competitor_checks").fetchone()[0]
        n["competitor_does_solve"] = conn.execute(
            "SELECT COUNT(*) FROM competitor_checks WHERE does_solve=1").fetchone()[0]
        n["competitor_unknown_trails"] = conn.execute(
            "SELECT COUNT(*) FROM competitor_checks "
            "WHERE gaps LIKE 'UNKNOWN:%'").fetchone()[0]
        n["prd_cards"] = {
            s: c for s, c in conn.execute(
                "SELECT status, COUNT(*) FROM prd_cards GROUP BY status").fetchall()
        }
        n["run_events"] = conn.execute(
            "SELECT COUNT(*) FROM run_events").fetchone()[0]
        n["problem_signatures"] = conn.execute(
            "SELECT COUNT(*) FROM problem_signatures").fetchone()[0]
        n["evidence_assessment"] = {
            c: k for c, k in conn.execute(
                "SELECT classification, COUNT(*) FROM evidence_assessment "
                "GROUP BY classification").fetchall()
        }
        n["workaround_status"] = {
            s: c for s, c in conn.execute(
                "SELECT workaround_status, COUNT(*) FROM pain_points "
                "GROUP BY workaround_status").fetchall()
        }
        n["max_score"] = conn.execute(
            "SELECT MAX(score) FROM pain_points").fetchone()[0]
        n["n_score_ge_70"] = conn.execute(
            "SELECT COUNT(*) FROM pain_points WHERE score>=70").fetchone()[0]
        n["score_distribution"] = {
            str(s): c for s, c in conn.execute(
                "SELECT score, COUNT(*) FROM pain_points "
                "GROUP BY score ORDER BY score DESC").fetchall()
        }
        n["db_integrity"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
        results = evaluate_all(conn)
        n["gate_qualified"] = sum(1 for r in results if r["qualified"])
        n["gate_not_qualified"] = sum(1 for r in results if not r["qualified"])
        n["gate_fingerprint"] = fingerprint(results)
        n["top_scores"] = [
            {"pain_id": r["pain_id"], "score": r["score"],
             "failure_reason": r["failure_reason"]}
            for r in sorted(results, key=lambda x: (-x["score"], x["pain_id"]))[:5]
        ]
    # R2-04 diff CSV must agree with the live DB scores.
    diff = list(csv.DictReader(
        (ROOT / "reports" / "rework2" / "score_diff.csv").read_text().splitlines()))
    n["score_diff_rows"] = len(diff)
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        for row in diff:
            live = conn.execute(
                "SELECT score FROM pain_points WHERE pain_id=?",
                (row["pain_id"],)).fetchone()[0]
            assert int(row["new_score"]) == live, row["pain_id"]
    # DIRECT links per assessed theme, from the assessment CSV.
    assess = list(csv.DictReader(
        (ROOT / "reports" / "rework2" / "evidence_assessment.csv")
        .read_text().splitlines()))
    n["evidence_assessment_rows"] = len(assess)
    n["direct_links_by_theme"] = {}
    for row in assess:
        if row["classification"] == "DIRECT_SAME_PAIN":
            n["direct_links_by_theme"].setdefault(row["pain_id"], []).append(
                row["source_url"])
    # prd_cards md_paths must all exist on disk.
    with dbmod.connect(ROOT / "data" / "demand_radar.sqlite") as conn:
        missing = [p for (p,) in conn.execute(
            "SELECT md_path FROM prd_cards") if not (ROOT / p).exists()]
    n["prd_cards_md_missing"] = len(missing)

    assert n["source_items_total"] == 218
    assert (n["source_verified"], n["source_rejected"]) == (200, 18)
    assert n["pain_points_total"] == 221
    assert n["max_score"] == 45 and n["n_score_ge_70"] == 0
    assert n["evidence_assessment"] == {
        "ADJACENT_CONTEXT": 10, "DIRECT_SAME_PAIN": 38,
        "DUPLICATE": 5, "OUT_OF_SCOPE": 23}, n["evidence_assessment"]
    assert sum(n["evidence_assessment"].values()) == 76
    assert n["competitor_checks_total"] == 34
    assert n["competitor_does_solve"] == 0
    assert n["competitor_unknown_trails"] == 6
    assert n["prd_cards"] == {"SUPERSEDED": 17}
    assert n["prd_cards_md_missing"] == 0
    assert n["gate_qualified"] == 0 and n["gate_not_qualified"] == 221
    assert n["gate_fingerprint"] == R204_FINGERPRINT
    assert n["db_integrity"] == "ok"
    OUT.write_text(json.dumps(n, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(n, indent=2, ensure_ascii=False))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
