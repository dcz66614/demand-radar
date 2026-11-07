# PRD — da75a85dbf1cb9f121cc

- Domain: UK
- Job to be done: plan a transit journey
- Blocker: routing, transfers or fares drop valid journeys or give wrong costs
- Score: 80 (E=30 (9 indep) S=20 (core workflow fails) F=15 (local/public data, some engineering complexity) G=10 (no complete free solution found in checks for this specific blocker) L=5 (reusable data/software skill))
- Independent evidence: 9

## Background and sources
- https://github.com/opentripplanner/OpenTripPlanner/issues/8176
- https://github.com/opentripplanner/OpenTripPlanner/issues/8088
- https://github.com/opentripplanner/OpenTripPlanner/issues/8153
- https://github.com/opentripplanner/OpenTripPlanner/issues/8110
- https://github.com/planarnetwork/gb-transit/issues/129
- https://github.com/opentripplanner/OpenTripPlanner/issues/8128
- https://github.com/opentripplanner/OpenTripPlanner/issues/8144
- https://github.com/opentripplanner/OpenTripPlanner/issues/8095
- https://github.com/opentripplanner/OpenTripPlanner/issues/8143

## User
A user of the tools in the evidence above, trying to complete the job above.

## Job to be done
plan a transit journey

## Current blocker
routing, transfers or fares drop valid journeys or give wrong costs

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
