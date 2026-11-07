# PRD — e3091fb34139fdf57dbd

- Domain: FIN
- Job to be done: fetch market/financial data reliably
- Blocker: fetchers fail, leak resources, or return wrong values
- Score: 80 (E=30 (16 indep) S=20 (core workflow fails) F=15 (local/public data, some engineering complexity) G=10 (no complete free solution found in checks for this specific blocker) L=5 (reusable data/software skill))
- Independent evidence: 16

## Background and sources
- https://github.com/ranaroussi/yfinance/issues/2963
- https://github.com/ranaroussi/yfinance/issues/2939
- https://github.com/openbq-org/OpenBB/issues/7645
- https://github.com/ranaroussi/yfinance/issues/2931
- https://github.com/openbq-org/OpenBB/issues/7650
- https://github.com/ranaroussi/yfinance/issues/2997
- https://github.com/ranaroussi/yfinance/issues/2937
- https://github.com/ranaroussi/yfinance/issues/2930
- https://github.com/openbq-org/OpenBB/issues/7655
- https://github.com/openbq-org/OpenBB/issues/7813
- https://github.com/openbq-org/OpenBB/issues/7656
- https://github.com/ranaroussi/yfinance/issues/3004
- https://github.com/ranaroussi/yfinance/issues/3033
- https://github.com/ranaroussi/yfinance/issues/2964
- https://github.com/dgunning/edgartools/issues/1855
- https://github.com/openbq-org/OpenBB/issues/7651

## User
A user of the tools in the evidence above, trying to complete the job above.

## Job to be done
fetch market/financial data reliably

## Current blocker
fetchers fail, leak resources, or return wrong values

## Measurable impact
See the linked issues: failures, lost time, or wrong output as described in the sources. No market-size claim is made.

## Competitor gap
Checked: the upstream project's own docs / issue tracker (linked above) and the obvious free alternatives for this workflow. No complete free solution for this specific blocker was found in those checks; the PRD does not claim a market gap beyond the linked evidence.

## MVP input / output
- Input: the public data / files described in the evidence.
- Output: a local, reproducible result addressing the blocker, with source links preserved.

## Features and explicit exclusions
- In scope: the single job above, local execution, source links, CSV export.
- Out of scope: login, payment, external posting, private data, medical/financial decisions.

## Acceptance scenarios
1. Reproduce the blocker from a linked public sample.
2. Run the MVP on that sample and show the blocker is addressed.
3. Export preserves the source URL.
4. Invalid input shows a clear error, no crash / no data loss.
5. At least 10 automated assertions pass.

## Privacy / compliance
Public sources only, short excerpts, no personal data exported.

## Unknowns / stop conditions
If the linked sources are withdrawn or the blocker is fixed upstream, this PRD is withdrawn.
