# Full retest — 2026-11-05 (after first delivery)

Done by Muse itself, no free-model quota. All commands run, none assumed.

## 1. Local (~/projects/demand-radar, existing venv)

- `python -m pytest -q` — 40 passed
- `python -m ruff check .` — All checks passed
- `python -m demand_radar init` — created DB (idempotent)
- `python -m demand_radar report --stage final` — source_items 218, pain_points 221, evidence_links 369; by domain AI 45, BIO 44, FIN 45, JOB 23, RES 33, UK 28
- `python -m demand_radar score` — OK (deterministic scorer message)
- `python -m demand_radar export --format csv/json` — 218 rows each
- Reconciliation: JSONL lines 231, DB 218, CSV 218 — difference is 13 duplicates rejected by idempotent ingest (expected, documented in final report)
- PRD files: 17; ranking.csv rows: 221
- Evidence re-check, 2nd sample (ranking rows 4–6, 20 URLs): 20 OK, 0 failed
- Streamlit: workbench 200, MVP A 200, MVP B 200 (localhost, headless)

## 2. Clean room (from the delivered zip)

- First attempt in /tmp FAILED with `No space left on device`: /tmp is a 512 MB tmpfs, only 126 MB free; pip install of pandas/streamlit does not fit. This is an environment limit, not a project defect. Cleaned /tmp (freed 348 MB from the failed attempt).
- Second attempt in ~/workspace/clean-test/demand-radar-clean (150 GB disk):
  - Unzipped the delivered zip, fresh venv, `pip install -r requirements.txt`, `pip install -e . --no-deps`
  - `python -m pytest -q` — 40 passed
  - `python -m ruff check .` — All checks passed
  - `python -m demand_radar init` — OK
  - `python -m demand_radar ingest --file data/inbox/AI/pilot.jsonl` — 0 new (idempotent, DB already contains them)
  - `python -m demand_radar report --stage final` — identical counts: 218 / 221 / 369
  - MVP tests alone: 24 passed
  - Clean-test directory removed after verification.

## 3. Issue found and fixed during retest

- README told a fresh user to run `pip install -r requirements.txt`, but no requirements.txt existed (P00 installed deps from an explicit pip list). Fixed: added `requirements.txt` (same ranges as pyproject.toml, runtime + pytest/ruff) and re-tested the clean install with it. This zip includes the fix.

## 4. Delivery

- Rebuilt zip from the current tree (includes this report + requirements.txt).
- Updated the same Drive file (Demand Radar folder, same link as first delivery) in place; verified size and modified time after update.
- No other files changed. Counts, scores and PRDs are unchanged from the first delivery.
