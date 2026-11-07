"""R1-B real upstream validation tests (R2-05).

Every test here calls the REAL upstream libraries (neurokit2 0.3.0 /
wfdb 4.3.1) via real_upstream.py. The whole module SKIPS (never fails,
never fakes) when neurokit2 is missing; the record test additionally
skips when wfdb is missing. In the main venv these tests skip; in the
.venv-real test venv they run against the real libraries.

Measured values recorded here were obtained 2026-11-06 with
neurokit2 0.3.0, wfdb 4.3.1, numpy 2.5.4, Python 3.12.3. The four FAIL
rows below are DETECTIONS (a real upstream failure reproduced and
flagged), not defects in this project — the same convention as the
fixture suite's 7 fail rows.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("neurokit2", reason="neurokit2 not installed")

import real_upstream
from signalcheck import rsp_process_guarded


def test_real_rsp_process_still_crashes_on_8s_recording():
    # #1242 reproduced against the CURRENT upstream release: the real
    # library raises IndexError on an 8 s recording (deterministic
    # across seeds 42/1/7/123). The check row records it as a failure
    # to be flagged, not as a pass.
    result = real_upstream.real_rsp_short_crash()
    assert not result.passed
    assert "IndexError" in result.measured
    assert "0.3.0" in result.detail


def test_guarded_path_handles_the_same_real_8s_signal():
    import neurokit2 as nk

    rsp = nk.rsp_simulate(duration=8, sampling_rate=100, respiratory_rate=15,
                          random_state=42)
    out = rsp_process_guarded([float(x) for x in rsp], 100.0)
    assert out["status"] == "ok" and abs(out["cycles"] - 2) <= 1


def test_real_rsp_phase_durations_from_upstream_peaks():
    correct, bad = real_upstream.real_rsp_phase_from_upstream()
    assert correct.passed  # durations from real peaks, samples / fs
    assert not bad.passed  # seconds-as-samples error still fails
    assert "99%" in bad.detail


def test_real_rsa_crosscheck_agrees_in_sign_and_magnitude():
    (cross, flagged) = real_upstream.real_rsa_crosscheck()
    assert cross.passed
    assert "Porges-Bohrer" in cross.measured
    # The rate-based error value must still be flagged by check_rsa.
    assert not flagged.passed


def test_real_dfa_is_unit_invariant():
    result = real_upstream.real_dfa_invariance()
    assert result.passed
    assert "1.332878" in result.measured  # real alpha on the probe signal
    assert "spread 1.55e-15" in result.measured


def test_real_emg_filter_is_fs_aware():
    result = real_upstream.real_emg_fs_awareness()
    assert result.passed
    assert "0.0004x" in result.measured  # 900 Hz attenuated at the true fs
    assert "0.99x" in result.measured  # ...but passes with the assumed 1 kHz


def test_real_signal_power_agrees_with_local_trapezoid():
    result = real_upstream.real_signal_power_agreement()
    assert result.passed
    assert "2.0000" in result.measured


def test_real_ecg_record_excerpt_detects_annotated_beats():
    pytest.importorskip("wfdb", reason="wfdb not installed")
    result = real_upstream.real_ecg_record_excerpt()
    assert result.passed
    assert "11/14" in result.measured
    assert "72 bpm" in result.measured


def test_run_all_real_returns_nine_rows_with_known_outcomes():
    rows = real_upstream.run_all_real()
    assert len(rows) == 9
    by_case = {r.case: r for r in rows}
    # 6 pass, 3 fail-detections (real crash, unit error, rate error).
    assert sum(r.passed for r in rows) == 6
    assert not by_case["rsp-short-real-upstream"].passed
    assert not by_case["rsp-phase-real-upstream-seconds-as-samples"].passed
    assert not by_case["rsa-real-upstream-rate-value-flagged"].passed
    assert by_case["rsp-phase-real-upstream-correct"].passed
    assert by_case["rsa-real-upstream-crosscheck"].passed
    assert by_case["dfa-real-upstream-invariance"].passed
    assert by_case["emg-filter-real-upstream"].passed
    assert by_case["signal-power-real-upstream"].passed
    assert by_case["ecg-record-real-upstream"].passed
    assert all(r.source_url.startswith("https://") for r in rows)


def test_real_upstream_versions_recorded():
    versions = real_upstream.real_upstream_versions()
    assert versions["neurokit2"] == "0.3.0"
    assert versions["wfdb"] == "4.3.1"
    assert versions["numpy"] == "2.5.4"
