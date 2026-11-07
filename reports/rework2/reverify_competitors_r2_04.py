"""R2-04 competitor re-verification (idempotent).

Re-examines the 10 competitor_checks rows of the 5 R05 candidate themes
against the SAME user task and SAME acceptance case from R2-03 §5
(the R2-03 sample input per theme). The other 24 rows (non-qualifying
pains) are NOT re-examined; their evidence_level stays NULL.

Verdict rule (brief §R2-04):
- KEEP does_solve=0 only when the check identifies a specific executable
  function (or a documented scope that excludes the acceptance input),
  with an official evidence link, and the reason ties to the R2-03
  sample. Evidence level is SCOPE_DOCUMENTED: the determination is a
  documented function/scope argument, NOT an execution test — no
  competitor was executed against the sample input (recorded honestly;
  execution-level confirmation is NOT_TESTED).
- UNKNOWN when the check rests only on official-homepage marketing copy,
  or the product IS the broken library, or the check never addresses the
  sample input. UNKNOWN is recorded by prefixing gaps with 'UNKNOWN: '
  (the existing convention — unknown_check_count counts it), keeping the
  product name so history is preserved. UNKNOWN blocks G and the gate.

Live re-reads 2026-11-06 (read-only public pages, all HTTP 200):
- HeartPy README: heart-rate analysis only (PPG/ECG -> BPM/IBI/SDNN/
  RMSSD/LF/HF); no EMG/DFA/RSP/signal-power function.
- pyEDFlib README: EDF+/BDF+ read/write only (highlevel.read_edf/
  write_edf); no WFDB reader/writer.
- LiteLLM docs home: completion() with "streaming, retries, fallbacks,
  and the cost of each call".
- LangSmith observability docs: tracing/monitoring/evaluation — a
  post-hoc record of what happened.

Old rows are preserved in reports/rework1/competitor_checks.jsonl (R04
export, untouched). This script snapshots the pre-update DB rows to
reports/rework2/competitor_checks_before_r2_04.jsonl, applies the
updates, and exports the after-state to
reports/rework2/competitor_checks_r2_04.jsonl (all 34 rows).

Usage (from the rework2 root, venv active):
    python reports/rework2/reverify_competitors_r2_04.py
Exit 0. Idempotent: re-running produces identical rows.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from demand_radar import db as dbmod
from demand_radar.competitors import insert_competitor_check, list_checks

DB = ROOT / "data" / "demand_radar.sqlite"
CHECKED_AT = "2026-11-06"

# Acceptance cases from reports/rework2/r2_03.md §5 (the R2-03 sample
# input per theme). 0b7a/4bb7 failed the evidence gate, so they have no
# §5 sample; their cases are the single DIRECT link (0b7a) and the
# PRD R1 acceptance inputs (4bb7).
CASE_0B7A = ("edgartools #1848: compare_holdings()/holding_history() "
             "cross-match of 13F filings (Bank of America Q2/Q3 2024)")
CASE_4BB7 = ("NeuroKit #1212: emg_process filter assumes 1 kHz, 4x shift "
             "at 4 kHz (representative of the theme's EMG/DFA/RSP/"
             "signal_power acceptance cases)")
CASE_6513 = ("LangChain #41708: exactly one completed chunk when "
             "response.output_item.done arrives for a function_call; "
             "none without it (plus #340: token count within 2%)")
CASE_CD02 = ("wfdb #618: wfdb.rdrecord('sample-data/100') then wrsamp() "
             "round-trip must complete without TypeError")
CASE_E309 = ("yfinance #2964: 2026-08-28 session present for "
             "^GSPC/^IXIC/IWM/RSP/ANET, or flagged missing, never "
             "silently skipped")

# (pain_id, product) -> new verdict fields. Version/url/capability are
# carried over from the existing row (not re-typed here).
UPDATES = {
    ("0b7adcf63ec0f2075fab", "OpenBB"): {
        "verdict": "UNKNOWN",
        "executable_function": "OpenBB terminal/workspace (investment research workspace)",
        "acceptance_case": CASE_0B7A,
        "evidence_level": "UNKNOWN",
        "gap": ("UNKNOWN: the product IS the broken library — the pain's own "
                "evidence issues are filed against OpenBB itself (workspace/UI "
                "features missing or broken); a check against the failing "
                "product cannot support does_solve=0."),
        "reviewer_reason": ("R2-04: OpenBB is one of the products the pain is "
                            "filed against (OpenBB #7640/#7641 are attached "
                            "REJECTED links; #7744 is an OpenBB chart RFC). "
                            "The check's evidence was the openbb.co homepage. "
                            "Neither the broken-library identity nor homepage "
                            "copy can support does_solve=0."),
    },
    ("0b7adcf63ec0f2075fab", "TradingView"): {
        "verdict": "UNKNOWN",
        "executable_function": "TradingView charting/screener (homepage claim; no function executed against the sample)",
        "acceptance_case": CASE_0B7A,
        "evidence_level": "UNKNOWN",
        "gap": ("UNKNOWN: evidence is the official homepage's marketing copy "
                "only ('Track All Markets'); no executable function was tied "
                "to the 13F compare input, so does_solve=0 is unsupported."),
        "reviewer_reason": ("R2-04: the check recorded only the tradingview.com "
                            "homepage. Nothing in it addresses comparing 13F "
                            "holdings across periods or the (Cusip, PutCall) "
                            "identity loss. Marketing copy cannot support "
                            "does_solve=0."),
    },
    ("4bb734fac7245033d327", "HeartPy"): {
        "verdict": "KEEP 0",
        "executable_function": "heartpy.process() — heart-rate analysis from PPG/ECG signals (BPM, IBI, SDNN, RMSSD, LF/HF)",
        "acceptance_case": CASE_4BB7,
        "evidence_level": "SCOPE_DOCUMENTED",
        "gap": ("Narrow scope (heart-rate analysis only); no EMG processing, "
                "DFA, RSP-phase or signal-power function, so it cannot "
                "execute the acceptance inputs."),
        "reviewer_reason": ("R2-04: repo README re-read live 2026-11-06 confirms "
                            "HR-only scope — heartpy.process takes PPG/ECG and "
                            "outputs BPM/IBI/SDNN/RMSSD/LF/HF. No function "
                            "exists for EMG filtering, DFA exponents, RSP phase "
                            "durations or signal power, so the acceptance "
                            "inputs cannot be executed in HeartPy. "
                            "Scope-documented, not execution-tested: no "
                            "HeartPy run was performed."),
    },
    ("4bb734fac7245033d327", "NeuroKit2"): {
        "verdict": "UNKNOWN",
        "executable_function": "NeuroKit2 signal-processing functions (emg_process, hrv_rsa, fractal_dfa, rsp_process, ...)",
        "acceptance_case": CASE_4BB7,
        "evidence_level": "UNKNOWN",
        "gap": ("UNKNOWN: the product IS the broken library — the reported "
                "signal-processing crashes/wrong values are filed against "
                "NeuroKit itself (#1160–#1242); a check against the failing "
                "product cannot support does_solve=0."),
        "reviewer_reason": ("R2-04: all 12 DIRECT links of this theme are "
                            "NeuroKit issues. The check's evidence was the "
                            "NeuroKit docs homepage. A check against the "
                            "failing product cannot support does_solve=0."),
    },
    ("6513d051954cbe1b5027", "LangSmith"): {
        "verdict": "KEEP 0",
        "executable_function": "LangSmith tracing via SDK/env vars — records traces of LLM calls for post-hoc inspection",
        "acceptance_case": CASE_6513,
        "evidence_level": "SCOPE_DOCUMENTED",
        "gap": ("Observability only: it records failures after they happen; "
                "it does not prevent API failures, wrong results, or silent "
                "default substitution."),
        "reviewer_reason": ("R2-04: observability docs re-read live 2026-11-06 "
                            "confirm tracing/monitoring/evaluation — a post-hoc "
                            "record of what happened. Tracing cannot emit the "
                            "missing completed event or validate the token "
                            "count at call time, so the #41708/#340 acceptance "
                            "cases cannot be satisfied by it. "
                            "Scope-documented, not execution-tested."),
    },
    ("6513d051954cbe1b5027", "LiteLLM"): {
        "verdict": "KEEP 0",
        "executable_function": "litellm.completion() with retries, fallbacks, load-balancing across providers",
        "acceptance_case": CASE_6513,
        "evidence_level": "SCOPE_DOCUMENTED",
        "gap": ("Retries and fallbacks do not fix wrong results or silent "
                "substitution of model defaults; no result-validation or "
                "hidden-default detection is offered."),
        "reviewer_reason": ("R2-04: docs home re-read live 2026-11-06 confirms "
                            "completion() with 'streaming, retries, fallbacks, "
                            "and the cost of each call'. A retry re-issues the "
                            "call; it cannot detect that count_tokens "
                            "substituted the GPT-4 tokenizer (a wrong count "
                            "returned as success) nor emit the missing "
                            "completed event. Scope-documented, not "
                            "execution-tested."),
    },
    ("cd021eac3c93ed0d2de1", "MNE-Python"): {
        "verdict": "UNKNOWN",
        "executable_function": "mne.io read/write of EEG/MEG data (FIFF/EDF)",
        "acceptance_case": CASE_CD02,
        "evidence_level": "UNKNOWN",
        "gap": ("UNKNOWN: MNE is itself one of the evidence products (MNE "
                "#14431 split-file names and #14460 lost subcortical source "
                "spaces are DIRECT evidence), and the check never addresses "
                "the wfdb #618 round-trip input; 'partly the broken library' "
                "plus no sample link cannot support does_solve=0."),
        "reviewer_reason": ("R2-04: the check recorded the MNE docs homepage "
                            "and 'heavy dependency and limited format "
                            "coverage'. MNE is a DIRECT-evidence product for "
                            "this theme, and nothing in the check addresses "
                            "the wfdb #618 wrsamp round-trip."),
    },
    ("cd021eac3c93ed0d2de1", "pyEDFlib"): {
        "verdict": "KEEP 0",
        "executable_function": "pyedflib.highlevel.read_edf / write_edf — EDF+/BDF+ files only",
        "acceptance_case": CASE_CD02,
        "evidence_level": "SCOPE_DOCUMENTED",
        "gap": ("EDF+/BDF+ only; file reading/writing, format conversion and "
                "parameter-handling failures for other biosignal formats "
                "remain."),
        "reviewer_reason": ("R2-04: repo README re-read live 2026-11-06 confirms "
                            "EDF+/BDF+ read/write only (highlevel.read_edf / "
                            "write_edf). The acceptance input is a WFDB "
                            "record; pyEDFlib has no WFDB reader/writer, so it "
                            "cannot execute the round-trip. Scope-documented, "
                            "not execution-tested."),
    },
    ("e3091fb34139fdf57dbd", "pandas-datareader"): {
        "verdict": "UNKNOWN",
        "executable_function": "pandas_datareader.get_data_yahoo() — remote data readers",
        "acceptance_case": CASE_E309,
        "evidence_level": "UNKNOWN",
        "gap": ("UNKNOWN: docs confirm remote readers exist, but the check "
                "cites no source-specific evidence that its Yahoo reader "
                "returns the missing 2026-08-28 session (or fails the same "
                "way); 'same failure class' is asserted, not shown for the "
                "sample input. No execution was performed."),
        "reviewer_reason": ("R2-04: whether pandas-datareader's Yahoo reader "
                            "returns the missing session depends on whether "
                            "the omission is Yahoo-side or yfinance-side — "
                            "the check does not distinguish, and cites no "
                            "source-specific deprecation for the Yahoo daily "
                            "reader. Unproven either way, so UNKNOWN."),
    },
    ("e3091fb34139fdf57dbd", "yfinance"): {
        "verdict": "UNKNOWN",
        "executable_function": "yfinance Ticker/download fetchers",
        "acceptance_case": CASE_E309,
        "evidence_level": "UNKNOWN",
        "gap": ("UNKNOWN: the product IS the broken library — the reported "
                "fetcher failures, resource leaks and wrong values are filed "
                "against yfinance itself; a check against the failing product "
                "cannot support does_solve=0."),
        "reviewer_reason": ("R2-04: 8 of this theme's 13 DIRECT links are "
                            "yfinance issues. The check's evidence was the "
                            "yfinance repo page. A check against the failing "
                            "product cannot support does_solve=0."),
    },
}


def _dump(conn, path: Path) -> int:
    rows = []
    for pid in conn.execute("SELECT DISTINCT pain_id FROM competitor_checks ORDER BY pain_id"):
        rows.extend(list_checks(conn, pid[0]))
    rows.sort(key=lambda r: (r["pain_id"], r["product"]))
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    return len(rows)


def main() -> int:
    dbmod.init_db(DB)  # applies the R2-04 migration (idempotent)
    with dbmod.connect(DB) as conn:
        n_before = _dump(conn, ROOT / "reports" / "rework2" / "competitor_checks_before_r2_04.jsonl")
        for (pain_id, product), upd in sorted(UPDATES.items()):
            old = [c for c in list_checks(conn, pain_id) if c["product"] == product]
            assert len(old) == 1, f"expected exactly 1 check for {pain_id[:6]} {product}, got {len(old)}"
            old = old[0]
            insert_competitor_check(
                conn,
                pain_id=pain_id,
                product=product,
                version=old["version"],
                url=old["checked_url"],
                capability=old["capability"],
                gap=upd["gap"],
                reviewer_reason=upd["reviewer_reason"],
                does_solve=0,
                checked_at=CHECKED_AT,
                executable_function=upd["executable_function"],
                acceptance_case=upd["acceptance_case"],
                evidence_level=upd["evidence_level"],
            )
            print(f"{pain_id[:6]} {product}: {upd['verdict']} "
                  f"(was does_solve=0, gap={old['gaps'][:60]!r})")
        n_after = _dump(conn, ROOT / "reports" / "rework2" / "competitor_checks_r2_04.jsonl")
    print(f"rows before: {n_before}, rows after: {n_after}")
    assert n_before == n_after == 34
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
