"""R1-B — signal-data validator for physiological signal processing.

PRD 4bb734fac7245033d327 (BIO: process physiological signals correctly).
This is NOT an issue list viewer. It parses offline fixture biosignal data
and checks the NUMBERS against expected values, one check per recorded
failure class. Every check returns pass/fail with measured vs expected
values and the source issue URL.

Recorded failure classes (NeuroKit, all from the PRD evidence):
- #1212 emg_process: amplitude filter silently assumes 1 kHz; at 4 kHz the
  filter frequencies shift fourfold. STILL OPEN (live-checked 2026-11-05).
- #1230 RSA_PorgesBohrer computed on heart rate instead of heart period, so
  it comes out negative. Closed completed 2026-11-01 — the validator checks
  the failure class on the RECORDED reproducer; it does not claim upstream
  is still broken for this item.
- #1208 fractal_dfa results depend on amplitude units, fail for small
  amplitudes. Closed completed 2026-11-01 — same caveat as #1230.
- #1196 rsp_intervalrelated phase durations too small on epoched data.
  Closed completed 2026-11-04 — same caveat.
- #1242 rsp_process raises IndexError on an 8-second simulated recording.
  STILL OPEN.
- #1183 signal_power calls np.trapz, removed in numpy 2.0 (AttributeError).
  Closed completed 2026-03-16 — same caveat; the check runs on numpy 2.5.4
  here, where np.trapz no longer exists.

Fixtures are synthetic signals generated with the parameters stated in the
cited issues (e.g. 4 kHz EMG, 8 s RSP at 15 breaths/min, RR period series);
they are NOT the original recordings, and the fixture files say so.
"""

import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

EMG_BAND = (10.0, 500.0)  # intended EMG amplitude-filter band, Hz (#1212)
RSA_FS = 4.0  # RR period series sampled at 4 Hz in the #1230 reproducer
DFA_TOLERANCE = 1e-6  # PRD acceptance test 3: same exponent within 1e-6


@dataclass
class CheckResult:
    case: str
    check: str
    passed: bool
    measured: str
    expected: str
    source_url: str
    detail: str


# ---------------------------------------------------------------------------
# #1212 — sampling-rate-aware EMG filter frequencies
# ---------------------------------------------------------------------------

def buggy_effective_cutoffs(fs: float, assumed_fs: float = 1000.0) -> tuple[float, float]:
    """Cutoffs a 1-kHz-assuming implementation effectively applies at fs."""
    return (EMG_BAND[0] * fs / assumed_fs, EMG_BAND[1] * fs / assumed_fs)


def check_emg_filter(fs: float, effective_low: float, effective_high: float) -> CheckResult:
    measured = f"({effective_low:.1f}, {effective_high:.1f}) Hz at fs={fs:.0f}"
    expected = f"({EMG_BAND[0]:.1f}, {EMG_BAND[1]:.1f}) Hz"
    ok = (
        abs(effective_low - EMG_BAND[0]) / EMG_BAND[0] <= 0.01
        and abs(effective_high - EMG_BAND[1]) / EMG_BAND[1] <= 0.01
    )
    return CheckResult(
        case=f"emg-filter-fs{fs:.0f}", check="emg_filter", passed=ok,
        measured=measured, expected=expected,
        source_url="https://github.com/neuropsychology/NeuroKit/issues/1212",
        detail=(
            "filter frequencies match the intended band"
            if ok else
            "filter frequencies shifted by assuming 1 kHz: "
            f"effective low is {effective_low / EMG_BAND[0]:.1f}x the intended value"
        ),
    )


# ---------------------------------------------------------------------------
# #1230 — RSA must be computed on heart period, never heart rate
# ---------------------------------------------------------------------------

