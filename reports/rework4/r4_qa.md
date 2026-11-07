# R4 QA — Independent verification of the REWORK4 delivery zip

QA reviewer: independent (built none of R4-00–R4-05). Method: fresh
extract of the final delivery zip only, README commands verbatim,
every exit code recorded, plus own-design randomised counter-checks
against the real validator code. No GPT review is involved.

Date: 2026-11-06. QA working dir: `~/workspace/clean-test-r4-qa`
(home disk, NOT /tmp).

## 1. Zip integrity, provenance, and old-zip preservation

| file | SHA-256 observed | expected | result |
|---|---|---|---|
| `demand-radar-rework4-2026-11-06.zip` | `637e9cfd83867eb8225103ec8f97ef6d447eab7447f0f5059a7c580919e49645` | `637e9cfd…` | MATCH |
| original `demand-radar-2026-11-05.zip` | `963568deaff04e778123d17cd4f5cdaba7f9957212d248079240c12588f2b261` | `963568de…` | UNCHANGED |
| REWORK1 `demand-radar-rework1-2026-11-05.zip` | `0e736693b535f75641abce5e265c8e9ee91a5b63224fd0c5b9972e2ba89ea5c3` | `0e736693…` | UNCHANGED |
| REWORK2 `demand-radar-rework2-2026-11-05.zip` | `14c95a64e6c5c69412b03bb7e39e9f57d99fa32391ac56c8028499aff2ecf65b` | `14c95a64…` | UNCHANGED |
| REWORK3 `demand-radar-rework3-2026-11-06.zip` | `1b0e4e8f248791893f96ac9f29bd09b19e08910c941dd2456e306d7a15094fa7` | `1b0e4e8f…` | UNCHANGED |

`RELEASE_SHA256.txt` (outside the zip) matches exactly: SHA
`637e9cfd…e49645`, size **1,341,874 bytes** (observed file size
identical), 305 files in zip (MANIFEST 260). `unzip -t`: no errors.
The zip contains a single top-level directory `demand-radar-rework4/`;
`cd demand-radar-rework4` works.

**Self-SHA check (P2-D provenance defect from the last audit):**
`unzip -p` over the whole zip piped to grep for the full final SHA
`637e9cfd83867eb8225103ec8f97ef6d447eab7447f0f5059a7c580919e49645`
returns **0 occurrences**. No file inside the zip contains the zip's
own SHA — the final report §13 and `r4_04.md` §5 correctly defer to
`RELEASE_SHA256.txt` (outside the zip) and the decision log. The
pass-1 SHA `8e6b9de1…` is recorded in `r4_04.md` §5 (an intermediate
zip's SHA, not the delivery's).

## 2. README verbatim run (main venv, §1–§3)

Environment observed: Python 3.12.3, numpy 2.5.4, pandas 3.1.1,
pydantic 2.14.3, pytest 9.2.0, RapidFuzz 3.14.6, ruff 0.17.4,
streamlit 1.67.0 — all match the claimed pins.

| step | result | exit |
|---|---|---|
| `python3 -m venv .venv` | created | 0 |
| `pip install -r requirements.txt` | installed | 0 |
| `pip install -e . --no-deps` | installed | 0 |
| `demand_radar init` | DB created/migrated | 0 |
| `demand_radar score` | 221 pains | 0 |
| `demand_radar report --stage final` | 218 / 221 / 369 | 0 |
| `export --format csv` | 200 rows | 0 |
| `export --format json` | 200 rows | 0 |
| `export --format csv --all` | 218 rows | 0 |
| `export --format csv` (re-export) | 200 rows | 0 |
| `diff reports/ranking.csv reports/rework2/ranking_r2_04.csv` | byte-identical | 0 |
| `pytest tests/test_rework2_adversarial.py tests/test_independent_r2.py tests/test_independent_r3.py -q` | **19 passed** | 0 |
| `pytest -q` | **312 passed, 8 skipped** | 0 |
| `ruff check .` | All checks passed | 0 |
| `sha256sum -c reports/rework4/MANIFEST.sha256` (immediately after §2 exports, as the README now prescribes) | **260/260 OK** | 0 |

The R3 QA ordering nit is confirmed fixed: with the README's
re-export line, the MANIFEST check passes right after §2 with no
extra step.

Frozen files: `tests/test_independent_r2.py` SHA-256
`aa91307d12c9db5a4bc077aac5ef46bb9edb3d0ad8e221d6b8dd475caf237f15`,
byte-identical (`cmp` clean) to the REWORK3 audit handoff copy;
`tests/test_independent_r3.py` SHA-256
`8c61b5f81e7388970ac00e37ad1d4985f816312385c15193be8a2e7187f562fc`,
byte-identical to
`~/workspace/user/files/rework4-handoff/Demand_Radar_REWORK3_Independent_Regression_Tests.py`.
No independent-test expectation was modified.

