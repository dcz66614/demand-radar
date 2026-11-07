# Demand Radar — POST-R4 Independent QA report (P0)

- **QA agent:** independent; built none of the POST-R4 code (P0-00–P0-05).
- **Date:** 2026-11-06 (17:02 GMT).
- **Delivery zip verified:** `/home/hatch/projects/demand-radar-post-r4-2026-11-06.zip`
- **SHA-256 (verified first, before any other check):**
  `c84fa88feadf3ed833bfc2ca7dbafd646b74d7350facdcdef509851c886656f1` — matches the expected value.
- **Zip:** `ZipFile.testzip()` = None (clean), 286 files, single top-level dir `demand-radar-post-r4/`.
- **QA extract:** `/home/hatch/workspace/qa-p0/demand-radar-post-r4/` (fresh extract on the home disk, NOT /tmp). All checks below were run from that extract, following `README_POST_R4.md` verbatim and in order.
- **Verdict: ACCEPTED_RESEARCH_PROTOTYPE_ONLY**

The fifth-round audit's single P1 defect is fixed and verified. Research conclusions stand unchanged: 0 qualifying PRDs, 2 prototypes PARTIALLY_REAL_WORLD_VALIDATED, #340 Qwen NOT_REAL_WORLD_VALIDATED.

## 1. Zip integrity

| check | observed |
|---|---|
| SHA-256 | `c84fa88f…` — matches expected value exactly |
| `ZipFile.testzip()` | None (no corrupt entries) |
| files / top-level dirs | 286 files, single top-level dir `demand-radar-post-r4/` |

## 2. README §1–§2, verbatim and in order (every exit code recorded)

| command | exit code | observed |
|---|---|---|
| `python3 -m venv .venv` | 0 | |
| `pip install -r requirements.txt` | 0 | NumPy 2.5.4, Streamlit 1.67.0, pytest 9.2.0, ruff 0.17.4, pandas 3.1.1, pydantic 2.14.3 |
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

- `pytest -q` → **334 passed, 8 skipped**, exit 0 (matches README claim 334/8).
- `ruff check .` → **All checks passed!**, exit 0.

## 5. Real venv (§4: tiktoken 0.14.0, neurokit2 0.3.0, wfdb 4.3.1, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2)

