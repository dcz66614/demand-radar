"""Generate mvps/r1_b/data/cases.json (deterministic, offline).

Signals are synthetic, generated with the parameters stated in the cited
issues (4 kHz EMG, 8 s RSP at 15 breaths/min, RR period series at 4 Hz);
they are NOT the original recordings. Expected values are computed with
signalcheck.py's own reference functions and stored in the file.
Run: python mvps/r1_b/make_fixtures.py
"""

import json
import math
import random
from pathlib import Path

from signalcheck import (
    buggy_effective_cutoffs,
    dfa_exponent,
    make_dfa_signal,
    rsa_from_period,
    signal_power,
)

HERE = Path(__file__).resolve().parent
URL = "https://github.com/neuropsychology/NeuroKit/issues/{}"


def rsa_series() -> list[float]:
    rng = random.Random(7)
    return [
        800 + 50 * math.sin(2 * math.pi * 0.25 * (i / 4.0)) + rng.gauss(0.0, 5.0)
        for i in range(240)
    ]


def rsp_short_signal(fs: float = 100.0) -> list[float]:
    return [math.sin(2 * math.pi * 0.25 * (i / fs)) for i in range(int(8 * fs))]


def power_signal(fs: float = 100.0) -> list[float]:
    return [2.0 * math.sin(2 * math.pi * 1.0 * (i / fs)) for i in range(int(10 * fs))]


def build() -> list:
    period = rsa_series()
    rsa_expected = rsa_from_period(period)
    rate = [60000.0 / p for p in period]
    rsa_on_rate = rsa_from_period(rate)

    dfa_signal = make_dfa_signal()
    dfa_exp = dfa_exponent(dfa_signal)
    dfa_tiny = [x * 1e-9 for x in dfa_signal]
    dfa_exp_tiny = dfa_exponent(dfa_tiny)

    power = power_signal()
    power_expected = signal_power(power, 100.0)

    low4, high4 = buggy_effective_cutoffs(4000.0)
    return [
        {"check": "emg_filter", "case": "emg-4khz-correct", "fs": 4000.0,
         "effective_low": 10.0, "effective_high": 500.0,
         "source_url": URL.format(1212)},
        {"check": "emg_filter", "case": "emg-4khz-buggy-1khz-assumption", "fs": 4000.0,
         "effective_low": low4, "effective_high": high4,
         "source_url": URL.format(1212)},
        {"check": "emg_filter", "case": "emg-1khz-control", "fs": 1000.0,
         "effective_low": 10.0, "effective_high": 500.0,
         "source_url": URL.format(1212)},
        {"check": "rsa", "case": "rsa-heart-period", "period_ms": period,
         "reported_rsa": rsa_expected, "input_unit": "ms",
         "source_url": URL.format(1230)},
        {"check": "rsa", "case": "rsa-heart-rate-input", "period_ms": rate,
         "reported_rsa": rsa_on_rate, "input_unit": "bpm",
         "source_url": URL.format(1230)},
        {"check": "rsa", "case": "rsa-negative-value", "period_ms": period,
         "reported_rsa": -1.2, "input_unit": "ms",
         "source_url": URL.format(1230)},
        {"check": "dfa", "case": "dfa-correct", "signal": dfa_signal,
         "reported_by_unit": {"uV": round(dfa_exp, 6), "mV": round(dfa_exp, 6)},
         "source_url": URL.format(1208)},
        {"check": "dfa", "case": "dfa-reported-differs-by-unit", "signal": dfa_signal,
         "reported_by_unit": {"uV": round(dfa_exp + 0.3, 6), "mV": round(dfa_exp - 0.2, 6)},
         "source_url": URL.format(1208)},
        {"check": "dfa", "case": "dfa-small-amplitude", "signal": dfa_tiny,
         "reported_by_unit": {"uV": round(dfa_exp_tiny, 6), "mV": round(dfa_exp_tiny, 6)},
         "source_url": URL.format(1208)},
        {"check": "rsp_phase", "case": "rsp-phase-correct", "intervals": [[0, 200], [200, 400]],
         "fs": 100.0, "reported_durations": [2.0, 2.0], "index_unit": "samples",
         "source_url": URL.format(1196)},
        {"check": "rsp_phase", "case": "rsp-phase-seconds-as-samples",
         "intervals": [[0, 2], [2, 4]], "fs": 100.0,
         "reported_durations": [0.02, 0.02], "index_unit": "seconds",
         "source_url": URL.format(1196)},
        {"check": "rsp_short", "case": "rsp-8s-recording", "signal": rsp_short_signal(),
         "fs": 100.0, "source_url": URL.format(1242)},
        {"check": "signal_power", "case": "power-correct", "signal": power,
         "fs": 100.0, "reported_power": power_expected,
         "source_url": URL.format(1183)},
        {"check": "signal_power", "case": "power-wrong-value", "signal": power,
         "fs": 100.0, "reported_power": power_expected * 0.5,
         "source_url": URL.format(1183)},
    ]


if __name__ == "__main__":
    cases = build()
    out = HERE / "data" / "cases.json"
    out.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(cases)} cases)")
    print(f"  RSA expected from period: {rsa_from_period(rsa_series()):.2f} ln(ms^2); "
          f"on rate: {rsa_from_period([60000.0 / p for p in rsa_series()]):.2f}")
    print(f"  DFA exponent: {dfa_exponent(make_dfa_signal()):.6f}")
    print(f"  signal power (A=2 sine): {signal_power(power_signal(), 100.0):.4f} (expected 2.0)")
