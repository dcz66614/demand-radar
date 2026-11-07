# R02 — Source review state and trace (2026-11-05)

Reviewer: Muse (this agent). Every one of the 218 source_items was checked
against the live post. No verdict was copied from the old rule-based review.

## Result

| Verdict | Count |
|---|---:|
| VERIFIED | 200 |
| REJECTED | 18 |
| PENDING | 0 |
| **Total checked** | **218** |

By domain (VERIFIED / REJECTED): AI 42/3, BIO 44/0, FIN 42/3, JOB 16/7,
RES 33/0, UK 23/5. Live states: 111 GitHub OPEN, 102 GitHub CLOSED,
5 HN open. `closed_at` captured for 88 of the 102 closed issues (see §4).

DB `source_items.status` now mirrors the verdict (was `FETCHED` for all 218):
`status`/`review_verdict` counts are VERIFIED 200, REJECTED 18. `review_reason`,
`reviewed_at`, `author_hash` (sha256 hex only — no login names stored),
`issue_state`, `issue_state_checked_at`, `issue_labels` are persisted for all 218.

## Method and tools (all read-only; no external writes)

- GitHub: authenticated GitHub MCP via `/opt/hatch/bin/github call-read-tool`.
  `issue_read` is NOT in the reviewed read-only set — it errors
  ("use `call-tool` so it receives write-capable approval"), so it was NOT
  used. `list_issues` (per repo OPEN+CLOSED, cursor pagination, stop when all
  needed numbers found, max 15 pages/state) returned number/title/body/state/
  author/labels/created_at/updated_at for all 213 GitHub issues
  (6,048 issues scanned across 14 repos; 0 fetch errors).
  `search_issues` (title/body/single-token keyword queries, filtered by issue
  number) supplied `closed_at`/`state_reason` for 88 closed issues.
- Hacker News: Firebase API `https://hacker-news.firebaseio.com/v0/item/<id>.json`
  for all 5 items.
- Scripts: `reports/rework1/fetch_live_r02.py` (exit 0),
  `fetch_closed_meta_r02.py` (exit 0, 37/102 matched),
  `fetch_closed_meta_r02b.py` (exit 0, +50 matched),
  single-token retry inline (exit 0, +1 matched),
  `build_verdicts_r02.py` (exit 0, 218 lines, 200/18/0).
- Raw evidence: `reports/rework1/review_r02_raw_github.json`,
  `review_r02_raw_hn.json`, `review_r02_raw_closed.json`,
  `review_r02_working.json`.
- Review trail: `reports/rework1/review_r02.jsonl` (one line per source:
  source_id, url, verdict, reason, issue_state, closed_at, checked_at,
  excerpt_hash = sha256 of live body first 300 chars).

## Rubric (read from the live post; repo membership alone is NOT enough)

- VERIFIED: live post states a concrete firsthand problem/blocker (bug, wrong
  result, silent failure, missing capability with a concrete use case, or a
  genuine question about a failure) relevant to its assigned domain. Feature
  requests / RFCs with a concrete use case count. Closed state alone does NOT
  reject (resolution was not checked from comments); the state is recorded so
  R03/R05 can weigh it.
- REJECTED: spam/bot content, vendor self-promotion, withdrawn post,
  listing/survey thread with no blocker, title-only request with no use case,
  or content belonging to another domain.

## Rejections (18) — all with a written reason in review_r02.jsonl

- AI (3): markitdown#2799 spam PDF "HAVAALAN" (pilot rejection preserved);
  AgentLab#288 self-promotion of the reporter's own libraries;
  HN 50366117 "What's your current AI agentic setup?" survey thread.
- FIN (3): OpenBB#7640 ViBo paid-product promotion; OpenBB#7641 NeuForge Pay
  promotion; OpenBB#7667 withdrawn by author.
- JOB (7): HN 50338728 "Who is hiring?" listing thread and HN 50377668
  Dependabot-fatigue discussion (both pilot rejections preserved);
  jupyterlab#20035/#20062/#20177/#20183 real bugs but wrong domain for JOB
  (P05 rejections preserved); JobSpy#440 title-only feature request, empty body.
- UK (5): HN 50363461 Gemini-training privacy post (pilot rejection preserved,
  wrong domain); jupyterlab#20017/#20167/#20304 real bugs but wrong domain
  (P05 preserved); gb-transit#230 Renovate Dependency Dashboard bot listing.
