"""Independent fourth-round regressions for Demand Radar REWORK3.

Run from extracted project root:
  python -m pytest /mnt/data/Demand_Radar_REWORK3_Independent_Regression_Tests.py -v

These tests do not modify the source repo and make no external requests.
The first four test functions are known failures in the inspected REWORK3 ZIP.
Existing valid-behaviour controls must stay green.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(os.environ.get('DEMAND_RADAR_ROOT', str(Path.cwd())))
sys.path.insert(0, str(ROOT / 'mvps' / 'r1_a'))
from validator import (  # noqa: E402
    SimulatedTransport,
    _validate_payload,
    check_factual_content,
    run_step,
    validate_stream,
)

@pytest.mark.parametrize('invalid_json', [
    '{"n":NaN}',
    '{"n":Infinity}',
    '{"n":-Infinity}',
])
def test_raw_response_must_reject_nonstandard_json_constants(invalid_json):
    outcome, passed, detail = _validate_payload({}, {'raw': invalid_json})
    assert not passed and outcome != 'ok', (outcome, passed, detail)


def test_streaming_function_arguments_must_reject_json_nan():
    events = [
        {'type':'response.output_item.added', 'output_index':0,
         'item': {'type':'function_call', 'id':'fc_test', 'call_id':'call_test', 'arguments':''}},
        {'type':'response.function_call_arguments.delta', 'output_index':0,
         'item_id':'fc_test', 'delta':'{"n":NaN}'},
        {'type':'response.output_item.done', 'output_index':0,
         'item': {'type':'function_call', 'id':'fc_test','call_id':'call_test','arguments':'{"n":NaN}'}}
    ]
    verdict = validate_stream(events, emit_on_done=True)
    assert not verdict['passed'], verdict


def test_not_checked_factual_result_must_not_inflate_pass_count():
    scenario = {'name':'Keyword Only','kind':'api_call', 'source_url':'https://example.org/dummy'}
    step = {'call':'answer', 'response_content':'Paris is NOT the capital of France.',
            'expected_keywords':['Paris']}
    r = run_step(scenario, step, SimulatedTransport())
    assert r.outcome == 'not-checked', r
    assert r.passed is False, ('NOT_CHECKED must not count as a verified PASS',r)


def test_completed_response_with_unfinished_function_call_must_not_pass():
    events = [
        {'type':'response.output_item.added', 'output_index':0,
         'item': {'type':'function_call', 'id':'fc_aborted','call_id':'c_aborted'}},
        {'type':'response.completed'},
    ]
    v = validate_stream(events, emit_on_done=True)
    assert v['outcome'] != 'ok' and not v['passed'], v


# Positive and negative controls: protect legitimate prior behaviour.
def test_strict_valid_json_still_passes():
    assert _validate_payload({}, {'raw':'{"n":2,"ok":true}'})[:2] == ('ok',True)


def test_expected_answer_contradiction_still_fails():
    assert check_factual_content('The capital of France is London.',
                                  expected_answer='The capital of France is Paris.')[1] is False


def test_boolean_not_integer_still_fails():
    assert _validate_payload({'expected_schema':{'x':'integer'}}, {'x':True})[1] is False


def test_legal_no_arguments_completed_function_call_still_passes():
    events = [
        {'type':'response.output_item.added', 'output_index':0,
         'item': {'type':'function_call', 'id':'fc_empty','call_id':'call_empty','arguments':''}},
        {'type':'response.output_item.done', 'output_index':0,
         'item': {'type':'function_call', 'id':'fc_empty','call_id':'call_empty','arguments':''}}
    ]
    assert validate_stream(events, emit_on_done=True)['passed'] is True
