"""Generate mvps/r1_a/data/fixtures.json (deterministic, offline).

Reference token counts are computed with validator.py's own counters and
stored in the file, so the fixtures are self-consistent: the validator's job
is to DETECT the GPT-4 substitution, not to re-derive the counts.
Passages are realistic texts written for this fixture; the measured error
rates they produce approximate the #340 measurements (Chinese +108.3%,
English +11.7%, Japanese +18.5%, code 0%) and are recorded in the file.
Run: python mvps/r1_a/make_fixtures.py
"""

import json
from pathlib import Path

from validator import count_tokens_for_model, count_tokens_gpt4, overcount_pct

HERE = Path(__file__).resolve().parent
MODEL = "litellm/qwen3-coder-30b"

CHINESE = "调用大模型接口时，如果令牌计数错误，提示词会被错误地截断，导致智能体在执行多步骤任务时中途失败。"
ENGLISH = "The agent calls the model, counts the tokens, and checks the response carefully before it acts."
JAPANESE = "APIを呼び出すとき、トークン数が間違っていると、プロンプトが切り捨てられ、エージェントは途中で失敗します。"
CODE = "def count_tokens(text, model):\n    return len(text.split())"

STREAM_EVENTS = [
    {"type": "response.output_item.added",
     "item": {"type": "function_call", "name": "search", "call_id": "call_1"}},
    {"type": "response.function_call_arguments.delta", "delta": "{\"q\": "},
    {"type": "response.function_call_arguments.delta", "delta": "\"paris\"}"},
    {"type": "response.output_item.done",
     "item": {"type": "function_call", "name": "search", "call_id": "call_1"}},
]


def token_cases():
    cases = []
    for name, text in [
        ("chinese", CHINESE), ("english", ENGLISH),
        ("japanese", JAPANESE), ("code", CODE),
    ]:
        cases.append({
            "case": f"{name}-buggy", "text": text, "model": MODEL, "sut": "buggy",
            "true_count": count_tokens_for_model(text, MODEL),
            "gpt4_count": count_tokens_gpt4(text),
            "overcount_pct": round(overcount_pct(text), 3),
        })
        cases.append({
            "case": f"{name}-correct", "text": text, "model": MODEL, "sut": "correct",
            "true_count": count_tokens_for_model(text, MODEL),
            "gpt4_count": count_tokens_gpt4(text),
            "overcount_pct": round(overcount_pct(text), 3),
        })
    return cases


def build() -> list:
    return [
        {
            "name": "tokenizer-substitution-340", "kind": "token_count",
            "source_url": "https://github.com/ServiceNow/AgentLab/issues/340",
            "note": "AgentLab #340: count_tokens substitutes GPT-4 tokenizer; "
                    "measured +108.3% Chinese / +11.7% English / +18.5% Japanese / 0% code. "
                    "Fixture overcounts are approximations (see overcount_pct).",
            "cases": token_cases(),
        },
        {
            "name": "streaming-completed-41708", "kind": "streaming",
            "source_url": "https://github.com/langchain-ai/langchain/issues/41708",
            "case": "correct-handler", "emit_on_done": True, "events": STREAM_EVENTS,
        },
        {
            "name": "streaming-completed-41708-buggy", "kind": "streaming",
            "source_url": "https://github.com/langchain-ai/langchain/issues/41708",
            "case": "buggy-handler-41708", "emit_on_done": False, "events": STREAM_EVENTS,
        },
        {
            "name": "streaming-no-done", "kind": "streaming",
            "source_url": "https://github.com/langchain-ai/langchain/issues/41710",
            "case": "truncated-stream", "emit_on_done": True,
            "events": STREAM_EVENTS[:3],
        },
        {
            "name": "retry-429-then-success", "kind": "api_call",
            "source_url": "https://github.com/ServiceNow/AgentLab/issues/182",
            "steps": [{"call": "chat", "model": MODEL, "fault": ["http429", None],
                       "expected_schema": {"content": "str"}, "response_content": "ok"}],
        },
        {
            "name": "retry-429-exhausted", "kind": "api_call",
            "source_url": "https://github.com/ServiceNow/AgentLab/issues/182",
            "steps": [{"call": "chat", "model": MODEL, "fault": "http429",
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "timeout-exhausted", "kind": "api_call",
            "source_url": "https://github.com/ServiceNow/AgentLab/issues/182",
            "steps": [{"call": "chat", "model": MODEL, "fault": "timeout",
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "server-error-500", "kind": "api_call",
            "source_url": "https://news.ycombinator.com/item?id=50382039",
            "steps": [{"call": "chat", "model": MODEL, "fault": "http500",
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "malformed-response", "kind": "api_call",
            "source_url": "https://news.ycombinator.com/item?id=50382039",
            "steps": [{"call": "chat", "model": MODEL, "fault": "malformed_json",
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "schema-violation", "kind": "api_call",
            "source_url": "https://github.com/langchain-ai/langchain/issues/41708",
            "steps": [{"call": "chat", "model": MODEL, "wrong_schema": True,
                       "expected_schema": {"content": "str", "citations": "list"}}],
        },
        {
            "name": "token-budget", "kind": "api_call",
            "source_url": "https://github.com/ServiceNow/AgentLab/issues/340",
            "steps": [{"call": "chat", "model": MODEL, "prompt_tokens": 9000,
                       "max_tokens": 2000, "token_budget": 10000,
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "silent-trim", "kind": "api_call",
            "source_url": "https://github.com/ServiceNow/AgentLab/issues/340",
            "steps": [{"call": "chat", "model": MODEL, "silent_trim": True,
                       "prompt_tokens": 9000, "max_tokens": 500,
                       "token_budget": 10000,
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "false-response-openrouter", "kind": "api_call",
            "source_url": "https://news.ycombinator.com/item?id=50382039",
            "steps": [{"call": "chat", "model": "openrouter/model",
                       "fault": "false_response", "latency_ms": 45000,
                       # R2-05: the ground truth lives HERE, in the fixture —
                       # the validator judges the response content against it,
                       # never a factual=False flag in the payload.
                       "expected_answer": "The capital of France is Paris.",
                       "expected_keywords": ["paris"],
                       "forbidden_claims": ["berlin"],
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "true-response-openrouter", "kind": "api_call",
            "source_url": "https://news.ycombinator.com/item?id=50382039",
            "steps": [{"call": "chat", "model": "openrouter/model",
                       "response_content": "The capital of France is Paris.",
                       "latency_ms": 1200,
                       "expected_answer": "The capital of France is Paris.",
                       "expected_keywords": ["paris"],
                       "forbidden_claims": ["berlin"],
                       "expected_schema": {"content": "str"}}],
        },
        {
            "name": "hidden-default-substitution", "kind": "api_call",
            "source_url": "https://github.com/ServiceNow/AgentLab/issues/340",
            "steps": [{"call": "count_tokens", "model": MODEL,
                       "prompt_text": CHINESE, "prompt_tokens": 30,
                       "substitute_model": True, "gpt4_tokens": count_tokens_gpt4(CHINESE),
                       "expected_schema": {"content": "str", "usage": "dict"}}],
        },
    ]


if __name__ == "__main__":
    scenarios = build()
    out = HERE / "data" / "fixtures.json"
    out.write_text(json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(scenarios)} scenarios)")
    for case in scenarios[0]["cases"]:
        print(f"  {case['case']}: true={case['true_count']} gpt4={case['gpt4_count']} "
              f"overcount={case['overcount_pct']:.1%}")
