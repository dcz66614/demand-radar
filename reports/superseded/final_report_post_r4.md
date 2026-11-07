# Demand Radar — Final report (POST-R4, current version)

Standalone project. No P number, no relation to the P series.
Date: 2026-11-06. Execution: Muse itself. Extra spend: £0.
No Drive/GitHub upload in REWORK4 (packaging only; delivery handled separately).

> **This is the single current report.** It supersedes
> `reports/superseded/final_report_rework4.md` (REWORK4),
> `reports/superseded/final_report_rework3.md` (REWORK3),
> `reports/superseded/final_report_rework2.md` (REWORK2) and
> `reports/superseded/final_report.md` (REWORK1), all preserved as
> history in `reports/superseded/`. Research numbers (§1–§6,
> Appendices A/B) are UNCHANGED from REWORK2: they were re-computed
> from the live DB on 2026-11-06 by
> `reports/rework2/compute_final_numbers.py` (output:
> `reports/rework2/final_numbers_r2_06.json`, all assertions passed,
> gate fingerprint identical) — no number was hand-copied from an
> older report. What POST-R4 changes is the validator termination
> model (§8), the test suite (§9), the MVP A capability statement
> (§7), and the packaging (§10). Stage reports:
> `reports/post_r4/p0_01_02_03.md`, `p0_04.md`, `p0_05.md`;
> REWORK4 stage reports: `reports/rework4/r4_01_02_03.md`,
> `r4_04.md`, `r4_05.md`.
> **QA status: the independent QA verdict for POST-R4 is
> ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (see §13) — the REWORK4
> verdict (ACCEPTED_RESEARCH_PROTOTYPE_ONLY) applied to the
> REWORK4 zip only, not to this one.

## Verdict in one paragraph

**0 qualifying PRDs.** Under the R2-04 evidence-bound scoring rule the
gate (70, unchanged — never lowered) is met by no pain: the highest new
score anywhere is 45. The 5 PRDs REWORK1 rewrote are superseded by the
re-score; their files moved to `reports/prds/superseded/` and
`prd_cards` now reads 0 QUALIFIED / 17 SUPERSEDED. The 2 built MVPs
(R1-A, R1-B) are **PARTIALLY_REAL_WORLD_VALIDATED prototypes**, not
products that solve a qualified PRD, and they must not be used to offset
the eliminated PRDs. What survives POST-R4 is: a corrected evidence
base (200 VERIFIED / 18 REJECTED sources), a corrected scoring rule
with an independent re-derivation, 38 DIRECT evidence links in 5
problem signatures, 4 scope-documented competitor non-solves, and two
validators with real upstream validation paths — now with the
fifth-round audit's single new P1 defect actually fixed and verified
(P0-01/P0-02: `response.failed` / `response.incomplete` / `error`
are failure terminals that always fail, never a pass; P0-03: the UI
never counts a failure terminal as passed and labels open streams as
"not yet proven"), on top of the REWORK4 fixes (R4-01 strict JSON,
R4-02 not-checked never a pass, R4-03 `response.completed` as a
terminal signal), plus a delivery whose provenance is recorded
outside the zip. The independent QA verdict for POST-R4 is
**ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (see §13).

## 1. Sources — 218 items, 200 VERIFIED / 18 REJECTED

Live DB (`data/demand_radar.sqlite`, `PRAGMA integrity_check` = ok),
R02 review state (2026-11-05, live-checked per issue then; not
re-checked live in REWORK2 except the 9 load-bearing issues in R2-03).

| domain | VERIFIED | REJECTED | total |
|---|---|---|---|
| AI | 42 | 3 | 45 |
| BIO | 44 | 0 | 44 |
| FIN | 42 | 3 | 45 |
| JOB | 16 | 7 | 23 |
| RES | 33 | 0 | 33 |
| UK | 23 | 5 | 28 |
| **total** | **200** | **18** | **218** |

GitHub 213 items (111 open / 102 closed at R02) + Hacker News 5 (open).
136 distinct GitHub authors. `source_items.status` == `review_verdict`
for all 218 (0 mismatches, re-verified by R07 and unchanged since).
14 of the 102 closed items have NULL `closed_at`/`state_reason`
(R02 honest gap — three query strategies failed; listed in
`reports/rework1/review_r02.md`, not fabricated). Closed ≠ solved:
resolution was never checked from comments.

## 2. Pains and scores — 221 pains, max 45, 0 ≥ 70

Pains by domain: AI 45, BIO 46, FIN 47, JOB 21, RES 35, UK 27 (total 221).
Score distribution under the R2-04 rule: 45 ×3, 40 ×3, 35 ×3, 30 ×78,
25 ×2, 20 ×21, 15 ×103, 10 ×2, 5 ×6. **Maximum possible score under the
new rule without documented F/L evidence is 60** (E30+S20+F0+G10+L0);
no pain can reach 70 without a documented workaround (F) or documented
reuse evidence (L) — neither exists anywhere in the record
(`workaround_status` = UNKNOWN for all 221 pains).

### 2.1 The 5 old candidates, old → new (full diff: `reports/rework2/score_diff.csv`)

| theme | old | new | E | S | F | G | L | DIRECT / orgs / authors | real checks | UNKNOWN checks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0b7a FIN workspace | 70 | **30** | 10 | 20 | 0 | 0 | 0 | 1 / 1 / 1 | 0 | 2 |
| 4bb7 BIO signals | 70 | **30** | 10 | 20 | 0 | 0 | 0 | 12 / 1 / 8 | 1 | 1 |
| 6513 AI reliability | 70 | **45** | 15 | 20 | 0 | 10 | 0 | 2 / 2 / 2 | 2 | 0 |
| cd02 BIO files | 70 | **35** | 15 | 20 | 0 | 0 | 0 | 10 / 2 / 9 | 1 | 1 |
| e309 FIN fetch | 70 | **35** | 15 | 20 | 0 | 0 | 0 | 13 / 2 / 11 | 0 | 2 |

Old scores are from the pre-R2-04 snapshot
`reports/rework2/score_old_snapshot.csv` (221 rows); old E/S/F/G/L parsed
from the stored old `score_reason`. The new scores were independently
re-derived without importing `score.py`
(`reports/rework2/rederive_scores_r2_04.py`): **ALL 5 MATCH**.

### 2.2 The scoring rule (R2-04, `src/demand_radar/score.py` docstring)

- **E** — from DIRECT_SAME_PAIN evidence only (R2-03 counts) for assessed
  pains; unassessed pains keep the R03 org-group count. Same E_MAP as
  before (0/1/2/3/4/5+ orgs → 0/10/15/20/25/30).
- **S** — UNCHANGED (keyword-derived severity). Residual limitation, not
  silently fixed: even with S=20 retained, no theme reaches 70. If S were
  also zeroed the five would fall to 10 / 10 / 25 / 15 / 15.
- **F** — 15 ONLY when `pain_points.workaround_status = 'DOCUMENTED'`.
  The old placeholder `'see linked issues'` (17 pains) and NULL (204)
  are UNKNOWN → F=0. A paid/rate-limit keyword mention is not feasibility
  evidence. F=0 for all 221 pains.
