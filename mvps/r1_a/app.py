"""R1-A Streamlit app — fault-injection validator (PRD 6513d0).

Run: python -m streamlit run mvps/r1_a/app.py
Loads data/fixtures.json (or an uploaded scenario JSON), runs every scenario
through the simulated transport, and shows pass/fail per step with outcome,
attempts and simulated elapsed time. No network calls.
"""

import io
from pathlib import Path

import streamlit as st
from validator import _parse_strict_json, load_scenarios, run_all

HERE = Path(__file__).resolve().parent
DEFAULT_FIXTURES = HERE / "data" / "fixtures.json"


def _load_default():
    return load_scenarios(DEFAULT_FIXTURES)


st.set_page_config(page_title="API Reliability Validator — R1-A", layout="wide")
st.title("API Reliability Validator (R1-A)")
st.warning(
    "Positioning: **PARTIALLY_REAL_WORLD_VALIDATED** (R2-05, R3-01–R3-03). "
    "Three separate capabilities — do not conflate them: (1) stream event "
    "count — completed chunks emitted vs done events received; "
    "(2) function argument integrity — per-call dual-key correlation, "
    "ordered accumulation, and cross-validation against the done item's "
    "final arguments; (3) factual truth — content comparison against a "
    "known-good answer as a normalized word-multiset match (a keyword "
    "rule alone is NOT factual verification, and word order is ignored). "
    "Streaming is replayed from the recorded #41708/#41710 event "
    "sequences through the real handler; a stream with no terminal "
    "event is reported 'open' and counted as **pending**: its chunks "
    "may be coherent, but the request's success is not yet proven — "
    "a pending result is not a completed success and never counts "
    "toward the pass total. A response that ends with response.failed, "
    "response.incomplete or an error event is a failure and never "
    "counts as passed, even when every call completed first. "
    "Tokenizer substitution is "
    "validated with REAL tiktoken counts for OpenAI models only. The #340 "
    "Qwen substitution claim is still approximation-only "
    "(NOT_REAL_WORLD_VALIDATED), and no real API is ever called. This "
    "validator does not fix AgentLab or LangChain and must not be used to "
    "offset PRDs eliminated by re-scoring. See README.md for the full scope."
)
st.markdown(
    "Controlled fault-injection validator for PRD 6513d0 (AI agent / API "
    "reliability). Faults are injected locally into recorded traces — "
    "timeouts, 429/500, malformed responses, hidden model-default "
    "substitution, token-budget errors. Nothing here calls a real API."
)

uploaded = st.file_uploader("Upload a scenario JSON (optional)", type=["json"])
scenarios = None
if uploaded is not None:
    try:
        # Strict JSON: an uploaded file with NaN/Infinity constants or
        # non-finite numbers is not a valid scenario file (R4-01).
        data = _parse_strict_json(uploaded.getvalue().decode("utf-8"))
        if not isinstance(data, list) or not data:
            raise ValueError("scenario file must be a non-empty JSON list")
        for item in data:
            if not isinstance(item, dict) or not item.get("name") or not item.get("kind"):
                raise ValueError("each scenario needs at least name and kind")
        scenarios = data
        st.success(f"Loaded {len(scenarios)} uploaded scenario(s)")
    except (ValueError, UnicodeDecodeError) as exc:
        st.error(f"Invalid scenario file: {exc}")
        st.stop()
if scenarios is None:
    scenarios = _load_default()

kind_filter = st.selectbox("Scenario kind", ["all"] + sorted({s["kind"] for s in scenarios}))
outcome_filter = st.selectbox("Outcome", ["all", "pass", "fail", "not-checked", "pending"])

if st.button("Run validation"):
    results = run_all([s for s in scenarios if kind_filter == "all" or s["kind"] == kind_filter])
    # Four separate counts (P2-A, sixth-round audit): "passed" counts
    # only requests that completed successfully
    # (``request_completed_successfully``); a chunk-valid open stream is
    # "pending" (PENDING/INDETERMINATE) and never inflates the pass
    # rate. "failed" counts only real failures (outcome != not-checked).
    passed = sum(1 for r in results if r.request_completed_successfully)
    pending = sum(1 for r in results if r.request_status == "pending")
    not_checked = sum(1 for r in results if r.outcome == "not-checked")
    failed = len(results) - passed - pending - not_checked
    shown = [
        r
        for r in results
        if outcome_filter == "all"
        or (outcome_filter == "pass" and r.request_completed_successfully)
        or (outcome_filter == "fail" and not r.passed and r.outcome != "not-checked")
        or (outcome_filter == "not-checked" and r.outcome == "not-checked")
        or (outcome_filter == "pending" and r.request_status == "pending")
    ]
    st.markdown(
        f"**{passed} passed, {failed} failed, {not_checked} not checked, "
        f"{pending} pending** of {len(results)} checks"
    )
    st.markdown(f"Showing {len(shown)} of {len(results)} checks")
    rows = [
        {
            "scenario": r.scenario,
            "step": r.step,
            "outcome": r.outcome,
            "passed": r.passed,
            "termination": r.termination,
            "request_status": r.request_status,
            "attempts": r.attempts,
            "elapsed_ms": r.elapsed_ms,
            "source_url": r.source_url,
            "detail": r.detail,
        }
        for r in shown
    ]
    st.dataframe(rows, width="stretch")
    import csv as _csv

    out = io.StringIO()
    writer = _csv.DictWriter(
        out,
        fieldnames=[
            "scenario",
            "kind",
            "step",
            "outcome",
            "passed",
            "attempts",
            "elapsed_ms",
            "source_url",
            "detail",
            "termination",
            "request_completed_successfully",
            "request_status",
        ],
    )
    writer.writeheader()
    for r in results:
        writer.writerow(
            {
                "scenario": r.scenario,
                "kind": r.kind,
                "step": r.step,
                "outcome": r.outcome,
                "passed": r.passed,
                "attempts": r.attempts,
                "elapsed_ms": r.elapsed_ms,
                "source_url": r.source_url,
                "detail": r.detail,
                "termination": r.termination,
                "request_completed_successfully": r.request_completed_successfully,
                "request_status": r.request_status,
            }
        )
    st.download_button(
        "Download CSV (with source_url)",
        out.getvalue(),
        file_name="r1_a_validation.csv",
        mime="text/csv",
    )
