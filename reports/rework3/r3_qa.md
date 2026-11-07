# R3 QA — Independent verification of the REWORK3 delivery zip

QA reviewer: independent (built none of R3-00–R3-05). Method: fresh
extract of the final delivery zip only, README commands verbatim,
every exit code recorded, plus own-design randomised counter-checks
against the real validator code. No GPT review is involved.

Date: 2026-11-06. QA working dir: `~/workspace/clean-test-r3-qa`
(home disk, NOT /tmp).

## 1. Zip integrity and old-zip preservation

| file | SHA-256 observed | expected | result |
|---|---|---|---|
| `demand-radar-rework3-2026-11-06.zip` | `17781712a616d993eb7a7c457571018b49c5cfba6ec9f4c3b29eb1fad2750a15` | `17781712…` | MATCH |
| original `demand-radar-2026-11-05.zip` | `963568deaff04e778123d17cd4f5cdaba7f9957212d248079240c12588f2b261` | `963568de…` | UNCHANGED |
| REWORK1 `demand-radar-rework1-2026-11-05.zip` | `0e736693b535f75641abce5e265c8e9ee91a5b63224fd0c5b9972e2ba89ea5c3` | `0e736693…` | UNCHANGED |
| REWORK2 `demand-radar-rework2-2026-11-05.zip` | `14c95a64e6c5c69412b03bb7e39e9f57d99fa32391ac56c8028499aff2ecf65b` | `14c95a64…` | UNCHANGED |

`unzip -t`: no errors. The zip contains a single top-level directory
`demand-radar-rework3/` (285 files, 4,984,423 bytes uncompressed);
`cd demand-radar-rework3` works — audit P1-03 is fixed.

## 2. README verbatim run (main venv, §1–§3)

Environment observed: Python 3.12.3, numpy 2.5.4, pandas 3.1.1,
pydantic 2.14.3, pytest 9.2.0, RapidFuzz 3.14.6, ruff 0.17.4,
streamlit 1.67.0 — all match the claimed pins.

| step | result | exit |
|---|---|---|
| `python3 -m venv .venv` | created | 0 |
| `pip install -r requirements.txt` | installed | 0 |
| `pip install -e . --no-deps` | installed | 0 |
| `demand_radar init` | DB created/migrated | 0 |
| `demand_radar score` | 221 pains | 0 |
| `demand_radar report --stage final` | 218 / 221 / 369 | 0 |
| `export --format csv` | 200 rows | 0 |
| `export --format json` | 200 rows | 0 |
| `export --format csv --all` | 218 rows | 0 |
| `diff reports/ranking.csv reports/rework2/ranking_r2_04.csv` | byte-identical | 0 |
| `pytest tests/test_rework2_adversarial.py tests/test_independent_r2.py -q` | **9 passed** | 0 |
| `pytest -q` | **280 passed, 8 skipped** | 0 |
| `ruff check .` | All checks passed | 0 |

Frozen independent file: `tests/test_independent_r2.py` SHA-256
`aa91307d12c9db5a4bc077aac5ef46bb9edb3d0ad8e221d6b8dd475caf237f15`,
byte-identical to the audit handoff copy at
`~/workspace/user/files/rework3-handoff/tests/test_independent_r2.py`
(same full hash). No independent-test expectation was modified.

### MANIFEST — one ordering nit (not a code defect)

`sha256sum -c reports/rework3/MANIFEST.sha256` run immediately after
README §2 gives **241/242 OK**: the single failure is
`./data/exports/source_items.csv`, because §2's last command
(`export --format csv --all`, 218 rows) overwrites the shipped
200-row file, which is covered by the manifest. Re-exporting the
default CSV (`export --format csv`, 200 rows) restores **242/242 OK**.
So the manifest itself is correct, and `r3_05.md` §3's "242/242 OK"
is reproducible — but only with an extra re-export step the README
does not state. Suggested fix (doc-only, for a future revision):
add one line to README §2/§3 noting the re-export, or run the
MANIFEST check before §2's exports. This does not affect any
validation result and does not change this verdict.

## 3. Real-upstream venv (§4)

Built `.venv-real` per README §4 (tiktoken 0.14.0, neurokit2 0.3.0,
wfdb 4.3.1, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2;
all installs exit 0). `pytest -q`: **297 passed, 0 skipped**,
6 warnings (wfdb `Pandas4Warning`, third-party — matches the README
note). Exit 0.

## 4. Apps (§5)

Headless `streamlit run` + curl: workbench **200**, R1-A **200**,
R1-B **200**.

## 5. DB / report / gate alignment

- `PRAGMA integrity_check`: **ok**; `PRAGMA foreign_key_check`: 0 errors.
- `reports/rework2/run_gate_r2_04.py`: `qualified 0`, `not qualified 221`,
  fingerprint `3d26137fd5e36e53ed08db7fea14c65d823c31dac3870b0e1386d8fe262fafe6`.
- `reports/rework2/compute_final_numbers.py` re-run: max score **45**,
  gate 0/221, sources 218 (200 VERIFIED / 18 REJECTED), pains 221,
  evidence 38 DIRECT / 10 ADJACENT / 5 DUPLICATE / 23 OUT_OF_SCOPE.
- `reports/mvp_selection.json`: prd_eligible **0**, mvp_built **2**,
  not_selected **221**, superseded **5**.
