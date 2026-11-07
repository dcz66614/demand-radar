# Demand Radar — STATUS (current: REWORK4)

Standalone project. No P number, no relation to the P series.
Storage after completion: separate Google Drive folder (not `agent project auto`).
Execution: Muse itself, no free-model quota used. Extra spend: £0.

> **Current version is REWORK4 (2026-11-06).** The REWORK3 report
> (`reports/superseded/final_report_rework3.md`), the REWORK2 report
> (`reports/superseded/final_report_rework2.md`) and the REWORK1 report
> (`reports/superseded/final_report.md`) are preserved as history in
> `reports/superseded/` — do not read them as current state.
> Current report: `reports/final_report_rework4.md`.
> Stage reports: `reports/rework4/r4_01_02_03.md`, `r4_04.md`, `r4_05.md`.
> Original + REWORK1 + REWORK2 + REWORK3 delivery zips are read-only;
> the REWORK4 zip is `demand-radar-rework4-2026-11-06.zip` (see
> `reports/rework4/r4_04.md` for its SHA-256 and `RELEASE_SHA256.txt`
> outside the zip).

## Original build (P00–P10, 2026-11-05)
STATUS: DONE — see `reports/superseded/STATUS.md` for the P00–P10 record.
218 source_items (207 VERIFIED / 11 rejected at the time), 221 pain_points,
17 PRDs, 2 MVPs (A issue_triage, B doc_trace). Delivered as
`demand-radar-2026-11-05.zip` (SHA-256 `963568de…`, 377,294 bytes).

## REWORK1 (R01–R07, 2026-11-05)
STATUS: DONE — see `reports/rework1/STATUS.md` and `reports/rework1/r07.md`.
218 sources re-reviewed live (VERIFIED 200 / REJECTED 18); 5 PRDs rewritten;
2 new MVPs (R1-A, R1-B); R07 QA first returned REWORK_REQUIRED on 3 narrow
items, all fixed and re-verified (pytest 154 passed ×7, ruff clean).
Delivered as `demand-radar-rework1-2026-11-05.zip` (SHA-256 `0e736693…`,
839,767 bytes). **REWORK1's conclusions are superseded by REWORK2/REWORK3.**

## REWORK2 (R2-01–R2-06, 2026-11-06)
STATUS: DONE — independent QA verdict ACCEPTED_RESEARCH_PROTOTYPE_ONLY
(0 failed items; see `reports/rework2/r2_qa.md`). Delivered as
`demand-radar-rework2-2026-11-05.zip` (SHA-256 `14c95a64…`, 1,163,895 bytes).
**REWORK2's conclusions are superseded by REWORK3/REWORK4 below** (research
numbers unchanged; the validator code and packaging are what changed).

- R2-01: 5 adversarial regression tests RED → GREEN (RSA, RSP phase,
  JSON schema bool, streaming correlation). Suite 212 at the time.
- R2-02: trapz test fixed; suite passes in main venv (NumPy 2.5.4)
  and NumPy 2.3.5 venv; Python 3.13 NOT_TESTED (not installed).
- R2-03: 76 evidence links classified (38 DIRECT / 10 ADJACENT /
  5 DUPLICATE / 23 OUT_OF_SCOPE / 0 UNKNOWN); DIRECT-only recount.
- R2-04: evidence-bound scoring (F=0/L=0 unproven, UNKNOWN competitor
  blocks G); gate 70 UNCHANGED; **qualifying PRDs 0** (max new score 45).
- R2-05: both MVPs PARTIALLY_REAL_WORLD_VALIDATED (real tiktoken 0.14.0,
  real neurokit2 0.3.0 / wfdb 4.3.1, real MIT-BIH 100 10 s sample);
  #340 Qwen claim stays NOT_REAL_WORLD_VALIDATED. Validators must NOT
  offset PRDs eliminated by re-scoring.
- R2-06: final report; old reports archived to `reports/superseded/`;
  `reports/mvp_selection.json` restructured (`prd_eligible` 0,
  `mvp_built` 2 prototypes); `prd_cards` aligned to the R2-04 gate
  (0 QUALIFIED / 17 SUPERSEDED); delivery zip rebuilt and clean-room
  verified.

## REWORK3 (R3-00–R3-05, 2026-11-06)
STATUS: DONE — independent QA verdict
**ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (2026-11-06, see
`reports/rework3/r3_qa.md`). Delivered as
`demand-radar-rework3-2026-11-06.zip` (SHA-256 `1b0e4e8f…`).
**REWORK3's conclusions are superseded by REWORK4 below** (research
numbers unchanged; the validator code and provenance are what changed).

