import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validator import (
    MAX_ATTEMPTS,
    PER_ATTEMPT_WAIT_MS,
    StreamingHandler,
    count_tokens_for_model,
    count_tokens_gpt4,
    load_scenarios,
    overcount_pct,
    run_all,
    run_scenario,
    validate_stream,
    validate_token_count,
)

HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "data" / "fixtures.json"

CHINESE = "调用大模型接口时，如果令牌计数错误，提示词会被错误地截断，导致智能体在执行多步骤任务时中途失败。"
ENGLISH = "The agent calls the model, counts the tokens, and checks the response carefully before it acts."
JAPANESE = "APIを呼び出すとき、トークン数が間違っていると、プロンプトが切り捨てられ、エージェントは途中で失敗します。"
CODE = "def count_tokens(text, model):\n    return len(text.split())"
MODEL = "litellm/qwen3-coder-30b"

EVENTS = [
    {"type": "response.output_item.added",
     "item": {"type": "function_call", "name": "search", "call_id": "call_1"}},
    {"type": "response.function_call_arguments.delta", "delta": "{\"q\": "},
    {"type": "response.function_call_arguments.delta", "delta": "\"paris\"}"},
    {"type": "response.output_item.done",
     "item": {"type": "function_call", "name": "search", "call_id": "call_1"}},
]


def _scenario(name):
    return next(s for s in load_scenarios(FIXTURES) if s["name"] == name)


def _result(name):
    return run_scenario(_scenario(name))


# --- #340 tokenizer substitution -------------------------------------------

def test_chinese_buggy_is_default_substituted():
    check = validate_token_count(CHINESE, MODEL, count_tokens_gpt4(CHINESE))
    assert check["outcome"] == "default-substituted" and not check["passed"]
    assert 0.8 < overcount_pct(CHINESE) < 1.2  # measured #340: +108.3%


def test_chinese_correct_count_passes():
    check = validate_token_count(CHINESE, MODEL, count_tokens_for_model(CHINESE, MODEL))
    assert check["outcome"] == "ok" and check["passed"]


def test_english_overcount_approximates_measured():
    assert 0.05 < overcount_pct(ENGLISH) < 0.20  # measured #340: +11.7%


def test_japanese_overcount_approximates_measured():
    assert 0.10 < overcount_pct(JAPANESE) < 0.30  # measured #340: +18.5%


def test_code_counts_identical():
    assert count_tokens_gpt4(CODE) == count_tokens_for_model(CODE, MODEL)
    assert overcount_pct(CODE) == 0.0  # measured #340: 0% on code


def test_arbitrary_wrong_count_is_wrong_result_not_substitution():
    check = validate_token_count(CHINESE, MODEL, 999)
    assert check["outcome"] == "wrong-result"


# --- #41708 streaming completion -------------------------------------------

def test_streaming_done_emits_exactly_one_completed_chunk():
    handler = StreamingHandler(emit_on_done=True)
    for ev in EVENTS:
        handler.handle(ev)
    assert len(handler.completed) == 1
    assert handler.completed[0]["function_call"]["arguments"] == "{\"q\": \"paris\"}"


def test_streaming_buggy_handler_emits_none():
    check = validate_stream(EVENTS, emit_on_done=False)
    assert check["outcome"] == "wrong-result" and not check["passed"]
    assert check["emitted"] == 0


def test_streaming_without_done_emits_none():
    check = validate_stream(EVENTS[:3], emit_on_done=True)
    assert check["passed"] and check["emitted"] == 0


# --- fault injection: retries, budget, classification ----------------------

def test_429_then_success_recovers():
    (r,) = _result("retry-429-then-success")
    assert r.outcome == "ok" and r.passed and r.attempts == 2


def test_persistent_429_is_rate_limited_within_budget():
    (r,) = _result("retry-429-exhausted")
    assert r.outcome == "rate-limited" and not r.passed
    assert r.attempts == MAX_ATTEMPTS  # budget never exceeded


def test_persistent_timeout_reports_elapsed_and_budget():
    (r,) = _result("timeout-exhausted")
    assert r.outcome == "timeout" and not r.passed
    assert r.attempts == MAX_ATTEMPTS
    assert r.elapsed_ms == MAX_ATTEMPTS * PER_ATTEMPT_WAIT_MS  # 60s/attempt, #182


def test_500_is_server_error_not_wrong_result():
    (r,) = _result("server-error-500")
    assert r.outcome == "server-error" and not r.passed


def test_malformed_json_is_wrong_result():
    (r,) = _result("malformed-response")
    assert r.outcome == "wrong-result" and "JSON" in r.detail


def test_schema_violation_is_wrong_result():
    (r,) = _result("schema-violation")
    assert r.outcome == "wrong-result" and "missing" in r.detail


