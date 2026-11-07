# PRD — cd021eac3c93ed0d2de1

- Domain: BIO
- Job to be done: read and write biosignal files
- Blocker: file reading/writing, format conversion or parameter handling fails
- Score: 80 (E=30 (16 indep) S=20 (core workflow fails) F=15 (local/public data, some engineering complexity) G=10 (no complete free solution found in checks for this specific blocker) L=5 (reusable data/software skill))
- Independent evidence: 16

## Background and sources
- https://github.com/neuropsychology/NeuroKit/issues/1162
- https://github.com/MIT-LCP/wfdb-python/issues/618
- https://github.com/mne-tools/mne-python/issues/14428
- https://github.com/MIT-LCP/wfdb-python/issues/528
- https://github.com/MIT-LCP/wfdb-python/issues/568
- https://github.com/MIT-LCP/wfdb-python/issues/522
- https://github.com/MIT-LCP/wfdb-python/issues/515
- https://github.com/mne-tools/mne-python/issues/14460
- https://github.com/MIT-LCP/wfdb-python/issues/554
- https://github.com/MIT-LCP/wfdb-python/issues/524
- https://github.com/MIT-LCP/wfdb-python/issues/543
- https://github.com/MIT-LCP/wfdb-python/issues/594
- https://github.com/MIT-LCP/wfdb-python/issues/593
- https://github.com/MIT-LCP/wfdb-python/issues/534
- https://github.com/MIT-LCP/wfdb-python/issues/547
- https://github.com/mne-tools/mne-python/issues/14431

## User
A user of the tools in the evidence above, trying to complete the job above.

## Job to be done
read and write biosignal files

## Current blocker
file reading/writing, format conversion or parameter handling fails

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