- R3-00: isolated dir extracted from the REWORK2 zip; old 5 regressions
  5/5 GREEN; the audit's 4 new independent tests copied verbatim and
  confirmed RED (4 failed, log kept); source hashes + env recorded.
- R3-01: StreamingHandler true multi-call correlation — canonical
  `item.id`, namespace-separated dual-key maps, key conflicts
  fail-closed, keyless deltas only for a single pending call,
  duplicate sequences dropped, done arguments cross-validated;
  `validate_stream` checks count + association + argument integrity.
  Verified against the real OpenAI Python SDK event contract.
- R3-02: factual content actually compared — `expected_answer` via
  normalized word-multiset match; keyword-only → `not-checked`,
  never claimed as factual verification; negation never passes.
- R3-03: schema fail-closed — JSON Schema standard type names
  supported with an explicit contract; unknown types are config
  errors; NaN/±Inf never satisfy a numeric type; bool never
  satisfies number/integer.
- R3-04: delivery zip has a single top-level directory
  `demand-radar-rework3/`; README §1 commands executed verbatim from
  an empty directory in the clean-room verification.
- R3-05: this report; MVP A capability statement split into three
  separate capabilities (stream event count, function argument
  integrity, factual truth) in its README and app banner.
  Independent QA verdict **ACCEPTED_RESEARCH_PROTOTYPE_ONLY**
  (2026-11-06, `reports/rework3/r3_qa.md`): all 4 audit defects
  verified fixed by fresh-extract checks + own-design randomised
  counter-checks (39/39), MANIFEST 243/243, 3 apps HTTP 200.
  One doc-only fix after QA (README §2 re-export line, MANIFEST
  ordering nit), then the zip was rebuilt and smoke-verified again.

## REWORK4 (R4-00–R4-05, 2026-11-06)
STATUS: DONE — independent QA verdict
**ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (2026-11-06, see
`reports/rework4/r4_qa.md`): all 4 fourth-round audit defects verified
fixed by fresh-extract checks + own-design randomised counter-checks
(363/363), MANIFEST 261/261, 3 apps HTTP 200. One doc-only fix after
QA (README §3 stale "9 tests" paragraph removed), then the zip was
rebuilt and smoke-verified again.

- R4-00: isolated dir extracted from the REWORK3 zip; old 9 regressions
  9/9 GREEN; the fourth-round audit's 10 new tests copied verbatim and
  confirmed RED 6/4, log kept; source hashes + env recorded.
- R4-01: strict JSON parsing — one `_parse_strict_json` (parse_constant
  rejects NaN/Infinity/-Infinity; recursive walk rejects non-finite
  floats like 1e999); used by `_validate_payload` (raw body),
  `_handle_done` (final + accumulated arguments), `load_scenarios`,
  and the R1-A app upload path. Rejection is wrong-result / not valid.
- R4-02: not-checked is not a pass — all three `check_factual_content`
  not-checked returns now carry `passed=False`; the R1-A app shows
  three separate counts (passed / failed / not checked) with its own
  NOT_CHECKED count and filter. Three ordinary tests updated (frozen 9
  untouched); no fixture step is keyword-only, so fixture counts are
  unchanged.
- R4-03: stream termination — `response.completed` is the terminal
  signal; events after it are `event_after_completed` anomalies;
  `validate_stream` returns a `termination` field (completed / open /
  none); completed-with-pending FAILS; an open partial stream keeps
  its verdict but is reported `open`, never silently finished.
- R4-04: this report; delivery provenance recorded OUTSIDE the zip
  (`RELEASE_SHA256.txt`); the R3 report's pending/accepted
  contradiction fixed in the header.

## Headline numbers (all computed from the live DB, 2026-11-06)
- Sources: 218 (VERIFIED 200 / REJECTED 18)
- Pains: 221; max score 45; 0 pains ≥ 70
- Qualifying PRDs: **0** (REWORK1's 5 are superseded)
- Built MVPs: 2 prototypes, both PARTIALLY_REAL_WORLD_VALIDATED
- Tests: main venv 312 passed / 8 skipped; real-upstream venv 329 passed
- Ruff: clean
- QA verdict: **ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (independent QA agent, 2026-11-06; 363/363 fresh-seed counter-checks; two non-blocking observations: README §3 stale paragraph — fixed by removal — and the disclosed open-stream / sequence-gap residuals)
