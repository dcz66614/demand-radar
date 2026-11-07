# R1-A — API Reliability Validator (PRD 6513d051954cbe1b5027)

Controlled fault-injection validator for the AI agent/API reliability pain.
It does NOT browse issues. It runs recorded traces through a simulated
transport (local, no network, no paid calls, deterministic virtual clock)
and classifies every outcome.

## Positioning — PARTIALLY_REAL_WORLD_VALIDATED (R2-05, R3-01–R3-03)

R1-A is a validator, not a product that fixes AgentLab or LangChain.
After R2-05 it has three REAL validation paths and one remaining
approximation-only claim. The three streaming/factual capabilities
are DIFFERENT checks and must never be conflated (R3-05):

| capability | what it actually checks | status / evidence |
|---|---|---|
| **Stream event count** | Whether the number of completed chunks emitted equals the number of function_call done events (one per unique done; duplicate done emits once; done for a never-added call is an orphan; a call added but never done emits nothing). | REAL — replayed. Recorded #41708/#41710 sequences through the REAL `StreamingHandler`: correct handler emits exactly 1 completed chunk; buggy handler emits 0; no-done emits 0. Tests: `tests/test_real_paths.py`, `tests/test_rework3_contract.py` (§R3-01). |
| **Function argument integrity** | Whether each completed call carries the CORRECT arguments: deltas are correlated per call through dual-key mappings (`item_id` + `output_index` must agree — verified against the OpenAI Python SDK event contract), appended in order, deduplicated by `sequence_number`, and cross-validated against the done item's final `arguments` (must be valid JSON and equal the accumulated deltas). A mismatch, a key conflict, or an unknown item fails the stream — it is never silently attributed to another call. | REAL — replayed + adversarial. The REWORK2 audit's dual-key case (two parallel calls losing both argument payloads yet passing) is now caught: 4 frozen independent tests + 14 contract tests GREEN. Empty final + empty accumulated arguments is a legal no-argument call. |
| **Factual truth** | Whether a response's CONTENT matches the fixture's known-good expected answer — as a normalized word-multiset match (case-, punctuation- and word-order-insensitive). A keyword rule alone is NOT factual verification: keywords present with no expected answer returns `not-checked`, and a negation ("Paris is NOT the capital") never passes on a keyword hit. | REAL — content check, lexical only. The response is judged against the expected answer in the fixture (`"The capital of France is Paris."`, keywords `paris`, forbidden `berlin`). A `factual=False` payload flag is no longer trusted (removed R2-05). A true response passes as a positive control. Known limit: word order is ignored, so this verifies the same words, not the same sentence structure — it is a lexical match, not a semantic verification. |
| Tokenizer substitution, OpenAI models | REAL — tiktoken | `real_tokenizer.py` uses real tiktoken encodings (tiktoken 0.14.0): gpt-4o (o200k) vs GPT-4 (cl100k) substitution detected on Chinese (51 vs 34, +50%) and Japanese (54 vs 43, +25.6%). |
| Tokenizer substitution, non-OpenAI models (#340 Qwen) | NOT_REAL_WORLD_VALIDATED — approximation only | No real tokenizer exists for Qwen in this module: `count_tokens_real` returns `None` and `validate_token_count_real` raises `ValueError` instead of silently approximating. The #340 Qwen claim still rests on the approximation in `validator.py`. |
| English/code substitution (OpenAI) | NOT detectable with real tokenizers | cl100k and o200k give identical counts (English 19/19, code 13/13), so a GPT-4 count reported for gpt-4o is indistinguishable there. Recorded in tests, not hidden. |

No real API is ever called. The validator must NOT be presented as a
product that solves the real upstream problems, and must NOT be used to
offset PRDs eliminated by re-scoring.

## What it proves

- **Hidden default substitution (#340):** a reported token count is checked
  against the named model's tokenizer (within the PRD's 2% tolerance). A
  count matching the GPT-4 tokenizer instead is classified
  `default-substituted`. Fixture overcounts approximate the measured #340
  errors: Chinese +91.7% (measured +108.3%), English +10.5% (+11.7%),
  Japanese +21.2% (+18.5%), code 0% (0%). The two counters are small
  deterministic approximations, not the real tokenizers — detection is the
  product, tokenization is not. For OpenAI models the same check now also
  runs against REAL tiktoken counts (see Positioning above).
- **Streaming completion and argument integrity (#41708):** the recorded
  event sequence (added + deltas + done) must emit exactly one completed
  chunk carrying the recorded arguments; the buggy handler emits none and
  is flagged. Without a done event, no chunk may be emitted. These are
  two checks, not one: event count (chunks vs dones) and argument
  integrity (dual-key per-call correlation, ordered accumulation,
  cross-validation against the done item's final arguments). #41708
  itself closed `not_planned` (unresolved); the same bug is still open
  as #41710.
- **Fault handling (#182, HN #50382039):** 429/timeout/500 are retried within
  a hard budget (max 3 attempts, 60 s simulated per timeout attempt) and
  reported with attempt counts and elapsed time — never silently retried past
  the budget, never returned as success. Malformed JSON and schema violations
  are `wrong-result`; a false OpenRouter response is classified by content
  comparison against the expected answer (normalized word-multiset match),
  with its 45 s latency; a true response passes as a control; prompt+max
  over budget is `token-budget` (0 attempts); a silent prompt trim is
  `wrong-result`. Schema types are fail-closed: an unknown type name is a
  configuration error, never a silent pass, and NaN/Inf never satisfy a
  numeric type.

## What it does NOT prove

- It does not fix AgentLab or LangChain, and it does not call any real API.
  It validates *detection* of the failure classes on recorded reproducers.
- The tokenizers are approximations (see `validator.py` docstring). A real
  deployment must plug in the actual per-model tokenizers and re-run the
  same checks — the 2% tolerance test is written to accept them. For
  OpenAI models this is now done with real tiktoken counts
  (`real_tokenizer.py`); for non-OpenAI models it is still approximation
  only.

## Run

```bash
python -m streamlit run mvps/r1_a/app.py   # UI: 2 filters (kind, outcome), CSV export
python -m pytest mvps/r1_a/tests/ -q        # 65 tests (58 in a venv without tiktoken; 7 real-tokenizer tests skip)
python mvps/r1_a/make_fixtures.py           # regenerate data/fixtures.json
```

Fixtures: `data/fixtures.json` (15 scenarios, 22 checks; every scenario
carries its `source_url`). The UI also accepts an uploaded scenario JSON;
malformed files are rejected with an error, not a crash. CSV export keeps
`source_url` on every row.

Real-tokenizer tests need tiktoken plus its downloaded encoding tables
(first run needs network to OpenAI's public blob store; afterwards the
tables are cached and the tests run offline). In the `.venv-real` test
venv they run; elsewhere they skip with a clear reason.