## 3. Real-upstream venv (§4)

Built `.venv-real` per README §4 (tiktoken 0.14.0, neurokit2 0.3.0,
wfdb 4.3.1, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2;
all installs exit 0). `pytest -q`: **329 passed, 0 skipped**,
6 warnings (wfdb `Pandas4Warning`, third-party — matches the README
note). Exit 0.

## 4. Apps (§5)

Headless `streamlit run` + curl: workbench **200**, R1-A **200**,
R1-B **200**.

## 5. DB / report / gate alignment

- `PRAGMA integrity_check`: **ok**; `PRAGMA foreign_key_check`: 0 errors.
- `reports/rework2/run_gate_r2_04.py`: `qualified 0`, `not qualified 221`,
  fingerprint `3d26137fd5e36e53ed08db7fea14c65d823c31dac3870b0e1386d8fe262fafe6`.
- `reports/rework2/compute_final_numbers.py` re-run: max score **45**,
  gate 0/221, sources 218 (200 VERIFIED / 18 REJECTED), pains 221,
  evidence 38 DIRECT / 10 ADJACENT / 5 DUPLICATE / 23 OUT_OF_SCOPE.
- `reports/mvp_selection.json`: prd_eligible **0**, mvp_built **2**,
  not_selected **221**, superseded **5**.
- Final report §11 spot-checks: item 6 (Python 3.13 NOT_TESTED —
  this QA ran on Python 3.12.3), item 14 (factual check is lexical,
  word order ignored — confirmed by counter-check §6b: a word-order
  variant passes), item 17 (strict JSON NOT used by
  `mvps/r1_b/signalcheck.py:502` and `src/demand_radar/ingest.py:17`
  — honestly disclosed as an inconsistency, not hidden), item 18
  (the §11.15 sequence-gap residual still stands — see §7 below).
- R1-A README Positioning table and app banner state the three
  capabilities separately as claimed.

## 6. Independent counter-checks (own design, fresh seed 777002)

Script: `~/workspace/clean-test-r4-qa/qa_countercheck.py` (kept
outside the delivery). Run against the REAL `StreamingHandler`,
`validate_stream`, `_parse_strict_json`, `_validate_payload`,
`run_step`, and the real R1-A fixtures from the fresh extract.
**363 assertions, 363 passed, 0 failed.**

- (a) Streaming, 40 randomised trials, 4 parallel dual-key calls,
  random 1–4 chunk splits, random cross-call interleaving (per-call
  chunk order preserved, as real streams deliver), random done
  order, globally unique sequence numbers, `response.completed`
  terminator: **40/40 ok**, termination `completed`, emitted 4,
  and per-call arguments verified intact through the real handler
  (each completed chunk's `function_call.arguments` equals the
  intended JSON for its call key).
- (a2) Termination adversaries: 20 trials with `response.completed`
  arriving while one call is still pending → **20/20
  wrong-result**, passed False, termination `completed`. Targeted:
  delta after completed → wrong-result; done after completed →
  wrong-result; empty event list → not-checked, termination `none`.
  Open stream (one call added, never done, no completed) →
  termination **`open`**, detail "stream still open" (see §7).
  All-done with no completed terminator → termination `open`,
  outcome ok, emitted 4.
- (b) Strict JSON (17 reject + 9 accept + 4 payload cases): bare
  `NaN` / `Infinity` / `-Infinity` rejected; the same constants
  nested at depths 2–4 inside dicts and lists rejected; `1e999`,
  `-1e999`, `1e400` rejected at top level and nested; `"NaN"` as
  string TEXT accepted (`{"s": "NaN"}`, `{"a": ["NaN", 1]}`,
  `"the word NaN inside text"`); `1e10` and `-0.0` accepted.
  Through `_validate_payload` raw bodies: `{"x": NaN}` →
  wrong-result; nested `1e999` → wrong-result; `{"s": "NaN"}` →
  ok.
- (c) Not-checked: keyword-only via `run_step` → outcome
  **not-checked, passed False**; keyword missing → wrong-result;
  expected-answer match → ok (control). Fixture sweep over all
  22 shipped R1-A results: **0 not-checked results pass**
  (9 passed, 13 failed — the 13 failures are the fixtures'
  deliberate negative cases: buggy transport, false responses,
  etc.). UI three-way counts driven live through Streamlit
  AppTest (click "Run validation"): rendered
  "**9 passed, 13 failed, 0 not checked** of 22 checks" —
  exactly the real fixture counts.

### Two expectations corrected during QA (my errors, not defects)

1. My first counter-check used a `call_key` field on completed
   chunks; the real shape is `key` + `function_call.arguments`.
   Script bug, fixed.
