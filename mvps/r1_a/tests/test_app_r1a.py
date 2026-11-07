"""UI smoke test for the R1-A app — drives the real flow with AppTest:
load fixtures, run validation, check the result view, apply filters.
More than a bare HTTP 200.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def _run_app():
    at = AppTest.from_file(str(APP)).run(timeout=30)
    assert not at.exception, f"app raised: {at.exception}"
    return at


def _click_and_settle(at):
    """Click Run and wait for the result table to settle.

    AppTest is synchronous in isolation, but under full-suite load its
    widget rerun has been observed once not to have rendered the dataframe
    on the first run() (R06/R07: 2 occurrences in ~15 full runs, never
    reproduced in isolation, 10/10). This is a bounded settle — at most 2
    extra run() calls within the SAME test run — not a rerun-until-green:
    if no dataframe appears, the test still fails below.

    R2-02: a second, distinct failure mode was observed once
    (numpy 2.3.5 venv, 2026-11-06): `at.button[0].click().run(timeout=30)` raised
    from `require_widgets_deltas` — the ScriptRunner did not emit a
    completion event within AppTest's DEFAULT 3 s timeout. The fix is a
    deterministic wait condition, not a retry: every run() here passes
    an explicit `timeout=30`, a fixed upper bound; the test still fails
    if the script never completes inside it.
    """
    at.button[0].click().run(timeout=30)
    for _ in range(2):
        if at.dataframe:
            break
        at.run(timeout=30)
    return at


def test_app_runs_and_shows_results_after_click():
    at = _run_app()
    assert len(at.button) == 1
    _click_and_settle(at)
    assert not at.exception
    assert any("passed" in m.value for m in at.markdown)
    assert len(at.dataframe) == 1
    assert len(at.dataframe[0].value) == 22  # R2-05: +1 true-response control


def test_outcome_filter_narrows_results():
    at = _run_app()
    at.selectbox[1].set_value("fail").run(timeout=30)  # Outcome filter
    at.button[0].click().run(timeout=30)
    assert not at.exception
    df = at.dataframe[0].value
    assert len(df) == 13  # 13 of 22 checks are injected-fault detections
    assert not df["passed"].any()


def test_kind_filter_narrows_to_token_scenarios():
    at = _run_app()
    at.selectbox[0].set_value("token_count").run(timeout=30)  # Scenario kind filter
    at.button[0].click().run(timeout=30)
    assert not at.exception
    df = at.dataframe[0].value
    assert len(df) == 8
    assert set(df["scenario"]) == {"tokenizer-substitution-340"}


def test_banner_labels_open_stream_and_failure_terminals():
    """POST-R4 (P0-03): the banner must say an open stream is not a
    verified success, and a failure terminal never counts as passed.
    P2-A: the banner must also say an open stream is counted as pending."""
    at = _run_app()
    assert len(at.warning) == 1
    banner = at.warning[0].value
    assert "not yet proven" in banner
    assert "never" in banner and "counts as passed" in banner
    assert "response.failed" in banner
    assert "pending" in banner


def test_pending_filter_narrows_to_open_streams():
    """P2-A: the pending filter shows exactly the two open chunk-valid
    streaming checks — both still passed=True on chunk coherence, both
    request_status pending, both termination open."""
    at = _run_app()
    at.selectbox[1].set_value("pending").run(timeout=30)  # Outcome filter
    at.button[0].click().run(timeout=30)
    assert not at.exception
    df = at.dataframe[0].value
    assert len(df) == 2
    assert set(df["scenario"]) == {"streaming-completed-41708", "streaming-no-done"}
    assert df["passed"].all()
    assert set(df["request_status"]) == {"pending"}
    assert set(df["termination"]) == {"open"}


def test_summary_counts_after_p2a():
    """P2-A: the fixture sweep now reads 7 passed / 13 failed /
    0 not checked / 2 pending of 22 checks — the two open chunk-valid
    streaming checks (streaming-completed-41708, streaming-no-done)
    moved from passed to pending; no fixture changed and the failed
    count is unchanged."""
    at = _run_app()
    _click_and_settle(at)
    assert not at.exception
    assert any("7 passed, 13 failed, 0 not checked, 2 pending" in m.value for m in at.markdown)
