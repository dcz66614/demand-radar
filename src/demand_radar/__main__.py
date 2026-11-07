"""CLI: python -m demand_radar init | ingest --file | report --stage | score | export --format csv/json

REWORK1 (R01): `score` is a real orchestrated command — it recomputes every
VERIFIED pain from the DB (E from distinct independence groups, G from
competitor_checks, UNKNOWN=0 when none) and writes reports/ranking.csv.
`report --stage` validates the stage; unknown stages exit non-zero.
`export` is VERIFIED-only by default; use --all to include REJECTED rows.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "demand_radar.sqlite"

from . import db as dbmod
from .ingest import ingest_file
from .score import score_components, store_score

STAGES = {
    "pilot": "P00-P03 pilot: 30 real candidates, first checkpoint",
    "p04": "P04 expansion: ~240 candidates",
    "p05": "P05 review / dedupe / competitor checks",
    "final": "P10 final QA: full funnel, PRDs, MVPs",
}


def run_score(db_path=None, root=None) -> int:
    """Recompute scores for all VERIFIED pains and write ranking.csv.
    Deterministic: sort by total desc, independent desc, pain_id asc."""
    if db_path is None:
        db_path = DB
    if root is None:
        root = ROOT
    if not Path(db_path).exists():
        print("db missing, run init first", file=sys.stderr)
        return 2
    with dbmod.connect(db_path) as conn:
        # R02 runs in parallel and may hold the writer briefly; wait instead
        # of failing immediately on a locked DB.
        conn.execute("PRAGMA busy_timeout = 30000")
        pains = conn.execute(
            "SELECT pain_id, domain, job_to_be_done, blocker FROM pain_points "
            "WHERE status='VERIFIED' ORDER BY pain_id"
        ).fetchall()
        rows = []
        for pid, domain, job, blocker in pains:
            comp = score_components(conn, pid, job, blocker)
            # R03: store independent count in pain_points; retry on locked DB
            # (R02 agent may hold the writer briefly).
            store_score(conn, pid, comp)
            urls = [
                r[0] for r in conn.execute(
                    "SELECT s.url FROM evidence_links e JOIN source_items s "
                    "ON s.source_id=e.source_id WHERE e.pain_id=? AND s.status='VERIFIED' ORDER BY s.url",
                    (pid,),
                )
            ]
            rows.append((pid, domain, job, comp["n_raw"], comp["n_independent"],
                         comp["n_orgs"], comp["total"],
                         comp["capped"], comp["reason"], urls))
        conn.commit()
    rows.sort(key=lambda r: (-r[6], -r[4], r[0]))
    out = Path(root) / "reports" / "ranking.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pain_id", "domain", "job", "evidence_count_raw_urls",
                    "independent_evidence_count", "independent_organisations",
                    "total", "cap_applied", "score_reason", "evidence_urls"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                        " | ".join(r[9])])
    print(f"scored {len(rows)} pains -> {out}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="demand_radar")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    pi = sub.add_parser("ingest")
    pi.add_argument("--file", required=True)
    pr = sub.add_parser("report")
    pr.add_argument("--stage", default="pilot", choices=list(STAGES))
    sub.add_parser("score")
    pe = sub.add_parser("export")
    pe.add_argument("--format", choices=["csv", "json"], default="csv")
    pe.add_argument("--all", action="store_true",
                    help="include REJECTED source rows; default is VERIFIED-only")
    args = p.parse_args(argv)

    if args.cmd == "init":
        dbmod.init_db(DB)
        print(f"created {DB}")
        return 0
    if args.cmd == "ingest":
        if not DB.exists():
            print("db missing, run init first", file=sys.stderr)
            return 2
        n = ingest_file(DB, args.file)
        print(f"ingested {n} new source_items from {args.file}")
        return 0
    if args.cmd == "report":
        if not DB.exists():
            print("db missing", file=sys.stderr)
            return 2
        with dbmod.connect(DB) as conn:
            counts = dbmod.counts(conn)
        counts["stage"] = args.cmd and args.stage
        counts["stage_meaning"] = STAGES[args.stage]
        print(json.dumps(counts, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "score":
        return run_score()
    if args.cmd == "export":
        if not DB.exists():
            print("db missing", file=sys.stderr)
            return 2
        outdir = ROOT / "data" / "exports"
        outdir.mkdir(parents=True, exist_ok=True)
        where = "" if args.all else "WHERE status='VERIFIED'"
        with dbmod.connect(DB) as conn:
            rows = conn.execute(
                "SELECT platform, external_id, url, title, excerpt, published_at, "
                f"fetched_at, domain, source_type, status FROM source_items {where} "
                "ORDER BY domain, published_at"
            ).fetchall()
            cols = ["platform", "external_id", "url", "title", "excerpt",
                    "published_at", "fetched_at", "domain", "source_type", "status"]
        if args.format == "csv":
            path = outdir / "source_items.csv"
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(rows)
        else:
            path = outdir / "source_items.json"
            path.write_text(json.dumps([dict(zip(cols, r)) for r in rows],
                                       ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"exported {len(rows)} rows to {path}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
