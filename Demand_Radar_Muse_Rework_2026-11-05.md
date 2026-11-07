# Muse REWORK1 - Mandatory corrective execution order

The original project `demand-radar-2026-11-05.zip` is **NOT ADOPTED** for final research/product acceptance. Read the full independent audit `Demand_Radar_Full_Audit_2026-11-05.md` and the original execution plan before acting. Your role is implementation, not planning. Do not try to defend prior results or silently relax a gate.

## Non-negotiable constraints

- Work in a new isolated copy/branch named `demand-radar-rework1`. Preserve original ZIP/DB/PRDs unchanged, with SHA-256.
- No extra paid resources, private files, public posting, GitHub writes, messages or account signups.
- No attempt to force 20 PRDs or 2 MVPs. Real evidence and actual gate results determine delivery size.
- Maintain `reports/rework1/STATUS.md` and `reports/rework1/decision_log.jsonl`; every stage logs commands, exit codes, row counts, check samples and failures.
- Start only once all files were read. Then execute R01 onward, not a new speculative design discussion.

## R01: Make package executable and testable (first)

1. Update README to use `python -m pip install -e .` after dependencies. Verify an untouched fresh extract and clean venv runs exact README commands; document command output.
2. Replace the CLI `score` stub with a real orchestrated scoring command. Make `report --stage` non-deceptive (actual stage filtering or remove option).
3. Add tests for `__main__.py`, HN collector, `extract.py`, status transitions and deterministic exports; execute all tests.
4. New integration tests must fail on the old code and pass on the fixed code. Do not alter expectations to make failures disappear.

## R02: Correct source-review state and trace

1. Inspect all 218 source records. Capture title, URL, excerpt hash, platform ID, created/updated timestamp, GitHub state and state reason, published issue labels where obtainable.
2. Review each record against the actual original post, with verdict VERIFIED / REJECTED / PENDING and a written problem-relevance rationale. GitHub repository membership by itself is not sufficient.
3. Preserve prior pilot rejections unless a reviewer documents a reason to override. Exclude weak HN listing threads and cross-domain content from eligible evidence.
4. Persist source_items.status and audit trail; default UI and VERIFIED export must exclude rejects.
5. Persist a privacy-preserving author hash for internal duplicate/repost checks; do not export personal identifiers or author login names.

## R03: Repair independence, grouping and scoring

1. Preserve issue-level raw evidence and source links; separate theme/category labels from actual distinct needs.
2. `evidence_count` must mean one documented unit consistently: preferably raw unique URLs. Add `independent_evidence_count` derived from documented author/context/organization groups, not raw issue rows.
3. Add tests proving: three issues from one author count once, two reposts of one issue count once, two unrelated issues in the same repository are not automatically the same demand, and one repository theme is not automatically corroborated across organizations.
4. Recalculate evidence E, cap-59, PRD gate and MVP gate from independent count. Produce before/after rank diffs and include selected-old scores vs corrected scores.
5. F/S/L values require case-specific rationale, not one default per thematic label. If unknown, cap/reject conservatively rather than pretend validated.

## R04: Real competitor evidence

1. Implement `src/demand_radar/competitors.py` and populate `competitor_checks` with exactly grounded product names, versions, official URLs, observed capabilities, gaps, check date and reviewer reasoning.
2. For each PRD candidate inspect at least two real alternatives or record a bounded and reproducible failed-search trail. If there is no evidence, mark the competitor gap UNKNOWN and block the original qualifying gate instead of awarding G=10.
3. Add competitor gating tests. Never write a generic sentence that 'obvious free alternatives were checked' unless records exist.

## R05: Rewrite PRDs, run gates again

1. Re-score and re-rank after R02-R04. Produce `reports/rework1/ranking.csv`, `reports/rework1/qualifying_prds.csv`, `reports/rework1/not_qualified.csv`.
2. Archive old PRDs as `superseded`, retain provenance. Rewrite only qualified ones; each must include a precise user task, source quotations/paraphrases with URL, actual workaround and impact, two competitor checks, sample input, expected output and 3-5 unique acceptance tests.
3. Implement deterministic `selection.py`, `prd.py` and unit tests. Same selection must regenerate from the same database; maintain `mvp_selection.json` with explicit rejection reasons.

## R06: Deliver real, problem-matched MVPs

- If selecting AI API reliability: a controlled fault-injection validator (timeouts, 429/500, bad structured responses, hidden model defaults, token-budget errors), producing independently verifiable pass/fail and regression tests. Not a generic issue list viewer.
- If selecting SEC/XBRL extraction: actual public SEC filings/filing facts, expected concept labels and values, a parser/validator, source URL/accession/fiscal period, and precision tests. A diff of two unrelated GitHub issue descriptions does not qualify.
- If different candidates are stronger after correction, select them deterministically and develop those instead.
- Each MVP needs >=2 real UI filters, working source-preserving CSV export, invalid-input handling, reproducible offline fixtures, and >=10 meaningful tests. Browser/UI smoke cannot be replaced by bare HTTP 200.
- Do not finalize any MVP unless its *specific PRD blocker* is demonstrably addressed on a genuine example.

## R07: Independent final QA and archival

1. Reproduce T01-T16 from the frozen original plan, mapping each ID to a test and log. Run unit, integration, end-to-end, schema and negative/fault injection tests.
2. Recheck at least 20 explicit evidence URLs including their live issue state; persist checked URL and response metadata, not only '20/20'.
3. Review the original 15-issue spot-check set, including duplicates #41708/#41709/#41710 and closed issues #187/#7634/#1857.
4. Check that `source_items.status`, `pain_points.status`, `prd_cards.status`, scores and exports all agree. Populate `run_events` or document an equivalent immutable machine-readable event trail.
5. Package only source, reproducible data, DB and reports; exclude `.pytest_cache`, `.ruff_cache`, `.venv`. Record SHA256 manifest, dependency versions, clean-room command logs and independent review signoff.
6. Final summary must clearly distinguish VERIFIED, UNKNOWN, REJECTED, BLOCKED, FAILED and NOT_TESTED. Never describe an API/SEC issue browser as a fixed API/SEC product.

## Exact stop/go

- Gate R02 fails -> stop scoring and MVP work.
- Gate R03 fails -> stop PRD and selection.
- Gate R04 fails -> deliver research evidence only; 0 qualifying PRDs under original gate.
- Gate R05 has <2 eligible MVP pains -> build 0-1 MVP; record `MVP_GATE_NOT_PASSED`.
- Gate R06 behavior does not solve cited example -> mark MVP `NOT_ACCEPTED`, keep failed tests.
- Gate R07 tests or fresh-install README fail -> mark delivery `REWORK_REQUIRED`.

Begin execution now. Only ask the owner before extra paid spending, credential/identity authorization or external write actions. Save regular progress snapshots and deliver actual files, not reassurance.