def _moving_average(values: list[float], window: int) -> list[float]:
    half = window // 2
    out = []
    for i in range(len(values)):
        lo, hi = max(0, i - half), min(len(values), i + half + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def rsa_from_period(period_ms: list[float], fs: float = RSA_FS) -> float:
    """Porges-Bohrer-style RSA: ln(variance of the detrended period series).

    Detrend = subtract a 2.5 s moving average (removes slow drift, keeps the
    ~0.25 Hz respiratory component); RSA is ln(ms^2). It can be NEGATIVE:
    ln(variance) < 0 whenever the detrended variance is below 1 ms^2
    (e.g. a near-constant period series). The REWORK1 docstring claiming
    "RSA must be >= 0" was mathematically wrong (independent review P0-01)
    and is removed here; a correct negative RSA must pass validation.
    """
    if len(period_ms) < 8:
        raise ValueError("period series too short for RSA")
    trend = _moving_average(period_ms, max(3, int(fs * 2.5)))
    detrended = [x - t for x, t in zip(period_ms, trend)]
    var = sum(d * d for d in detrended) / len(detrended)
    if var <= 0:
        raise ValueError("no respiratory variation in period series")
    return math.log(var)


# RSA tolerance (REWORK2, reviewed parameters — see check_rsa docstring).
# RSA is a LOG-variance, ln(ms^2): an absolute tolerance of 0.05 ln(ms^2)
# means the underlying variance may differ by ~5% (e^0.05 = 1.051), the
# smallest difference the #1230 reproducer can meaningfully distinguish and
# the same 5% the PRD acceptance test used as its bound. The relative term
# (2% of |expected|) only keeps the bound from being absurdly tight when
# |expected| is large (e.g. expected 20 -> tolerance 0.4); near zero the
# absolute term dominates, so expected ~= 0 is judged in absolute units.
RSA_ABS_TOL = 0.05
RSA_REL_TOL = 0.02


def check_rsa(
    period_ms: list[float], reported_rsa: float, input_unit: str = "ms",
    abs_tol: float = RSA_ABS_TOL, rel_tol: float = RSA_REL_TOL,
) -> CheckResult:
    url = "https://github.com/neuropsychology/NeuroKit/issues/1230"
    if not isinstance(reported_rsa, (int, float)) or isinstance(reported_rsa, bool) \
            or not math.isfinite(reported_rsa):
        return CheckResult(
            case="rsa-nonfinite-reported", check="rsa", passed=False,
            measured=f"reported RSA {reported_rsa!r} (not a finite number)",
            expected="a finite RSA value in ln(ms^2)",
            source_url=url,
            detail="reported RSA is NaN, infinite, or not a number — rejected outright",
        )
    if input_unit != "ms":
        return CheckResult(
            case="rsa-heart-rate-input", check="rsa", passed=False,
            measured=f"input unit {input_unit}, reported RSA {reported_rsa:.2f}",
            expected="heart period in ms, RSA in ln(ms^2) (may be negative)",
            source_url=url,
            detail="RSA computed on heart rate instead of heart period (#1230)",
        )
    if not isinstance(period_ms, list) or len(period_ms) < 8:
        return CheckResult(
            case="rsa-short-series", check="rsa", passed=False,
            measured=f"period series of length {len(period_ms) if isinstance(period_ms, list) else 'not-a-list'}",
            expected="at least 8 heart-period samples",
            source_url=url,
            detail="period series too short for RSA — cannot validate, not a pass",
        )
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x)
           for x in period_ms):
        return CheckResult(
            case="rsa-nonfinite-input", check="rsa", passed=False,
            measured="period series contains a non-finite or non-numeric value",
            expected="finite heart-period samples in ms",
            source_url=url,
            detail="period series contains NaN/inf — rejected outright",
        )
    try:
        expected = rsa_from_period(period_ms)
    except ValueError as exc:
        return CheckResult(
            case="rsa-no-variation", check="rsa", passed=False,
            measured=f"period series has no usable respiratory variation: {exc}",
            expected="a period series with real respiratory variation",
            source_url=url,
            detail=str(exc),
        )
    # REWORK2 fix (review P0-01): the old code divided by the SIGNED expected
    # value, so for expected < 0 the relative error came out negative and
    # any reported value passed, while a correct negative RSA failed the
    # `reported_rsa >= 0` gate. Compare absolute difference against a
    # tolerance built from |expected|; near zero the absolute term rules.
    delta = abs(reported_rsa - expected)
    scale = max(abs(expected), 1e-8)
    tol = max(abs_tol, rel_tol * scale)
    ok = delta <= tol
    return CheckResult(
        case="rsa-heart-period", check="rsa", passed=ok,
        measured=f"reported RSA {reported_rsa:.4f} ln(ms^2)",
        expected=f"RSA {expected:.4f} ln(ms^2) from heart period (tolerance {tol:.4f})",
        source_url=url,
        detail=(
            "RSA matches the heart-period computation"
            if ok else
            f"reported RSA differs from the heart-period value by {delta:.4f} "
            f"ln(ms^2) (tolerance {tol:.4f})"
        ),
    )


