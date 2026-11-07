"""R1-B Streamlit app — signal-data validator (PRD 4bb734fac7245033d327).

Run: python -m streamlit run mvps/r1_b/app.py
Loads data/cases.json (or an uploaded case JSON), runs every check on the
offline fixture signals, and shows pass/fail per check with measured vs
expected values and the source issue URL. No network calls.
"""

import io
import json
from pathlib import Path

import streamlit as st
from signalcheck import load_cases, run_all

HERE = Path(__file__).resolve().parent
DEFAULT_CASES = HERE / "data" / "cases.json"


def _load_default():
    return load_cases(DEFAULT_CASES)


st.set_page_config(page_title="Signal Validator — R1-B", layout="wide")
st.title("Physiological Signal Validator (R1-B)")
st.warning(
    "Positioning: **PARTIALLY_REAL_WORLD_VALIDATED** (R2-05). The failure "
    "classes are also checked against REAL upstream outputs (neurokit2 "
    "0.3.0 / wfdb 4.3.1): real rsp_process still raises IndexError on an "
    "8 s recording (#1242, still live upstream); real fractal_dfa is "
    "unit-invariant; real signal_power agrees with the local trapezoid; "
    "a real MIT-BIH record excerpt is read with real wfdb. The "
    "fixture-based checks remain synthetic signals. This validator does "
    "not fix NeuroKit and must not be used to offset PRDs eliminated by "
    "re-scoring. See README.md for the full scope."
)
st.markdown(
    "Signal-data validator for PRD 4bb7 (BIO signal processing). It parses "
    "offline fixture signals and checks the numbers: EMG filter frequencies "
    "against the real sampling rate (#1212), RSA on heart period not heart "
    "rate (#1230), DFA unit-invariance (#1208), RSP phase durations in "
    "seconds (#1196), short-recording handling (#1242), and signal power "
    "without np.trapz (#1183). Fixtures are synthetic signals built from the "
    "parameters in the cited issues, not the original recordings."
)

uploaded = st.file_uploader("Upload a case JSON (optional)", type=["json"])
cases = None
if uploaded is not None:
    try:
        data = json.loads(uploaded.getvalue().decode("utf-8"))
        if not isinstance(data, list) or not data:
            raise ValueError("case file must be a non-empty JSON list")
        for item in data:
            if not isinstance(item, dict) or not item.get("check"):
                raise ValueError("each case needs at least a check field")
        cases = data
        st.success(f"Loaded {len(cases)} uploaded case(s)")
    except (ValueError, UnicodeDecodeError) as exc:
        st.error(f"Invalid case file: {exc}")
        st.stop()
if cases is None:
    cases = _load_default()

check_filter = st.selectbox(
    "Check", ["all"] + sorted({c["check"] for c in cases})
)
outcome_filter = st.selectbox("Outcome", ["all", "pass", "fail"])

if st.button("Run validation"):
    results = run_all(
        [c for c in cases if check_filter == "all" or c["check"] == check_filter]
    )
    shown = [
        r for r in results
        if outcome_filter == "all"
        or (outcome_filter == "pass" and r.passed)
        or (outcome_filter == "fail" and not r.passed)
    ]
    passed = sum(r.passed for r in results)
    st.markdown(f"**{passed} passed, {len(results) - passed} failed** of {len(results)} checks")
    st.markdown(f"Showing {len(shown)} of {len(results)} checks")
    rows = [
        {
            "case": r.case,
            "check": r.check,
            "passed": r.passed,
            "measured": r.measured,
            "expected": r.expected,
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
        fieldnames=["case", "check", "passed", "measured", "expected",
                    "source_url", "detail"],
    )
    writer.writeheader()
    for r in results:
        writer.writerow({
            "case": r.case, "check": r.check, "passed": r.passed,
            "measured": r.measured, "expected": r.expected,
            "source_url": r.source_url, "detail": r.detail,
        })
    st.download_button(
        "Download CSV (with source_url)", out.getvalue(),
        file_name="r1_b_validation.csv", mime="text/csv",
    )
