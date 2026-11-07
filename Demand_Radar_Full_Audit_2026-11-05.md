# Demand Radar - Full delivery acceptance audit

**Audit date:** 2026-11-05 (UTC)  
**Original source:** https://drive.google.com/drive/folders/1Rh_3opzWcHwO8XMeiHhEuwwO98r0doXJ  
**File:** `demand-radar-2026-11-05.zip` (`1Ut526EsAbkNUEe7EqnsfP9CfzHkLg0sL`)  
**Disposition:** **REWORK REQUIRED / NOT ADOPTED** for evidence-backed product discovery; **ACCEPTABLE PROTOTYPE BASE** for local engineering exploration.

## 1. What was actually inspected

- Archive list: 145 entries = 113 files + 32 directory entries, 1,380,164 uncompressed bytes. Among files, 23 are `.pytest_cache` or `.ruff_cache` artifacts; 90 are project files.
- Archive checked with `ZipFile.testzip()` and safe-path checks: no CRC failure, no path traversal or symlinks detected.
- All 13 JSONL files parsed, 231 records checked for unique IDs; 218 unique records (13 redundant occurrences). The six inbox domains were counted separately.
- SQLite opened read-only in the review process, schema/table integrity checked (`PRAGMA integrity_check = ok`, foreign key check empty). Tables and fields reviewed.
- All 17 PRD Markdown files screened for required sections, repetitive boilerplate, evidence-link reconciliation and core claims. Their linked evidence rows were compared to SQLite.
- All production Python files, both MVPs, test code, configuration, SQL, documentation and reports were inspected. 40 tests re-run independently. Python compileall passed.
- An independent coverage run yielded **58% for the included production module set** (excluding tests); the Streamlit pages, CLI, HN collector and extractor had 0% statement coverage in that run.
- GitHub connector fetched 15 selected underlying issues for independent spot checks of titles, state and creation/closure metadata. 9/15 were closed at inspection. These are sample checks, NOT a verification of all 213 GitHub issue URLs.
- `ruff` and the Streamlit GUI were **not** independently run in this audit environment (binaries/dependencies absent), so the submitted claims of lint success and HTTP 200 were not independently certified.
- The archive was copied/extracted for testing; **no Drive contents were edited**.

## 2. Counts: confirmed vs interpretation

| Metric | Observed | Interpretation |
|---|---:|---|
| Source items | 218 | Real stored issue/post records; project target 240 is short by 22 (disclosed) |
| Github / Hacker News items | 213 / 5 | Very concentrated in developer issue trackers |
| Script-labelled VERIFIED / REJECTED | 207 / 11 | Reviewer classifications, not individually re-verified in this audit |
| `source_items.status` equal to `FETCHED` | 218 | The reviewer result is NOT persisted in source status |
| Strict near-duplicate pain records | 204 | Many are single-issue records, not independently corroborated needs |
| Thematic pain records | 17 | The same underlying evidence is reused, not 17 fresh sources |
| Combined pain-point records | 221 | Not equivalent to 221 unique independently confirmed demands |
| Evidence associations | 369 | Links across strict AND thematic records; not 369 independent sources |
| Competitor-check database rows | **0** | Violates an explicit mandatory PRD/MVP gate |
| PRDs | 17 | All are `DRAFT`, `template_id='TBD'` |
| Run events | **0** | No machine-readable execution/decision audit trail |
| MVPs delivered | 2 | Demonstration utilities, not validated solutions to claimed blockers |
| Unit tests | **40 passed** | Independently reproduced in this audit environment |

## 3. Critical defects (block acceptance)

### P0-01: Competitor evidence invented at the reporting layer

**Evidence:** `data/demand_radar.sqlite:competitor_checks` contains exactly **0 rows**. `score_prd.py:34-39` awards all pains `G=10` with an assertion that no complete free solution was found. `score_prd.py:94-95` writes the same assertion to every PRD. The execution plan section 5.2 requires >=2 recorded checks per qualifying PRD.

