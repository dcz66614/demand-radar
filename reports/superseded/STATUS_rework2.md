# Demand Radar — STATUS (current: REWORK2)

Standalone project. No P number, no relation to the P series.
Storage after completion: separate Google Drive folder (not `agent project auto`).
Execution: Muse itself, no free-model quota used. Extra spend: £0.

> **Current version is REWORK2 (2026-11-06).** The REWORK1 report
> (`reports/final_report.md`) and the original P00–P10 status file
> (`progress/STATUS.md`) are preserved as history in
> `reports/superseded/` — do not read them as current state.
> Current report: `reports/final_report_rework2.md`.
> Stage reports: `reports/rework2/r2_01.md` … `r2_06.md`.
> Original + REWORK1 delivery zips are read-only; the REWORK2 zip is
> `demand-radar-rework2-2026-11-05.zip` (see `reports/rework2/r2_06.md`
> for its SHA-256).

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
839,767 bytes). **REWORK1's conclusions are superseded by REWORK2 below.**

## REWORK2 (R2-01–R2-06, 2026-11-06)
STATUS: DONE (packaging complete; independent QA verdict pending — see
`reports/rework2/r2_06.md` §7, to be filled by the QA agent)

- R2-01: 5 adversarial regression tests RED → GREEN (RSA, RSP phase,
  JSON schema bool, streaming correlation). Suite 212 at the time.
- R2-02: trapz test fixed (asserts `np.trapezoid` use + numeric value,
  not `hasattr(np,'trapz')`); suite passes in main venv (NumPy 2.5.4)
  and NumPy 2.3.5 venv; Python 3.13 NOT_TESTED (not installed).
- R2-03: 76 evidence links classified (38 DIRECT / 10 ADJACENT /
  5 DUPLICATE / 23 OUT_OF_SCOPE / 0 UNKNOWN); DIRECT-only recount.
- R2-04: evidence-bound scoring (F=0/L=0 unproven, UNKNOWN competitor
  blocks G); gate 70 UNCHANGED; **qualifying PRDs 0** (max new score 45).
- R2-05: both MVPs PARTIALLY_REAL_WORLD_VALIDATED (real tiktoken 0.14.0,
  real neurokit2 0.3.0 / wfdb 4.3.1, real MIT-BIH 100 10 s sample);
  #340 Qwen claim stays NOT_REAL_WORLD_VALIDATED. Validators must NOT
  offset PRDs eliminated by re-scoring.
- R2-06: this report; old reports archived to `reports/superseded/`;
  `reports/mvp_selection.json` restructured (`prd_eligible` 0,
  `mvp_built` 2 prototypes); `prd_cards` aligned to the R2-04 gate
  (0 QUALIFIED / 17 SUPERSEDED); delivery zip rebuilt and clean-room
  verified.

## Headline numbers (all computed from the live DB, 2026-11-06)
- Sources: 218 (VERIFIED 200 / REJECTED 18)
- Pains: 221; max score 45; 0 pains ≥ 70
- Qualifying PRDs: **0** (REWORK1's 5 are superseded)
- Built MVPs: 2 prototypes, both PARTIALLY_REAL_WORLD_VALIDATED
- Tests: main venv 243 passed / 8 skipped; real-upstream venv 260 passed
- Ruff: clean
- QA verdict: PENDING (independent QA agent)