- Final report §11 spot-checks: item 14 (factual check is lexical,
  word order ignored) and item 6 (Python 3.13 NOT_TESTED) are honestly
  stated; item 15 (streaming sequence gaps) is real — see §7 below.
- R1-A README Positioning table and app banner state the three
  capabilities separately (stream event count / function argument
  integrity / factual truth) as claimed.

## 6. Independent counter-checks (own design, fresh seed 777001)

Script: `~/workspace/clean-test-r3-qa/qa_countercheck.py` (kept
outside the delivery). Run against the REAL `StreamingHandler`,
`validate_stream`, `check_factual_content`, `_validate_payload`
from the fresh extract. **39 assertions, 39 passed, 0 failed.**

- (a) Streaming, 40 randomised trials, 5 parallel dual-key calls,
  random 1–4 chunk splits, random cross-call interleaving (per-call
  chunk order preserved, as real streams deliver), random done
  order, globally unique sequence numbers: **40/40 ok**.
- (a2) Targeted adversaries, all correctly rejected
  (`wrong-result`): conflicting dual keys, duplicate sequence
  number, done with wrong arguments, done with invalid JSON,
  unknown `item_id` delta, keyless delta with 2 pending,
  delta after done, orphan done. Legal cases pass: no-arg call,
  empty event list → `not-checked`, output-index-only keying.
- (b) Factual content (12 cases): correct answer → ok; word-order
  variant → ok (lexical, documented); opposite / negation /
  refusal / paraphrase → wrong-result; keyword-only present →
  not-checked; keyword missing → wrong-result; forbidden present →
  wrong-result; no rules → not-checked; only-forbidden absent →
  not-checked.
- (c) Schema via `_validate_payload` (14 cases): bool ≠ integer,
  bool ≠ number, 2.0 ≠ integer, NaN/+inf/−inf ≠ number/float,
  unknown type (top-level and nested) → `not-checked` config
  error, nested NaN → wrong-result, bool inside integer array →
  wrong-result, valid payload → ok, missing field → wrong-result,
  null rules correct.

### Two false alarms raised and resolved during QA (my errors, not defects)

1. My first counter-check script used the event type
   `response.function_call_arguments.done` for done events. That
   type does not exist in the handler's dispatch (nor in the
   contract tests); the real type is `response.output_item.done`.
   Five initial "failures" were this script bug. After fixing the
   type, all pass.
2. My first expectation that "empty done args + non-empty deltas
   must fail" was wrong: the RECORDED #41708 fixture
   (`mvps/r1_a/data/fixtures.json`, `streaming-completed-41708`)
   has exactly that shape — its done item carries NO `arguments`
   field at all, and the correct handler must complete it with
   `{"q": "paris"}` from the deltas. The builder's "accumulated
   deltas stand" rule is REQUIRED by the recorded real evidence.
   The audit's P1-01 test (full done arguments, correct
   attribution) passes; the old defect was argument LOSS, and the
   completed chunks now carry the correct arguments (verified:
   `{"fc_A": '{"q":"paris"}', "fc_B": '{"x":2}'}`).

## 7. Confirmed residual (disclosed, not a blocker)

Final report §11.15 (streaming sequence gaps) is real. Probe:
true arguments `{"a":1,"b":2}`; the trailing chunk `,"b":2}` is
lost; done carries empty arguments → `validate_stream` returns
`ok` with completed arguments `{"a":1}` (silently incomplete),
no anomaly. When the done event carries the true full arguments,
the same gap IS caught (`arguments_mismatch` → wrong-result).
So the gap is exploitable only when done carries no arguments
AND the lost chunk leaves the remainder valid JSON. The report
discloses this honestly; it is not one of the audit's four
defects, and fixing it (per-call sequence contiguity) is a
follow-up, not a condition of this acceptance.

## 8. Stage-report cross-check

- `r3_01_02_03.md`: SDK event contract, designs, and counts match
  the code and the observed results; the 4 independent tests were
  RED on the REWORK2 baseline per the kept RED log and are GREEN
  here (re-verified §2).
- `r3_04.md`: pass-1 numbers (9/9, 280/8, 297/0, MANIFEST 240/240
  for pass 1, SHA `67a30c05…`) are consistent with the final-zip
  observations; the pass-1→final diff claim (2 files added, 3
  common files differ) is stated with its reconstruction method.
- `r3_05.md`: test totals (280/8, 297/0, 9/9) and MANIFEST 242
  match observation (subject to the §2 ordering nit above).
- `final_report_rework3.md` §10: "242 files verified in clean
  room" — verified 242/242 after the default re-export (§2).

## 9. Findings summary

- Genuine false-PASS defects found: **none**. All four audit
  defects (P1-01 dual-key argument loss, P1-02 expected-answer
  never compared, P2-01 fail-open schema types, P2-02 NaN as
  valid JSON) are fixed and verified, including by the frozen
  audit tests and by QA's own randomised counter-checks.
- Packaging defect P1-03: fixed (single top-level directory;
  README §1 works verbatim).
- Research conclusions unchanged as required: 0 qualifying PRDs,
  gate 70 unchanged, 2 PARTIALLY_REAL_WORLD_VALIDATED prototypes,
  #340 Qwen NOT_REAL_WORLD_VALIDATED.
- Observations (non-blocking): (1) the MANIFEST ordering nit in
  §2 above — one doc line would remove it; (2) the disclosed
  sequence-gap residual in §7 — a follow-up, not a blocker.

QA VERDICT: ACCEPTED_RESEARCH_PROTOTYPE_ONLY