- BIO 0, RES 0.

One P05 rejection was OVERTURNED with a documented reason:
jupyterlab#20323 ("please update snapshots" bot) — the live body shows a real
CI failure (bot fails to commit since August due to a broken pre-commit hook,
with root cause and fix). The P05 spam keyword matched the bot command name,
not spam content. Now VERIFIED.

## Audit spot-checks re-verified (exact)

- LangChain #41708/#41709/#41710: same author (one author hash), same title
  and body, filed within minutes; #41708/#41709 CLOSED, #41710 OPEN. Each is
  individually a real bug report (VERIFIED); they count as ONE independent
  source in R03, not three.
- AgentLab #187: VERIFIED, CLOSED, closed_at 2025-01-06T13:48:28Z,
  state_reason completed (matches audit: closed 2025-01-06).
- OpenBB #7634: VERIFIED, CLOSED, closed_at 2026-10-11T19:48:25Z,
  state_reason completed (matches audit: closed 2026-10-11).
- EdgarTools #1857: VERIFIED, CLOSED, closed_at 2026-11-01T23:34:12Z,
  state_reason completed (matches audit: closed 2026-11-01).
- Also confirmed as same-author duplicate filings (R03 input):
  LangChain HSTC #41716/#41717/#41718 (one author, 26 min span),
  OpenBB #7650/#7651 (one author, 9 min apart, identical body),
  yfinance #3011/#3012 (one author, resubmission, 2 min apart).
- Same-author concentration found (R03 input): 136 distinct authors for 213
  GitHub issues; synfonia-llc 18 issues, krassowski 15, joelfuller2016 5,
  tompollard 4, iis-MarkKuang 4, abhi85 4, t2gran 4.

## Limitations (honest gaps)

1. `closed_at`/`state_reason` missing for 14 of 102 closed issues
   (jupyterlab#20017, mne#14463, OpenBB#7640/#7641/#7650/#7655/#7656/#7667,
   pandas#71769, gb-transit#129/#76/#93, yfinance#2930/#2966). Three query
   strategies (title keywords, body keywords, single distinctive token) via
   `search_issues` did not return these records; `list_issues` does not
   expose `closed_at`; `issue_read` requires write-capable approval, out of
   scope. Their `issue_state` (closed) IS recorded; `closed_at` is NULL, not
   invented.
2. Closed-issue resolution was not checked from comments: a closed issue may
   be fixed, wontfix, or duplicate. Verdicts record the problem as real; R05
   must weigh closed state before treating a closed report as an unmet need.
3. Stored titles differ from live titles for 4 issues only by HTML-entity
   escaping (`<` vs `&lt;`, `&` vs `&amp;`, `.values` vs `(<str column>.values`);
   same title semantically. Stored excerpts match the live body after
   whitespace normalisation for 212/213 (exception: JobSpy#440, live body is
   empty — the stored excerpt is the title itself).
4. Excerpt hash is over the live body first 300 chars (whitespace-normalised
   in the working file); it is a review-trail fingerprint, not a claim that
   the stored excerpt is byte-identical.

## UI / export verification (commands + exit codes)

- `python -m demand_radar export --format csv` → 200 rows (VERIFIED-only
  default); `--all` → 218 rows. Same for JSON. Exit 0.
- `app/streamlit_app.py` fixed in R02: default query now adds
  `AND status='VERIFIED'`; a checkbox "显示已拒绝 (REJECTED) 的来源" opts in
  to all 218. `python -m py_compile app/streamlit_app.py` OK;
  `ruff check app/streamlit_app.py` clean; Streamlit headless smoke:
  HTTP 200 on localhost:8501 (exit 0).
- Full suite: `cd /home/hatch/projects/demand-radar-rework1 &&
  . .venv/bin/activate && python -m pytest -q` → **76 passed, exit 0**
  (58 at R01; other parallel R03/R04 agents added tests meanwhile).

## Gate

R02 PASS: 218/218 sources reviewed against live posts, 0 PENDING, verdicts
persisted, REJECTED excluded from default UI and default export, audit
spot-checks re-verified exactly. R03 may proceed (note the 14 missing
`closed_at` values and the same-author clusters above).
