import csv
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from signalcheck import (
    buggy_effective_cutoffs,
    check_rsa,
    check_rsp_phase,
    dfa_exponent,
    export_csv,
    load_cases,
    make_dfa_signal,
    rsa_from_period,
    rsp_process_buggy,
    rsp_process_guarded,
    run_all,
    run_case,
    signal_power,
)

HERE = Path(__file__).resolve().parents[1]
CASES = HERE / "data" / "cases.json"


def _case(name):
    return next(c for c in load_cases(CASES) if c["case"] == name)


def _results(name):
    return run_case(_case(name))


# --- #1212 EMG filter ------------------------------------------------------

def test_emg_correct_4khz_passes():
    (r,) = _results("emg-4khz-correct")
    assert r.passed


def test_emg_buggy_4khz_is_fourfold_off():
    low, high = buggy_effective_cutoffs(4000.0)
    assert (low, high) == (40.0, 2000.0)
    (r,) = _results("emg-4khz-buggy-1khz-assumption")
    assert not r.passed and "4.0x" in r.detail


def test_emg_1khz_control_passes():
    (r,) = _results("emg-1khz-control")
    assert r.passed


# --- #1230 RSA -------------------------------------------------------------

def test_rsa_on_heart_period_passes_and_matches_independent_recompute():
    # REWORK2: the old assertion `rsa_from_period(period) >= 0` encoded the
    # false premise "RSA must be non-negative" (review P0-01). RSA is
    # ln(variance); it is negative whenever variance < 1 ms^2. The correct
    # assertion is agreement with an independently written recomputation.
    period = _case("rsa-heart-period")["period_ms"]
    assert rsa_from_period(period) == pytest.approx(
        _independent_rsa(period), rel=0, abs=1e-9)
    (r,) = _results("rsa-heart-period")
    assert r.passed


def test_rsa_on_heart_rate_fails_with_wrong_domain():
    (r,) = _results("rsa-heart-rate-input")
    assert not r.passed and "heart rate" in r.detail


def test_rsa_wrong_negative_value_fails_by_mismatch_not_by_sign():
    # REWORK2: this fixture reports -1.2 against an expected +6.19, so it
    # must fail — but because the VALUE mismatches by 7.39 ln(ms^2), not
    # because it is negative. A correct negative RSA passes (see the
    # parametrised cases below and the adversarial tests).
    (r,) = _results("rsa-negative-value")
    assert not r.passed and "differs" in r.detail and "7.3932" in r.detail


# --- #1208 DFA -------------------------------------------------------------

def test_dfa_exponent_is_unit_invariant_within_1e6():
    sig = make_dfa_signal()
    assert abs(dfa_exponent(sig) - dfa_exponent([x * 1000 for x in sig])) <= 1e-6


def test_dfa_small_amplitude_does_not_raise_and_is_invariant():
    sig = make_dfa_signal()
    tiny = [x * 1e-9 for x in sig]
    exp = dfa_exponent(tiny)  # must not raise
    assert abs(exp - dfa_exponent(sig)) <= 1e-6


def test_dfa_reported_exponents_differing_by_unit_fail():
    (r,) = _results("dfa-reported-differs-by-unit")
    assert not r.passed and "differ" in r.detail


def test_dfa_correct_reported_passes():
    (r,) = _results("dfa-correct")
    assert r.passed


# --- #1196 RSP phase -------------------------------------------------------

def test_rsp_phase_correct_passes():
    (r,) = _results("rsp-phase-correct")
    assert r.passed


def test_rsp_phase_seconds_as_samples_fails_too_small():
    (r,) = _results("rsp-phase-seconds-as-samples")
    assert not r.passed and "too small" in r.detail


# --- #1242 short RSP -------------------------------------------------------

def test_rsp_short_guarded_completes_with_two_cycles():
    from make_fixtures import rsp_short_signal

    out = rsp_process_guarded(rsp_short_signal(), 100.0)
    assert out["status"] == "ok" and out["cycles"] == 2


def test_rsp_short_buggy_raises_index_error():
    from make_fixtures import rsp_short_signal

    with pytest.raises(IndexError):
        rsp_process_buggy(rsp_short_signal(), 100.0)