All installs exit 0 (versions as pinned). `pytest -q` → **351 passed, 0 skipped**, 6 warnings (the documented wfdb `Pandas4Warning` from inside wfdb's annotation reader), exit 0. Matches README claim 351/0.

## 6. MANIFEST + no self-hash

- `sha256sum -c reports/post_r4/MANIFEST.sha256` from project root → **285/285 OK**, exit 0 — re-checked after the gate re-run (§7) rewrote gate outputs; still 285/285.
- `grep -r` for the delivery SHA `c84fa88f…` across the extracted tree (excluding `.venv`) → **0 occurrences**. The zip does not contain its own hash.

## 7. Gate + selection

`reports/rework2/run_gate_r2_04.py` → **qualified 0, not qualified 221**, fingerprint
`3d26137fd5e36e53ed08db7fea14c65d823c31dac3870b0e1386d8fe262fafe6` — matches the REWORK2 fingerprint exactly. Exports 200 / 200 / 218 as in §2.
`reports/mvp_selection.json`: prd_eligible **0**, mvp_built **2**, not_selected **221**, superseded_rework1_prd_eligible **5**.

## 8. The 3 apps, headless + curl

Workbench (8501), R1-A (8502), R1-B (8503) all **HTTP 200**. (The shell's exit signal 15 in that step was QA's own `pkill` of the background Streamlit processes, not an app failure.)

## 9. RED baseline re-verification (REWORK4 zip, fresh extract)

Extracted `/home/hatch/projects/demand-radar-rework4-2026-11-06.zip` (SHA `15d391be…` re-verified before use) fresh into `/home/hatch/workspace/qa-p0/demand-radar-rework4/`, copied `tests/test_post_r4_termination.py` from the POST-R4 zip into it byte-identical, built a fresh venv, ran the file:

**5 failed / 2 passed** — exactly as the fifth-round audit claimed:

- FAILED: `test_terminal_failure_or_incomplete_is_not_pass[True-response.failed]`,
  `[True-response.incomplete]`, `[False-response.failed]`, `[False-response.incomplete]`
- FAILED: `test_error_event_cannot_be_counted_as_pass`
- PASSED: `test_normal_completed_call_remains_pass`, `test_completed_with_pending_call_remains_fail`

The RED log's failure mode is visible in the output (REWORK4 verdict `{'outcome': 'ok', 'passed': True, 'termination': 'open'}` for a `response.failed` stream). The POST-R4 zip turns all 7 GREEN (§3).

## 10. QA's own fresh-seed randomised counter-checks

- **Seed: 20261106** (builder used 20261108 — different seed, independent design).
- Script: `/home/hatch/workspace/qa-p0/p0_random_check.py` (kept outside the delivery tree).
- **40 randomised trials, 207 assertions, 0 failures.**
- Design per trial: 1–4 function calls, each randomly done (70%) or left pending; a random terminal from {none, completed, failed, incomplete, error} (with realistic reason payloads: `failed` carries `server_error: boom`, `incomplete` carries `max_output_tokens`, `error` carries `server_error: upstream exploded`); 40% chance of a data event after the terminal; 30% chance of a second terminal (same kind half the time, a conflicting kind otherwise).
- Invariants asserted:
  - failure terminal ⇒ passed False, outcome ≠ 'ok', termination names the kind, detail names the kind **and** its reason;
  - completed + all calls done + no post-terminal events ⇒ passed True, outcome 'ok', termination 'completed';
  - completed + pending call ⇒ passed False, detail says 'still pending';
  - conflicting second terminal ⇒ passed False (conflicting_terminal);
  - data after any terminal ⇒ passed False (event_after_completed / event_after_terminal);
  - no terminal ⇒ termination 'open', detail contains 'not yet proven'; open + all done keeps the chunk-coherence verdict (passed True) — the documented design;
  - duplicate same-kind terminal is tolerated (verdict follows the first terminal).
- **R1-A app driven live via AppTest** (script `/home/hatch/workspace/qa-p0/p0_apptest2.py`): no exception; banner contains 'not yet proven' **and** 'never counts as passed' (failure-terminal wording); after clicking "Run validation" the summary reads exactly **"9 passed, 13 failed, 0 not checked" of 22 checks**; dataframe shows 22 rows.

## 11. Frozen files byte-identical

| file | SHA-256 observed | matches |
|---|---|---|
| `tests/test_post_r4_termination.py` | `244882a3868e0199d4f9b45671e37a3c3959351d8ad2a8fada68ee2f26466ebe` | audit copy `Demand_Radar_R4_Additional_Termination_Tests.py` — identical |
| `tests/test_independent_r2.py` | `aa91307d12c9db5a4bc077aac5ef46bb9edb3d0ad8e221d6b8dd475caf237f15` | final report §9 (`aa91307d…`) |
| `tests/test_independent_r3.py` | `8c61b5f81e7388970ac00e37ad1d4985f816312385c15193be8a2e7187f562fc` | final report §9 (`8c61b5f8…`) |

## 12. Final report header vs §13, and README claims

- `reports/final_report_post_r4.md` header: "**QA status: the independent QA verdict for POST-R4 is pending** (see §13) — the REWORK4 verdict … applied to the REWORK4 zip only". §13 is titled "QA verdict — PENDING" and repeats the same statement. **No contradiction** — the header and §13 agree, and both correctly scope the REWORK4 verdict to the REWORK4 zip.
- README claims vs observed: 334/8 main ✓, 351/0 real ✓, 26 baseline ✓, 285 MANIFEST ✓, gate 0/221 + fingerprint ✓. All match what QA actually ran.
- Final report §9 numbers (334/8, 351/0, 26/26, MANIFEST 285) also match observed values.

## Non-blocking observations

1. **Open stream with all calls done still returns passed=True** (with termination 'open' and 'not yet proven' in the detail). This is the documented design carried over from REWORK4 (chunk-coherence semantics preserved; only the label/detail changed), not a defect — but it means an open stream can still contribute a pass in the fixture sweep. Worth keeping in mind if a future round wants "not yet proven" to also mean "not counted as passed".
2. The stale-residual disclosures from REWORK4 remain as documented (§11): factual check is lexical, not semantic; the §11.15 sequence-gap residual; strict JSON not applied to `signalcheck.py:502` / `ingest.py:17`; Python 3.13 NOT_TESTED; competitor execution NOT_TESTED. None of these is in the scope of the fifth-round P1 fix, and none blocks this verdict.
3. QA's AppTest first attempt failed on a path-resolution mistake in QA's own script (relative path resolved against the script file, not the cwd) — fixed by using an absolute path; the app itself was never at fault.

## What QA could NOT verify

- Nothing material: every check in the brief was run and observed. Python 3.13, competitor execution, and the #340 Qwen claim remain NOT_TESTED / NOT_REAL_WORLD_VALIDATED, as the report itself states — QA does not claim otherwise.

## Files QA wrote

- This report: `reports/post_r4/p0_qa.md` (the only file QA wrote inside the work tree; the delivery zip was never modified).
- QA's own scripts (outside the tree, in `/home/hatch/workspace/qa-p0/`): `p0_random_check.py`, `p0_apptest.py`, `p0_apptest2.py`.
