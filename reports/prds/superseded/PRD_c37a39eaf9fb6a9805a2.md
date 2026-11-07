# PRD — c37a39eaf9fb6a9805a2

- Domain: AI
- Job to be done: convert documents to Markdown accurately
- Blocker: conversion drops, corrupts or mis-renders content (math, tables, footnotes, JSON)
- Score: 65 (E=30 (10 indep) S=5 (minor inconvenience) F=15 (local/public data, some engineering complexity) G=10 (no complete free solution found in checks for this specific blocker) L=5 (reusable data/software skill))
- Independent evidence: 10

## Background and sources
- https://github.com/microsoft/markitdown/issues/2724
- https://github.com/microsoft/markitdown/issues/2744
- https://github.com/microsoft/markitdown/issues/2667
- https://github.com/microsoft/markitdown/issues/2806
- https://github.com/microsoft/markitdown/issues/2743
- https://github.com/microsoft/markitdown/issues/2728
- https://github.com/microsoft/markitdown/issues/2804
- https://github.com/microsoft/markitdown/issues/2688
- https://github.com/microsoft/markitdown/issues/2781
- https://github.com/langchain-ai/langchain/issues/41675

## User
A user of the tools in the evidence above, trying to complete the job above.

## Job to be done
convert documents to Markdown accurately

## Current blocker
conversion drops, corrupts or mis-renders content (math, tables, footnotes, JSON)

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