def test_rsp_short_case_reports_both_rows():
    rows = _results("rsp-8s-recording")
    assert len(rows) == 2
    assert rows[0].passed and not rows[1].passed
    assert "IndexError" in rows[1].measured


# --- #1183 signal power ----------------------------------------------------

def test_signal_power_matches_analytic_value():
    from make_fixtures import power_signal

    assert abs(signal_power(power_signal(), 100.0) - 2.0) <= 0.01  # A=2 sine -> A^2/2


def test_signal_power_wrong_reported_fails():
    (r,) = _results("power-wrong-value")
    assert not r.passed


def test_signal_power_does_not_use_removed_trapz():
    # R2-02 (brief §R2-02, review §3): the old assertion
    # `assert not hasattr(np, "trapz")` treated a NumPy version's
    # implementation state as a software requirement — it fails on
    # NumPy 2.3.5 where np.trapz still exists, even though the
    # production code is already correct. A library version's attribute
    # list is not a requirement of this project, so the assertion itself
    # was the defect and is deleted here. What the project actually
    # requires — and what this test now asserts — is:
    #   (a) production code CALLS numpy.trapezoid;
    #   (b) production code never CALLS the old np.trapz API
    #       (mentions of "np.trapz" in comments/docstrings are fine);
    #   (c) the computed value is correct (A=2 sine -> 2.0000).
    from make_fixtures import power_signal

    src = (HERE / "signalcheck.py").read_text(encoding="utf-8")
    assert "np.trapezoid(" in src
    assert "np.trapz(" not in src
    assert abs(signal_power(power_signal(), 100.0) - 2.0) <= 0.01


# --- fixtures, loading, export ---------------------------------------------

def test_all_fixture_cases_run_and_every_row_has_source():
    results = run_all(load_cases(CASES))
    assert len(results) == 15
    assert all(r.source_url.startswith("https://github.com/neuropsychology/NeuroKit/issues/")
               for r in results)
    assert len({r.case for r in results}) == 14  # rsp-8s-recording yields 2 rows


def test_load_invalid_json_raises_value_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(bad)


def test_load_unknown_check_raises_value_error():
    with pytest.raises(ValueError):
        run_case({"check": "telepathy", "source_url": "https://example.com/x"})


