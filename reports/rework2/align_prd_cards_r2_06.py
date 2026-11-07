"""R2-06: align prd_cards with the R2-04 gate (brief forced test #4).

REWORK1's fix_r07_findings.py marked 5 PRDs QUALIFIED under the R05 gate.
The R2-04 re-score (evidence-bound F/L/G, DIRECT-only E) fails all 5, so
the table now contradicts the final report if left as-is. This script:

  1. moves the 5 REWORK1 PRD files reports/prds/PRD_<id>_r1.md into
     reports/prds/superseded/ (same filenames; the old 17 live there as
     PRD_<id>.md, so no clash — files are kept, not deleted);
  2. sets all 17 prd_cards rows to SUPERSEDED, md_path pointing at the
     file's real location, gate_reason = the R2-04 failure reason from
     reports/rework2/not_qualified_r2_04.csv for the 5 (the other 12 keep
     their R05 gate_reason).

Idempotent: re-running finds the files already moved and the rows already
SUPERSEDED, and asserts the end state (0 QUALIFIED, 17 SUPERSEDED, all
md_paths exist). Does NOT touch reports/rework1/ originals or R2-03/R2-04
data. The R07 test test_prd_cards_agree_with_gate was updated in R2-06
to check against the R2-04 gate file instead of the R05 one.

Usage: python reports/rework2/align_prd_cards_r2_06.py
Exit 0 on success.
"""
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

DB = ROOT / "data" / "demand_radar.sqlite"
PRDS = ROOT / "reports" / "prds"
SUPERSEDED_DIR = PRDS / "superseded"
GATE_CSV = ROOT / "reports" / "rework2" / "not_qualified_r2_04.csv"


def main() -> int:
    reasons = {
        r["pain_id"]: r["failure_reason"]
        for r in csv.DictReader(GATE_CSV.read_text().splitlines())
    }
    con = sqlite3.connect(DB)
    moved = 0
    for prd_id, pain_id, status, md_path in con.execute(
            "SELECT prd_id, pain_id, status, md_path FROM prd_cards").fetchall():
        src = ROOT / md_path
        if status == "QUALIFIED":
            # Move the live PRD file into superseded/ (keep filename).
            dst = SUPERSEDED_DIR / src.name
            assert src.exists(), f"QUALIFIED card file missing: {src}"
            if not dst.exists():
                src.rename(dst)
                moved += 1
            new_path = f"reports/prds/superseded/{src.name}"
            reason = reasons.get(pain_id, "")
            assert reason, f"no R2-04 failure reason for {pain_id}"
            con.execute(
                "UPDATE prd_cards SET status='SUPERSEDED', md_path=?, "
                "gate_reason=? WHERE prd_id=?",
                (new_path,
                 f"R2-04 re-score: {reason} — see reports/rework2/r2_04.md",
                 prd_id))
        else:
            assert (ROOT / md_path).exists(), f"md_path missing: {md_path}"
    con.commit()
    counts = dict(con.execute(
        "SELECT status, COUNT(*) FROM prd_cards GROUP BY status").fetchall())
    assert counts == {"SUPERSEDED": 17}, f"unexpected prd_cards: {counts}"
    stale = con.execute(
        "SELECT COUNT(*) FROM prd_cards WHERE md_path NOT LIKE "
        "'reports/prds/superseded/%'").fetchone()[0]
    assert stale == 0
    print(f"prd_cards: {counts} (moved {moved} PRD files to superseded/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
