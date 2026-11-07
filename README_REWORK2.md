# Demand Radar — README (REWORK2)

Current version: **REWORK2** (2026-11-06). Read
`reports/final_report_rework2.md` first — it is the single current report
(0 qualifying PRDs; 2 MVPs are PARTIALLY_REAL_WORLD_VALIDATED prototypes).
The old REWORK1 report and original status are in `reports/superseded/`.

Everything below is copy-pasteable. All commands run from the extracted
project root. Python 3.12 is required (tested on 3.12.3; Python 3.13 was
NOT_TESTED — no 3.13 interpreter on the build machine).

## 1. Unzip and set up the main venv

```bash
unzip demand-radar-rework2-2026-11-05.zip
cd demand-radar-rework2
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e . --no-deps
```

What this proves: the package installs from `requirements.txt` and the
CLI works. (In the clean-room verification these commands ran on a fresh
extract with a fresh venv; see `reports/rework2/r2_06.md` §5.)

## 2. Run the pipeline (uses the shipped SQLite DB — no re-collection)

```bash
.venv/bin/python -m demand_radar init      # idempotent; runs DB migrations
.venv/bin/python -m demand_radar score     # re-scores 221 pains
.venv/bin/python -m demand_radar report --stage final
.venv/bin/python -m demand_radar export --format csv    # 200 VERIFIED rows
.venv/bin/python -m demand_radar export --format json   # 200 VERIFIED rows
.venv/bin/python -m demand_radar export --format csv --all  # 218 rows incl. REJECTED
```

Expected: `score` writes `reports/ranking.csv` (byte-identical to the
shipped `reports/rework2/ranking_r2_04.csv`); max score 45; 0 pains ≥ 70.
`export` defaults to VERIFIED-only (200 rows); `--all` gives 218.

## 3. Run the tests (main venv)

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
```

Expected: **243 passed, 8 skipped** (exit 0); ruff **All checks passed**.
The 8 skips are the 7 real-tokenizer tests + the 1 real-upstream module
(`importorskip` — they need the second venv below). The 5 adversarial
regression tests (`tests/test_rework2_adversarial.py`) pass inside the
full suite; run them alone with:

```bash
.venv/bin/python -m pytest tests/test_rework2_adversarial.py -q   # 5 passed
```

## 4. Set up the real-upstream venv (proves the real validation paths)

The main venv cannot run the real-upstream tests: it has no tiktoken,
neurokit2 or wfdb. Build a second venv:

```bash
python3 -m venv .venv-real
.venv-real/bin/python -m pip install -r requirements.txt
.venv-real/bin/python -m pip install -e . --no-deps
.venv-real/bin/python -m pip install "tiktoken==0.14.0" "neurokit2==0.3.0" "wfdb==4.3.1" "scipy==1.18.1" "scikit-learn==1.9.1" "matplotlib==3.11.2"
.venv-real/bin/python -m pytest -q
```

Expected: **260 passed, 0 skipped** (exit 0). Every real-path test runs
here: real tiktoken substitution detection (OpenAI models),
recorded-event replay, and real neurokit2/wfdb calls including the
vendored MIT-BIH 100 10 s excerpt (`mvps/r1_b/data/`).

Notes:
- tiktoken fetches its encoding tables from OpenAI's public blob store
  **once**, on first `get_encoding`; afterwards the tests run offline
  (tables cached). In a fresh offline environment the 7 real-tokenizer
  tests skip instead of failing.
- Both venvs are excluded from the delivery zip (`.venv/`, `.venv-real/`
  are in `.gitignore`); rebuild them with the commands above.
- Full freezes: `reports/rework2/pip_freeze_r2_06_main.txt`,
  `reports/rework2/pip_freeze_r2_06_real.txt`.

## 5. Run the three Streamlit apps (headless check)

```bash
.venv/bin/python -m streamlit run app/streamlit_app.py --server.headless true --server.port 8501 &
.venv/bin/python -m streamlit run mvps/r1_a/app.py --server.headless true --server.port 8502 &
.venv/bin/python -m streamlit run mvps/r1_b/app.py --server.headless true --server.port 8503 &
curl -s -o /dev/null -w "workbench:%{http_code}\n" http://localhost:8501/
curl -s -o /dev/null -w "r1-a:%{http_code}\n" http://localhost:8502/
curl -s -o /dev/null -w "r1-b:%{http_code}\n" http://localhost:8503/
```

Expected: all three HTTP 200. The workbench shows 200 VERIFIED rows by
default (REJECTED opt-in); R1-A shows 22 checks (15 scenarios), R1-B
shows 15 checks (14 cases). Both MVP apps carry a warning banner stating
their PARTIALLY_REAL_WORLD_VALIDATED positioning.

## 6. Reproduce the gate (0 qualifying PRDs)

```bash
.venv/bin/python reports/rework2/run_gate_r2_04.py
```

Expected: `qualified 0, not qualified 221`, fingerprint
`3d26137fd5e36e53ed08db7fea14c65d823c31dac3870b0e1386d8fe262fafe6`.
(The script writes `reports/rework2/mvp_selection_r2_04.json`,
`ranking_r2_04.csv`, `qualifying_prds_r2_04.csv`,
`not_qualified_r2_04.csv` — re-running reproduces them identically.)

Other reproducibility scripts (all exit 0, all idempotent):

```bash
.venv/bin/python reports/rework2/rederive_scores_r2_04.py   # ALL 5 MATCH (no score.py import)
.venv/bin/python reports/rework2/assess_r2_03.py             # 76 classifications -> DB + CSV
.venv/bin/python reports/rework2/compute_final_numbers.py    # every number in the final report
.venv/bin/python reports/rework2/build_mvp_selection_r2_06.py  # rebuilds reports/mvp_selection.json
.venv/bin/python reports/rework2/align_prd_cards_r2_06.py   # prd_cards -> R2-04 gate (0 QUALIFIED)
```

## 7. What this delivery is — and is not

- IS: a corrected evidence base, a corrected scoring rule with an
  independent re-derivation, 5 problem signatures with 38 DIRECT links,
  4 scope-documented competitor non-solves, 2 validators with real
  upstream validation paths, and a full test suite that passes in two
  venvs.
- IS NOT: a set of qualified PRDs (0 qualify under the unchanged gate
  of 70), a product that solves any upstream problem, or a claim that
  the #340 Qwen substitution, competitor execution, or Python 3.13 were
  validated — they were not (see `reports/final_report_rework2.md` §11).

## 8. Layout (top level)

| path | what it is |
|---|---|
| `README_REWORK2.md` | this file |
| `README.md` | original README (historical) |
| `reports/final_report_rework2.md` | current final report |
| `reports/rework2/` | R2-01–R2-06 stage reports, gate outputs, logs, freezes |
| `reports/rework1/` | REWORK1 stage reports (untouched history) |
| `reports/superseded/` | old final report + STATUS; `reports/prds/superseded/` holds all 17 PRD files |
| `reports/mvp_selection.json` | new shape: `prd_eligible` (0), `mvp_built` (2), `not_selected` (221), `superseded_rework1_prd_eligible` (5) |
| `data/demand_radar.sqlite` | the DB (218 sources, 221 pains, 369 evidence links, 34 competitor checks) |
| `mvps/r1_a/`, `mvps/r1_b/` | the two PARTIALLY_REAL_WORLD_VALIDATED prototypes |
| `mvps/superseded/` | original MVP A/B demos (history) |
| `app/streamlit_app.py` | workbench (200 VERIFIED rows by default) |
| `tests/` | full suite (243 passed / 8 skipped in main venv) |
