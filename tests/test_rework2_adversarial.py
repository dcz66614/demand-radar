"""Independent REWORK2 adversarial regression tests.

Copy this file to tests/test_rework2_adversarial.py at the root of the
Demand Radar REWORK1 project, then run:
    python -m pytest tests/test_rework2_adversarial.py -q
These tests are intentionally RED on the reviewed REWORK1 version.
Each test names an observed real defect and passes after the intended repair.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "mvps").is_dir():
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "mvps" / "r1_a"))
sys.path.insert(0, str(ROOT / "mvps" / "r1_b"))

from signalcheck import check_rsa, check_rsp_phase, rsa_from_period
from validator import StreamingHandler, _validate_payload


def _small_variation_periods() -> list[float]:
    return [1000 + 0.1 * math.sin(2 * math.pi * i / 16) for i in range(64)]


def test_rsa_correct_negative_log_variance_must_pass() -> None:
    periods = _small_variation_periods()
    expected = rsa_from_period(periods)
    assert expected < 0  # log(variance in ms^2) can be negative
    assert check_rsa(periods, expected).passed is True


def test_rsa_million_mismatch_must_not_pass() -> None:
    periods = _small_variation_periods()
    assert rsa_from_period(periods) < 0
    assert check_rsa(periods, 1_000_000).passed is False


def test_rsp_phase_extra_duration_must_not_pass() -> None:
    check = check_rsp_phase([(0, 100), (100, 200)], 100, [1, 1, 999], "samples")
    assert check.passed is False


def test_schema_boolean_cannot_satisfy_integer() -> None:
    status, passed, _ = _validate_payload({"expected_schema": {"n": "int"}}, {"n": True})
    assert status == "wrong-result"
    assert passed is False


def test_two_completed_function_calls_are_not_dropped() -> None:
    events = [
        {"type": "response.output_item.added", "item": {"type": "function_call", "id": "a", "name": "A"}},
        {"type": "response.output_item.added", "item": {"type": "function_call", "id": "b", "name": "B"}},
        {"type": "response.output_item.done", "item": {"type": "function_call", "id": "a"}},
        {"type": "response.output_item.done", "item": {"type": "function_call", "id": "b"}},
    ]
    handler = StreamingHandler()
    for event in events:
        handler.handle(event)
    assert len(handler.completed) == 2
    assert {x["function_call"]["item"]["id"] for x in handler.completed} == {"a", "b"}
