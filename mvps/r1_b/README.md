# R1-B — Physiological Signal Validator (PRD 4bb734fac7245033d327)

Signal-data validator for the BIO signal-processing pain. It does NOT
browse issues. It parses offline fixture signals and checks the NUMBERS
against expected values, one check per recorded failure class.

## Positioning — PARTIALLY_REAL_WORLD_VALIDATED (R2-05)

R1-B is a validator, not a signal-processing library and not a product
that fixes NeuroKit. After R2-05 it has REAL upstream validation paths
(`real_upstream.py`, neurokit2 0.3.0 / wfdb 4.3.1) alongside the
synthetic fixture checks:

| check | real path | measured result (2026-11-06) |
|---|---|---|
| rsp_short (#1242) | real `nk.rsp_process` on 8 s simulated RSP | **IndexError reproduced** — #1242 is still live in neurokit2 0.3.0 (deterministic across seeds 42/1/7/123; completes at 10 s). The guarded local path handles the same signal. |
| rsp_phase (#1196) | `check_rsp_phase` on intervals from real `rsp_process` peaks/troughs | Correct durations pass; seconds-as-samples error fails (99% off). |
| rsa (#1230) | real `nk.hrv_rsa` Porges-Bohrer vs local `rsa_from_period`, same RR periods | Real 4.172 vs local 4.691 ln(ms²), delta 0.518 — same sign/magnitude, NOT identical (different detrending; loose 1.0 cross-implementation bound, not the PRD 0.05). Rate-based value flagged. |
| dfa (#1208) | real `nk.fractal_dfa` at uV / mV / 1e-9 scales | Invariant to 1.55e-15 (alpha 1.332878) — property holds upstream. Local implementation gives 1.4348 on the same signal (different box sizes), recorded, not claimed as agreement. |
| emg_filter (#1212) | real `nk.signal_filter` / `nk.emg_amplitude` at fs=4000 vs assumed 1 kHz | 900 Hz tone attenuated 0.0004x at the true fs, passes 0.99x with the assumed fs; amplitude mean 0.054 vs 0.203 (3.74x). The symptom is reproduced by the caller's wrong fs. |
| signal_power (#1183) | real `nk.signal_power` vs local trapezoid, same A=2 sine | 2.0000 vs 1.9998 (0.01% difference). |
| ecg_record | real `wfdb.rdrecord` + real `nk.ecg_process` on the MIT-BIH 100 excerpt (`data/mitdb_100_10s.*`) | 12 peaks detected; 11/14 annotated beats matched within 100 ms (2 missed at the record edge, 1 offset 133 ms); 72 bpm. |

The fixture-based checks remain synthetic. The validator must NOT be
presented as a product that solves the real upstream problems, and must
NOT be used to offset PRDs eliminated by re-scoring.

## What it proves (one check per cited failure)

| check | recorded failure | what is actually computed |
|---|---|---|
| emg_filter | #1212: filter assumes 1 kHz, shifts 4x at 4 kHz | effective vs intended (10, 500) Hz band — note upstream's envelope band is (10, 400) Hz, not (10, 500) Hz |
| rsa | #1230: RSA on heart rate, comes out negative | RSA recomputed from heart period (6.19 ln(ms^2) on fixture); rate input (1.47) and negative values fail |
| dfa | #1208: exponent depends on amplitude units | DFA exponent computed in uV, mV and 1e-9 scale; must agree within 1e-6 |
| rsp_phase | #1196: phase durations too small on epoched data | durations recomputed from index + sampling rate |
| rsp_short | #1242: IndexError on an 8 s recording | guarded path returns 2 cycles; unguarded path reproduces the IndexError |
| signal_power | #1183: np.trapz removed in numpy 2.0 | power by trapezoid rule; A=2 sine gives exactly 2.0 (A^2/2) |

## What it does NOT prove

- It does not fix NeuroKit, and it is not a signal-processing library.
  It validates *detection* of the failure classes on recorded reproducers.
- Three cited items (#1208, #1230, #1196) closed `completed` upstream
  (live-checked 2026-11-05); the validator checks the failure class on the
  recorded reproducer and does NOT claim upstream is still broken for those.
  The pain stays live through the still-open items (#1212, #1242, #1200,
  #1238, #1240, #1241). Exception: #1242 was REPRODUCED against the real
  current upstream release (neurokit2 0.3.0, 2026-11-06) — see Positioning.
- Fixtures are synthetic signals built from the parameters in the cited
  issues (4 kHz EMG, 8 s RSP at 15 breaths/min, RR period series at 4 Hz),
  not the original recordings. The one real recording is the MIT-BIH 100
  10 s excerpt in `data/` (see `data/README.md`).

## Run

```bash
python -m streamlit run mvps/r1_b/app.py   # UI: 2 filters (check, outcome), CSV export
python -m pytest mvps/r1_b/tests/ -q        # 67 tests in .venv-real (57 in the main venv; 10 real-upstream tests skip without neurokit2/wfdb)
python mvps/r1_b/make_fixtures.py           # regenerate data/cases.json
```

Cases: `data/cases.json` (14 cases, 15 check rows; every case carries its
`source_url`). The UI also accepts an uploaded case JSON; malformed files
are rejected with an error, not a crash. CSV export keeps `source_url` on
every row.

Real-upstream tests need neurokit2 + wfdb (installed in the `.venv-real`
test venv; `pytest.importorskip` skips them elsewhere with a clear
reason). They run offline: tiktoken/neurokit2 data are generated or
vendored, no network calls at test time.
