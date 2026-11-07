# PRD (R05 rewrite) — 0b7adcf63ec0f2075fab

- Domain: FIN
- Job to be done: use a financial research tool
- Blocker: UI, chart or workspace features are missing or broken
- Score: 70 (corrected R03/R04 scoring; see score_reason below)
- Score reason: E=20 (3 indep orgs, 3 distinct authors, 4 raw URLs) job='use a financial research tool' S=20 (blocker 'UI, chart or workspace features are missing or broken' matches failure keywords ['broken']) F=15 (recorded workaround exists ('see linked issues'); feasibility indicated but NOT validated — F capped at 15 of 20 max) G=10 (checked 2 alternatives, none fully solves (see competitor_checks)) L=5 (no transfer/reuse evidence in record; L capped at 5 (minimum) — no cross-domain reuse claim made) | cross-org corroborated
- Independent organisations: 3; VERIFIED evidence: 4 links (3 closed, 1 open)

## User task
As an investor using a financial research tool (OpenBB workspace, edgartools or yfinance), compare holdings or render charts and get correct, complete values — not wrong numbers, missing data, or an unpatched vulnerable dependency under the hood.

## Evidence (VERIFIED sources only, with quotations/paraphrases)
- [closed] [dgunning/edgartools] https://github.com/dgunning/edgartools/issues/1848
  - [DATA] 13F comparison and history cross-match equity, Put and Call positions on the same CUSIP
  - Quoted/paraphrased from the post: "## Data Quality Issue Details **Issue Type:** - [x] Incorrect financial values (wrong numbers) - [x] Missing financial data (expected data not present) - [ ] Calculation errors (formulas producing wrong results) - [x] Data inconsistency (different values for same metric) - [x] Historical data pro..."
- [open] [openbq-org/OpenBB] https://github.com/openbq-org/OpenBB/issues/7744
  - [Workspace RFC] Pluggable chart renderers, configurable library selection, and optional commercial licensing
  - Quoted/paraphrased from the post: "## Title **[Workspace RFC] Pluggable chart renderers, configurable library selection, and optional commercial licensing** ## Body ### Summary Could Workspace support chart rendering through a documented adapter interface, allowing deployments to choose open-source or commercially licensed librari..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/3011
  - Track CVE-2026-111497 in Brotli bundled with the default curl_cffi backend
  - Quoted/paraphrased from the post: "Superseded by #3012, which uses the required bug-report form headings. This original report was automatically closed by the template checker and could not be reopened. ### Describe bug CVE-2026-111497 is a publicly disclosed memory-safety vulnerability in the Brotli decoder. I am reporting a down..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/3012
  - Track CVE-2026-111497 in Brotli bundled with the default curl_cffi backend
  - Quoted/paraphrased from the post: "### Describe bug Resubmission of #3011: the original was automatically closed for using level-2 headings instead of the required issue-form headings. Its body was corrected, but GitHub does not allow me to reopen it. Please use this report; the original will be marked as superseded. CVE-2026-1114..."

## Actual workaround and impact
No workaround is documented in the record. The OpenBB item (#7744) is an RFC proposing pluggable chart renderers — a requested feature, not a workaround. The yfinance items (#3011/#3012) are a CVE tracking report filed twice (resubmission with corrected headings), not a workaround. Nothing in the record shows a user getting correct 13F cross-match values by another route.

From the evidence: the edgartools 13F comparison cross-matches equity, Put and Call positions on the same CUSIP with incorrect financial values, missing financial data and inconsistent values for the same metric (#1848). The yfinance default curl_cffi backend bundles a Brotli decoder with publicly disclosed memory-safety vulnerability CVE-2026-111497 (#3011/#3012). OpenBB Workspace chart rendering is not pluggable or configurable — deployments cannot choose their rendering library (#7744, an RFC with a concrete use case).

## Competitor checks (R04, checked 2026-11-05, 0 solve the pain)
- OpenBB (not stated on checked page) — https://openbb.co/ (checked 2026-11-05)
  - Observed capability: OpenBB home page: 'Build your own financial workspace' - free investment research platform (terminal/workspace). HTTP 200, 2026-11-05.
  - Gap vs this pain: Does not fix the reported pain: the FIN research-tool issues are filed against OpenBB itself (workspace/UI features missing or broken). An alternative workspace with the same bug class, not a fix.
- TradingView (not stated (web app, no versioned release)) — https://www.tradingview.com/ (checked 2026-11-05)
  - Observed capability: TradingView home page: 'Track All Markets' - charting, screeners and market data. HTTP 200, 2026-11-05.
  - Gap vs this pain: Charting/screener product, not an open research workbench; advanced workspace features are paid tiers. Does not provide the missing/broken open research-tool workflow.

## Sample input
edgartools #1848: a 13F comparison and history cross-match of equity, Put and Call positions on the same CUSIP.

## Expected output
Put and Call positions on the same CUSIP cross-match with consistent values across history; any missing position is flagged as missing — never silently dropped and never shown as a wrong value.

## Acceptance tests
1. The 13F cross-match on the #1848 CUSIP returns the same value for the same metric across history; any missing position is flagged missing, not filled with a wrong value.
2. The bundled Brotli decoder version is checked against CVE-2026-111497 and reported as vulnerable or patched explicitly; a vulnerable default backend fails the check (#3011/#3012).
3. A workspace chart request naming a renderer uses the documented adapter interface instead of silently falling back to a default (#7744).
4. Re-running the same 13F comparison twice returns identical results (deterministic cross-match).

## Caveats and stop conditions
- Thinnest evidence of the five qualifiers: 4 VERIFIED links, effectively 3 distinct reports across 3 orgs (#3011/#3012 are one CVE report filed twice).
- 3 of the 4 VERIFIED evidence items are CLOSED (75%) — closed does not mean solved.
- 2 attached evidence links (OpenBB #7640/#7641, vendor promotion) are REJECTED and excluded from every count; the counted evidence is VERIFIED-only (verified in the R05 gate run).
- The #7744 item is a feature request with a concrete use case, not a bug report; the pain's 'missing or broken' wording covers both, and the PRD does not claim it as a crash.
- Closed evidence items are counted as evidence of a real problem, not as proof the problem is solved: R02 did not check resolution from comments.
- If the linked sources are withdrawn or the blocker is fixed upstream, this PRD is withdrawn.