# ---------------------------------------------------------------------------
# #1208 — fractal DFA must be unit-invariant and not raise on small amplitudes
# ---------------------------------------------------------------------------

def _detrend_rms(segment: list[float]) -> float:
    n = len(segment)
    xs = list(range(n))
    mx, my = (n - 1) / 2, sum(segment) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, segment))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    return math.sqrt(sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, segment)) / n)


def dfa_exponent(signal: list[float]) -> float:
    """Detrended fluctuation analysis exponent (pure Python, deterministic)."""
    if len(signal) < 16:
        raise ValueError("signal too short for DFA")
    mean = sum(signal) / len(signal)
    integrated = []
    total = 0.0
    for x in signal:
        total += x - mean
        integrated.append(total)
    sizes = [4, 8, 16, 32, 64]
    sizes = [n for n in sizes if n <= len(signal) // 4]
    log_n, log_f = [], []
    for n in sizes:
        boxes = len(integrated) // n
        f2 = sum(_detrend_rms(integrated[i * n:(i + 1) * n]) ** 2 for i in range(boxes)) / boxes
        if f2 <= 0:
            continue
        log_n.append(math.log(n))
        log_f.append(math.log(math.sqrt(f2)))
    if len(log_n) < 2:
        raise ValueError("DFA: too few box sizes")
    mx, my = sum(log_n) / len(log_n), sum(log_f) / len(log_f)
    sxx = sum((x - mx) ** 2 for x in log_n)
    sxy = sum((x - mx) * (y - my) for x, y in zip(log_n, log_f))
    return sxy / sxx if sxx else 0.0


def check_dfa(signal: list[float], reported_by_unit: dict) -> CheckResult:
    url = "https://github.com/neuropsychology/NeuroKit/issues/1208"
    exp_uv = dfa_exponent(signal)
    exp_mv = dfa_exponent([x * 1000 for x in signal])
    exp_small = dfa_exponent([x * 1e-9 for x in signal])  # must not raise
    invariant = abs(exp_uv - exp_mv) <= DFA_TOLERANCE and abs(exp_uv - exp_small) <= DFA_TOLERANCE
    rep_uv = reported_by_unit.get("uV")
    rep_mv = reported_by_unit.get("mV")
    reported_agree = (
        rep_uv is not None and rep_mv is not None and abs(rep_uv - rep_mv) <= DFA_TOLERANCE
    )
    ok = invariant and reported_agree
    return CheckResult(
        case="dfa-unit-invariance", check="dfa", passed=ok,
        measured=f"computed exponent uV={exp_uv:.6f} mV={exp_mv:.6f} tiny={exp_small:.6f}; "
                 f"reported uV={rep_uv} mV={rep_mv}",
        expected="same exponent within 1e-6 across units; small amplitude does not raise",
        source_url=url,
        detail=(
            "DFA exponent is unit-invariant"
            if ok else
            "reported exponents differ across amplitude units (#1208 symptom)"
            if not reported_agree else
            "computed exponents are not unit-invariant"
        ),
    )


# ---------------------------------------------------------------------------
# #1196 — RSP phase durations must use time, not raw index
# ---------------------------------------------------------------------------

def check_rsp_phase(
    intervals: list, fs: float, reported_durations: list, index_unit: str,
) -> CheckResult:
    """REWORK2 fix (review P1-04): validate everything BEFORE zip().

    The old code zipped reported_durations against expected and silently
    dropped extras, so [1, 1, 999] for two intervals passed. Length
    mismatch, fs <= 0 / non-finite, non-increasing or non-finite intervals,
    and non-finite / negative reported durations are now rejections with a
    reason, not crashes and not passes. An unknown index_unit is likewise a
    failed check (the validator must never crash on bad input).
    """
    url = "https://github.com/neuropsychology/NeuroKit/issues/1196"

    def _fail(case: str, measured: str, expected: str, detail: str) -> CheckResult:
        return CheckResult(
            case=case, check="rsp_phase", passed=False,
            measured=measured, expected=expected,
            source_url=url, detail=detail,
        )

    if not isinstance(fs, (int, float)) or isinstance(fs, bool) \
            or not math.isfinite(fs) or fs <= 0:
        return _fail(
            "rsp-phase-bad-fs", f"sampling rate fs={fs!r}",
            "a finite sampling rate fs > 0",
            "sampling rate must be finite and positive — cannot convert samples to seconds",
        )
    if index_unit not in ("samples", "seconds"):
        return _fail(
            "rsp-phase-bad-unit", f"index unit {index_unit!r}",
            "index_unit 'samples' or 'seconds'",
            f"unknown index_unit: {index_unit!r}",
        )
    if not isinstance(intervals, list) or not intervals:
        return _fail(
            "rsp-phase-no-intervals", f"intervals={intervals!r}",
            "at least one (start, end) interval with end > start",
            "no intervals to check",
        )
    for iv in intervals:
        if (not isinstance(iv, (list, tuple)) or len(iv) != 2
                or any(not isinstance(x, (int, float)) or isinstance(x, bool)
                       or not math.isfinite(x) for x in iv)
                or iv[1] <= iv[0] or iv[0] < 0):
            return _fail(
                "rsp-phase-bad-interval", f"interval {iv!r}",
                "intervals (start, end) with 0 <= start < end, finite",
                "interval is not a finite, strictly increasing (start, end) pair",
            )
    if not isinstance(reported_durations, list):
        return _fail(
            "rsp-phase-bad-reported", f"reported_durations={reported_durations!r}",
            "one reported duration per interval",
            "reported durations are not a list",
        )
    if len(reported_durations) != len(intervals):
        return _fail(
            "rsp-phase-length-mismatch",
            f"{len(reported_durations)} reported durations for {len(intervals)} intervals: "
            f"{reported_durations!r}",
            f"exactly {len(intervals)} durations, one per interval",
            "reported durations do not match the interval count — extra or missing "
            "values are rejected, never silently truncated",
        )
    if any(not isinstance(r, (int, float)) or isinstance(r, bool)
           or not math.isfinite(r) or r < 0 for r in reported_durations):
        return _fail(
            "rsp-phase-bad-reported",
            f"reported durations {reported_durations!r}",
            "finite, non-negative durations",
            "reported durations contain a non-finite or negative value",
        )
    if index_unit == "samples":
        expected = [(b - a) / fs for a, b in intervals]
    else:
        expected = [b - a for a, b in intervals]
    diffs = [abs(r - e) / e for r, e in zip(reported_durations, expected)]
    ok = all(d <= 0.01 for d in diffs)
    return CheckResult(
        case="rsp-phase-durations", check="rsp_phase", passed=ok,
        measured=f"reported {reported_durations} s (index unit: {index_unit})",
        expected=f"{[round(e, 3) for e in expected]} s at fs={fs:.0f}",
        source_url=url,
        detail=(
            "phase durations match the time-based values"
            if ok else
            f"phase durations off by up to {max(diffs):.0%} — index treated as "
            "the wrong unit, durations come out too small on epoched data"
        ),
    )


# ---------------------------------------------------------------------------
# #1242 — rsp_process must not raise IndexError on a short recording
# ---------------------------------------------------------------------------

def _find_peaks(signal: list[float], fs: float) -> list[int]:
    threshold = sum(signal) / len(signal) + 0.5 * (
        math.sqrt(sum((x - sum(signal) / len(signal)) ** 2 for x in signal) / len(signal))
    )
    min_dist = max(1, int(fs * 1.5))  # breaths are >= ~2 s apart at 15/min
    peaks, last = [], -min_dist
    for i in range(1, len(signal) - 1):
        if (signal[i] > signal[i - 1] and signal[i] >= signal[i + 1]
                and signal[i] > threshold and i - last >= min_dist):
            peaks.append(i)
            last = i
    return peaks


def rsp_process_guarded(signal: list[float], fs: float) -> dict:
    """Length-guarded RSP processing: returns a result, never IndexError."""
    peaks = _find_peaks(signal, fs)
    return {"status": "ok", "cycles": len(peaks),
            "duration_s": len(signal) / fs, "peaks": peaks}


def rsp_process_buggy(signal: list[float], fs: float) -> dict:
    """Reproduces the #1242 crash: indexes the third peak unconditionally."""
    peaks = _find_peaks(signal, fs)
    third_peak = peaks[2]  # IndexError when fewer than 3 peaks exist
    return {"status": "ok", "cycles": len(peaks), "third_peak": third_peak}


def check_rsp_short(signal: list[float], fs: float) -> list[CheckResult]:
    url = "https://github.com/neuropsychology/NeuroKit/issues/1242"
    guarded = rsp_process_guarded(signal, fs)
    ok = guarded["status"] == "ok" and abs(guarded["cycles"] - 2) <= 1
    results = [CheckResult(
        case="rsp-short-guarded", check="rsp_short", passed=ok,
        measured=f"{guarded['cycles']} cycles in {guarded['duration_s']:.0f} s, no error",
        expected="completes without IndexError, covering about two cycles",
        source_url=url,
        detail="guarded processing handles the 8 s recording",
    )]
    try:
        rsp_process_buggy(signal, fs)
        results.append(CheckResult(
            case="rsp-short-buggy", check="rsp_short", passed=False,
            measured="buggy path completed without error",
            expected="IndexError (the recorded #1242 crash)",
            source_url=url,
            detail="expected the recorded crash; got none — fixture may not reproduce it",
        ))
    except IndexError:
        results.append(CheckResult(
            case="rsp-short-buggy", check="rsp_short", passed=False,
            measured="IndexError on the 8 s recording (2 peaks, third indexed)",
            expected="IndexError (the recorded #1242 crash)",
            source_url=url,
            detail="buggy path reproduces the recorded crash; the validator flags it",
        ))
    return results


# ---------------------------------------------------------------------------
# #1183 — signal power must not use np.trapz (removed in numpy 2.0)
# ---------------------------------------------------------------------------

def signal_power(signal: list[float], fs: float) -> float:
    """Mean power via the trapezoidal rule (numpy.trapezoid, not np.trapz)."""
    import numpy as np

    dt = 1.0 / fs
    squared = [x * x for x in signal]
    return float(np.trapezoid(squared, dx=dt) / (len(signal) * dt))


def check_signal_power(signal: list[float], fs: float, reported_power: float) -> CheckResult:
    url = "https://github.com/neuropsychology/NeuroKit/issues/1183"
    computed = signal_power(signal, fs)
    rel = abs(reported_power - computed) / computed if computed else 1.0
    ok = rel <= 0.01
    return CheckResult(
        case="signal-power", check="signal_power", passed=ok,
        measured=f"reported power {reported_power:.4f}, computed {computed:.4f} (trapezoid)",
        expected="reported power matches the trapezoidal computation within 1%",
        source_url=url,
        detail=(
            "power computed without np.trapz (removed in numpy 2.0)"
            if ok else
            f"reported power differs from the trapezoidal value by {rel:.1%}"
        ),
    )


# ---------------------------------------------------------------------------
# Case runner / loading / export
# ---------------------------------------------------------------------------

def run_case(case: dict) -> list[CheckResult]:
    kind = case.get("check")
    if kind == "emg_filter":
        results = [check_emg_filter(case["fs"], case["effective_low"], case["effective_high"])]
    elif kind == "rsa":
        results = [check_rsa(case["period_ms"], case["reported_rsa"], case.get("input_unit", "ms"))]
    elif kind == "dfa":
        results = [check_dfa(case["signal"], case["reported_by_unit"])]
    elif kind == "rsp_phase":
        results = [check_rsp_phase(case["intervals"], case["fs"],
                                   case["reported_durations"], case["index_unit"])]
    elif kind == "rsp_short":
        results = check_rsp_short(case["signal"], case["fs"])
    elif kind == "signal_power":
        results = [check_signal_power(case["signal"], case["fs"], case["reported_power"])]
    else:
        raise ValueError(f"unknown check: {kind!r}")
    # Keep the fixture's case name on every row so pass/fail rows are distinct.
    for r in results:
        r.case = case.get("case", r.case)
    return results


def run_all(cases: list) -> list[CheckResult]:
    results: list[CheckResult] = []
    for case in cases:
        results.extend(run_case(case))
    return results


def load_cases(path: str | Path) -> list:
    """Load a check-case fixture file; invalid JSON or shape raises ValueError."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"case file not found: {path}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"case file is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ValueError("case file must be a non-empty JSON list")
    for item in data:
        if not isinstance(item, dict) or not item.get("check"):
            raise ValueError("each case needs at least a check field")
        if not str(item.get("source_url", "")).startswith("http"):
            raise ValueError(f"case {item.get('check')} needs a source_url")
    return data


def export_csv(results: list[CheckResult], path: str | Path) -> Path:
    """Source-preserving CSV export: every row keeps its source_url."""
    fields = ["case", "check", "passed", "measured", "expected", "source_url", "detail"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    return Path(path)


def make_dfa_signal(seed: int = 42, n: int = 512) -> list[float]:
    """Deterministic random-walk signal for the DFA fixtures."""
    rng = random.Random(seed)
    out, total = [], 0.0
    for _ in range(n):
        total += rng.gauss(0.0, 1.0)
        out.append(total)
    return out
