"""R1-A real validation paths (R2-05).

Two real paths, both offline-safe:

1. Recorded-event replay: the #41708/#41710 event sequences in
   data/fixtures.json are fed through the REAL StreamingHandler (not the
   simulated transport) and the handler's behaviour is asserted —
   exactly one completed chunk with the recorded arguments for the
   correct handler, none for the buggy one, none without a done event.
2. Real tokenizer: tiktoken's actual BPE counts for OpenAI models.
   These tests SKIP (never fail, never fake a count) when tiktoken is
   missing or its encoding tables cannot be fetched (first run needs
   network to OpenAI's public blob store; afterwards the tables are
   cached and the tests run offline).

Measured real counts (tiktoken 0.14.0, 2026-11-06) on the #340 fixture
texts: Chinese cl100k 51 / o200k 34 (+50%), Japanese 54 / 43 (+25.6%),
English 19 / 19, code 13 / 13.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validator import StreamingHandler, check_factual_content, load_scenarios, run_scenario

HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "data" / "fixtures.json"

CHINESE = "调用大模型接口时，如果令牌计数错误，提示词会被错误地截断，导致智能体在执行多步骤任务时中途失败。"
ENGLISH = "The agent calls the model, counts the tokens, and checks the response carefully before it acts."
JAPANESE = "APIを呼び出すとき、トークン数が間違っていると、プロンプトが切り捨てられ、エージェントは途中で失敗します。"
CODE = "def count_tokens(text, model):\n    return len(text.split())"


def _streaming_scenario(name):
    return next(s for s in load_scenarios(FIXTURES) if s["name"] == name)


def _replay(events, emit_on_done):
    """Feed recorded events through the real handler; return (handler, completed)."""
    handler = StreamingHandler(emit_on_done=emit_on_done)
    for ev in events:
        handler.handle(ev)
    return handler, handler.completed


# --- 1. Recorded-event replay through the real StreamingHandler -----------

def test_replay_recorded_41708_events_correct_handler_emits_one_completed():
    scenario = _streaming_scenario("streaming-completed-41708")
    handler, completed = _replay(scenario["events"], emit_on_done=True)
    assert len(completed) == 1
    # The recorded deltas concatenate to the exact arguments from #41708.
    assert completed[0]["function_call"]["arguments"] == '{"q": "paris"}'
    assert completed[0]["function_call"]["item"]["call_id"] == "call_1"
    assert handler.done_keys == ["call_1"]


def test_replay_recorded_41708_events_buggy_handler_emits_none():
    scenario = _streaming_scenario("streaming-completed-41708-buggy")
    handler, completed = _replay(scenario["events"], emit_on_done=False)
    assert completed == []
    # The done event DID arrive — the bug is that nothing was emitted for it.
    assert handler.done_keys == ["call_1"]


def test_replay_recorded_41710_events_no_done_emits_none():
    scenario = _streaming_scenario("streaming-no-done")
    handler, completed = _replay(scenario["events"], emit_on_done=True)
    assert completed == []
    assert handler.done_keys == []


def test_replay_matches_run_scenario_path():
    """The scenario runner's streaming path and the direct replay agree."""
    for name, expected_emitted in (
        ("streaming-completed-41708", 1),
        ("streaming-completed-41708-buggy", 0),
        ("streaming-no-done", 0),
    ):
        scenario = _streaming_scenario(name)
        (result,) = run_scenario(scenario)
        handler, completed = _replay(scenario["events"], scenario["emit_on_done"])
        assert len(completed) == expected_emitted
        assert result.passed == (expected_emitted == len(handler.done_keys))


# --- 2. Factual content check (judged by content, never by a flag) --------

def test_factual_content_false_statement_detected():
    outcome, passed, detail = check_factual_content(
        "The capital of France is Berlin.",
        expected_answer="The capital of France is Paris.",
        expected_keywords=["paris"], forbidden_claims=["berlin"],
    )
    assert outcome == "wrong-result" and not passed
    assert "berlin" in detail.lower() or "paris" in detail.lower()


def test_factual_content_true_statement_passes():
    outcome, passed, _ = check_factual_content(
        "The capital of France is Paris.",
        expected_answer="The capital of France is Paris.",
        expected_keywords=["paris"], forbidden_claims=["berlin"],
    )
    assert outcome == "ok" and passed


def test_factual_content_matching_is_case_and_punctuation_insensitive():
    outcome, passed, _ = check_factual_content(
        "PARIS is the capital of France!",
        expected_answer="The capital of France is Paris.",
        expected_keywords=["paris"], forbidden_claims=["berlin"],
    )
    assert passed


