"""Independent post-REWORK4 edge-case tests for Responses API termination.

Not part of Muse's original REWORK4 acceptance gate. Tested against exact
Drive ZIP SHA-256 15d391be750b0dc7b59a1070595006f48a4b26e7a86e44789c33d488cfe75537.

Usage:
  DEMAND_RADAR_ROOT=/path/to/extracted/demand-radar-rework4 \
  python -m pytest -q /mnt/data/Demand_Radar_R4_Additional_Termination_Tests.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(os.environ.get('DEMAND_RADAR_ROOT', Path.cwd()))
sys.path.insert(0, str(ROOT / 'mvps' / 'r1_a'))
from validator import validate_stream  # noqa: E402


def _events(complete_call: bool, terminal: str) -> list[dict]:
    events = [{
        'type': 'response.output_item.added',
        'output_index': 0,
        'item': {'type': 'function_call', 'id': 'fc_a',
                 'call_id': 'call_a', 'arguments': ''},
    }]
    if complete_call:
        events.extend([
            {'type': 'response.function_call_arguments.delta',
             'item_id': 'fc_a', 'output_index': 0, 'delta': '{"x":1}'},
            {'type': 'response.output_item.done', 'output_index': 0,
             'item': {'type': 'function_call', 'id': 'fc_a',
                      'call_id': 'call_a', 'arguments': '{"x":1}'}},
        ])
    if terminal == 'error':
        events.append({'type': 'error', 'message': 'server error', 'code': 'server_error'})
    else:
        status = terminal.replace('response.', '')
        events.append({'type': terminal, 'response': {'id': 'resp_t', 'status': status}})
    return events


@pytest.mark.parametrize('terminal', ['response.failed', 'response.incomplete'])
@pytest.mark.parametrize('complete_call', [True, False])
def test_terminal_failure_or_incomplete_is_not_pass(complete_call, terminal):
    verdict = validate_stream(_events(complete_call, terminal), emit_on_done=True)
    assert verdict['passed'] is False, verdict
    assert verdict['outcome'] != 'ok', verdict
    assert verdict['termination'] in {'failed', 'incomplete'}, verdict


def test_error_event_cannot_be_counted_as_pass():
    verdict = validate_stream(_events(True, 'error'), emit_on_done=True)
    assert verdict['passed'] is False, verdict


def test_normal_completed_call_remains_pass():
    verdict = validate_stream(_events(True, 'response.completed'), emit_on_done=True)
    assert verdict['outcome'] == 'ok' and verdict['passed'] is True, verdict
    assert verdict['termination'] == 'completed', verdict


def test_completed_with_pending_call_remains_fail():
    verdict = validate_stream(_events(False, 'response.completed'), emit_on_done=True)
    assert verdict['outcome'] != 'ok' and verdict['passed'] is False, verdict
    assert verdict['termination'] == 'completed', verdict