2. My first expectation that a lone `response.completed` (zero
   calls) must return not-checked was wrong: an empty completed
   response is legitimate — nothing was requested, nothing is
   pending, termination is clean, and the detail honestly states
   0 done / 0 emitted. The vacuous pass hides no lost work.

## 7. Confirmed residuals / observations (disclosed, not blockers)

- **Open stream with a pending call returns outcome `ok` /
  passed True** (emitted 0, termination `open`, detail "stream
  still open"). This is a deliberate, documented design decision
  carried from R3 — the final report (§8, termination table) and
  `r4_01_02_03.md` state it explicitly ("open stream, emitted 0,
  passed — only its status is now explicit"), and the R4-03 fix
  only changes the *completed*-with-pending case (which now
  fails, verified §6a2). It is not one of the fourth-round
  audit's defects, and the task's own check for the open stream
  is termination `open`, which holds. Noted here so the decision
  stays visible; changing it would be scope beyond the R4 brief.
- **§11.15 sequence-gap residual still stands**, as disclosed in
  final report §11 items 15/18: a lost trailing chunk + empty
  done args still passes with silently incomplete arguments when
  the done event carries no arguments. R4-03 narrows it (a done
  after `response.completed` is now an anomaly, and a completed
  response with a pending call fails), but a gap inside an
  otherwise open stream is still caught only when done carries
  the true arguments. Follow-up, not a blocker.

## 8. RED baseline independently re-verified

The 10 fourth-round tests were run against a fresh extract of the
**REWORK3** zip (own venv, same commands): **6 failed, 4 passed**
— exactly the RED state the stage report claims
(`reports/rework4/red_log_r4_00.txt` shows `FFFFFF....`).
The 6 failures are the audit's defect tests; the 4 passes are the
valid-behaviour controls. On the REWORK4 extract the same 10 are
**10/10 GREEN** (part of the 19/19 baseline).

## 9. Stage-report cross-check

- `r4_01_02_03.md`: 19/19 baseline, 312/8 main (×2), 329/0 real,
  10/10 audit file (was 6 RED / 4 GREEN) — all match observation.
  The builder's fresh-seed check (seed 20261107, 80/80) is a
  separate run from QA's (seed 777002, 363 assertions).
- `r4_04.md`: pass-1 numbers (19/19, 312/8, 329/0, MANIFEST
  258/258 for pass 1, SHA `8e6b9de1…`) are consistent with the
  final-zip observations; the pass-1 → final diff claim (2 files
  added, 3 common files differ) is stated with its reconstruction
  method, and the file counts check out (final 305 files vs
  pass-1 303; MANIFEST 260 vs 258).
- `r4_05.md`: test totals (312/8, 329/0, 19/19) and MANIFEST 260
  match observation.
- `final_report_rework4.md` §9/§10: 312/8, 329/0, 19/19, MANIFEST
  260 files — all match observation. Header and §13 agree the
  REWORK4 QA verdict is pending until this report, and that the
  REWORK3 verdict applied to the REWORK3 zip only — the P2-D
  pending/accepted contradiction is fixed.
- `progress/STATUS.md`: REWORK4 section says QA verdict pending;
  the ACCEPTED_RESEARCH_PROTOTYPE_ONLY mentions are correctly
  scoped to the REWORK2 and REWORK3 history sections.

## 10. Findings summary

- Genuine false-PASS defects found: **none**. All fourth-round
  audit defects are fixed and verified: strict JSON parsing
  (NaN/Infinity/1e999 rejected at nested depths, "NaN" as text
  still passes), not-checked never counted as a pass (runner
  `passed=False` and the UI's separate not-checked count, driven
  live), and `response.completed` as a terminal signal
  (completed-with-pending fails, events after it are anomalies,
  termination reported as completed/open/none). The REWORK3 fixes
  still stand (dual-key argument integrity, factual comparison,
  fail-closed schema, top-level directory).
- Packaging/provenance defect P2-D: fixed — the delivery SHA
  lives only in `RELEASE_SHA256.txt` outside the zip; no file
  inside the zip contains it.
- Research conclusions unchanged as required: 0 qualifying PRDs,
  gate 70 unchanged, 2 PARTIALLY_REAL_WORLD_VALIDATED prototypes,
  #340 Qwen NOT_REAL_WORLD_VALIDATED.
- Observations (non-blocking): (1) README §3 still carries a
  stale paragraph — "The baseline regression set is now 9 tests:
  the 5 old adversarial regressions plus the 4 independent
  regressions" — immediately contradicted by the command below
  it (three files, `# 19 passed`) and the following correct
  "now 19 tests" paragraph. Doc-only; the command is correct and
  was run verbatim (19 passed). (2) The disclosed open-stream
  and sequence-gap residuals in §7 — follow-ups, not blockers.

QA VERDICT: ACCEPTED_RESEARCH_PROTOTYPE_ONLY