- **G** — 0 if any check has `does_solve=1`; 0 if any UNKNOWN trail exists;
  10 if ≥2 real checks and none solves; 5 if exactly 1 real check.
- **L** — 0 always in this dataset. No documented transfer/reuse evidence
  exists; no reuse-evidence schema exists yet, so no L point can be
  awarded honestly.
- **Cap-59** unchanged but unreachable at 1 org (max 55 with 1 DIRECT org).
- **Gate: 70, unchanged** (`selection.GATE_MIN_SCORE == 70`, pinned by test).

### 2.3 Top 10 pains by new score (full list: `reports/rework2/not_qualified_r2_04.csv`, 221 rows)

| pain | domain | new score | gate failure |
|---|---|---|---|
| 28ccf8f8701bb84bf95b (read SEC filings accurately) | FIN | 45 | score 45 < 70 |
| 6513d051954cbe1b5027 (drive an AI agent / API reliably) | AI | 45 | score 45 < 70 |
| da75a85dbf1cb9f121cc (plan a transit journey) | UK | 45 | score 45 < 70 |
| 3955670369ee96d7b5d6 (find real job listings) | JOB | 40 | score 40 < 70; only 1 org |
| 908f662d8a749944fb20 (run and reproduce work in a notebook) | RES | 40 | score 40 < 70; only 1 org |
| bdef2d35b09f45a0e94a (analyse tabular data correctly) | RES | 40 | score 40 < 70; only 1 org |
| 6a7abaf0c0655b39aa36 (install and run an AI tool) | AI | 35 | score 35 < 70 |
| cd021eac3c93ed0d2de1 (read and write biosignal files) | BIO | 35 | score 35 < 70; 1 UNKNOWN competitor trail |
| e3091fb34139fdf57dbd (fetch market/financial data reliably) | FIN | 35 | score 35 < 70; 2 UNKNOWN competitor trails |
| 04231fb650afe3d53053 (JPM overhead ratios) | FIN | 30 | score 30 < 70; 1 org; 1 author; 0 checks |

Note: 28cc and da75 also reach 45 (old score 65 each) — they were never
PRD candidates and also fail on score alone.

## 3. Evidence assessment (R2-03) — 76 links, 38 DIRECT

All 76 evidence links of the 5 old candidates were classified against a
written `problem_signature` (actor, input_artifact, operation,
observed_failure, expected_output, affected_product,
version_or_environment) in `evidence_assessment` (5 signatures, 76 rows,
0 UNKNOWN). Full reasons: `reports/rework2/evidence_assessment.csv`.
Script: `reports/rework2/assess_r2_03.py` (idempotent; re-run reproduces
the DB rows and the CSV).

| theme | DIRECT | ADJACENT | DUPLICATE | OUT_OF_SCOPE | DIRECT orgs | DIRECT authors | survives admission? |
|---|---|---|---|---|---|---|---|
| 0b7a FIN workspace | 1 | 0 | 1 | 4 | 1 (edgartools) | 1 | NO — 1 org, 1 author |
| 4bb7 BIO signals | 12 | 3 | 0 | 4 | 1 (NeuroKit) | 8 | NO — 1 org |
| 6513 AI reliability | 2 | 4 | 3 | 10 | 2 | 2 | YES (caveat §3.1) |
| cd02 BIO files | 10 | 2 | 0 | 4 | 2 | 9 | YES |
| e309 FIN fetch | 13 | 1 | 1 | 1 | 2 | 11 | YES |
| **total** | **38** | **10** | **5** | **23** | | | |

38 of 76 links (50%) were excluded from all counts. Why, in brief:
duplicates are the same report filed twice (LangChain #41709/#41710,
#41717/#41718; yfinance #3011/#3012; OpenBB #7650/#7651); adjacent are a
different operation/product/failure (wfdb #538 GDF read, MNE #14321 EDF
edge artefact vs NeuroKit core-algorithm failures; AgentLab #182 loud
timeouts vs silent wrong/missing results); out-of-scope are not user
problems at all (docs CI #1176, packaging #1160/#1236, chart RFC #7744,
CVE tracking #3012, vendor promotion #7640/#7641, benchmark questions).
Two independent reports of the same underlying bug DO both count
(#522/#524 rdann OverflowError; #543/#618 wrsamp TypeError — different
authors/datasets).

### 3.1 The 6513 granularity decision (stricter reading adopted)

R2-03 recorded 6513 as surviving under a failure-class grouping: its two
DIRECT links are different mechanisms — AgentLab #340 (tokenizer silent
substitution, +108% CJK) vs LangChain #41708 (streaming missing completed
event). R2-04 adopted the **stricter mechanism-level reading**: a
tokenizer-substitution report does not corroborate a streaming-completion
demand (different reproducer, acceptance test, fix). Under the stricter
reading each mechanism stands at 1 DIRECT link / 1 org / 1 author, and
6513 fails the org and author gates as well as the score gate.
Qualification is unchanged under either reading (45 < 70 either way).
The gate CSV shows the class-reading numbers (2 orgs / 2 authors,
failure "score 45 < 70") because R2-03's assessments were not edited and
no mechanism field exists in the data; for 6513 to ever re-qualify, new
DIRECT evidence of the SAME mechanism in a second org would be needed.

### 3.2 Candidate samples (surviving themes only, R2-03 §5)

- **6513** — LangChain #41708 streaming completion: feed
  `_convert_responses_chunk_to_generation_chunk` a
  `response.output_item.done` chunk for a `function_call`
  (`call_id="call_1"`); expect exactly one completed chunk; without the
  `done` event, none. Support: #41708 + AgentLab #340 (2 orgs, 2 authors).
  #41708 CLOSED (resolution unverified), #340 OPEN.