**Impact:** All 17 PRDs fail the documented competitor-research entrance gate; their `G` dimension is unsupported. A textual statement of checking upstream issue trackers is not a substitute for records of product/version, URL, capability, findings and review date.

**Fix:** Write and execute `src/demand_radar/competitors.py`; store at least two direct, independently checked alternatives for each PRD *candidate*. If none are found after documented searches, store the actual search trail and set the appropriate unknown score (do not default to 10). Recalculate gates.

### P0-02: Independent evidence arithmetic is wrong

**Evidence:** `theme_cluster.py:105-110` sets `pain_points.evidence_count = len(items)`; `score_prd.py:15,38-39,58-59` uses that as the number of **independent** sources. Yet the evidence table already has `independence_group`. For instance, AI `ai-agent-api` has 19 issue associations but only **3 existing independence groups** (AgentLab, LangChain, HN); FIN `fin-data` has 9 issue associations but only **2 groups** (EdgarTools, OpenBB). Three LangChain issue IDs `#41708`, `#41709`, `#41710` are the same-title report from the same GitHub author, per GitHub issue metadata.

**Impact:** With *only* the E component corrected using distinct existing groups, AI score 80 -> 70; FIN score 80 -> **65**, below the selection gate of 70. Other themes with only 1 existing group were wrongly admitted as multi-source PRDs. Exact person-level independence is still unverified because author pseudonymous keys are not stored.

**Fix:** Add an explicit `count_independent_evidence(pain_id)` query and use it consistently for E, cap-59, PRD and MVP gates. Reintroduce privacy-preserving author hashes for internal independence reviews without exporting usernames. Document limitations and cluster at genuine shared-job/blocker granularity.

### P0-03: MVP results do not address the selected problem

**MVP A** (`mvps/mvp_a/triage.py`, `app.py`): keyword-classifies and displays public GitHub issues. Selected pain is *AI agent/API calls fail, wrong results, hidden defaults*. The MVP does not reproduce API faults or detect/recover the claimed failures. Triage of bug reports is a different user problem.

**MVP B** (`mvps/mvp_b/trace.py`, `app.py`, `data/sample.csv`): compares two text snippets taken from unrelated GitHub **issue descriptions**. These are not SEC filings or multiple versions of the same filing. It does not parse XBRL, check filed concepts or reproduce misclassification errors. The export function outputs only `kind,line`, not `source_url`, violating PRD acceptance scenario #3. UI exposes only one keyword filter, although the frozen minimum is two.

**Impact:** Both MVPs are functioning small demos, but neither demonstrates that the chosen user blocker has been fixed. They must NOT be described as validated solutions to the selected pain points.

**Fix:** Either choose new independently proven demand statements that exactly match the existing demos, OR rebuild the products to solve the original problems with source-grounded before/after fixtures and measurable assertions. Do not adapt tests to a weak implementation.

### P0-04: Review verdicts and reproducible auditability are incomplete

**Evidence:** `review_p05.py:32-48` marks most GitHub issues from seed repositories VERIFIED automatically if excerpts are long enough and not in a short spam list. This is not independent semantic review of who, job, actual blocker and relevance. Database `source_items.status` remains `FETCHED` for all 218 items, while reports claim 207 verified and 11 rejected. Eleven rejected items still appear in the exported 218 source-item rows and the default workbench.

**Impact:** A consumer of the exported database cannot reproduce the claimed verification funnel from the canonical `status` column. Previously rejected pilot items were re-admitted by the final keyword-based reviewer without per-record override evidence. No source-state or issue-resolution checks are persisted.

**Fix:** Persist review verdicts, reviewer rationale, checked timestamp, evidence URL and issue state; carry forward previous rejection unless explicitly overturned with a documented reason. Exclude rejected rows from VERIFIED exports/default UI. Store immutable review records and URL spot-check samples.

### P0-05: The documented clean installation does not work