def test_token_budget_exceeded_before_any_call():
    (r,) = _result("token-budget")
    assert r.outcome == "token-budget" and r.attempts == 0


def test_silent_trim_is_wrong_result():
    (r,) = _result("silent-trim")
    assert r.outcome == "wrong-result" and "silently trimmed" in r.detail


def test_false_openrouter_response_classified_with_latency():
    (r,) = _result("false-response-openrouter")
    assert r.outcome == "wrong-result" and not r.passed
    assert r.elapsed_ms == 45000  # long wait recorded, not hidden
    # R2-05: caught by CONTENT comparison against the fixture's expected
    # answer, not by a factual=False flag (the flag no longer exists).
    assert "paris" in r.detail.lower()


def test_hidden_default_substitution_detected_in_call():
    (r,) = _result("hidden-default-substitution")
    assert r.outcome == "default-substituted" and not r.passed


# --- fixtures, loading, export ---------------------------------------------

def test_all_fixture_scenarios_run_and_every_row_has_source():
    results = run_all(load_scenarios(FIXTURES))
    assert len(results) == 22  # R2-05: 15 scenarios (was 14) — +1 true-response control
    assert all(r.source_url.startswith("https://") for r in results)
    assert {r.outcome for r in results} <= {
        "ok", "timeout", "rate-limited", "server-error",
        "wrong-result", "default-substituted", "token-budget",
    }


def test_load_invalid_json_raises_value_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_scenarios(bad)


def test_load_missing_source_url_raises_value_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('[{"name": "x", "kind": "api_call"}]', encoding="utf-8")
    with pytest.raises(ValueError):
        load_scenarios(bad)


def test_load_unknown_kind_raises_value_error():
    with pytest.raises(ValueError):
        run_scenario({"name": "x", "kind": "telepathy", "source_url": "https://x.example"})


