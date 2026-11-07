"""P2-A contract tests: chunk validity vs request completion (sixth-round audit).

The audit's P2-A item: an open stream can still return passed=True, which
is chunk coherence, not a completed successful request. This file pins
the split: ``validate_stream`` now returns ``call_chunk_valid``,
``request_completed_successfully`` and ``request_status`` alongside the
unchanged ``passed`` / ``outcome`` / ``termination`` — the frozen files
assert an open stream passes, so ``passed`` keeps its chunk-coherence
meaning and the UI, not the validator, changes what it counts.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mvps" / "r1_a"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mvps" / "r1_b"))
from validator import export_csv, load_scenarios, run_all, run_scenario, validate_stream

FIXTURES = Path(__file__).resolve().parents[1] / "mvps" / "r1_a" / "data" / "fixtures.json"


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


# --- P2-A: the split itself. ---


def test_completed_stream_is_completed_and_counts_as_passed():
    verdict = validate_stream(_call_events(True, "response.completed"), emit_on_done=True)
    assert verdict["passed"] is True
    assert verdict["call_chunk_valid"] is True
    assert verdict["request_completed_successfully"] is True
    assert verdict["request_status"] == "completed"
    assert verdict["outcome"] == "ok"
    assert verdict["termination"] == "completed"


def test_open_chunk_valid_stream_is_pending_not_a_completed_success():
    # added only, no done, no terminal: chunks coherent, request unproven.
    # ``passed`` KEEPS its chunk-coherence meaning (frozen files assert
    # an open stream passes); only the new fields say it is not a
    # completed success.
    verdict = validate_stream(_call_events(False, None), emit_on_done=True)
    assert verdict["passed"] is True
    assert verdict["call_chunk_valid"] is True
    assert verdict["request_completed_successfully"] is False
    assert verdict["request_status"] == "pending"
    assert verdict["outcome"] == "ok"
    assert verdict["termination"] == "open"


def test_open_stream_with_done_call_is_pending_too():
    # Done call, no terminal: the recorded #41708 shape. Coherent chunks,
    # still pending — the request's success is not yet proven.
    verdict = validate_stream(_call_events(True, None), emit_on_done=True)
    assert verdict["passed"] is True
    assert verdict["request_completed_successfully"] is False
    assert verdict["request_status"] == "pending"


def test_failed_terminal_is_failed_not_pending():
    verdict = validate_stream(_call_events(False, "response.failed"), emit_on_done=True)
    assert verdict["passed"] is False
    assert verdict["call_chunk_valid"] is False
    assert verdict["request_completed_successfully"] is False
    assert verdict["request_status"] == "failed"
    assert verdict["outcome"] == "wrong-result"


def test_completed_with_pending_call_is_failed():
    events = _call_events(True, "response.completed")
    events.insert(
        0,
        {
            "type": "response.output_item.added",
            "output_index": 1,
            "item": {"type": "function_call", "id": "fc_b", "call_id": "call_b", "arguments": ""},
        },
    )
    verdict = validate_stream(events, emit_on_done=True)
    assert verdict["passed"] is False
    assert verdict["request_completed_successfully"] is False
    assert verdict["request_status"] == "failed"


def test_no_events_is_not_checked_status():
    verdict = validate_stream([], emit_on_done=True)
    assert verdict["outcome"] == "not-checked"
    assert verdict["passed"] is False
    assert verdict["call_chunk_valid"] is False
    assert verdict["request_completed_successfully"] is False
    assert verdict["request_status"] == "not-checked"


# --- P2-A: threading through run_scenario / CallResult. ---


def test_streaming_scenario_threads_the_new_fields():
    scenarios = load_scenarios(FIXTURES)
    scenario = next(s for s in scenarios if s["name"] == "streaming-no-done")
    (result,) = run_scenario(scenario)
    assert result.passed is True  # chunk coherence, unchanged
    assert result.termination == "open"
    assert result.request_completed_successfully is False
    assert result.request_status == "pending"


def test_completed_streaming_fixture_threads_completed():
    scenarios = load_scenarios(FIXTURES)
    scenario = next(s for s in scenarios if s["name"] == "streaming-completed-41708")
    (result,) = run_scenario(scenario)
    # The recorded #41708 replay has no terminal event: coherent but open.
    assert result.passed is True
    assert result.termination == "open"
    assert result.request_completed_successfully is False
    assert result.request_status == "pending"


def test_api_call_scenario_threads_completion_fields():
    scenarios = load_scenarios(FIXTURES)
    results = run_all(scenarios)
    api = [r for r in results if r.kind == "api_call"]
    assert api, "fixtures must contain api_call checks"
    for r in api:
        assert r.termination == ""  # not a stream
        assert r.request_completed_successfully == (r.outcome == "ok" and r.passed)
        expected = (
            "completed"
            if r.request_completed_successfully
            else ("failed" if r.outcome != "not-checked" else "not-checked")
        )
        assert r.request_status == expected


# --- P2-A: the fixture sweep under the new counting. ---


def test_fixture_sweep_counts_are_seven_thirteen_zero_two():
    results = run_all(load_scenarios(FIXTURES))
    passed = sum(1 for r in results if r.request_completed_successfully)
    pending = sum(1 for r in results if r.request_status == "pending")
    not_checked = sum(1 for r in results if r.outcome == "not-checked")
    failed = len(results) - passed - pending - not_checked
    assert (passed, failed, not_checked, pending) == (7, 13, 0, 2)
    # The two pending rows are exactly the open chunk-valid streams.
    assert {r.scenario for r in results if r.request_status == "pending"} == {
        "streaming-completed-41708",
        "streaming-no-done",
    }


def test_export_csv_carries_the_new_columns(tmp_path):
    results = run_all(load_scenarios(FIXTURES))
    out = tmp_path / "export.csv"
    export_csv(results, out)
    with open(out, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert "termination" in rows[0]
    assert "request_completed_successfully" in rows[0]
    assert "request_status" in rows[0]
    pending = [r for r in rows if r["request_status"] == "pending"]
    assert len(pending) == 2
    assert all(r["request_completed_successfully"] == "False" for r in pending)
