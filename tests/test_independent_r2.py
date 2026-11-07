"""Independent REWORK2 acceptance regressions: copy to tests/test_independent_r2.py.

Run from the project root:
    python -m pytest tests/test_independent_r2.py -v
These tests check requirements rather than the current implementation.
They intentionally fail on the ZIP delivered 2026-11-06.
No network, real accounts, or paid APIs are used.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / 'mvps').is_dir():
    ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'mvps' / 'r1_a'))

from validator import StreamingHandler, validate_stream, check_factual_content, _validate_payload  # noqa: E402


def _realistic_parallel_response_events():
    """OpenAI Responses SDK event shape: output item has id, delta has item_id AND output_index."""
    return [
        {'type':'response.output_item.added','output_index':0,'item':{'type':'function_call','id':'fc_A','call_id':'call_A','name':'search','arguments':''}},
        {'type':'response.output_item.added','output_index':1,'item':{'type':'function_call','id':'fc_B','call_id':'call_B','name':'calc','arguments':''}},
        {'type':'response.function_call_arguments.delta','output_index':0,'item_id':'fc_A','delta':'{"q":'},
        {'type':'response.function_call_arguments.delta','output_index':1,'item_id':'fc_B','delta':'{"x":2}'},
        {'type':'response.function_call_arguments.delta','output_index':0,'item_id':'fc_A','delta':'"paris"}'},
        {'type':'response.output_item.done','output_index':0,'item':{'type':'function_call','id':'fc_A','call_id':'call_A','name':'search','arguments':'{"q":"paris"}'}},
        {'type':'response.output_item.done','output_index':1,'item':{'type':'function_call','id':'fc_B','call_id':'call_B','name':'calc','arguments':'{"x":2}'}}
    ]


def test_parallel_stream_preserves_each_arguments_payload():
    handler = StreamingHandler()
    for event in _realistic_parallel_response_events():
        handler.handle(event)
    got = {x['function_call']['item']['id']: x['function_call']['arguments']
           for x in handler.completed}
    assert got == {'fc_A': '{"q":"paris"}', 'fc_B': '{"x":2}'}, got


def test_expected_answer_only_must_not_mark_contradiction_as_correct():
    status, passed, detail = check_factual_content(
        'The capital of France is London.',
        expected_answer='The capital of France is Paris.',
    )
    assert not passed, (status, detail)


def test_unsupported_schema_type_must_not_silently_pass():
    status, passed, detail = _validate_payload(
        {'expected_schema': {'n': 'integer'}}, {'n': True}
    )
    assert not passed, (status, detail)


def test_nonfinite_float_is_not_valid_json_number():
    status, passed, detail = _validate_payload(
        {'expected_schema': {'n': 'float'}}, {'n': float('nan')}
    )
    assert not passed, (status, detail)
