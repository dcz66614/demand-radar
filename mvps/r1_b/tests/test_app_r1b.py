"""UI smoke test for the R1-B app — drives the real flow with AppTest:
load cases, run validation, check the result view, apply filters.
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
    """Click Run and wait for the result table to settle (same AppTest
    harness timing note as r1_a: bounded settle, at most 2 extra run()
    calls in the same test run; still fails if no dataframe appears).
    R2-02: explicit `timeout=30` on every run() — AppTest's default
    3 s `require_widgets_deltas` timeout fired once in the numpy 2.3.5
    venv (2026-11-06) when the ScriptRunner was slow to emit completion.
    Fixed, deterministic upper bound; the test still fails on a real
    hang instead of being retried."""
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
    assert len(at.dataframe[0].value) == 15


def test_outcome_filter_narrows_results():
    at = _run_app()
    at.selectbox[1].set_value("fail").run(timeout=30)  # Outcome filter
    at.button[0].click().run(timeout=30)
    assert not at.exception
    df = at.dataframe[0].value
    assert len(df) == 7  # 7 of 15 checks are detected failures
    assert not df["passed"].any()


def test_check_filter_narrows_to_dfa():
    at = _run_app()
    at.selectbox[0].set_value("dfa").run(timeout=30)  # Check filter
    at.button[0].click().run(timeout=30)
    assert not at.exception
    df = at.dataframe[0].value
    assert len(df) == 3
    assert set(df["check"]) == {"dfa"}
