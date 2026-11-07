# Demand Radar — STATUS (current: P2-A)

Standalone project. No P number, no relation to the P series.
Storage after completion: separate Google Drive folder (not `agent project auto`).
Execution: Muse itself, no free-model quota used. Extra spend: £0.

> **Current version is P2-A (2026-11-07).** The POST-R4 report
> (`reports/superseded/final_report_post_r4.md`), the REWORK4 report
> (`reports/superseded/final_report_rework4.md`), the REWORK3 report
> (`reports/superseded/final_report_rework3.md`), the REWORK2 report
> (`reports/superseded/final_report_rework2.md`) and the REWORK1 report
> (`reports/superseded/final_report.md`) are preserved as history in
> `reports/superseded/` — do not read them as current state.
> Current report: `reports/final_report_p2a.md`.
> Current README: `README_P2A.md`.
> Stage reports: `reports/p2a/p2a_01_02.md`, `p2a_03.md`, `p2a_04.md`.
> Original + REWORK1 + REWORK2 + REWORK3 + REWORK4 + POST-R4 delivery
> zips are read-only; the P2-A zip is `demand-radar-p2a-2026-11-07.zip`
> (see `reports/p2a/p2a_04.md` for its SHA-256 and
> `RELEASE_SHA256_P2A.txt` outside the zip).

## P2-A (sixth-round audit P2-A, 2026-11-07)

STATUS: DONE — independent QA verdict ACCEPTED_RESEARCH_PROTOTYPE_ONLY
(2026-11-07, `reports/p2a/p2a_qa.md`, verified on the QA-bound zip SHA
`818ebb91…`, 301 files, MANIFEST 300), delivered as
`demand-radar-p2a-2026-11-07.zip` (SHA-256 `4e55558d…`, 1,503,535 bytes,
305 files, MANIFEST 304) in the Drive 'Demand Radar' folder, download-back
SHA verified twice; `RELEASE_SHA256_P2A.txt` uploaded alongside.
Seventh-round independent audit (2026-11-07): P2A_SCOPE_ACCEPTED /
ACCEPTED_RESEARCH_PROTOTYPE_ONLY on the final delivery bytes; see
`reports/p2a/p2a_06.md` for the errata repack that followed. Open
streams are now `pending`, never counted as a completed success:
`validate_stream` returns `call_chunk_valid` (= `passed`, chunk
coherence, unchanged) + `request_completed_successfully` +
`request_status`; the R1-A app counts the fixture sweep as **7 passed /
13 failed / 0 not checked / 2 pending** of 22 checks (the two pending
rows are the open streaming checks). Frozen baseline 26/26, full suite
346 passed / 8 skipped (×2), real venv 363 passed / 0 skipped, ruff
clean, builder fresh-seed counter-check seed 20261107: 301 trials /
1819 assertions / 0 failed, QA fresh-seed seed 20261109: 60 trials /
466 assertions / 0 failed. No fixture changed; no research conclusion
changed (gate 0/221). QA's 6 non-blocking doc P2s were all fixed at
final packaging (stale suite numbers, README naming the POST-R4 report
as current, missing full-suite logs, dangling p2a_05.md reference,
unrecorded QA-bound SHA); the final zip differs from the QA-bound zip
(SHA `818ebb91…`) only in documentation. The sixth-round audit's
remaining items (P2-B traceability — closed by that audit verifying the
final POST-R4 bytes; P2-C real-environment re-certification; P2-D
research is not a business outcome) still stand. Record correction:
the REWORK1 Drive file id in earlier records was mistranscribed
(`...FCvuOaVsO`); the real id is `1yt6LzAi6Auqr_PZtHE1g51gFCfuOaVsO`
— the file itself was never missing; all six old zips re-verified
unchanged by download-back SHA.

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
**REWORK4's conclusions are superseded by POST-R4 below** (research
numbers unchanged; the validator termination model is what changed).

## POST-R4 (P0-00–P0-05, 2026-11-06)
STATUS: DONE — independent QA verdict
**ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (2026-11-06, see
`reports/post_r4/p0_qa.md`): the fifth-round audit's single P1 defect
(failure terminals ignored, false PASS) is fixed and verified: 7/7 new
termination tests GREEN (was 5 failed / 2 passed), frozen 26/26, full
suite 334 passed / 8 skipped (main venv), MANIFEST 286/286, 3 apps
HTTP 200. QA's own fresh-seed counter-checks 207/207; RED baseline
independently re-verified 5 failed / 2 passed on a fresh REWORK4
extract.

- P0-00: isolated dir extracted from the REWORK4 zip (SHA 15d391be…
  verified); the fifth-round audit's 7 new tests copied verbatim and
  confirmed RED 5/2, log kept; source hashes + env recorded.
- P0-01: four terminal events — `response.completed` /
  `response.failed` / `response.incomplete` / `error` — recorded
  explicitly; data after any terminal is an anomaly; conflicting
  terminal events fail; duplicate identical terminals tolerated but
  recorded.
- P0-02: only a normal completion can pass — a failure terminal
  always FAILS (wrong-result, passed=False) with the terminal kind
  and reason in the detail; completed-with-pending still fails;
  an open stream keeps its chunk-coherence semantics but is labelled
  "request success not yet proven".
- P0-03: UI — the R1-A banner labels open streams and failure
  terminals; failed terminals never count in the passed total;
  fixture sweep unchanged (9 passed / 13 failed / 0 not checked
  of 22 checks).
- P0-04: this report; delivery provenance recorded OUTSIDE the zip
  (`RELEASE_SHA256.txt`); the final report's header states the QA
  verdict for THIS zip only.

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
- Tests: main venv 334 passed / 8 skipped; real-upstream venv 351 passed
- Ruff: clean
- QA verdict: **ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (independent QA agent, 2026-11-06; 207/207 fresh-seed counter-checks; one non-blocking observation: an open stream with all calls done still returns passed=True on chunk coherence — documented design, now labelled)
