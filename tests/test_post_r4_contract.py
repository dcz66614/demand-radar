"""POST-R4 contract tests: Responses API terminal-state coverage.

The frozen audit file (tests/test_post_r4_termination.py) covers the
7 RED→GREEN cases. This file covers the POST-R4 fix's own rules:
conflicting / duplicate terminal events, data after a failure terminal,
the open-stream "not yet proven" label, the terminal reason in the
detail, and that a failed-terminal streaming scenario is never counted
as a passed check.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Reuse the frozen file's helpers (same shapes as the audit's RED cases).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mvps" / "r1_a"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mvps" / "r1_b"))
from validator import run_scenario, validate_stream


def _call_events(complete_call: bool, terminal: str | None) -> list[dict]:
    events = [
        {
            "type": "response.output_item.added",
            "output_index": 0,
            "item": {"type": "function_call", "id": "fc_a", "call_id": "call_a", "arguments": ""},
        }
    ]
    if complete_call:
        events.extend(
            [
                {
                    "type": "response.function_call_arguments.delta",
                    "item_id": "fc_a",
                    "output_index": 0,
                    "delta": '{"x":1}',
                },
                {
                    "type": "response.output_item.done",
                    "output_index": 0,
                    "item": {
                        "type": "function_call",
                        "id": "fc_a",
                        "call_id": "call_a",
                        "arguments": '{"x":1}',
                    },
                },
            ]
        )
    if terminal is None:
        return events
    if terminal == "error":
        events.append({"type": "error", "message": "server error", "code": "server_error"})
    else:
        status = terminal.replace("response.", "")
        events.append({"type": terminal, "response": {"id": "resp_t", "status": status}})
    return events


# --- P0-02: failure terminals always fail, with the reason named. ---


def test_failed_terminal_detail_names_the_terminal():
    verdict = validate_stream(_call_events(True, "response.failed"), emit_on_done=True)
    assert verdict["passed"] is False
    assert verdict["outcome"] != "ok"
    assert verdict["termination"] == "failed"
    assert "terminated with failed" in verdict["detail"]


def test_incomplete_terminal_carries_its_reason():
    events = _call_events(True, None)
    events.append(
        {
            "type": "response.incomplete",
            "response": {
                "id": "resp_t",
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
            },
        }
    )
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is False
    assert verdict["termination"] == "incomplete"
    assert "max_output_tokens" in verdict["detail"]


def test_error_terminal_carries_code_and_message():
    verdict = validate_stream(_call_events(True, "error"), emit_on_done=True)
    assert verdict["passed"] is False
    assert verdict["termination"] == "error"
    assert "server_error" in verdict["detail"]
    assert "server error" in verdict["detail"]


def test_failed_terminal_alone_is_a_failed_response_not_not_checked():
    verdict = validate_stream(
        [{"type": "response.failed", "response": {"id": "resp_t", "status": "failed"}}],
        emit_on_done=True,
    )
    assert verdict["passed"] is False
    assert verdict["outcome"] == "wrong-result"
    assert verdict["termination"] == "failed"


# --- P0-01: conflicting / duplicate terminals, data after a terminal. ---


def test_conflicting_terminals_fail():
    events = _call_events(True, "response.completed")
    events.append({"type": "response.failed", "response": {"id": "resp_t", "status": "failed"}})
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is False
    assert verdict["outcome"] != "ok"
    assert "conflicting_terminal" in verdict["detail"]
    # The first terminal wins: the stream is still "completed".
    assert verdict["termination"] == "completed"


def test_failed_then_completed_is_also_a_conflict():
    events = _call_events(True, "response.failed")
    events.append(
        {"type": "response.completed", "response": {"id": "resp_t", "status": "completed"}}
    )
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is False
    assert "conflicting_terminal" in verdict["detail"]
    assert verdict["termination"] == "failed"


def test_duplicate_identical_terminal_is_tolerated_but_recorded():
    events = _call_events(True, "response.completed")
    events.append(
        {"type": "response.completed", "response": {"id": "resp_t", "status": "completed"}}
    )
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is True, verdict
    assert verdict["termination"] == "completed"
    assert "duplicate terminal" in verdict["detail"]


def test_data_after_failed_terminal_is_an_anomaly():
    events = _call_events(True, "response.failed")
    events.append(
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_a",
            "output_index": 0,
            "delta": '{"x":2}',
        }
    )
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is False
    assert "event_after_terminal" in verdict["detail"]


def test_data_after_error_terminal_is_an_anomaly():
    events = _call_events(True, "error")
    events.append(
        {
            "type": "response.output_item.done",
            "output_index": 0,
            "item": {
                "type": "function_call",
                "id": "fc_a",
                "call_id": "call_a",
                "arguments": '{"x":1}',
            },
        }
    )
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is False
    assert "event_after_terminal" in verdict["detail"]


def test_data_after_completed_still_uses_the_r4_kind_name():
    events = _call_events(True, "response.completed")
    events.append(
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_a",
            "output_index": 0,
            "delta": '{"x":2}',
        }
    )
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is False
    assert "event_after_completed" in verdict["detail"]


# --- P0-02: open streams keep their semantics but are labelled. ---


def test_open_stream_detail_says_success_not_yet_proven():
    verdict = validate_stream(_call_events(True, None), emit_on_done=True)
    assert verdict["passed"] is True, verdict
    assert verdict["termination"] == "open"
    assert "not yet proven" in verdict["detail"]


def test_open_stream_with_pending_call_is_labelled_too():
    verdict = validate_stream(_call_events(False, None), emit_on_done=True)
    assert verdict["passed"] is True, verdict
    assert verdict["termination"] == "open"
    assert "not yet proven" in verdict["detail"]
    assert "still open" in verdict["detail"]


# --- P0-03: a failed-terminal streaming scenario never counts as passed. ---


def test_streaming_scenario_with_failed_terminal_is_not_passed():
    scenario = {
        "id": "streaming-failed-terminal",
        "name": "streaming with response.failed",
        "kind": "streaming",
        "events": _call_events(True, "response.failed"),
        "emit_on_done": True,
    }
    results = run_scenario(scenario)
    assert len(results) == 1, results
    result = results[0]
    assert result.outcome == "wrong-result"
    assert result.passed is False
    assert "terminated with failed" in result.detail
    # The app counts a check as passed only when outcome == "ok" and
    # passed — a failed terminal can never satisfy either condition.
    assert not (result.outcome == "ok" and result.passed)