def test_export_csv_preserves_source_url(tmp_path):
    results = run_all(load_scenarios(FIXTURES))
    out = tmp_path / "export.csv"
    from validator import export_csv

    export_csv(results, out)
    with open(out, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(results)
    assert "source_url" in rows[0]
    assert all(r["source_url"].startswith("https://") for r in rows)
    assert any(r["outcome"] == "default-substituted" for r in rows)


# --- REWORK2 R2-01: schema bool/int + nested types (review P1-02) ----------

def test_schema_bool_true_is_not_int():
    from validator import _validate_payload

    status, passed, _ = _validate_payload({"expected_schema": {"n": "int"}}, {"n": True})
    assert status == "wrong-result" and not passed


def test_schema_bool_false_is_not_int():
    from validator import _validate_payload

    status, passed, _ = _validate_payload({"expected_schema": {"n": "int"}}, {"n": False})
    assert status == "wrong-result" and not passed


@pytest.mark.parametrize("value,ok", [(3, True), (0, True), (-7, True), (3.5, False), ("3", False), (None, False)])
def test_schema_int_accepts_only_real_ints(value, ok):
    from validator import _validate_payload

    _, passed, _ = _validate_payload({"expected_schema": {"n": "int"}}, {"n": value})
    assert passed is ok


@pytest.mark.parametrize("value,ok", [(3.5, True), (3, True), (True, False), ("3.5", False)])
def test_schema_float_accepts_numbers_not_bool(value, ok):
    from validator import _validate_payload

    _, passed, _ = _validate_payload({"expected_schema": {"x": "float"}}, {"x": value})
    assert passed is ok


def test_schema_nested_object_bool_rejected():
    from validator import _validate_payload

    schema = {"user": {"type": "object", "properties": {"age": "int", "name": "str"}}}
    _, passed, _ = _validate_payload({"expected_schema": schema}, {"user": {"age": True, "name": "a"}})
    assert not passed
    _, passed, _ = _validate_payload({"expected_schema": schema}, {"user": {"age": 30, "name": "a"}})
    assert passed


def test_schema_nested_array_bool_rejected():
    from validator import _validate_payload

    schema = {"vals": {"type": "array", "items": "int"}}
    _, passed, _ = _validate_payload({"expected_schema": schema}, {"vals": [1, True, 3]})
    assert not passed
    _, passed, _ = _validate_payload({"expected_schema": schema}, {"vals": [1, 2, 3]})
    assert passed


# --- REWORK2 R2-01: streaming correlation (review P1-03) -------------------

def test_streaming_interleaved_calls_keep_arguments_separate():
    handler = StreamingHandler(emit_on_done=True)
    events = [
        {"type": "response.output_item.added", "item": {"type": "function_call", "id": "a", "name": "A"}},
        {"type": "response.output_item.added", "item": {"type": "function_call", "id": "b", "name": "B"}},
        {"type": "response.function_call_arguments.delta", "item_id": "a", "delta": "AAA"},
        {"type": "response.function_call_arguments.delta", "item_id": "b", "delta": "BBB"},
        {"type": "response.function_call_arguments.delta", "item_id": "a", "delta": "aaa"},
        {"type": "response.output_item.done", "item": {"type": "function_call", "id": "b"}},
        {"type": "response.output_item.done", "item": {"type": "function_call", "id": "a"}},
    ]
    for ev in events:
        handler.handle(ev)
    assert len(handler.completed) == 2
    by_id = {x["function_call"]["item"]["id"]: x for x in handler.completed}
    assert by_id["a"]["function_call"]["arguments"] == "AAAaaa"
    assert by_id["b"]["function_call"]["arguments"] == "BBB"


def test_streaming_duplicate_done_emits_once():
    handler = StreamingHandler(emit_on_done=True)
    events = [
        {"type": "response.output_item.added", "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.done", "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.done", "item": {"type": "function_call", "id": "a"}},
    ]
    for ev in events:
        handler.handle(ev)
    assert len(handler.completed) == 1
    assert handler.duplicate_dones == ["a"]


def test_streaming_done_before_added_is_orphan_not_completed():
    handler = StreamingHandler(emit_on_done=True)
    handler.handle({"type": "response.output_item.done", "item": {"type": "function_call", "id": "x"}})
    assert handler.completed == []
    assert handler.orphan_dones == ["x"]
    assert not validate_stream(
        [{"type": "response.output_item.done", "item": {"type": "function_call", "id": "x"}}],
        emit_on_done=True)["passed"]


def test_streaming_output_index_keying():
    check = validate_stream([
        {"type": "response.output_item.added", "output_index": 0,
         "item": {"type": "function_call", "name": "A"}},
        {"type": "response.output_item.added", "output_index": 1,
         "item": {"type": "function_call", "name": "B"}},
        {"type": "response.output_item.done", "output_index": 1,
         "item": {"type": "function_call", "name": "B"}},
        {"type": "response.output_item.done", "output_index": 0,
         "item": {"type": "function_call", "name": "A"}},
    ], emit_on_done=True)
    assert check["passed"] and check["emitted"] == 2


def test_streaming_call_id_keying_matches_recorded_fixtures():
    # The recorded #41708 fixtures carry call_id, not id.
    check = validate_stream(EVENTS, emit_on_done=True)
    assert check["passed"] and check["emitted"] == 1


def test_streaming_partial_done_counts_only_finished_calls():
    check = validate_stream([
        {"type": "response.output_item.added", "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.added", "item": {"type": "function_call", "id": "b"}},
        {"type": "response.output_item.done", "item": {"type": "function_call", "id": "a"}},
    ], emit_on_done=True)
    assert check["passed"] and check["emitted"] == 1


def test_streaming_randomised_interleaving():
    """Seeded random counterexamples: 3 interleaved calls, random delta
    order — every done call completes exactly once, arguments never cross."""
    import random

    rng = random.Random(20261105)
    for trial in range(50):
        ids = ["a", "b", "c"]
        added_events = [{"type": "response.output_item.added",
                         "item": {"type": "function_call", "id": k}} for k in ids]
        # Per-call chunk order must be preserved when interleaving: the
        # handler appends deltas in arrival order, so shuffling a call's own
        # chunks would change the expected argument string itself.
        expected_args = {k: "" for k in ids}
        per_call_chunks: dict[str, list[str]] = {k: [] for k in ids}
        for k in ids:
            for _ in range(rng.randint(1, 3)):
                chunk = f"{k}{rng.randint(0, 9)}"
                expected_args[k] += chunk
                per_call_chunks[k].append(chunk)
        delta_events = []
        remaining = {k: list(v) for k, v in per_call_chunks.items()}
        while any(remaining.values()):
            k = rng.choice([k for k in ids if remaining[k]])
            chunk = remaining[k].pop(0)
            delta_events.append({"type": "response.function_call_arguments.delta",
                                 "item_id": k, "delta": chunk})
        done_order = ids[:]
        rng.shuffle(done_order)
        done_events = [{"type": "response.output_item.done",
                        "item": {"type": "function_call", "id": k}} for k in done_order]
        # Stream causality holds: no delta for a call arrives after its
        # done event (all deltas precede all dones here).
        handler = StreamingHandler(emit_on_done=True)
        for ev in added_events + delta_events + done_events:
            handler.handle(ev)
        assert len(handler.completed) == 3, f"trial {trial}"
        by_id = {x["function_call"]["item"]["id"]: x for x in handler.completed}
        for k in ids:
            assert by_id[k]["function_call"]["arguments"] == expected_args[k], f"trial {trial}"