def test_factual_content_without_expected_answer_is_not_checked():
    # No ground truth supplied: the validator must NOT claim a detection.
    # R4-02: a not-checked result is not a verified pass (passed=False).
    outcome, passed, detail = check_factual_content("The capital of France is Berlin.")
    assert outcome == "not-checked" and not passed
    assert "not checked" in detail


def test_false_response_fixture_is_caught_by_content_not_flag():
    # The transport no longer carries a factual=False flag (R2-05); the
    # fixture's expected answer is what convicts the response.
    (result,) = run_scenario(next(
        s for s in load_scenarios(FIXTURES) if s["name"] == "false-response-openrouter"))
    assert result.outcome == "wrong-result" and not result.passed
    assert "paris" in result.detail.lower()
    assert "factual" not in result.detail.lower()


def test_true_response_fixture_passes_content_check():
    (result,) = run_scenario(next(
        s for s in load_scenarios(FIXTURES) if s["name"] == "true-response-openrouter"))
    assert result.outcome == "ok" and result.passed


# --- 3. Real tokenizer (tiktoken) ------------------------------------------
# NOTE: no module-level importorskip here — the replay and factual tests
# above are pure Python and must run in every venv. Only the tokenizer
# tests below skip when tiktoken (or its encoding tables) is unavailable.

from real_tokenizer import (
    REAL_ENCODINGS,
    count_tokens_encoding,
    count_tokens_real,
    validate_token_count_real,
)


def _real_encodings_or_skip():
    """Skip (do not fake) if tiktoken or its encoding tables are unavailable."""
    pytest.importorskip("tiktoken", reason="tiktoken not installed")
    try:
        from real_tokenizer import _encoding

        _encoding("cl100k_base")
        _encoding("o200k_base")
    except Exception as exc:  # network down on first run, cache missing, etc.
        pytest.skip(f"tiktoken encoding tables unavailable: {exc}")


def test_real_token_counts_match_measured_values():
    _real_encodings_or_skip()
    assert count_tokens_real(CHINESE, "gpt-4") == 51
    assert count_tokens_real(CHINESE, "gpt-4o") == 34
    assert count_tokens_real(JAPANESE, "gpt-4") == 54
    assert count_tokens_real(JAPANESE, "gpt-4o") == 43
    assert count_tokens_real(ENGLISH, "gpt-4") == 19
    assert count_tokens_real(CODE, "gpt-4") == 13


def test_real_substitution_detected_gpt4o_vs_cl100k_chinese():
    _real_encodings_or_skip()
    reported = count_tokens_real(CHINESE, "gpt-4")  # the substituted tokenizer
    check = validate_token_count_real(CHINESE, "gpt-4o", reported)
    assert check["outcome"] == "default-substituted" and not check["passed"]
    assert check["true_count"] == 34 and check["substituted_count"] == 51


def test_real_substitution_detected_gpt4o_vs_cl100k_japanese():
    _real_encodings_or_skip()
    reported = count_tokens_real(JAPANESE, "gpt-4")
    check = validate_token_count_real(JAPANESE, "gpt-4o", reported)
    assert check["outcome"] == "default-substituted" and not check["passed"]


def test_real_correct_count_passes_gpt4o_and_gpt4():
    _real_encodings_or_skip()
    assert validate_token_count_real(CHINESE, "gpt-4o", 34)["passed"]
    assert validate_token_count_real(CHINESE, "gpt-4", 51)["passed"]
    assert validate_token_count_real(ENGLISH, "gpt-4o", 19)["passed"]


def test_real_substitution_indistinguishable_on_english_and_code():
    # Honest limit: cl100k and o200k give identical counts for these
    # texts, so a GPT-4 count reported for gpt-4o is NOT detectable here.
    _real_encodings_or_skip()
    assert count_tokens_real(ENGLISH, "gpt-4") == count_tokens_real(ENGLISH, "gpt-4o")
    assert count_tokens_real(CODE, "gpt-4") == count_tokens_real(CODE, "gpt-4o")
    check = validate_token_count_real(ENGLISH, "gpt-4o", 19)
    assert check["outcome"] == "ok"  # cannot be told apart — recorded, not hidden


def test_real_tokenizer_unknown_model_raises_instead_of_approximating():
    _real_encodings_or_skip()
    assert count_tokens_real(CHINESE, "litellm/qwen3-coder-30b") is None
    with pytest.raises(ValueError, match="no real tokenizer"):
        validate_token_count_real(CHINESE, "litellm/qwen3-coder-30b", 48)
    # The #340 Qwen substitution stays approximation-only (validator.py),
    # NOT_REAL_WORLD_VALIDATED — see reports/rework2/r2_05.md.


def test_real_tokenizer_model_map_covers_known_openai_models():
    _real_encodings_or_skip()
    for model in ("gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"):
        assert model in REAL_ENCODINGS
    assert count_tokens_encoding(CHINESE, "p50k_base") == 111