- **cd02** — wfdb #618 wrsamp TypeError: `wfdb.rdrecord("sample-data/100",
  sampto=1000).wrsamp(write_dir="out")` → `TypeError: unsupported operand
  type(s) for %: 'NoneType' and 'int'`; expect the write to complete or a
  clear error naming the missing `d_signal`. Support: 8 wfdb + 2 MNE links
  (2 orgs, 9 authors; DIRECT open/closed 5/5).
- **e309** — yfinance #2964 missing session: `yf.Ticker(sym).history(
  period="10d", interval="1d")` for ^GSPC/^IXIC/IWM/RSP/ANET; expect the
  2026-08-28 session present or explicitly flagged missing. Support: 8
  yfinance + 5 OpenBB links (2 orgs, 11 authors; DIRECT open/closed 2/11
  — the most closed-heavy set; live state must be re-checked before
  building on any of them). #2963/#2997 may originate at the Yahoo end.

## 4. Competitor evidence (R2-04) — 34 checks, 0 solve, 6 UNKNOWN

`competitor_checks`: 34 rows, 0 `does_solve=1`, 6 UNKNOWN trails.
The 10 checks of the 5 candidate themes were re-verified against the
SAME user task and SAME acceptance case (R2-03 §5 samples). The other 24
checks were NOT re-examined. Verdict rule: KEEP `does_solve=0` only for a
specific executable function (or documented scope excluding the
acceptance input) with an official evidence link tied to the sample.
UNKNOWN when the check rests only on homepage marketing copy, the product
IS the broken library, or the check never addresses the sample. UNKNOWN
blocks G and the gate. Old rows preserved in
`reports/rework1/competitor_checks.jsonl` (untouched) and
`reports/rework2/competitor_checks_before_r2_04.json`; after-state in
`reports/rework2/competitor_checks_r2_04.jsonl` (34 rows).
Live re-reads 2026-11-06 (read-only public pages, all HTTP 200): HeartPy
README, pyEDFlib README, LiteLLM docs, LangSmith docs.

| theme | product | executable function | verdict |
|---|---|---|---|
| 0b7a | OpenBB | OpenBB terminal/workspace | UNKNOWN — the product IS the broken library |
| 0b7a | TradingView | charting/screener (homepage claim) | UNKNOWN — homepage marketing only |
| 4bb7 | HeartPy 1.2.5 | heartpy.process() — PPG/ECG heart-rate analysis | KEEP 0 — HR-only scope; no EMG/DFA/RSP/signal-power function |
| 4bb7 | NeuroKit2 0.2.14.dev115 | NeuroKit2 signal functions | UNKNOWN — the product IS the broken library |
| 6513 | LangSmith | LangSmith tracing (SDK/env vars) | KEEP 0 — observability is post-hoc; cannot emit the missing event or validate the count at call time |
| 6513 | LiteLLM | litellm.completion() with retries/fallbacks | KEEP 0 — a retry re-issues the call; cannot detect a substituted tokenizer or emit the missing event |
| cd02 | MNE-Python 1.13.2 | mne.io read/write (FIFF/EDF) | UNKNOWN — MNE is itself a DIRECT-evidence product; check never addresses the wfdb #618 round-trip |
| cd02 | pyEDFlib v0.1.42 | highlevel.read_edf / write_edf | KEEP 0 — EDF+/BDF+ only; cannot read/write a WFDB record |
| e309 | pandas-datareader 0.11.2.dev2 | get_data_yahoo() | UNKNOWN — no source-specific evidence it returns the missing 2026-08-28 session |
| e309 | yfinance 1.8.0 | Ticker/download fetchers | UNKNOWN — the product IS the broken library |

Result: **4 KEEP 0, 6 UNKNOWN.** G per theme: 0b7a 0 (0 real), 4bb7 0
(1 real + 1 UNKNOWN → blocked), 6513 10 (2 real), cd02 0 (1 real +
1 UNKNOWN → blocked), e309 0 (0 real). Only 6513 keeps any G points and
still fails on score (45 < 70). No competitor was executed against any
sample input — the 4 KEEP verdicts are SCOPE_DOCUMENTED arguments from
official docs/repos, not functional tests (see §11).

## 5. The gate — 0 qualified, 221 not qualified

Gate (unchanged): score ≥ 70 AND ≥ 2 orgs AND ≥ 2 authors AND ≥ 2
competitor checks with 0 `does_solve=1` AND 0 UNKNOWN trails AND evidence
from VERIFIED sources only (DIRECT-only for assessed pains).
Run: `python reports/rework2/run_gate_r2_04.py` → **qualified 0, not
qualified 221**, fingerprint
`3d26137fd5e36e53ed08db7fea14c65d823c31dac3870b0e1386d8fe262fafe6`
(reproduced identically by R2-06 from the live DB, see §10).
Per-candidate failures (`reports/rework2/not_qualified_r2_04.csv`):
- 0b7a (30): score < 70; only 1 org; only 1 author; 2 UNKNOWN trails.
- 4bb7 (30): score < 70; only 1 org; 1 UNKNOWN trail.
- 6513 (45): score < 70. (Under the stricter §3.1 reading, also only
  1 org / 1 author per mechanism.)
- cd02 (35): score < 70; 1 UNKNOWN trail.
- e309 (35): score < 70; 2 UNKNOWN trails.
`reports/rework2/qualifying_prds_r2_04.csv` is header-only (0 rows).

## 6. PRDs — 5 superseded, 0 current

No PRD is written in REWORK2 (none qualifies). The 5 REWORK1 PRDs
(`reports/prds/PRD_<id>_r1.md`, written under the old scoring rule) were
moved by R2-06 (`reports/rework2/align_prd_cards_r2_06.py`, idempotent)
into `reports/prds/superseded/` — kept as history, not deleted.
`prd_cards` now reads **0 QUALIFIED / 17 SUPERSEDED** (was 5 / 12);
all 17 `md_path` values exist on disk and point under
`reports/prds/superseded/`. The other 12 cards were already SUPERSEDED
under R05. `reports/mvp_selection.json` records the old 5 under
`superseded_rework1_prd_eligible` with their old scores (70) preserved
and the R2-04 supersession reason; the pre-R2-06 file is preserved at
`reports/rework2/mvp_selection_before_r2_06.json` (SHA-256 `2a1ce4e9…`).

## 7. MVPs — 2 prototypes, both PARTIALLY_REAL_WORLD_VALIDATED

Neither MVP is a product that solves a qualified PRD (there is no
qualified PRD). Neither may offset PRDs eliminated by re-scoring.
Labels are in each README ("Positioning" section), each app's warning
banner, and `reports/rework2/r2_05.md`.

### R1-A — AI fault-injection validator (`mvps/r1_a/`), pain 6513

Three SEPARATE capabilities — never conflate them (R3-05; full
statement in `mvps/r1_a/README.md` "Positioning" and the app banner):

- **Stream event count** — completed chunks emitted vs done events
  received. Real, validated: recorded-event replay of LangChain
  #41708/#41710 through the real `StreamingHandler` (correct handler:
  exactly 1 completed chunk; buggy handler: 0 despite the done
  event); duplicate done emits once; done for a never-added call is
  an orphan; a call added but never done emits nothing.
- **Function argument integrity** — each completed call carries the
  CORRECT arguments. Real, validated (R3-01): deltas are correlated
  per call through dual-key mappings (`item_id` + `output_index`
  must agree — verified against the OpenAI Python SDK event
  contract), appended in order, deduplicated by `sequence_number`,
  and cross-validated against the done item's final `arguments`
  (must be valid JSON and equal the accumulated deltas). A key
  conflict, an unknown item, or a mismatch fails the stream — never
  silently attributed to another call. The audit's dual-key case
  (two parallel calls losing both payloads yet passing) is caught.
  Arguments are parsed STRICTLY (R4-01): `NaN` / `Infinity` /
  `1e999`-style overflows are rejected as invalid JSON, in the raw
  body and in done/accumulated arguments alike. Termination is
  explicit (R4-03, extended POST-R4): all four terminal events —
  `response.completed`, `response.failed`, `response.incomplete`,
  `error` — are recorded; a failure terminal always FAILS (even
  when every call completed first) and is never counted in the UI's
  passed total; data after any terminal event and mutually
  conflicting terminal events are anomalies; a stream with no
  terminal signal is reported `open` (incomplete) and its detail
  says the request's success is not yet proven.
- **Factual truth** — content comparison against the fixture's
  known-good expected answer, as a normalized word-multiset match
  (case-, punctuation- and word-order-insensitive). Real, validated
  (R3-02), LEXICAL ONLY: the `factual=False` self-grading flag was
  REMOVED (R2-05) — the transport no longer grades its own homework;
  HN #50382039's false response is convicted by the comparison; a
  keyword rule alone returns `not-checked` and is never claimed as
  factual verification; a negation ("Paris is NOT the capital")
  never passes. Known limit: word order is ignored — this verifies
  the same words, not the same sentence structure, and is not a
  semantic verification. A `not-checked` result is never counted as
  a verified pass (R4-02): `passed=False`, and the UI shows it in
  its own not-checked count, separate from passed and failed.
- **Real tiktoken 0.14.0 substitution detection for OpenAI models**
  (Chinese cl100k 51 vs o200k 34, +50%; Japanese 54 vs 43, +25.6%).
- **Not real-world validated:** #340 Qwen substitution (approximation
  only — `count_tokens_real` returns None / raises for models with no
  tiktoken encoding, never silently approximates); English/code OpenAI
  substitution (real tokenizers indistinguishable: 19 vs 19, 13 vs 13);
  no live API call ever made.
- Fixtures: 15 scenarios, 22 checks (was 14 / 21).

### R1-B — BIO signal validator (`mvps/r1_b/`), pain 4bb7

- **Real, validated:** real neurokit2 0.3.0 / wfdb 4.3.1 calls —
  `rsp_process` on 8 s simulated RSP reproduces the #1242 IndexError
  deterministically (seeds 42/1/7/123; completes at 10 s; #1242 still
  live in neurokit2 0.3.0); real `hrv_rsa` Porges-Bohrer 4.172 vs local
  4.691 ln(ms²) (same sign/magnitude, NOT identical — different
  detrending; cross-implementation bound 1.0, not the PRD 0.05 tolerance);
  real `fractal_dfa` invariant to 1.55e-15 across scales (alpha 1.332878);
  real `signal_filter`/`emg_amplitude` at fs=4000 vs assumed 1 kHz
  (900 Hz tone attenuated 0.0004x at true fs, passes 0.99x at assumed fs);
  real `signal_power` 2.0000 vs local 1.9998; real `wfdb.rdrecord`/`rdann`
  + `nk.ecg_process` on the vendored MIT-BIH 100 10 s excerpt
  (12 R-peaks, 11/14 annotated beats matched within 100 ms, 72 bpm;
  misses recorded honestly: 2 at the record edge, 1 offset 133 ms).
  `run_all_real()` = 9 rows: 6 pass, 3 fail-DETECTIONS.
- **Not real-world validated:** fixture-based checks remain synthetic
  signals generated from issue parameters, not original recordings.
- Real record provenance: `mvps/r1_b/data/mitdb_100_10s.dat` (7.2 KB) /
  `.hea` / `.atr` (14 annotations), first 10 s of channel MLII, fs 360 Hz,
  from MIT-BIH Arrhythmia Database record 100, downloaded 2026-11-06
  from https://physionet.org/files/mitdb/1.0.0/100.dat (+ `.hea`, `.atr`),
  sliced with `wfdb.wrsamp` / `wfdb.wrann`. Full record (1.95 MB) was
  downloaded to /tmp for slicing and is not shipped. Note in
  `mvps/r1_b/data/README.md`.

## 8. Code fixes (R2-01, R2-02, R3-01, R3-02, R3-03, R3-04, R4-01, R4-02, R4-03, R4-04, P0-01, P0-02, P0-03, P0-04)

- **R2-01** — five adversarial tests RED → GREEN, all in
  `mvps/r1_b/signalcheck.py` and `mvps/r1_a/validator.py`:
  RSA false "≥ 0" premise removed (signed-denominator bug; new rule
  `delta = abs(reported − expected)`, `scale = max(abs(expected), 1e-8)`,
  pass iff `delta ≤ max(abs_tol, rel_tol·scale)`, abs_tol 0.05 ln(ms²),
  rel_tol 0.02, non-finite → immediate fail); RSP phase validates
  length/fs/intervals before zip; JSON schema explicitly excludes bool
  from int/float; streaming uses a per-call state dict keyed by
  item.id / call_id / output_index / item_id (exactly one completed per
  done). 53 new tests, incl. 200 seeded randomised RSA counterexamples
  and 50 seeded randomised 3-call interleavings. Two REWORK1 tests that
  encoded the false RSA premise were corrected with reasons recorded.
  The adversarial test file itself was NOT modified in expectations.
- **R2-02** — trapz test fixed: deleted `assert not hasattr(np, "trapz")`
  (NumPy 2.3.5 has the attribute; a version's attribute list is not a
  software requirement); the test now asserts `np.trapezoid` is called,
  `np.trapz` is never called, and the A=2 sine value is 2.0 ± 0.01.
  Production code unchanged. AppTest flake fixed with a deterministic
  `timeout=30` wait (not reruns): one real 3 s timeout was observed in
  the NumPy 2.3.5 venv and fixed; 6 consecutive runs green in both venvs.
- **R3-01** — true multi-call argument correlation
  (`mvps/r1_a/validator.py`, `StreamingHandler` + `validate_stream`;
  full design in `reports/rework3/r3_01_02_03.md` §1). Canonical
  identity is the added item's `item.id`; three namespace-separated
  maps (`item.id`, `item.call_id`, `event.output_index`) must all
  agree — a delta carrying both `item_id` and `output_index` that
  disagree is a fail-closed `key_conflict`, never attributed to
  another call. Keyless deltas (the recorded #41708 shape) are
  attributed only when exactly one call is pending; otherwise
  `ambiguous_delta`/`unknown_delta`. Duplicate `sequence_number`
  deltas are dropped; deltas after done are dropped; the done item's
  final `arguments` are cross-validated against the accumulated
  deltas (must be valid JSON and equal — else `arguments_mismatch` /
  `invalid_arguments_json`, chunk marked `arguments_valid=False`).
  `validate_stream` now checks completion count + correct association
  + argument integrity; an event list with no streaming events
  returns `not-checked`, other failures `wrong-result`, never `ok`.
  Verified against the real OpenAI Python SDK event contract (fetched
  2026-11-06: delta carries `item_id` + `output_index` +
  `sequence_number`; the SDK's own helper resolves by `output_index`
  and raises on unknown indexes). 14 new contract tests; fresh-seed
  randomised check 60/60 trials (4 dual-key calls).
- **R3-02** — factual content actually compared
  (`check_factual_content`, `reports/rework3/r3_01_02_03.md` §2).
  The three rules are now separate: `expected_answer` is compared as
  a normalized word-multiset match (case-, punctuation- and
  word-order-insensitive) — a contradiction, a paraphrase, and a
  refusal all fail; a negation fails because its word multiset
  differs. `expected_keywords` alone returns `not-checked` ("factual
  truth not checked") and is never claimed as verified correctness.
  `forbidden_claims` present → `wrong-result`; absent alone →
  `not-checked`. `_validate_payload` propagates `not-checked` instead
  of swallowing it into `"ok"`. Known limit, stated: word order is
  ignored — the check verifies the same words, not the same sentence
  structure; it is a lexical match, not a semantic verification.
  11 new contract tests.
- **R3-03** — schema fail-closed (`_matches_type`,
  `reports/rework3/r3_01_02_03.md` §3). Explicit contract: JSON
  Schema standard names (`integer`, `number`, `string`, `boolean`,
  `array`, `object`, `null`) plus the short fixture names (`int`,
  `float`, `str`, `bool`, `list`, `dict`). `integer`/`int` = Python
  int, never bool, never float (2.0 does not satisfy it, by
  contract). `number`/`float` = int or float, never bool, always
  finite — NaN/±Inf never satisfy a numeric type. Any other type
  name raises `SchemaConfigError`, surfaced by `_validate_payload`
  as `("not-checked", False, "schema configuration error: ...")`.
  The same rules apply inside nested `object.properties` /
  `array.items`. 7 new contract tests (incl. parametrised).
- **R3-04** — the delivery zip now has a single top-level directory
  `demand-radar-rework3/` (audit P1-03: the REWORK2 zip unpacked
  flat, so README's `cd demand-radar-rework2` had no target).
  `README_REWORK3.md` §1 is `unzip` + `cd demand-radar-rework3`
  and was executed verbatim from an empty directory in the
  clean-room verification (`reports/rework3/r3_04.md`).
- **R4-01** — strict JSON parsing (`_parse_strict_json`,
  `reports/rework4/r4_01_02_03.md` §1). `parse_constant` rejects
  `NaN` / `Infinity` / `-Infinity`; a recursive finiteness walk
  rejects non-finite floats the parser produces (`1e999` -> inf),
  at any nesting depth. No regex: a "NaN" inside a JSON string is
  legal text and is preserved. Used by `_validate_payload` (raw
  body), `_handle_done` (final AND accumulated arguments),
  `load_scenarios`, and the R1-A app's upload path. Rejection is
  `wrong-result` / `passed=False` (or an `invalid_arguments_json`
  anomaly for streamed arguments).
- **R4-02** — not-checked is not a pass (`check_factual_content`,
  `run_step`, `mvps/r1_a/app.py`;
  `reports/rework4/r4_01_02_03.md` §2). All three `"not-checked"`
  returns now carry `passed=False`; the UI counts verified passes,
  real failures, and not-checked results separately, with its own
  NOT_CHECKED count and a "not-checked" filter option. Three
  ordinary tests were updated to the new assertion (frozen 9
  untouched); no fixture step is keyword-only, so the 22-check
  fixture counts are unchanged.
- **R4-03** — stream termination (`StreamingHandler`,
  `validate_stream`; `reports/rework4/r4_01_02_03.md` §3).
  `response.completed` is recorded as the terminal signal; any
  streaming event after it is an `event_after_completed` anomaly.
  `validate_stream` returns a `termination` field (`completed` /
  `open` / `none`): completed-with-pending → `wrong-result`,
  `passed=False`; a partial stream with no completion signal keeps
  its previous verdict (added-but-never-done emits nothing) but is
  reported `open` with "stream still open" in the detail.
- **P0-01** — four terminal events (`StreamingHandler`,
  `reports/post_r4/p0_01_02_03.md` §2). The terminal enumeration
  is now `response.completed` / `response.failed` /
  `response.incomplete` / `error`, verified against the OpenAI
  Python SDK event contract. The first terminal event ends the
  response; a failure terminal is never an "open" stream. Data
  after any terminal event is an anomaly (`event_after_completed`
  after completed, `event_after_terminal` after any other
  terminal); a second terminal of a different kind is a
  `conflicting_terminal` anomaly; a duplicate identical terminal
  is tolerated but recorded.
- **P0-02** — only a normal completion can pass
  (`validate_stream`, `reports/post_r4/p0_01_02_03.md` §3). A
  failure terminal always gives `passed=False`, outcome
  `wrong-result`, and a detail naming the terminal and its reason
  (error code/message, incomplete reason, failed error dict).
  Completed-with-pending still fails; completed-with-complete
  still passes. An open stream keeps its chunk-coherence semantics
  but its detail now says "request success not yet proven".
- **P0-03** — UI (`mvps/r1_a/app.py`,
  `reports/post_r4/p0_01_02_03.md` §4). The banner now labels open
  streams as not yet proven success and failure terminals as never
  counting as passed. Counting is unchanged in shape (passed =
  outcome ok AND passed) and was verified: a failed-terminal
  scenario lands in "failed", never "passed". Fixture sweep
  unchanged: 9 passed / 13 failed / 0 not checked of 22 checks.
- **P0-04** — delivery provenance (see §10 / `p0_04.md`):
  `RELEASE_SHA256.txt` is written OUTSIDE the zip with the final
  SHA-256 and size; the final report's header no longer says the QA
  verdict is pending while §13 says it passed (the R4 report's
  header was already fixed in R4-04; the same rule is applied here
  for POST-R4).
- **R4-04** — delivery provenance (see §10 / `r4_04.md`):
  `RELEASE_SHA256.txt` is written OUTSIDE the zip with the final
  SHA-256 and size; the final report's header no longer says the QA
  verdict is pending while §13 says it passed (the R3 report's
  contradiction, audit P2-D).

## 9. Tests and environments

| environment | Python | NumPy | Streamlit | pytest | ruff | suite | exit |
|---|---|---|---|---|---|---|---|
| main `.venv` | 3.12.3 | 2.5.4 | 1.67.0 | 9.2.0 | 0.17.4 | **334 passed, 8 skipped** | 0 |
| real-upstream `.venv-real` | 3.12.3 | 2.5.4 | 1.67.0 | 9.2.0 | 0.17.4 | **351 passed, 0 skipped** | 0 |
| NumPy 2.3.5 venv (R2-02) | 3.12.3 | 2.3.5 | 1.67.0 | 9.2.0 | 0.17.4 | 212 passed (then-current suite) | 0 |
| Python 3.13 × any NumPy | — | — | — | — | — | **NOT_TESTED** (not installed) | — |

- Main venv: 334 passed, 8 skipped (the 8 skips are the 7 tiktoken tests
  + the 1 real-upstream module, `importorskip`, clear reason).
  Baseline regressions: **26/26 passed** — the 5 old adversarial tests
  (`tests/test_rework2_adversarial.py`), the 4 frozen independent
  tests (`tests/test_independent_r2.py`, 4/4 RED on the REWORK2
  baseline, 4/4 GREEN here; the file is byte-identical to the audit's
  copy, SHA-256 `aa91307d…`), the 10 frozen fourth-round tests
  (`tests/test_independent_r3.py`, 6/10 RED on the REWORK3 baseline,
  10/10 GREEN here; byte-identical to the audit's copy, SHA-256
  `8c61b5f8…`), and the 7 frozen fifth-round termination tests
  (`tests/test_post_r4_termination.py`, 5/7 RED on the REWORK4
  baseline, 7/7 GREEN here; byte-identical to the audit's copy,
  SHA-256 `244882a3…`). The 33 REWORK3 contract tests
  (`tests/test_rework3_contract.py`), the 22 REWORK4 contract tests
  (`tests/test_rework4_contract.py`), the 13 POST-R4 contract tests
  (`tests/test_post_r4_contract.py`) and the 2 new AppTest tests are
  included in the 334. Full logs: `reports/post_r4/full_suite_p0_main.txt`
  (main venv, run twice consecutively, both exit 0).
- Real venv: 351 passed, 0 skipped (329 in REWORK4 + 7 independent +
  13 contract + 2 AppTest); every real-path test runs there, offline
  (encoding tables cached, signals generated, record vendored). The 6
  warnings are a `Pandas4Warning` from inside wfdb's annotation reader
  (deprecated `DataFrame.set_index(inplace=...)`) — third-party, not
  this project's code. Log: `reports/post_r4/full_suite_p0_real.txt`.
- Ruff: `python -m ruff check .` → **All checks passed** (exit 0) in both
  venvs. One config note: the frozen `tests/test_independent_r2.py`,
  `tests/test_independent_r3.py` and `tests/test_post_r4_termination.py`
  have unsorted imports and unused imports; those rules are waived for
  those three files only via `[tool.ruff.lint.per-file-ignores]` in
  `pyproject.toml` — the files themselves are untouched.
- AppTest: 8 MVP UI tests pass in both venvs (6 + 2 POST-R4 banner/count tests); workbench driver
  (`reports/rework2/apptest_workbench_r2_02.py`) passes in both venvs
  (default 200 VERIFIED rows; REJECTED opt-in; domain/source/keyword
  filters match DB counts). Headless `streamlit run` + curl: workbench,
  R1-A, R1-B all HTTP 200 (re-verified in the R3-04 clean room).
- Freezes: `reports/post_r4/pip_freeze_p0_main.txt`,
  `reports/post_r4/pip_freeze_p0_real.txt` (REWORK4 freezes kept in
  `reports/rework4/`).
  Key pins: numpy 2.5.4, pandas 3.1.1, pydantic 2.14.3, streamlit 1.67.0,
  pytest 9.2.0, ruff 0.17.4; real venv adds tiktoken 0.14.0,
  neurokit2 0.3.0, wfdb 4.3.1, scipy 1.18.1, scikit-learn 1.9.1,
  matplotlib 3.11.2.

## 10. Alignment — everything agrees with everything else

Checked live by R2-06 (`reports/rework2/compute_final_numbers.py`,
all assertions passed; `reports/rework2/final_numbers_r2_06.json`)
and re-checked live in REWORK3 (same script re-run 2026-11-06,
identical output, gate fingerprint identical):

| check | result |
|---|---|
| DB integrity (`PRAGMA integrity_check`) | ok |
| source status == review verdict (218) | 0 mismatches |
| evidence_links review_status vs source verdict | 0 stale (13 REJECTED / 356 VERIFIED) |
| ranking.csv vs live re-score | byte-identical; also identical to `reports/rework2/ranking_r2_04.csv` |
| gate fingerprint vs R2-04 | identical (`3d26137f…fafe6`) |
| score_diff.csv new scores vs live DB scores | all 5 match |
| `reports/rework2/qualifying_prds_r2_04.csv` | header-only (0 rows) |
| `reports/rework2/not_qualified_r2_04.csv` | 221 rows |
| prd_cards vs R2-04 gate | 0 QUALIFIED / 17 SUPERSEDED; all md_paths exist |
| `reports/mvp_selection.json` vs live gate | prd_eligible 0, not_selected 221, mvp_built 2, superseded 5 |
| exports (regenerated 2026-11-06) | CSV 200 rows (VERIFIED-only default), JSON 200 rows, `--all` 218 rows |
| MANIFEST.sha256 (delivery zip) | 286 files verified in clean room (see p0_04.md / p0_05.md §3) |
| POST-R4 zip layout | single top-level directory `demand-radar-post-r4/`; README §1 commands executed verbatim from an empty directory (see p0_04.md) |
| RELEASE_SHA256.txt (outside the zip) | final SHA-256 + byte size, written after packaging; the zip never contains its own hash |

## 11. NOT_TESTED / UNKNOWN / residual items

Honest list — nothing here is presented as passed:

1. **Competitor execution:** no competitor was executed against any
   R2-03 sample input. The 4 KEEP verdicts are SCOPE_DOCUMENTED
   (official docs/repos), not EXECUTED. A real execution test (e.g.
   `heartpy.process` on the #1212 signal, `read_edf` on a WFDB record,
   `litellm.completion` on the #41708 event sequence) would be needed to
   upgrade them.
2. **S (severity):** still keyword-derived. No real loss measure (time
   lost, work blocked, money) was collected for any theme.
3. **L (reuse):** no reuse-evidence schema exists; L can only become
   positive if one is defined and populated.
4. **6513 mechanism split:** no mechanism field exists in the assessment
   data; the stricter reading (§3.1) is a documented judgement, not a
   computed gate field.
5. **Live issue state:** the R02 states (2026-11-05) were not re-checked
   live in REWORK2 except the 9 load-bearing issues in R2-03 (all matched
   the R02 record). e309's 11/13 closed DIRECT links and all other closed
   links are "closed, resolution unverified" — closed ≠ fixed.
6. **Python 3.13:** not installed on this VM; no 3.13 combination was run.
7. **NumPy other than 2.5.4 / 2.3.5:** not tested (e.g. 2.0–2.2).
   Production code only uses `np.trapezoid` (exists since NumPy 2.0);
   no known incompatibility, but unmeasured.
8. **Export download click:** AppTest verifies the export button appears
   after running; the downloaded payload is covered by `export_csv`
   unit tests, not by clicking download in AppTest.
9. **#340 Qwen claim:** NOT_REAL_WORLD_VALIDATED (no Qwen tokenizer
   installed; `transformers` + Qwen tokenizer not attempted).
10. **Real RSA agreement is loose:** real `hrv_rsa` 4.172 vs local 4.691
    (delta 0.518) — the 1.0 bound is a cross-implementation bound, not the
    PRD 0.05 tolerance. Local DFA (1.4348) vs real `fractal_dfa` (1.3329)
    differ on the same signal; only the real function's invariance is
    asserted. The fixture EMG band (10, 500) Hz differs from upstream's
    envelope default (10, 400) Hz.
11. **tiktoken encoding tables** need one network fetch on first use; in
    a fresh offline environment the 7 real-tokenizer tests skip.
12. **Audit's 9 unnamed spot-check items** (REWORK1 audit traceability
    gap, carried from R07): still NOT_TESTED — cannot be reproduced by
    anyone from the audit document.
13. **R2-03's 9 live re-reads** are the only live checks in REWORK2; no
    new sources were collected and no issue author was contacted.
14. **Factual truth is lexical, not semantic (R3-02):** the expected-answer
    check is a normalized word-multiset match. Word order is ignored,
    so "dog bites man" vs "man bites dog" would match; paraphrases
    are not verified; only the fixture's short factual sentences are
    in scope. No semantic/LLM judge was used.
15. **Streaming sequence gaps:** duplicate `sequence_number` deltas
    are dropped, but a missing sequence number (a gap — a lost delta)
    is not itself flagged; only its consequences (arguments mismatch
    at done) are. A stream that silently drops a delta AND a matching
    done would pass.
16. **REWORK3's live checks:** no new live GitHub re-reads were done
    in REWORK3 (no new external data, per the brief); the SDK event
    contract was verified from the fetched openai-python source, not
    by calling the live API.
17. **Strict JSON scope (R4-01):** `_parse_strict_json` is used by the
    R1-A validator paths and the R1-A app upload path, but NOT by
    `mvps/r1_b/signalcheck.py:502` (local fixture loading) or
    `src/demand_radar/ingest.py:17` (DB source ingestion) — those
    still use bare `json.loads`. Neither path feeds a "valid JSON"
    claim to the validator, but the inconsistency is real.
18. **Sequence gaps (R3, carried):** the §11.15 residual stands —
    a lost trailing chunk + empty done args still passes with
    silently incomplete arguments when the done event carries no
    arguments. R4-03 narrows it (a done AFTER `response.completed`
    is now an anomaly, and a completed response with a pending call
    fails), but a gap inside an otherwise open stream is still
    caught only when done carries the true arguments.
19. **REWORK4's live checks:** no new live GitHub re-reads were done
    in REWORK4 (no new external data, per the brief); the fourth-round
    audit ran against the REWORK3 Drive zip only.

## 12. What was NOT done (and why)

- No new PRD was written (none qualifies; writing one would require
  lowering the gate or fabricating evidence).
- No new MVP was built (the brief forbids building MVPs to substitute
  for remediation).
- No threshold was lowered at any stage (gate 70, org/author/competitor
  minima unchanged; S kept at 20 is conservative in the review's
  direction).
- No Drive/GitHub upload in REWORK3 (packaging only).
- No new data collection, no external posts/submissions, no paid API
  calls, no private-project access, no new external data at all
  (REWORK3 brief R3-05).
- The 4 independent tests were not modified in expectations; R2-03/R2-04
  data was not modified; the R2-06 gate/score outputs were not modified.
- The REWORK2 final report was moved to `reports/superseded/` (not
  deleted); the REWORK2 decision log was not appended to — REWORK3 has
  its own log in `reports/rework3/decision_log.jsonl` (audit §5
  residual #6: version audit logs should stay separate).
- No new PRD was written in REWORK4 either; no new MVP was built; no
  threshold was lowered; no new data was collected. The REWORK3
  final report was moved to `reports/superseded/` (not deleted);
  REWORK4 has its own decision log in
  `reports/rework4/decision_log.jsonl` — the REWORK3 log was not
  appended to.
- The brief's "best" option for R4-02 (independent `rule_matched` /
  `factual_verified` fields on `CallResult`) was NOT taken: the
  `outcome` field already is the separate state, and the minimal
  change is what the audit test requires. Recorded in
  `reports/rework4/r4_01_02_03.md` §2.
- No new PRD was written in POST-R4 either; no new MVP was built; no
  threshold was lowered; no new data was collected. The REWORK4
  final report was moved to `reports/superseded/` (not deleted);
  POST-R4 has its own decision log in
  `reports/post_r4/decision_log.jsonl` — the REWORK4 log was not
  appended to. The 7 frozen fifth-round tests were not modified in
  expectations; no fixture was added or changed.

## 13. QA verdict — ACCEPTED_RESEARCH_PROTOTYPE_ONLY

> **QA verdict: ACCEPTED_RESEARCH_PROTOTYPE_ONLY** (independent QA
> agent, 2026-11-06, report `reports/post_r4/p0_qa.md`, from a fresh
> extract of the delivery zip, README commands verbatim, plus its own
> fresh-seed randomised counter-checks against the real validator
> code: 207 assertions, 207 passed, seed 20261106). The fifth-round
> audit's single P1 defect is fixed and verified — a failure
> terminal (`response.failed` / `response.incomplete` / `error`)
> always fails (never a pass), conflicting terminals and data after
> a terminal are anomalies, and open streams are labelled "not yet
> proven". Main venv 334 passed / 8 skipped, real venv 351 passed,
> baseline 26/26, MANIFEST 286/286, ranking byte-identical, gate
> 0/221. The RED baseline was independently re-verified on a fresh
> REWORK4 extract (5 failed / 2 passed, exactly as claimed). The
> verdict is RESEARCH_PROTOTYPE_ONLY (not full ACCEPTED) because the
> research conclusions stand as they must: 0 qualifying PRDs, 2
> PARTIALLY_REAL_WORLD_VALIDATED prototypes, #340 Qwen
> NOT_REAL_WORLD_VALIDATED. One non-blocking observation: an open
> stream with all calls done still returns passed=True on chunk
> coherence (documented design, now labelled) — a future round could
> consider making "not yet proven" also mean "not counted as
> passed". The delivery zip is
> `demand-radar-post-r4-2026-11-06.zip` (SHA-256 in
> `RELEASE_SHA256.txt`, outside the zip, and in
> `reports/post_r4/p0_05.md` §3 / the decision log). The REWORK4
> verdict (ACCEPTED_RESEARCH_PROTOTYPE_ONLY, 2026-11-06,
> `reports/rework4/r4_qa.md`) applied to the REWORK4 zip only.

## Appendix A — DIRECT evidence links (38)

Full per-link reasons: `reports/rework2/evidence_assessment.csv`.
States are the R02 values (2026-11-05); closed ≠ solved.

### 0b7a FIN workspace (1 DIRECT)

- dgunning/edgartools#1848 — https://github.com/dgunning/edgartools/issues/1848

### 4bb7 BIO signals (12 DIRECT)

- neuropsychology/NeuroKit#1163 — https://github.com/neuropsychology/NeuroKit/issues/1163
- neuropsychology/NeuroKit#1182 — https://github.com/neuropsychology/NeuroKit/issues/1182
- neuropsychology/NeuroKit#1183 — https://github.com/neuropsychology/NeuroKit/issues/1183
- neuropsychology/NeuroKit#1196 — https://github.com/neuropsychology/NeuroKit/issues/1196
- neuropsychology/NeuroKit#1200 — https://github.com/neuropsychology/NeuroKit/issues/1200
- neuropsychology/NeuroKit#1208 — https://github.com/neuropsychology/NeuroKit/issues/1208
- neuropsychology/NeuroKit#1212 — https://github.com/neuropsychology/NeuroKit/issues/1212
- neuropsychology/NeuroKit#1230 — https://github.com/neuropsychology/NeuroKit/issues/1230
- neuropsychology/NeuroKit#1238 — https://github.com/neuropsychology/NeuroKit/issues/1238
- neuropsychology/NeuroKit#1240 — https://github.com/neuropsychology/NeuroKit/issues/1240
- neuropsychology/NeuroKit#1241 — https://github.com/neuropsychology/NeuroKit/issues/1241
- neuropsychology/NeuroKit#1242 — https://github.com/neuropsychology/NeuroKit/issues/1242

### 6513 AI reliability (2 DIRECT)

- ServiceNow/AgentLab#340 — https://github.com/ServiceNow/AgentLab/issues/340
- langchain-ai/langchain#41708 — https://github.com/langchain-ai/langchain/issues/41708

### cd02 BIO files (10 DIRECT)

- MIT-LCP/wfdb-python#515 — https://github.com/MIT-LCP/wfdb-python/issues/515
- MIT-LCP/wfdb-python#522 — https://github.com/MIT-LCP/wfdb-python/issues/522
- MIT-LCP/wfdb-python#524 — https://github.com/MIT-LCP/wfdb-python/issues/524
- MIT-LCP/wfdb-python#528 — https://github.com/MIT-LCP/wfdb-python/issues/528
- MIT-LCP/wfdb-python#543 — https://github.com/MIT-LCP/wfdb-python/issues/543
- MIT-LCP/wfdb-python#554 — https://github.com/MIT-LCP/wfdb-python/issues/554
- MIT-LCP/wfdb-python#593 — https://github.com/MIT-LCP/wfdb-python/issues/593
- MIT-LCP/wfdb-python#618 — https://github.com/MIT-LCP/wfdb-python/issues/618
- mne-tools/mne-python#14431 — https://github.com/mne-tools/mne-python/issues/14431
- mne-tools/mne-python#14460 — https://github.com/mne-tools/mne-python/issues/14460

### e309 FIN fetch (13 DIRECT)

- openbq-org/OpenBB#7645 — https://github.com/openbq-org/OpenBB/issues/7645
- openbq-org/OpenBB#7650 — https://github.com/openbq-org/OpenBB/issues/7650
- openbq-org/OpenBB#7655 — https://github.com/openbq-org/OpenBB/issues/7655
- openbq-org/OpenBB#7656 — https://github.com/openbq-org/OpenBB/issues/7656
- openbq-org/OpenBB#7813 — https://github.com/openbq-org/OpenBB/issues/7813
- ranaroussi/yfinance#2930 — https://github.com/ranaroussi/yfinance/issues/2930
- ranaroussi/yfinance#2931 — https://github.com/ranaroussi/yfinance/issues/2931
- ranaroussi/yfinance#2937 — https://github.com/ranaroussi/yfinance/issues/2937
- ranaroussi/yfinance#2939 — https://github.com/ranaroussi/yfinance/issues/2939
- ranaroussi/yfinance#2963 — https://github.com/ranaroussi/yfinance/issues/2963
- ranaroussi/yfinance#2964 — https://github.com/ranaroussi/yfinance/issues/2964
- ranaroussi/yfinance#2997 — https://github.com/ranaroussi/yfinance/issues/2997
- ranaroussi/yfinance#3004 — https://github.com/ranaroussi/yfinance/issues/3004


## Appendix B — DB migrations in REWORK2

| stage | change | file |
|---|---|---|
| R2-03 | new tables `problem_signatures` (5 rows), `evidence_assessment` (76 rows) | `src/demand_radar/db.py::init_db`, `src/demand_radar/evidence_assessment.py` |
| R2-04 | `pain_points.workaround_status` (idempotent backfill; raw `current_workaround` text NEVER overwritten: 204 NULL, 17 `'see linked issues'`); `competitor_checks.executable_function`, `acceptance_case`, `evidence_level` (backfill UNKNOWN for NULL/placeholder) | `src/demand_radar/db.py::init_db`, `src/demand_radar/score.py`, `src/demand_radar/competitors.py` |
| R2-06 | no schema change; `prd_cards` status/md_path/gate_reason updated to the R2-04 gate (script `reports/rework2/align_prd_cards_r2_06.py`); `mvp_selection.json` restructured (script `reports/rework2/build_mvp_selection_r2_06.py`) | — |

All migrations are idempotent (`init_db` re-runs cleanly on the shipped
DB; verified by the R2-06 clean room running the exact README commands).

## Appendix C — File map (current version)

- Current report: `reports/final_report_post_r4.md` (this file)
- Status: `progress/STATUS.md`
- Stage reports: `reports/post_r4/p0_01_02_03.md`, `p0_04.md`,
  `p0_05.md`; REWORK4: `reports/rework4/r4_01_02_03.md`, `r4_04.md`,
  `r4_05.md`; REWORK3: `reports/rework3/r3_01_02_03.md`, `r3_04.md`,
  `r3_05.md`; REWORK2: `reports/rework2/r2_01.md` … `r2_06.md`
- Gate outputs: `reports/rework2/qualifying_prds_r2_04.csv` (0 rows),
  `reports/rework2/not_qualified_r2_04.csv` (221 rows),
  `reports/rework2/ranking_r2_04.csv`, `reports/rework2/score_diff.csv`,
  `reports/rework2/score_old_snapshot.csv`
- Evidence: `reports/rework2/evidence_assessment.csv` (76 rows),
  `reports/rework2/competitor_checks_r2_04.jsonl` (34 rows),
  `reports/rework2/competitor_checks_before_r2_04.jsonl`
- Selection: `reports/mvp_selection.json` (new shape),
  `reports/rework2/mvp_selection_before_r2_06.json` (REWORK1 snapshot),
  `reports/rework2/mvp_selection_r2_04.json` (R2-04 gate output)
- Superseded history: `reports/superseded/` (old final reports +
  STATUS files, incl. `final_report_rework4.md`),
  `reports/prds/superseded/` (all 17 PRD files),
  `reports/rework1/` (REWORK1 stage reports, untouched),
  `mvps/superseded/` (original MVP A/B demos)
- Tests: `tests/test_rework2_adversarial.py` (5, untouched),
  `tests/test_independent_r2.py` (4, frozen audit file, untouched),
  `tests/test_independent_r3.py` (10, frozen fourth-round audit file, untouched),
  `tests/test_post_r4_termination.py` (7, frozen fifth-round audit file, untouched),
  `tests/test_post_r4_contract.py` (13, new),
  `tests/test_rework4_contract.py` (22),
  `tests/test_rework3_contract.py` (33),
  `tests/test_mvp_selection_r2_06.py` (4),
  `tests/test_scoring_r2_04.py` (10), `tests/test_evidence_assessment.py` (7)
- Entry point: `README_POST_R4.md`
- Release provenance: `RELEASE_SHA256.txt` (OUTSIDE the delivery zip)
