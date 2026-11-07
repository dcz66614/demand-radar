"""R05 PRD builder (reproducible).

Builds the 5 qualifying PRDs from the DB via prd.prd_from_db (VERIFIED
evidence + R04 competitor checks loaded from the DB) and renders them
with prd.render_markdown (which refuses incomplete PRDs).

The free-text fields below are the R05 author's, each grounded in the
cited evidence items — no invented workaround, impact figure, or test.
Where the record has no workaround, the text says so explicitly.
Run from the rework1 root:  python reports/rework1/build_prds_r05.py
Exit 0 on success; writes reports/prds/PRD_<pain_id>_r1.md (5 files).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from demand_radar import db as dbmod
from demand_radar.prd import prd_from_db, render_markdown, validate
from demand_radar.selection import gate_check

DB = ROOT / "data" / "demand_radar.sqlite"

CONTENT = {
    "6513d051954cbe1b5027": {
        "user_task": (
            "As a developer driving an AI agent (AgentLab / LangChain) or calling an LLM API, "
            "run a task end to end and get a result I can trust: the call completes, the result "
            "is what the model actually returned, and the token count matches the model actually used."
        ),
        "workaround": (
            "No reliable workaround is documented in the record. What reporters actually do: "
            "AgentLab absorbs failures with long pauses by default — 60 seconds per missed attempt, "
            "worst case about 16 minutes per step (AgentLab #182) — and re-run evaluations accepting "
            "lower reproduced scores (WebArena 25 vs 31.4 reported, #249). For the silent tokenizer "
            "substitution (#340) and the missing streaming-completed event (#41708) there is no "
            "workaround in the record at all: both failures are silent, so the user cannot work around "
            "what they cannot see. The HN poster (#50382039) asks how to verify AI responses quickly "
            "and no verified answer is recorded."
        ),
        "impact": (
            "Measured in the evidence: count_tokens() silently substitutes the GPT-4 tokenizer for "
            "every non-bare-OpenAI model name, with measured error 0% on code, +11.7% on English prose, "
            "+18.5% on Japanese and +108.3% on Chinese, and the wrong count feeds prompt trimming "
            "(AgentLab #340). Benchmark results are not reproducible: GenericAgent-GPT-4o reproduces "
            "WebArena at 25 against 31.4 reported (#249). A WorkArena L3 evaluation never stops running "
            "even after hours (#323). Responses API streaming never emits a completed event for "
            "function_call, so the agent never learns the call finished (LangChain #41708, filed three "
            "times by one author and counted once). CAPTCHA interrupts Google search in the demo (#187)."
        ),
        "sample_input": (
            "Two recorded reproducers, both from the evidence. (1) AgentLab #340: "
            "count_tokens(text, model=<a litellm-style non-OpenAI model name>) on a Chinese passage. "
            "(2) LangChain #41708: the Responses API event sequence response.output_item.added, then "
            "response.function_call_arguments.delta events, then response.output_item.done, for a "
            "function_call."
        ),
        "expected_output": (
            "(1) The token count is within 2% of the true tokenizer for the named model; the GPT-4 "
            "tokenizer value is rejected as wrong. (2) The streaming handler emits exactly one completed "
            "generation chunk when response.output_item.done arrives — and emits none if it never arrives."
        ),
        "acceptance_tests": [
            ("count_tokens with a litellm-style model name on the #340 Chinese passage returns a count "
            "within 2% of that model's real tokenizer; the GPT-4 tokenizer value is rejected as wrong."),
            ("Feeding the #41708 event sequence (added + deltas + done) emits exactly one completed chunk; "
            "without the done event, no completed chunk is emitted."),
            ("A 429/timeout fault injected into a call is reported as a failure with the attempt count and "
            "elapsed wait, never silently retried past the stated budget (AgentLab #182: 60s per attempt, "
            "~16 min worst case per step)."),
            ("A response whose content fails a schema/validation check is flagged as a wrong result, not "
            "passed through as a success."),
            ("The HN case (#50382039): an OpenRouter response that is false, or errors after a long wait, "
            "is classified (false / timeout / error) with the elapsed time, not returned as a normal result."),
        ],
        "caveats": [
            ("7 of 19 VERIFIED evidence items are CLOSED — closed does not mean solved; resolution was "
            "not checked from comments (R02 limitation)."),
            ("LangChain #41708/#41709/#41710 are the same bug report filed three times by one author; "
            "LangChain #41716/#41717/#41718 are the same HSTC feature proposal filed three times by one "
            "author. Both clusters count once (R03)."),
            ("This pain is a theme across 3 organisations, not one bug. R06 must pick the specific blocker "
            "(tokenizer substitution / streaming completion / fault handling) and prove it on the recorded "
            "reproducer — a generic issue list viewer does not address it."),
        ],
    },
    "4bb734fac7245033d327": {
        "user_task": (
            "As a researcher processing a real physiological recording (ECG, EMG, PPG or RSP) with "
            "NeuroKit, wfdb or MNE, run the processing function and get values I can trust: no crash, "
            "and no silently wrong numbers."
        ),
        "workaround": (
            "No working workaround is recorded for the wrong-value cases. Reporters file the bug; "
            "adjacent reports show people pinning versions instead (NeuroKit #1236: the setuptools<82 "
            "upper bound blocks picking up setuptools security fixes) or avoiding the broken function. "
            "Nothing in the record shows a user getting correct values out of the failing functions by "
            "another route."
        ),
        "impact": (
            "Wrong values, all measured in the evidence: fractal_dfa returns different scaling exponents "
            "for the same signal depending only on the amplitude units it is expressed in, and raises for "
            "sufficiently small-amplitude input (#1208); emg_process() accepts the EMG sampling rate but "
            "its amplitude filter silently assumes 1 kHz, so at 4 kHz the filter frequencies shift fourfold "
            "and can change whether muscle activity is detected (#1212); RSA_PorgesBohrer comes out "
            "negative because it is computed on heart rate instead of heart period (#1230); "
            "rsp_intervalrelated phase durations come out too small on epoched data (#1196). Crashes: "
            "signal_recompose() is broken on the homepage example (#1200); rsp_process() raises IndexError "
            "on an 8-second simulated recording (#1242); signal_power.py calls np.trapz, removed in numpy "
            "2.0, raising AttributeError (#1183); hrv(show=True) raises KeyError on ppg_peaks output (#1238)."
        ),
        "sample_input": (
            "Two recorded reproducers. (1) NeuroKit #1212: PhysioNet's public healthy EMG example recorded "
            "at 4 kHz, passed to emg_process(). (2) NeuroKit #1230: an ECG recording passed to hrv_rsa() "
            "with RSA_PorgesBohrer requested."
        ),
        "expected_output": (
            "(1) The EMG amplitude filter frequencies are computed from the actual 4 kHz sampling rate, "
            "not an assumed 1 kHz. (2) RSA_PorgesBohrer is positive, in ln(ms^2), computed on heart period — "
            "never on heart rate."
        ),
        "acceptance_tests": [
            ("emg_process() on the 4 kHz PhysioNet EMG example from #1212 uses 4 kHz filter frequencies; "
            "muscle-activity detection matches the 1 kHz reference within the stated tolerance."),
            ("hrv_rsa() on the #1230 ECG input returns RSA_PorgesBohrer >= 0 in ln(ms^2); a build that feeds "
            "heart rate instead of heart period fails this check."),
            ("fractal_dfa() on the same signal expressed in two amplitude units returns the same scaling "
            "exponent (within 1e-6); small-amplitude input does not raise (#1208)."),
            ("rsp_process() on the 8-second simulated recording from #1242 completes without IndexError and "
            "returns a result covering about two respiratory cycles."),
            "signal_power() on numpy 2.x completes without AttributeError (no np.trapz call, #1183).",
        ],
        "caveats": [
            "9 of 19 VERIFIED evidence items are CLOSED — closed does not mean solved.",
            ("Three items inside the theme are adjacent install/packaging reports, not signal-processing "
            "failures: #1160 (conda vs pip version mismatch), #1176 (documentation CI), #1236 (setuptools "
            "pin). The theme's core is the wrong-value/crash cases listed in the impact section."),
            ("The theme spans 3 organisations (NeuroKit, MNE, wfdb) with 15 distinct authors; the "
            "wrong-value cases are all NeuroKit reports, so an MVP must prove the fix on a NeuroKit "
            "reproducer, not on a different library's passing test."),
        ],
    },
    "cd021eac3c93ed0d2de1": {
        "user_task": (
            "As a researcher working with biosignal files, read a WFDB, EDF or FIFF file and write it back "
            "without the data changing and without the operation crashing."
        ),
        "workaround": (
            "No workaround is documented in the record. Reporters describe the failure and file it; "
            "wfdb #547 asks for documentation on how to access WFDB files from cloud URIs, which is a "
            "documentation gap, not a workaround for the read/write failures."
        ),
        "impact": (
            "Read/write failures in the evidence: calc_adc_params produces off-by-one values that crash "
            "wrsamp with an IndexError on values at the int32 bounds (wfdb #515); rdann raises OverflowError "
            "on LUED annotations with numpy 2.2 (#522) and on NSRDB annotations (#524); a HeaderSyntaxError "
            "is raised processing the PTB-XL+ database headers (#528); Record.wrsamp() fails with a "
            "TypeError when the record has no d_signal (#618); csv_to_wfdb mishandles defaults, scalar "
            "broadcasting and checksums (#593); read_forward_solution loses subcortical source spaces on a "
            "write/read round trip (MNE #14460)."
        ),
        "sample_input": (
            "Two recorded reproducers. (1) wfdb #515: a record with chmin=-2147483648 and "
            "chmax=2147483648, written with wrsamp. (2) wfdb #618: wfdb.rdrecord('sample-data/100', "
            "sampto=1000) followed by record.wrsamp(write_dir='out')."
        ),
        "expected_output": (
            "(1) wrsamp completes and the ADC parameters fit the data — no off-by-one, no IndexError. "
            "(2) wrsamp on a record with no d_signal either writes successfully or raises a clear error "
            "naming the missing signal — never a TypeError about '%' formatting on NoneType."
        ),
        "acceptance_tests": [
            ("wrsamp on the #515 boundary record (chmin=-2147483648, chmax=2147483648) completes, and a "
            "re-read of the written record returns values inside the int32 range."),
            ("rdrecord('sample-data/100', sampto=1000) followed by wrsamp() from #618 does not raise "
            "TypeError; either it writes, or it reports 'no d_signal' explicitly."),
            "rdann on the #522 LUED annotation file with numpy 2.2 returns annotations without OverflowError.",
            ("A forward solution built with a subcortical source space survives a write/read round trip with "
            "the subcortical space intact (#14460)."),
            ("csv_to_wfdb with scalar-per-channel defaults broadcasts the scalar to every channel and writes "
            "matching checksums (#593)."),
        ],
        "caveats": [
            "8 of 16 VERIFIED evidence items are CLOSED — closed does not mean solved.",
            ("Two items inside the theme are adjacent, not file-I/O failures: #534 (a proposal to replace "
            "pn_dir/file_name with a single path argument) and #547 (a documentation request for cloud URIs)."),
            ("The theme spans 3 organisations (wfdb, MNE, NeuroKit) with 13 distinct authors; the "
            "round-trip case (#14460) is MNE-specific and the ADC case (#515) is wfdb-specific, so an MVP "
            "must prove one of them on its own library's reproducer."),
        ],
    },
    "e3091fb34139fdf57dbd": {
        "user_task": (
            "As an investor or researcher fetching market and financial data for a symbol, get the right "
            "values, completely, without the fetcher leaking resources or corrupting its cache."
        ),
        "workaround": (
            "No workaround is documented in the record. Reporters file the bug; for the worst case there "
            "is nothing to work around with — yfinance get_news() returns [] for every symbol because the "
            "Yahoo endpoint it posts to now answers 404 (#3004), and analyst upgrades/downgrades simply "
            "stop flowing after 8/25 with no error reported (#2963)."
        ),
        "impact": (
            "Measured in the evidence: the daily session for Friday 2026-08-28 is missing across ^GSPC, "
            "^IXIC, IWM, RSP and ANET although the S&P 500 traded normally that day — the series jumps "
            "straight from 2026-08-27 to 2026-08-31 (#2964); valuations differ between yfinance.info and "
            "the Yahoo website (Enterprise Value/EBITDA 12.18 on the site vs 9.25 from info, #2931); the "
            "openbb_sec Form 4 fetcher leaks sockets in CLOSE_WAIT under concurrent downloads (#7650, filed "
            "twice by one author and counted once); the company-facts fetcher never actually caches — it "
            "re-downloads the full companyfacts.json for every statement type (#7655); the shared on-disk "
            "Form 4 cache corrupts under concurrent calls (#7656); ^VXN and ^VXD return no intraday data "
            "while ^VIX works (#2997); implied volatility for deep out-of-the-money options comes back at "
            "500–2000%, impossible in real markets (#2937)."
        ),
        "sample_input": (
            "Two recorded reproducers. (1) yfinance #2964: yf download of ^GSPC at interval 1d spanning "
            "2026-08-27 to 2026-08-31. (2) OpenBB #7650: concurrent Form 4 (insider trading) downloads for "
            "one symbol."
        ),
        "expected_output": (
            "(1) The 2026-08-28 session is present in the returned frame — or, if the source omits it, the "
            "result flags the session as missing from the source instead of silently jumping 08-27 to 08-31. "
            "(2) Concurrent Form 4 downloads complete and the process socket count returns to its pre-run "
            "baseline (no CLOSE_WAIT leak)."
        ),
        "acceptance_tests": [
            ("^GSPC 1d history spanning 2026-08-27 to 2026-08-31 contains the 2026-08-28 session; if the "
            "source omits it, the result flags the missing session instead of silently jumping 08-27 to 08-31 (#2964)."),
            ("Concurrent Form 4 downloads for one symbol complete and the process socket count returns to "
            "its pre-run baseline — no CLOSE_WAIT leak (#7650)."),
            ("Two consecutive company-facts fetches for the same symbol issue one network download of "
            "companyfacts.json, not two (#7655)."),
            ("Concurrent calls sharing the Form 4 on-disk cache each return correct data, with no corruption "
            "(#7656)."),
            ("get_news() for a symbol either returns items or reports the endpoint failure explicitly; an "
            "empty list with no error is a failure (#3004)."),
        ],
        "caveats": [
            ("14 of 16 VERIFIED evidence items are CLOSED — the most closed-heavy of the five qualifying "
            "pains. Closed does not mean solved; R06 must re-check the live state of the cited issues "
            "before building on any one of them."),
            "OpenBB #7650/#7651 are the same report filed twice by one author, 9 minutes apart; counted once.",
            ("yfinance #3033 (release 1.8.0 not on PyPI because the publish built 1.7.0) is a release-packaging "
            "report inside the theme, not a fetch failure."),
        ],
    },
    "0b7adcf63ec0f2075fab": {
        "user_task": (
            "As an investor using a financial research tool (OpenBB workspace, edgartools or yfinance), "
            "compare holdings or render charts and get correct, complete values — not wrong numbers, "
            "missing data, or an unpatched vulnerable dependency under the hood."
        ),
        "workaround": (
            "No workaround is documented in the record. The OpenBB item (#7744) is an RFC proposing "
            "pluggable chart renderers — a requested feature, not a workaround. The yfinance items "
            "(#3011/#3012) are a CVE tracking report filed twice (resubmission with corrected headings), "
            "not a workaround. Nothing in the record shows a user getting correct 13F cross-match values "
            "by another route."
        ),
        "impact": (
            "From the evidence: the edgartools 13F comparison cross-matches equity, Put and Call positions "
            "on the same CUSIP with incorrect financial values, missing financial data and inconsistent "
            "values for the same metric (#1848). The yfinance default curl_cffi backend bundles a Brotli "
            "decoder with publicly disclosed memory-safety vulnerability CVE-2026-111497 (#3011/#3012). "
            "OpenBB Workspace chart rendering is not pluggable or configurable — deployments cannot choose "
            "their rendering library (#7744, an RFC with a concrete use case)."
        ),
        "sample_input": (
            "edgartools #1848: a 13F comparison and history cross-match of equity, Put and Call positions "
            "on the same CUSIP."
        ),
        "expected_output": (
            "Put and Call positions on the same CUSIP cross-match with consistent values across history; "
            "any missing position is flagged as missing — never silently dropped and never shown as a "
            "wrong value."
        ),
        "acceptance_tests": [
            ("The 13F cross-match on the #1848 CUSIP returns the same value for the same metric across "
            "history; any missing position is flagged missing, not filled with a wrong value."),
            ("The bundled Brotli decoder version is checked against CVE-2026-111497 and reported as "
            "vulnerable or patched explicitly; a vulnerable default backend fails the check (#3011/#3012)."),
            ("A workspace chart request naming a renderer uses the documented adapter interface instead of "
            "silently falling back to a default (#7744)."),
            "Re-running the same 13F comparison twice returns identical results (deterministic cross-match).",
        ],
        "caveats": [
            ("Thinnest evidence of the five qualifiers: 4 VERIFIED links, effectively 3 distinct reports "
            "across 3 orgs (#3011/#3012 are one CVE report filed twice)."),
            "3 of the 4 VERIFIED evidence items are CLOSED (75%) — closed does not mean solved.",
            ("2 attached evidence links (OpenBB #7640/#7641, vendor promotion) are REJECTED and excluded "
            "from every count; the counted evidence is VERIFIED-only (verified in the R05 gate run)."),
            ("The #7744 item is a feature request with a concrete use case, not a bug report; the pain's "
            "'missing or broken' wording covers both, and the PRD does not claim it as a crash."),
        ],
    },
}


def main() -> int:
    outdir = ROOT / "reports" / "prds"
    with dbmod.connect(DB) as conn:
        for pain_id, text in CONTENT.items():
            gate = gate_check(conn, pain_id)
            if not gate["qualified"]:
                print(f"REFUSED: {pain_id} does not pass the gate: {gate['failure_reason']}",
                      file=sys.stderr)
                return 2
            prd = prd_from_db(conn, pain_id, **text)
            problems = validate(prd)
            if problems:
                print(f"REFUSED: PRD {pain_id} incomplete: {'; '.join(problems)}",
                      file=sys.stderr)
                return 2
            path = outdir / f"PRD_{pain_id}_r1.md"
            path.write_text(render_markdown(prd), encoding="utf-8")
            print(f"wrote {path} ({len(prd.evidence)} evidence, "
                  f"{len(prd.competitors)} competitors, "
                  f"{len(prd.acceptance_tests)} acceptance tests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
