"""Fix the 3 substantive R07 findings (reproducible, idempotent).
Run: python reports/rework1/fix_r07_findings.py  (from the project root)
1. prd_cards: 5 qualifying pains -> QUALIFIED with real md_path to the
   rewritten PRD; the other 12 -> SUPERSEDED with md_path to superseded/.
2. evidence_links.review_status: REJECTED where the source is REJECTED,
   VERIFIED where the source is VERIFIED (was stale VERIFIED for 13 links).
3. run_events: populate from reports/rework1/decision_log.jsonl (the table
   had 0 rows; the jsonl trail already existed).
Exit 0 on success; asserts 0 stale rows remain.
"""
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "demand_radar.sqlite"


def main() -> int:
    qual = {r["pain_id"] for r in csv.DictReader(
        (ROOT / "reports/rework1/qualifying_prds.csv").read_text().splitlines())}
    notq = {r["pain_id"]: r["failure_reason"] for r in csv.DictReader(
        (ROOT / "reports/rework1/not_qualified.csv").read_text().splitlines())}
    con = sqlite3.connect(DB)
    for prd_id, pain_id, md_path in con.execute(
            "SELECT prd_id, pain_id, md_path FROM prd_cards").fetchall():
        if pain_id in qual:
            con.execute(
                "UPDATE prd_cards SET status='QUALIFIED', template_id='R1', "
                "md_path=?, gate_reason=? WHERE prd_id=?",
                (f"reports/prds/PRD_{pain_id}_r1.md",
                 ("gate PASS: score>=70, >=2 orgs, >=2 authors, "
                 ">=2 competitor checks, 0 solves"), prd_id))
        else:
            con.execute(
                "UPDATE prd_cards SET status='SUPERSEDED', template_id='TBD', "
                "md_path=?, gate_reason=? WHERE prd_id=?",
                (f"reports/prds/superseded/{md_path.split('/')[-1]}",
                 f"not qualified: {notq.get(pain_id, 'no gate record')}", prd_id))
    con.execute(
        "UPDATE evidence_links SET review_status='REJECTED' WHERE source_id "
        "IN (SELECT source_id FROM source_items WHERE status='REJECTED')")
    con.execute(
        "UPDATE evidence_links SET review_status='VERIFIED' WHERE source_id "
        "IN (SELECT source_id FROM source_items WHERE status='VERIFIED')")
    # run_events from the decision log (idempotent by event_id).
    n_events = 0
    for i, line in enumerate(
            (ROOT / "reports/rework1/decision_log.jsonl").read_text().splitlines()):
        d = json.loads(line)
        con.execute(
            "INSERT OR IGNORE INTO run_events "
            "(event_id, stage_id, agent_role, event_type, detail_json, event_at) "
            "VALUES (?, ?, 'muse', 'stage_result', ?, ?)",
            (f"r07fix-{i:04d}", d.get("stage", "unknown"),
             json.dumps(d, ensure_ascii=False), d.get("ts", "")))
        n_events += 1
    con.commit()
    stale = con.execute(
        "SELECT COUNT(*) FROM evidence_links e JOIN source_items s "
        "ON s.source_id=e.source_id WHERE "
        "(s.status='REJECTED' AND e.review_status!='REJECTED') OR "
        "(s.status='VERIFIED' AND e.review_status!='VERIFIED')").fetchone()[0]
    assert stale == 0, f"{stale} stale evidence review_status rows remain"
    assert all(Path(r[0]).exists() for r in con.execute(
        "SELECT md_path FROM prd_cards").fetchall()), "prd_cards md_path missing"
    print(f"prd_cards: {dict(con.execute('SELECT status, COUNT(*) FROM prd_cards GROUP BY status').fetchall())}")
    print(f"evidence review_status: {dict(con.execute('SELECT review_status, COUNT(*) FROM evidence_links GROUP BY review_status').fetchall())}")
    print(f"run_events rows: {con.execute('SELECT COUNT(*) FROM run_events').fetchone()[0]} (from {n_events} log lines)")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
