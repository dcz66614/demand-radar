"""REWORK3 contract tests (R3-01 / R3-02 / R3-03).

Written by Muse for the REWORK3 fixes — these are NOT the frozen
independent regression file (tests/test_independent_r2.py, which must
not be edited). They cover the contract cases the REWORK3 brief
requires beyond the 4 independent tests: dual-key streaming
correlation, factual-content rules, and fail-closed schema types.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "mvps").is_dir():
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "mvps" / "r1_a"))
# Both mvps carry a make_fixtures.py; the R1-B tests import theirs
# (power_signal) with a deferred import, so r1_b must stay ahead of
# r1_a on sys.path — same order as tests/test_rework2_adversarial.py.
sys.path.insert(0, str(ROOT / "mvps" / "r1_b"))

from validator import (
    StreamingHandler,
    _validate_payload,
    check_factual_content,
    validate_stream,
)


def _dual_key_events():
    """Three parallel calls in the real Responses API shape: added
    carries item.id + call_id + output_index; deltas carry item_id AND
    output_index; dones carry the final arguments."""
    events = []
    for i, (cid, call, name) in enumerate([
        ("fc_A", "call_A", "search"),
        ("fc_B", "call_B", "calc"),
        ("fc_C", "call_C", "lookup"),
    ]):
        events.append({
            "type": "response.output_item.added", "output_index": i,
            "item": {"type": "function_call", "id": cid, "call_id": call, "name": name, "arguments": ""},
        })
    deltas = [
        (0, "fc_A", '{"q":'),
        (1, "fc_B", '{"x":'),
        (2, "fc_C", '{"k":'),
        (0, "fc_A", '"paris"}'),
        (1, "fc_B", '2}'),
        (2, "fc_C", '"v"}'),
    ]
    for idx, item_id, chunk in deltas:
        events.append({
            "type": "response.function_call_arguments.delta",
            "output_index": idx, "item_id": item_id, "delta": chunk,
        })
    index_of = {"fc_A": 0, "fc_B": 1, "fc_C": 2}
    for cid, call, args in [
        ("fc_B", "call_B", '{"x":2}'),
        ("fc_A", "call_A", '{"q":"paris"}'),
        ("fc_C", "call_C", '{"k":"v"}'),
    ]:
        events.append({
            "type": "response.output_item.done", "output_index": index_of[cid],
            "item": {"type": "function_call", "id": cid, "call_id": call, "arguments": args},
        })
    return events


# --- R3-01: true multi-call argument correlation --------------------------

def test_r3_01_interleaved_three_calls_dual_key():
    handler = StreamingHandler()
    for ev in _dual_key_events():
        handler.handle(ev)
    assert len(handler.completed) == 3
    assert not handler.anomalies
    got = {x["function_call"]["item"]["id"]: x["function_call"]["arguments"]
           for x in handler.completed}
    assert got == {"fc_A": '{"q":"paris"}', "fc_B": '{"x":2}', "fc_C": '{"k":"v"}'}
    assert all(x["arguments_valid"] for x in handler.completed)
    assert validate_stream(_dual_key_events(), emit_on_done=True)["passed"]


def test_r3_01_same_index_conflict_is_fail_closed():
    events = [
        {"type": "response.output_item.added", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "call_id": "call_A"}},
        {"type": "response.output_item.added", "output_index": 1,
         "item": {"type": "function_call", "id": "fc_B", "call_id": "call_B"}},
        # item_id says fc_A, output_index says fc_B: contradictory.
        {"type": "response.function_call_arguments.delta",
         "output_index": 1, "item_id": "fc_A", "delta": '{"q":"paris"}'},
        # Both dones carry no final arguments, so the only way the
        # contested delta could appear is by misattribution.
        {"type": "response.output_item.done", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "arguments": ""}},
        {"type": "response.output_item.done", "output_index": 1,
         "item": {"type": "function_call", "id": "fc_B", "arguments": ""}},
    ]
    handler = StreamingHandler()
    for ev in events:
        handler.handle(ev)
    assert any(a["kind"] == "key_conflict" for a in handler.anomalies)
    # The contested delta reached neither call.
    by_id = {x["function_call"]["item"]["id"]: x for x in handler.completed}
    assert by_id["fc_A"]["function_call"]["arguments"] == ""
    assert by_id["fc_B"]["function_call"]["arguments"] == ""
    assert not validate_stream(events, emit_on_done=True)["passed"]


def test_r3_01_duplicate_delta_sequence_dropped_once():
    handler = StreamingHandler()
    events = [
        {"type": "response.output_item.added", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "call_id": "call_A"}},
        {"type": "response.function_call_arguments.delta", "output_index": 0,
         "item_id": "fc_A", "sequence_number": 7, "delta": '{"q":'},
        {"type": "response.function_call_arguments.delta", "output_index": 0,
         "item_id": "fc_A", "sequence_number": 7, "delta": '{"q":'},
        {"type": "response.function_call_arguments.delta", "output_index": 0,
         "item_id": "fc_A", "sequence_number": 8, "delta": '"paris"}'},
        {"type": "response.output_item.done", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "arguments": '{"q":"paris"}'}},
    ]
    for ev in events:
        handler.handle(ev)
    assert any(a["kind"] == "duplicate_sequence" for a in handler.anomalies)
    assert handler.completed[0]["function_call"]["arguments"] == '{"q":"paris"}'
    assert not validate_stream(events, emit_on_done=True)["passed"]


def test_r3_01_unknown_item_id_delta_dropped_not_attributed():
    handler = StreamingHandler()
    events = [
        {"type": "response.output_item.added", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "call_id": "call_A"}},
        {"type": "response.function_call_arguments.delta", "output_index": 0,
         "item_id": "fc_NEVER_ADDED", "delta": '{"q":"paris"}'},
        {"type": "response.output_item.done", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "arguments": ""}},
    ]
    for ev in events:
        handler.handle(ev)
    assert any(a["kind"] == "key_conflict" for a in handler.anomalies)
    assert handler.completed[0]["function_call"]["arguments"] == ""
    assert not validate_stream(events, emit_on_done=True)["passed"]


def test_r3_01_keyless_delta_with_two_pending_is_ambiguous():
    handler = StreamingHandler()
    events = [
        {"type": "response.output_item.added",
         "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.added",
         "item": {"type": "function_call", "id": "b"}},
        {"type": "response.function_call_arguments.delta", "delta": "XYZ"},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "b"}},
    ]
    for ev in events:
        handler.handle(ev)
    assert any(a["kind"] == "ambiguous_delta" for a in handler.anomalies)
    assert all(x["function_call"]["arguments"] == "" for x in handler.completed)
    assert not validate_stream(events, emit_on_done=True)["passed"]


def test_r3_01_delta_after_done_recorded():
    handler = StreamingHandler()
    events = [
        {"type": "response.output_item.added",
         "item": {"type": "function_call", "id": "a"}},
        {"type": "response.function_call_arguments.delta", "item_id": "a", "delta": "AAA"},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a", "arguments": "AAA"}},
        {"type": "response.function_call_arguments.delta", "item_id": "a", "delta": "LATE"},
    ]
    for ev in events:
        handler.handle(ev)
    assert any(a["kind"] == "delta_after_done" for a in handler.anomalies)
    assert handler.completed[0]["function_call"]["arguments"] == "AAA"
    assert not validate_stream(events, emit_on_done=True)["passed"]


def test_r3_01_done_arguments_mismatch_fails():
    events = [
        {"type": "response.output_item.added", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "call_id": "call_A"}},
        {"type": "response.function_call_arguments.delta", "output_index": 0,
         "item_id": "fc_A", "delta": '{"q":"paris"}'},
        {"type": "response.output_item.done", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "arguments": '{"q":"london"}'}},
    ]
    handler = StreamingHandler()
    for ev in events:
        handler.handle(ev)
    assert handler.completed[0]["arguments_valid"] is False
    assert any(a["kind"] == "arguments_mismatch" for a in handler.anomalies)
    assert not validate_stream(events, emit_on_done=True)["passed"]


def test_r3_01_done_arguments_invalid_json_fails():
    events = [
        {"type": "response.output_item.added",
         "item": {"type": "function_call", "id": "a"}},
        {"type": "response.function_call_arguments.delta", "item_id": "a", "delta": "{bad"},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a", "arguments": "{bad"}},
    ]
    handler = StreamingHandler()
    for ev in events:
        handler.handle(ev)
    assert handler.completed[0]["arguments_valid"] is False
    assert not validate_stream(events, emit_on_done=True)["passed"]


def test_r3_01_done_final_arguments_without_deltas_is_valid():
    # Deltas may be absent; the done item's arguments are authoritative.
    check = validate_stream([
        {"type": "response.output_item.added", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "call_id": "call_A"}},
        {"type": "response.output_item.done", "output_index": 0,
         "item": {"type": "function_call", "id": "fc_A", "arguments": '{"q":"paris"}'}},
    ], emit_on_done=True)
    assert check["passed"] and check["emitted"] == 1


def test_r3_01_no_argument_call_is_legal():
    check = validate_stream([
        {"type": "response.output_item.added",
         "item": {"type": "function_call", "id": "a", "name": "ping"}},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a", "arguments": ""}},
    ], emit_on_done=True)
    assert check["passed"] and check["emitted"] == 1


def test_r3_01_empty_event_list_is_not_checked():
    check = validate_stream([], emit_on_done=True)
    assert check["outcome"] == "not-checked" and not check["passed"]


def test_r3_01_duplicate_done_still_emits_once():
    handler = StreamingHandler()
    for ev in [
        {"type": "response.output_item.added",
         "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a", "arguments": '{"x":1}'}},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a", "arguments": '{"x":1}'}},
    ]:
        handler.handle(ev)
    assert len(handler.completed) == 1
    assert handler.duplicate_dones == ["a"]
    assert validate_stream([
        {"type": "response.output_item.added",
         "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a", "arguments": '{"x":1}'}},
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "a", "arguments": '{"x":1}'}},
    ], emit_on_done=True)["passed"]


def test_r3_01_done_before_added_is_orphan():
    check = validate_stream([
        {"type": "response.output_item.done",
         "item": {"type": "function_call", "id": "x", "arguments": '{"x":1}'}},
    ], emit_on_done=True)
    assert not check["passed"] and check["emitted"] == 0


# --- R3-02: factual content -----------------------------------------------

def test_r3_02_known_correct_passes():
    status, passed, detail = check_factual_content(
        "The capital of France is Paris.",
        expected_answer="The capital of France is Paris.",
    )
    assert status == "ok" and passed


def test_r3_02_opposite_answer_fails():
    status, passed, _ = check_factual_content(
        "The capital of France is London.",
        expected_answer="The capital of France is Paris.",
    )
    assert status == "wrong-result" and not passed


def test_r3_02_refusal_fails():
    status, passed, _ = check_factual_content(
        "I don't know the answer.",
        expected_answer="The capital of France is Paris.",
    )
    assert not passed


def test_r3_02_negation_sentence_fails():
    status, passed, _ = check_factual_content(
        "Paris is NOT the capital of France.",
        expected_answer="The capital of France is Paris.",
    )
    assert not passed


def test_r3_02_negation_with_keyword_only_is_not_claimed_correct():
    # Keyword "paris" is present, but the sentence denies the claim.
    # The keyword rule may pass; factual truth must be NOT_CHECKED.
    status, passed, detail = check_factual_content(
        "Paris is NOT the capital.",
        expected_keywords=["paris"],
    )
    assert status == "not-checked"
    assert "not checked" in detail.lower()
    assert "factual truth" in detail.lower()


def test_r3_02_keyword_missing_fails():
    status, passed, _ = check_factual_content(
        "The capital of France is a city.",
        expected_keywords=["paris"],
    )
    assert status == "wrong-result" and not passed


def test_r3_02_only_expected_answer_is_compared():
    status, passed, _ = check_factual_content(
        "The capital of France is Paris.",
        expected_answer="The capital of France is Paris.",
    )
    assert status == "ok" and passed
    status, passed, _ = check_factual_content(
        "The capital of France is Berlin.",
        expected_answer="The capital of France is Paris.",
    )
    assert not passed


def test_r3_02_only_forbidden_claims_is_not_checked():
    status, passed, detail = check_factual_content(
        "The capital of France is Paris.",
        forbidden_claims=["berlin"],
    )
    assert status == "not-checked" and not passed  # R4-02: not-checked is not a pass
    assert "not checked" in detail.lower()


def test_r3_02_forbidden_claim_present_fails():
    status, passed, _ = check_factual_content(
        "The capital of France is Berlin.",
        forbidden_claims=["berlin"],
    )
    assert status == "wrong-result" and not passed


def test_r3_02_no_rules_is_not_checked():
    status, passed, detail = check_factual_content("The capital of France is Berlin.")
    assert status == "not-checked" and not passed  # R4-02: not-checked is not a pass
    assert "not checked" in detail.lower()


def test_r3_02_word_order_variant_passes_but_is_lexical_only():
    # Same words, different order: passes as a word-multiset match.
    # The detail must say what the check is — it is not semantic.
    status, passed, detail = check_factual_content(
        "PARIS is the capital of France!",
        expected_answer="The capital of France is Paris.",
    )
    assert passed
    assert "word-multiset" in detail


# --- R3-03: schema fail-closed --------------------------------------------

@pytest.mark.parametrize("spec", ["integer", "int"])
def test_r3_03_int_and_integer_reject_bool(spec):
    _, passed, _ = _validate_payload({"expected_schema": {"n": spec}}, {"n": True})
    assert not passed
    _, passed, _ = _validate_payload({"expected_schema": {"n": spec}}, {"n": 7})
    assert passed
    _, passed, _ = _validate_payload({"expected_schema": {"n": spec}}, {"n": 2.0})
    assert not passed  # a float is not an integer here, by contract


@pytest.mark.parametrize("spec", ["number", "float"])
def test_r3_03_number_rejects_bool_and_nonfinite(spec):
    _, passed, _ = _validate_payload({"expected_schema": {"n": spec}}, {"n": True})
    assert not passed
    for bad in (float("nan"), float("inf"), float("-inf")):
        _, passed, detail = _validate_payload({"expected_schema": {"n": spec}}, {"n": bad})
        assert not passed, (spec, bad, detail)
    _, passed, _ = _validate_payload({"expected_schema": {"n": spec}}, {"n": 3.5})
    assert passed
    _, passed, _ = _validate_payload({"expected_schema": {"n": spec}}, {"n": 3})
    assert passed


def test_r3_03_unknown_type_is_config_error_not_pass():
    _, passed, detail = _validate_payload(
        {"expected_schema": {"n": "intger"}}, {"n": 3})
    assert not passed
    assert "not-checked" in detail or "configuration" in detail.lower()
    _, passed, detail = _validate_payload(
        {"expected_schema": {"n": "integer"}}, {"n": True})
    assert not passed  # "integer" IS supported — bool still fails it


def test_r3_03_unknown_type_in_nested_spec_is_config_error():
    schema = {"user": {"type": "object", "properties": {"age": "intger"}}}
    _, passed, detail = _validate_payload({"expected_schema": schema}, {"user": {"age": 30}})
    assert not passed
    assert "configuration" in detail.lower()
    schema = {"vals": {"type": "array", "items": "intger"}}
    _, passed, detail = _validate_payload({"expected_schema": schema}, {"vals": [1, 2]})
    assert not passed
    assert "configuration" in detail.lower()


def test_r3_03_nonfinite_in_nested_spec_rejected():
    schema = {"vals": {"type": "array", "items": "float"}}
    _, passed, _ = _validate_payload({"expected_schema": schema}, {"vals": [1.0, math.nan]})
    assert not passed
    schema = {"user": {"type": "object", "properties": {"score": "number"}}}
    _, passed, _ = _validate_payload(
        {"expected_schema": schema}, {"user": {"score": float("inf")}})
    assert not passed
    _, passed, _ = _validate_payload(
        {"expected_schema": schema}, {"user": {"score": 9.5}})
    assert passed


def test_r3_03_standard_json_schema_names_supported():
    schema = {
        "a": "integer", "b": "number", "c": "string",
        "d": "boolean", "e": "array", "f": "object", "g": "null",
    }
    payload = {"a": 1, "b": 2.5, "c": "x", "d": False, "e": [1], "f": {}, "g": None}
    _, passed, _ = _validate_payload({"expected_schema": schema}, payload)
    assert passed
    payload["d"] = 1
    _, passed, _ = _validate_payload({"expected_schema": schema}, payload)
    assert not passed
    payload = {"a": 1, "b": 2.5, "c": "x", "d": False, "e": [1], "f": {}, "g": 0}
    _, passed, _ = _validate_payload({"expected_schema": schema}, payload)
    assert not passed


def test_r3_03_bool_does_not_satisfy_number_or_integer():
    for spec in ("number", "integer", "int", "float"):
        _, passed, _ = _validate_payload({"expected_schema": {"n": spec}}, {"n": False})
        assert not passed, spec