**Evidence:** Root `README.md` says `pip install -r requirements.txt` then `python -m demand_radar init`, but this is a `src/`-layout project and no editable installation or `PYTHONPATH` is configured. Reproduced on the extracted archive: `python -m demand_radar init` -> `No module named demand_radar`. The self-reported clean-room retest did an **additional** `pip install -e . --no-deps` not included in README. With `PYTHONPATH=src`, the 40 tests pass.

**Further:** `src/demand_radar/__main__.py:56-58` has a `score` command that prints a message and exits 0 without calculating any score; `report --stage` ignores the stage. The generated ranking is created separately by `score_prd.py`, whose required execution path is missing from the README.

**Fix:** Add `python -m pip install -e .` to clean setup, implement a real CLI score/selection workflow, add a disposable database path, and verify exact README commands (not augmented commands) from a fresh archive.

## 4. Other material findings (P1/P2)

1. **PRDs are nearly identical scaffolds.** All 17 contain identical user-persona, impact and competitor paragraphs and the same five generic acceptance scenarios. No task-specific baseline, reproducible failure or quantitative success threshold is documented. See `reports/prds/PRD_*.md` and `score_prd.py:71-117`.
2. **Scores are largely preassigned, not evidence-derived.** `S` is based on keyword triggers in often model-written theme descriptions; `F=15`, `G=10`, `L=5` almost universally. This undermines a purported five-dimensional ranking.
3. **The source distribution violates the intended final diversity ratio.** The 35% cap applies inside the expansion script, not to the combined pilot+expansion datasets. Largest single-repository shares are RES 57.6%, BIO 43.2%, FIN 42.2%, JOB 73.9%, UK 64.3%; the shortfall is acknowledged but the final coverage report's cap claim is misleading.
4. **Open/closed status and resolution are missing.** In 15 GitHub issue spot checks, nine were closed. Examples: [AgentLab #187](https://github.com/ServiceNow/AgentLab/issues/187) closed 2025-01-06, [OpenBB #7634](https://github.com/openbq-org/OpenBB/issues/7634) closed 2026-10-11, [EdgarTools #1857](https://github.com/dgunning/edgartools/issues/1857) closed 2026-11-01. Closed is not always solved, but it requires a closer look before claiming an unmet need.
5. **Insufficient meaningful test coverage.** 40 tests pass, but 58% of included production statements were covered in our run. Streamlit screens, CLI, HN collector and issue extraction were untested; no integration test verifies the full source-to-MVP pipeline. Required frozen tests for cross-platform author independence, candidate gate, selection and README clean install are missing.
6. **Missing planned modules and logs:** `src/demand_radar/competitors.py`, `src/demand_radar/prd.py`, `src/demand_radar/selection.py`, `tests/test_selection.py`, `tests/test_dedupe.py`, `progress/blockers.md` absent. The `run_events` table has 0 rows. `progress/STATUS.md` contains a duplicate P01 heading.
7. **Weak reproducibility of evidence review.** URLs and <=300-character excerpts are present, but explicit source review excerpts, actor-level independence rationale, issue state and reviewer signatures are absent. The evidence URL recheck claims 20/20 but does not list its checked URLs and response traces.
8. **Data-model/status drift:** `source_items` is all FETCHED, `pain_points` all VERIFIED, and `prd_cards` all DRAFT/TBD. These are distinct concepts and should be reconciled through explicit state transitions.
9. **Default app is a basic issue browser.** It shows up to 200 of 218 rows with no pagination, no linked PRD/ranking view, and no default verified-only filter; it does not yet deliver the promised discovery decision cockpit.
10. **Distribution quality:** `.pytest_cache` and `.ruff_cache` are shipped in the ZIP (23 files). Update `.gitignore`/packaging rules; include checksums and reproducible command logs instead.

## 5. Positive findings to preserve

- Source records are not obviously fabricated: 15 sampled GitHub issue titles, IDs, and timestamps matched real provider data.
- Six-domain dataset exists, 231 JSONL lines reduce to 218 unique source IDs, CSV/JSON exports each have 218 rows. The gap to 240 is explicitly disclosed.
- SQLite passes integrity and foreign-key checks.
- Basic GitHub collector filters PRs and has a bounded retry path for rate-limits.
- No plaintext API secrets matching common token formats were found in source/config files; workflows are read-only toward external sites. This is a limited scan, not a comprehensive security certification.
- All 40 included pytest tests pass under `PYTHONPATH=src`; Python compilation passes.
- No evidence of unauthorized payments, account actions or changes to other local projects is visible in this archive; those claims cannot be confirmed solely from an exported ZIP.

## 6. Gate-based rework order

**G0 - Preserve original:** Record original ZIP SHA-256; produce a separate `rework1` branch/directory and immutable audit log. Do not overwrite the original source during correction.

**G1 - Restore evidence and review truth:** Reprocess all 218 source items; persist each verdict and reasons, categorize source state, remove bad HN and off-topic records from eligible evidence without deleting raw inputs, record closed/reopened timestamps and source URLs, and add privacy-preserving author/group IDs.

**G2 - Repair independent counting and clustering:** Add tests for multiple issues from one author, cross-platform repost, 1-repo theme, same underlying issue, and distinct genuine scenario. Report independent groups separately from raw references. Preserve the existing evidence relationship trace.

**G3 - Rebuild competitor checks:** For each PRD candidate, log >=2 actually inspected competitor/alternative sources or a bounded search-failure trail with UNKNOWN status. No default positive competitor-gap score.

**G4 - Re-score / re-gate PRDs:** Recompute all score components from documented inputs, cap weak independence at 59, and rebuild only qualifying PRDs. Do not target 20 arbitrarily. Current 17 PRDs are not accepted; archive them as `superseded`.

**G5 - Re-select MVPs:** Apply the original score >=70 and independence/competitor gates. An independent reviewer must sign off both selection ID and *user problem to implemented behavior* mapping. If fewer than two qualify, deliver 0-1 and mark `MVP_GATE_NOT_PASSED`.

**G6 - Rebuild actual prototypes:** For the chosen pains, use controlled real-world artifacts and exact before/after validation. If AI API reliability: validate timeout/error/invalid response/default substitution without paid API dependency. If SEC reading: load a real public filing/XBRL sample and validate mapped concepts/facts and provenance. Otherwise choose demos matching actual proven demand.

**G7 - Test and package:** Implement T01-T16, and >=10 independent targeted assertions per MVP. Include end-to-end CLI and UI tests and a clean-room README run on a fresh extract. Retain complete command output/exit codes and source review IDs. Set source state correctly and update default UI/export filters. Remove build caches from ZIP. Run CRC, schema integrity, score reconciliation and file manifest checks.

## 7. Machine-checkable exit criteria

- Database `source_items` statuses match independently recorded verdict counts; VERIFIED exports exclude REJECTED.
- Every PRD has >=2 truly independent first-hand sources and >=2 documented competitor checks (or explicit blocked/unknown gates); no raw issue count masquerades as an independence count.
- Every score's five components have independent evidence or an explicit UNKNOWN handling policy, and re-running the scoring CLI reproduces `ranking.csv` byte-for-byte or via canonical semantic equality.
- A selection candidate with corrected score <70 cannot be selected. Same-author/cross-post examples are covered by tests.
- MVP behavior matches the acceptance scenario in its PRD, including real input artifacts, measurable before/after output and source preservation in export. No UI based solely on issue excerpts counts as proof of solving financial-data or API errors.
- Following README instructions on a fresh archive runs CLI report, scoring, tests and at least the main app without undocumented environment variables or commands.
- Required tests T01-T16 are mapped to test names and result logs, both MVPs have >=10 tests, independent QA is evidenced.
- No added spend, no unauthorized external writes, no modifications to unrelated user projects.

## 8. Final call

**Do not adopt this as completed evidence-driven product incubation.** It is a useful starting prototype with authentic seed data and working basic tests, but its core scientific/decision claims are unsupported or incorrect. Rework evidence accounting, competitor research and MVP-to-pain alignment before investing in more candidate volume or more UI decoration. The source archive should remain unchanged pending explicit permission.
