# Demand Radar — STATUS

Standalone project. No P number, no relation to the P series.
Storage after completion: separate Google Drive folder (not `agent project auto`).
Execution: Muse itself, no free-model quota used.

## P00 — Isolation environment & capability check
STATUS: DONE
- Root: $HOME/projects/demand-radar, structure per Execution Plan §2.2
- Python 3.12.3, git 2.43.0, venv + deps installed, pytest 9.2.0, ruff 0.17.3
- GitHub API 200, HN API 200
- Artifacts: reports/environment.md, requirements-lock.txt, config/limits.yaml
- execution_surface: Muse personal Agent VM

## P01 — Model / DB / CLI skeleton
STATUS: IN_PROGRESS

## P01 — Model / DB / CLI skeleton
STATUS: DONE
- schema.sql, models.py (Pydantic), db.py (UPSERT), CLI init/ingest/report/score/export
- `python -m demand_radar init` OK; pytest 16 passed; ruff clean

## P02 — GitHub + HN collectors
STATUS: DONE
- github_issues.py (PRs excluded, 429 Retry-After respected), hackernews.py (Firebase API, local filter)
- Live check: GitHub API 200, HN API 200; at least one real public result per source
- Mock tests for PR exclusion, empty list, 429 retry — passed

## P03 — Pilot, 6 domains × 5
STATUS: DONE
- Fetched 30, ingested 30, SQLite == JSONL counts (5/domain)
- Independent review: 26/30 verified, 4 rejected (see reports/pilot_report.md)
- Gate G1: 26 >= 12 — PASS_NEXT_GATE
- Streamlit smoke: HTTP 200 on localhost:8501
- Artifacts: data/inbox/*/pilot.jsonl, data/demand_radar.sqlite, data/exports/source_items.csv, reports/pilot_report.md

## P04 — Expansion
STATUS: DONE (SOURCE_LIMITED)
- Fetched 201 new, ingested 188 new (13 duplicates vs pilot); total source_items 218 (target 240)
- By domain: AI 45, RES 33, BIO 44, FIN 45, JOB 23, UK 28
- Per-repo cap 35% enforced in collection

## P05 — Review / dedupe / competitor checks
STATUS: DONE
- VERIFIED 207, REJECTED 11 (spam/bot 2, wrong-domain 9)
- Strict clusters: 204 pain_points, 0 with >=2 independent sources
- Thematic clusters (P05b): 17 pains, documented in reports/theme_clusters.md
- Competitor checks: for PRD themes, upstream docs/issue trackers linked in PRDs; no complete free solution found for the specific blockers

## P06 — Scoring + PRDs
STATUS: DONE (PRD_SHORTFALL)
- ranking.csv: 221 pains scored deterministically, cap 59 applied where <2 sources
- PRDs written: 17 (target 20)

## P07 — MVP gate
STATUS: DONE
- Selected 2 (both 80, >=2 sources, different domains/templates): A AI/T1, B FIN/T2
- See reports/mvp_selection.json

## P08/P09 — MVP A + B
STATUS: DONE
- MVP A triage: 5 real issues, tests 12 passed, Streamlit HTTP 200
- MVP B doc_trace: 5 real filing extracts, tests 12 passed, Streamlit HTTP 200

## P10 — Final QA
STATUS: DONE
- pytest 40 passed, ruff clean, export csv+json, 20/20 evidence URLs re-checked OK
- Artifacts: reports/final_report.md, reports/coverage_report.md, reports/evidence_audit.md

## Archive — Drive (separate folder, not agent project auto)
STATUS: DONE
- Drive folder: Demand Radar (new, root level)
- File: demand-radar-2026-11-05.zip (367K, full project excl. .venv)
- Link: https://drive.google.com/file/d/1Ut526EsAbkNUEe7EqnsfP9CfzHkLg0sL/view?usp=drivesdk
- Local copy: ~/projects/demand-radar-2026-11-05.zip and ~/projects/demand-radar/
