"""REWORK4 contract tests (R4-01 strict JSON, R4-02 not-checked, R4-03 termination).

These cover the fixes beyond the frozen audit file
(tests/test_independent_r3.py, 10 tests): the 1e999 / nested
non-finite cases, the "NaN" string-in-text case, load_scenarios
strictness, the _validate_payload not-checked propagation, and the
termination-state cases (multi-call pending, zero pending, open
stream, done/delta after completed).
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "mvps").is_dir():
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "mvps" / "r1_a"))
# Both mvps carry a make_fixtures.py; the R1-B tests import theirs
# (power_signal) with a deferred import, so r1_b must stay ahead of
# r1_a on sys.path — same order as tests/test_rework2_adversarial.py
# and tests/test_rework3_contract.py.
sys.path.insert(0, str(ROOT / "mvps" / "r1_b"))

from validator import (
    SimulatedTransport,
    _parse_strict_json,
    _validate_payload,
    check_factual_content,
    load_scenarios,
    run_step,
    validate_stream,
)

# --- R4-01: strict JSON ------------------------------------------------------

@pytest.mark.parametrize("bad", [
    '{"n":NaN}',
    '{"n":Infinity}',
    '{"n":-Infinity}',
    '{"n":1e999}',
    '{"n":-1e999}',
    '{"a":{"b":[1,2,NaN]}}',
    '{"a":{"b":[1e999]}}',
])
def test_r4_01_strict_json_rejects_nonstandard_numbers(bad):
    with pytest.raises(ValueError):
        _parse_strict_json(bad)
    outcome, passed, detail = _validate_payload({}, {"raw": bad})
    assert outcome == "wrong-result" and not passed, (bad, outcome, passed, detail)


def test_r4_01_nan_as_string_text_is_legal():
    # "NaN" inside a JSON string is legal text — no regex may strip it.
    data = _parse_strict_json('{"s": "NaN and Infinity are words here"}')
    assert data["s"] == "NaN and Infinity are words here"
    outcome, passed, _ = _validate_payload({}, {"raw": '{"s": "NaN"}'})
    assert outcome == "ok" and passed


def test_r4_01_accumulated_only_nan_is_rejected():
    events = [
        {"type": "response.output_item.added", "output_index": 0,
         "item": {"type": "function_call", "id": "fc", "call_id": "c", "arguments": ""}},
        {"type": "response.function_call_arguments.delta", "output_index": 0,
         "item_id": "fc", "delta": '{"n":NaN}'},
        # done carries NO arguments: the accumulated deltas stand —
        # and they are not valid strict JSON, so the chunk is invalid.
        {"type": "response.output_item.done", "output_index": 0,
         "item": {"type": "function_call", "id": "fc", "call_id": "c"}},
    ]
    check = validate_stream(events, emit_on_done=True)
    assert not check["passed"] and check["outcome"] == "wrong-result"


def test_r4_01_load_scenarios_rejects_nonstandard_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('[{"name": "x", "kind": "api_call", "source_url": "http://x", "steps": [{"n": NaN}]}]', encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_scenarios(bad)


def test_r4_01_valid_json_still_parses():
    assert _parse_strict_json('{"n": 2, "ok": true, "s": "NaN"}') == {
        "n": 2, "ok": True, "s": "NaN"}


# --- R4-02: not-checked is not a pass ----------------------------------------

def test_r4_02_keyword_only_via_validate_payload_is_not_checked_not_pass():
    outcome, passed, detail = _validate_payload(
        {"expected_keywords": ["paris"]},
        {"content": "Paris is NOT the capital of France."},
    )
    assert outcome == "not-checked" and not passed
    assert "not checked" in detail.lower()


def test_r4_02_run_step_keyword_only_is_not_checked_not_pass():
    scenario = {"name": "Keyword Only", "kind": "api_call",
                "source_url": "https://example.org/dummy"}
    step = {"call": "answer",
            "response_content": "Paris is NOT the capital of France.",
            "expected_keywords": ["Paris"]}
    r = run_step(scenario, step, SimulatedTransport())
    assert r.outcome == "not-checked" and r.passed is False


def test_r4_02_no_rules_and_forbidden_absent_are_not_pass():
    for kwargs in ({}, {"forbidden_claims": ["berlin"]}):
        status, passed, _ = check_factual_content(
            "The capital of France is Paris.", **kwargs)
        assert status == "not-checked" and not passed, kwargs


def test_r4_02_expected_answer_match_is_still_a_real_pass():
    status, passed, _ = check_factual_content(
        "The capital of France is Paris.",
        expected_answer="The capital of France is Paris.")
    assert status == "ok" and passed


# --- R4-03: stream termination -----------------------------------------------

def _added(call_id, index=0):
    return {"type": "response.output_item.added", "output_index": index,
            "item": {"type": "function_call", "id": call_id,
                     "call_id": f"call_{call_id}", "arguments": ""}}


def _done(call_id, index=0, arguments=""):
    return {"type": "response.output_item.done", "output_index": index,
            "item": {"type": "function_call", "id": call_id,
                     "call_id": f"call_{call_id}", "arguments": arguments}}


def test_r4_03_completed_with_one_of_two_pending_fails():
    check = validate_stream(
        [_added("a", 0), _done("a", 0), _added("b", 1),
         {"type": "response.completed"}],
        emit_on_done=True)
    assert check["outcome"] == "wrong-result" and not check["passed"]
    assert check["termination"] == "completed"
    assert "still pending" in check["detail"]


def test_r4_03_completed_with_zero_pending_passes():
    check = validate_stream(
        [_added("a", 0), _done("a", 0), {"type": "response.completed"}],
        emit_on_done=True)
    assert check["passed"] and check["termination"] == "completed"


def test_r4_03_completed_alone_is_a_legal_empty_response():
    check = validate_stream([{"type": "response.completed"}], emit_on_done=True)
    assert check["passed"] and check["termination"] == "completed"
    assert check["emitted"] == 0


def test_r4_03_open_stream_is_incomplete_not_finished():
    check = validate_stream([_added("a", 0)], emit_on_done=True)
    assert check["termination"] == "open"
    assert check["emitted"] == 0
    # The emit constraint is preserved: nothing was emitted for the
    # call that was added but never done.
    assert "still open" in check["detail"]


def test_r4_03_empty_event_list_termination_is_none():
    check = validate_stream([], emit_on_done=True)
    assert check["termination"] == "none"
    assert check["outcome"] == "not-checked" and not check["passed"]


def test_r4_03_done_after_completed_is_an_anomaly():
    check = validate_stream(
        [_added("a", 0), {"type": "response.completed"}, _done("a", 0)],
        emit_on_done=True)
    assert check["outcome"] == "wrong-result" and not check["passed"]
    assert "event_after_completed" in check["detail"]


def test_r4_03_delta_after_completed_is_an_anomaly():
    check = validate_stream(
        [_added("a", 0),
         {"type": "response.function_call_arguments.delta", "output_index": 0,
          "item_id": "a", "delta": '{"x":1}'},
         {"type": "response.completed"},
         {"type": "response.function_call_arguments.delta", "output_index": 0,
          "item_id": "a", "delta": '{"x":1}'},
         _done("a", 0, '{"x":1}')],
        emit_on_done=True)
    assert check["outcome"] == "wrong-result" and not check["passed"]
    assert "event_after_completed" in check["detail"]
