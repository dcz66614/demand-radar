# Demand Radar — P2-A Independent QA report

- **QA agent:** independent; built none of the P2-A code (P2A-00–P2A-04).
- **Date:** 2026-11-07 (02:20–02:26 GMT).
- **Delivery zip verified:** `/tmp/demand-radar-p2a-preqa.zip`
- **SHA-256 (verified first, before any other check):**
  `818ebb91df7e2edd3bae0bda72139e7890de0115b2b735ec77fca4f6fe1a19b6` — matches the expected value.
- **Zip:** `ZipFile.testzip()` = None (clean), 301 files, single top-level dir `demand-radar-p2a/`.
- **QA extract:** `/home/hatch/workspace/qa-p2a/demand-radar-p2a/` (fresh extract on the home disk, NOT /tmp). All checks below were run from that extract, following `README_P2A.md` verbatim and in order.
- **Verdict: ACCEPTED_RESEARCH_PROTOTYPE_ONLY**

The sixth-round audit's P2-A item is fixed and verified: an open stream is now `pending` (PENDING/INDETERMINATE) and is never counted in the UI's pass total, while `passed` keeps its frozen chunk-coherence meaning. Research conclusions stand unchanged: 0 qualifying PRDs, 2 prototypes PARTIALLY_REAL_WORLD_VALIDATED, #340 Qwen NOT_REAL_WORLD_VALIDATED.

## 1. Zip integrity

| check | observed |
|---|---|
| SHA-256 | `818ebb91…` — matches expected value exactly |
| `ZipFile.testzip()` | None (no corrupt entries) |
| files / top-level dirs | 301 files, single top-level dir `demand-radar-p2a/` |

## 2. README §1–§2, verbatim and in order (every exit code recorded)

| command | exit code | observed |
|---|---|---|
| `python3 -m venv .venv` | 0 | |
| `pip install -r requirements.txt` | 0 | NumPy 2.5.4, Streamlit 1.67.0, pytest 9.2.0, ruff 0.17.4, pandas 3.1.1, pydantic 2.14.3; Python 3.12.3 |
| `pip install -e . --no-deps` | 0 | demand-radar 0.1.0 |
| `demand_radar init` | 0 | DB created (idempotent migration) |
| `demand_radar score` | 0 | scored 221 pains → `reports/ranking.csv` |
| `demand_radar report --stage final` | 0 | source_items 218, pain_points 221, evidence_links 369 |
| `export --format csv` | 0 | 200 rows |
| `export --format json` | 0 | 200 rows |
| `export --format csv --all` | 0 | 218 rows |
| `export --format csv` (re-export) | 0 | 200 rows restored |
| `ranking.csv` vs `reports/rework2/ranking_r2_04.csv` | — | **byte-identical** (`cmp` clean) |
| DB `PRAGMA integrity_check` | — | `ok` |
| DB `PRAGMA foreign_key_check` | — | 0 violations |
| DB counts | — | 218 sources, 221 pains |

## 3. Baseline regressions (26 expected)

`pytest tests/test_rework2_adversarial.py tests/test_independent_r2.py tests/test_independent_r3.py tests/test_post_r4_termination.py -q` → **26 passed**, exit 0.

## 4. Full suite, main venv + ruff

- `pytest -q` → **346 passed, 8 skipped**, exit 0 (matches README claim 346/8).
- `ruff check .` → **All checks passed!**, exit 0.

## 5. Real venv (§4: tiktoken 0.14.0, neurokit2 0.3.0, wfdb 4.3.1, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2)

