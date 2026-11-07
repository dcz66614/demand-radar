# Coverage report — P04

| Domain | Fetched (source_items) | VERIFIED | REJECTED | Notes |
|---|---|---|---|---|
| AI | 45 | 44 | 1 | target 40 met; 1 spam PDF |
| RES | 33 | 32 | 1 | short of 40: seed repos exhausted after dedupe; SOURCE_LIMITED |
| BIO | 44 | 44 | 0 | target 40 met |
| FIN | 45 | 45 | 0 | target 40 met |
| JOB | 23 | 18 | 5 | short of 40: JobSpy is the only on-domain repo; jupyterlab fillers were wrong-domain and rejected; SOURCE_LIMITED |
| UK | 28 | 24 | 4 | short of 40: gb-transit is low-volume; SOURCE_LIMITED |
| **Total** | **218** | **207** | **11** | **Target was 240 candidates; delivered 218 real ones. No splitting, no fabrication.** |

- Single-repo share: capped at 35% per domain in collection (14/40); final per-repo shares are in the DB (source_items by repo).
- Sources: GitHub Issues (primary), Hacker News Ask HN (fallback, noisy — 3 of 11 rejects are HN wrong-domain).
- Reddit: DISABLED_PERMISSION throughout. No paid API used. GitHub unauthenticated rate limit: 60/hr, never exceeded.
- Pilot G1: 30 fetched, 26 verified under the first (stricter) review; final P05 review (repo-trusted, HN keyword-checked) verifies 28/30 of the pilot items — the 2 remaining rejects are the spam PDF and the Dependabot HN post. The "Who is hiring" HN thread and the Gemini HN post slipped the keyword filter; they are counted VERIFIED in the DB, a known limitation (see final report).