def test_export_csv_preserves_source_url(tmp_path):
    results = run_all(load_cases(CASES))
    out = tmp_path / "export.csv"
    export_csv(results, out)
    with open(out, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(results)
    assert all(r["source_url"].startswith("https://") for r in rows)
    assert any(r["case"] == "emg-4khz-buggy-1khz-assumption" for r in rows)


# --- REWORK2 R2-01: RSA tolerance (review P0-01) ---------------------------
# 14 cases: positive / negative / near-zero / non-finite / missing / short.

def _independent_rsa(period_ms: list[float], fs: float = 4.0) -> float:
    """Second implementation of the RSA definition, written independently
    for cross-checking: ln(variance of the series after removing a 2.5 s
    centred moving average). No code shared with rsa_from_period."""
    w = max(3, int(fs * 2.5))
    half = w // 2
    detrended = []
    for i, x in enumerate(period_ms):
        lo, hi = max(0, i - half), min(len(period_ms), i + half + 1)
        detrended.append(x - sum(period_ms[lo:hi]) / (hi - lo))
    var = sum(d * d for d in detrended) / len(detrended)
    return math.log(var)


def _sine_periods(amplitude: float, n: int = 64, base: float = 1000.0) -> list[float]:
    return [base + amplitude * math.sin(2 * math.pi * i / 16) for i in range(n)]


_RSA_CASES = [
    # (label, periods, reported, expected_pass)
    ("positive-correct", _sine_periods(100.0), None, True),          # exp ~ +8.5
    ("positive-small-error", _sine_periods(100.0), "exp+0.01", True),
    ("positive-large-error", _sine_periods(100.0), "exp+0.5", False),
    ("negative-correct", _sine_periods(0.1), None, True),            # exp ~ -6.32
    ("negative-small-error", _sine_periods(0.1), "exp+0.01", True),
    ("negative-million", _sine_periods(0.1), 1_000_000.0, False),
    ("near-zero-correct", _sine_periods(1.414), None, True),         # exp ~ 0
    ("near-zero-small-error", _sine_periods(1.414), "exp+0.04", True),
    ("near-zero-large-error", _sine_periods(1.414), "exp+1.0", False),
    ("nan-reported", _sine_periods(100.0), float("nan"), False),
    ("inf-reported", _sine_periods(100.0), float("inf"), False),
    ("neg-inf-reported", _sine_periods(100.0), float("-inf"), False),
    ("short-series", [1000.0] * 5, 0.0, False),
    ("empty-series", [], 0.0, False),
    ("nan-in-series", [1000.0] * 32 + [float("nan")] + [1000.0] * 31, 0.0, False),
]


@pytest.mark.parametrize("label,periods,reported,expected_pass", _RSA_CASES)
def test_rsa_tolerance_cases(label, periods, reported, expected_pass):
    if reported is None:
        reported = _independent_rsa(periods)
    elif isinstance(reported, str) and reported.startswith("exp+"):
        reported = _independent_rsa(periods) + float(reported[4:])
    result = check_rsa(periods, reported)
    assert result.passed is expected_pass, f"{label}: {result.detail}"


def test_rsa_agrees_with_independent_implementation():
    for amp in (0.1, 1.414, 10.0, 100.0, 500.0):
        periods = _sine_periods(amp)
        assert rsa_from_period(periods) == pytest.approx(
            _independent_rsa(periods), rel=0, abs=1e-9)


def test_rsa_wrong_domain_negative_still_fails():
    # Heart-rate input (#1230): the value is negative AND wrong-domain.
    (r,) = _results("rsa-heart-rate-input")
    assert not r.passed


# --- REWORK2 R2-01: RSP phase validation (review P1-04) --------------------

def test_rsp_phase_extra_duration_rejected():
    r = check_rsp_phase([(0, 100), (100, 200)], 100, [1, 1, 999], "samples")
    assert not r.passed and "match" in r.detail


def test_rsp_phase_missing_duration_rejected():
    assert not check_rsp_phase([(0, 100), (100, 200)], 100, [1], "samples").passed


@pytest.mark.parametrize("fs", [0, -100, float("nan"), float("inf")])
def test_rsp_phase_bad_fs_rejected(fs):
    assert not check_rsp_phase([(0, 100)], fs, [1], "samples").passed


@pytest.mark.parametrize("intervals", [[(100, 100)], [(200, 100)], [(-5, 100)], [(0, float("nan"))], []])
def test_rsp_phase_bad_intervals_rejected(intervals):
    assert not check_rsp_phase(intervals, 100, [1] * max(len(intervals), 1), "samples").passed


def test_rsp_phase_nonfinite_reported_rejected():
    assert not check_rsp_phase([(0, 100)], 100, [float("nan")], "samples").passed
    assert not check_rsp_phase([(0, 100)], 100, [-1], "samples").passed


def test_rsp_phase_unknown_unit_rejected_not_raised():
    r = check_rsp_phase([(0, 100)], 100, [1], "minutes")
    assert not r.passed and "unknown" in r.detail


def test_rsp_phase_seconds_unit_correct_passes():
    assert check_rsp_phase([(0, 1), (1, 3)], 100, [1, 2], "seconds").passed


def test_rsa_randomised_counterexamples():
    """Seeded random counterexamples: correct values always pass, grossly
    wrong values always fail, whatever the sign of the true RSA."""
    rng = __import__("random").Random(20261105)
    for trial in range(200):
        amp = 10 ** rng.uniform(-1.5, 2.5)
        n = rng.choice([32, 64, 128])
        periods = [1000 + amp * math.sin(2 * math.pi * i / rng.choice([8, 16, 32]))
                   + rng.gauss(0, amp * 0.1) for i in range(n)]
        expected = _independent_rsa(periods)
        assert check_rsa(periods, expected).passed is True, f"trial {trial}"
        assert check_rsa(periods, expected + 10.0).passed is False, f"trial {trial}"
        assert check_rsa(periods, rng.choice([1e6, -1e6, 0.0])).passed is False, f"trial {trial}"