All installs exit 0 (versions as pinned, verified via `pip freeze`). `pytest -q` → **363 passed, 0 skipped**, 6 warnings (the documented wfdb `Pandas4Warning` from inside wfdb's annotation reader), exit 0. Matches README claim 363/0.

## 6. MANIFEST + no self-hash

- `sha256sum -c reports/p2a/MANIFEST.sha256` from project root → **300/300 OK**, exit 0.
- `grep -r` for the delivery SHA `818ebb91…` (full and 8-char prefix) across the extracted tree (excluding `.venv`, `.venv-real`) → **0 occurrences**. The zip does not contain its own hash.

## 7. Gate + selection

`reports/rework2/run_gate_r2_04.py` → **qualified 0, not qualified 221**, fingerprint
`3d26137fd5e36e53ed08db7fea14c65d823c31dac3870b0e1386d8fe262fafe6` — matches the REWORK2 fingerprint exactly. Exports 200 / 200 / 218 as in §2.
`reports/mvp_selection.json`: prd_eligible **0**, mvp_built **2**, not_selected **221**, superseded_rework1_prd_eligible **5**.

## 8. The 3 apps, headless + curl

Workbench (8501), R1-A (8502), R1-B (8503) all **HTTP 200**. (The shell's exit signal 15 in that step was QA's own `pkill` of the background Streamlit processes, not an app failure.)

## 9. Frozen files byte-identical

| file | SHA-256 observed | matches |
|---|---|---|
| `tests/test_independent_r2.py` | `aa91307d12c9db5a4bc077aac5ef46bb9edb3d0ad8e221d6b8dd475caf237f15` | final report §9 (`aa91307d…`) |
| `tests/test_independent_r3.py` | `8c61b5f81e7388970ac00e37ad1d4985f816312385c15193be8a2e7187f562fc` | final report §9 (`8c61b5f8…`) |
| `tests/test_post_r4_termination.py` | `244882a3868e0199d4f9b45671e37a3c3959351d8ad2a8fada68ee2f26466ebe` | final report §9 (`244882a3…`) |

## 10. P2-A claim check — `passed` semantics unchanged, new counting exact

**Frozen 26 on the POST-R4 delivery zip.** Extracted `/home/hatch/projects/demand-radar-post-r4-2026-11-06.zip` fresh (SHA `567856b8…` re-verified before use) into `/home/hatch/workspace/qa-p2a/post-r4/`, built a fresh venv, ran the frozen 26: **26 passed**. `passed` semantics did not change across the stage.

**Fixture sweep under the new counting (P2-A extract, QA's own run, not the builder's):** `run_all(load_scenarios(mvps/r1_a/data/fixtures.json))` → **7 passed / 13 failed / 0 not checked / 2 pending** of 22 checks. The two pending rows are exactly `streaming-completed-41708` and `streaming-no-done` — both `passed=True` (chunk coherence), `termination="open"`, `request_completed_successfully=False`. Under the old counting (outcome ok and passed) the same sweep is 9 passed: exactly the two open chunk-valid checks moved from passed to pending, failed count unchanged. Per-row invariants held on all 22 rows: streaming `request_completed_successfully == (passed and termination == "completed")`; api_call `request_completed_successfully == (outcome == "ok" and passed)`; zero violations.

## 11. QA's own fresh-seed randomised counter-checks

- **Seed: 20261109** (builder used 20261107 — different seed, independent design).
- Script: `/home/hatch/workspace/qa-p2a/p2a_random_check.py` (kept outside the delivery tree).
- **60 randomised trials, 466 assertions, 0 failures.**
- Design per trial: 1–4 function calls, each randomly done (70%) or left pending; a random terminal from {none, completed, failed, incomplete, error} (with realistic reason payloads: `failed` carries `server_error: boom`, `incomplete` carries `max_output_tokens`, `error` carries `server_error: upstream exploded`); 40% chance of a data event after the terminal; 30% chance of a second terminal (same kind half the time, a conflicting kind otherwise). Plus the no-events stream (outcome `not-checked` branch).
- Invariants asserted on every trial (the P2-A split):
  - `call_chunk_valid == passed`;
  - `request_completed_successfully == (passed and termination == "completed")`;
  - `request_status == "completed"` iff `request_completed_successfully`;
  - `request_status == "pending"` iff `termination == "open"` and `passed` (and pending implies passed and open);
  - `request_status` always in {completed, pending, failed, not-checked};
  - failure terminal ⇒ passed False, outcome ≠ 'ok', termination names the kind;
  - clean completed stream ⇒ passed True, rcs True, status completed;
  - completed-with-pending ⇒ passed False, status failed;
  - data after any terminal ⇒ passed False; no terminal ⇒ termination 'open';
  - no-events stream ⇒ outcome 'not-checked', passed False, rcs False, status 'not-checked', ccv False.
- **R1-A app driven live via AppTest** (script `/home/hatch/workspace/qa-p2a/p2a_apptest.py`): no exception; banner contains 'pending' **and** 'never counts toward the pass total'; after clicking "Run validation" the summary reads exactly **"7 passed, 13 failed, 0 not checked, 2 pending" of 22 checks**; dataframe shows 22 rows. With the Outcome filter set to "pending" before clicking, the table shows exactly **2 rows** — `streaming-completed-41708` and `streaming-no-done`, both `request_status` pending, both `passed=True` on chunk coherence, both `termination` open — and "Showing 2 of 22 checks". (One QA-script note: setting the filter *after* clicking clears the results block, because the results render only on the button-click rerun — standard Streamlit behaviour, not an app defect; the correct sequence is filter first, then click, which is what the passing check does.)

## 12. Final report header vs §13, and README claims

- `reports/final_report_p2a.md` header: "**QA status: independent QA for P2-A is pending at the time of the pass-1 build (see §13)** — the POST-R4 verdict … applied to the POST-R4 zip only". §13 is titled "QA verdict — pending independent QA" and repeats the same statement, adding that the QA-bound zip SHA is to be filled in `reports/p2a/p2a_04.md` §3 and the decision log. **No contradiction** — the header and §13 agree, and both correctly scope the POST-R4 verdict and the sixth-round audit verdict to the POST-R4 zip.
- No file in the delivered zip claims a QA verdict that did not happen: every `ACCEPTED…` / `FINAL_VERDICT` mention in the final report, README and stage reports is explicitly scoped to POST-R4 (or to the sixth-round audit of the POST-R4 bytes).
- README claims vs observed: 346/8 main ✓, 363/0 real ✓, 26 baseline ✓, 300 MANIFEST ✓, gate 0/221 + fingerprint ✓, 7/13/0/2 sweep ✓. All match what QA actually ran.
- Final report §9 numbers (346/8, 26/26, MANIFEST 300 — see §13 below for the one stale row) also match observed values, except the real-venv row noted in P2-1.

## 13. Non-blocking observations (P2 — documentation only; no code, test, gate, or research-conclusion impact)

1. **P2-1. Final report §9 table, real-venv row, still says "351 passed, 0 skipped".** QA measured **363 passed, 0 skipped** in the real venv (§5). 351 was the POST-R4 count. The bullet below the table phrases 351 as POST-R4's number ("351 passed, 0 skipped in POST-R4 … re-verified in the P2-A clean room"), so the bullet is defensible, but the table row presents 351 as the current P2-A figure. Fix: 363 in the table.
2. **P2-2. README_P2A.md carries stale POST-R4 suite numbers.** §7: "a full test suite that passes in two venvs (334 / 351)"; §8 layout table: "full suite (334 passed / 8 skipped in main venv; 351 in .venv-real)". Should read 346 / 363. (README §3 and §4 state the correct 346/8 and 363/0.)
3. **P2-3. README_P2A.md §8 layout table lists `reports/final_report_post_r4.md` as "current final report".** The current final report is `reports/final_report_p2a.md` — the README's own header says so. §7 also points residual disclosures at `reports/final_report_post_r4.md` §11; the current report's §11 is the right reference.
4. **P2-4. Final report §9 claims "Full logs: `reports/p2a/full_suite_p2a_main.txt`" — that file is not in the zip.** No P2-A full-suite log (main or real) is shipped; the real-venv bullet cites the POST-R4 log `reports/post_r4/full_suite_p0_real.txt` instead of a P2-A run. The suite numbers themselves were re-verified live by QA (§4–§5), so this is a missing-evidence-file gap, not a false claim.
5. **P2-5. `reports/p2a/p2a_04.md` references `p2a_05.md` §1 (pre-QA smoke test), but no `p2a_05.md` exists in the zip.** POST-R4 shipped `p0_05.md` for the same step.
6. **P2-6. The QA-bound zip SHA `818ebb91…` is recorded nowhere in the delivered docs.** Final report §13 says it is "to be filled in `reports/p2a/p2a_04.md` §3 and the decision log", but neither contains it (the decision log ends at P2A-04; its P2A-04 entry is also timestamped 02:18, earlier than the P2A-02/P2A-03 entries at 02:20/02:25 — a minor ordering oddity). This is the same traceability-gap class the sixth-round audit flagged as P2-B for POST-R4. The final delivery packaging should record the QA-bound SHA and the final delivery SHA in the stage report / decision log / final report §13, so the delivered bytes are traceable without this QA report. If the P2 items above are fixed at final-packaging time, the final zip SHA will differ from this QA-bound SHA — record it, and have the final bytes verified, as was done for POST-R4.

## What QA could NOT verify

- Nothing material: every check in the brief was run and observed. Python 3.13, competitor execution, and the #340 Qwen claim remain NOT_TESTED / NOT_REAL_WORLD_VALIDATED, as the report itself states — QA does not claim otherwise.

## Files QA wrote

- This report: `reports/p2a/p2a_qa.md` (the only file QA wrote inside the work tree; the delivery zip was never modified).
- QA's own scripts (outside the tree, in `/home/hatch/workspace/qa-p2a/`): `p2a_random_check.py`, `p2a_apptest.py`. QA extracts in `/home/hatch/workspace/qa-p2a/demand-radar-p2a/` (P2-A) and `/home/hatch/workspace/qa-p2a/post-r4/` (POST-R4).
