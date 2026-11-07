# Demand Radar — Final report

Standalone project. No P number, no relation to the P series.
Date: 2026-11-05. Execution: Muse itself, no free-model quota used. Extra spend: £0.

## Funnel (real counts, from SQLite)

- Fetched source_items: 218 (target ~240 — shortfall, SOURCE_LIMITED; see coverage)
- VERIFIED source_items: 207; REJECTED: 11 (spam/bot 2, wrong-domain 9)
- Strict pain points (near-duplicate clusters, >=90 similarity): 204, of which 0 have >=2 independent sources
- Thematic pain points (domain + job + failure class, >=3 items): 17
- Total pain_points in DB: 221; evidence_links: 369
- PRDs written: 17 (target 20 — PRD_SHORTFALL, thresholds not lowered)
- MVP selection: 2 selected, both score 80, >=2 sources
  - MVP A: AI ai-agent-api, T1 issue_triage, mvps/mvp_a/
  - MVP B: FIN fin-data, T2 doc_trace, mvps/mvp_b/
- Tests: pytest 40 passed (16 core + 12 + 12 MVP), ruff clean
- Evidence URL re-check: 20 sampled, 20 OK, 0 failed

## Top 5 pains (ranking.csv)

1. BIO process physiological signals correctly — 80, 19 evidence
2. AI drive an AI agent / API reliably — 80, 19 evidence
3. BIO read and write biosignal files — 80, 16 evidence
4. FIN fetch market/financial data reliably — 80, 16 evidence
5. FIN read SEC filings accurately — 80, 9 evidence

## What was delivered

- Workbench: Streamlit app (`app/streamlit_app.py`, HTTP 200), SQLite DB, CSV/JSON export
- MVP A: triage board over 5 real AI issues, theme/priority, filters, CSV export
- MVP B: document trace over 5 real FIN filing extracts, diff view, filters, CSV export
- All code, data, reports and tests under `~/projects/demand-radar/`

## Honest limitations

1. Strict clustering found no multi-source pain: seed-repo issues are repo-specific bugs.
   The 17 PRDs rest on thematic clustering (P05b, documented in `reports/theme_clusters.md`):
   distinct issues grouped by workflow + failure class, with every evidence URL listed.
   A theme is a workflow pain, not one identical bug — read the PRD evidence lists, not just the score.
2. Two HN items counted VERIFIED are weak: "Who is hiring?" (a listing thread, 1 of 8 items in the
   JOB job-scrape theme — removing it leaves 7 items, E stays 30, score unchanged) and the Gemini
   training post (matched "train" as a keyword; it is in no thematic pain, so it affects no PRD).
3. JOB/UK/RES are SOURCE_LIMITED (23/28/33 fetched vs 40 target): few on-domain public repos.
4. No market-size, revenue or product-market-fit claim is made anywhere. Scores are research priority, not demand proof.
5. No real user interviews were done (out of scope).

## Reproduce

```
cd ~/projects/demand-radar
. .venv/bin/activate
python -m demand_radar init
python -m demand_radar report --stage final
python -m pytest -q
python -m ruff check .
python -m streamlit run app/streamlit_app.py
python -m pytest mvps/mvp_a/tests mvps/mvp_b/tests -q
```

## Security / privacy

- Public sources only; short excerpts (<=300 chars); no author personal data exported (source_items.csv has no author_key values).
- No external posts, emails, submissions, purchases, or private-project access. Reddit disabled.
