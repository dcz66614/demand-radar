"""REWORK2 R2-03 assessment data + runner.

Classifies EVERY evidence link of the 5 REWORK1-qualifying themes against
that theme's problem_signature.  Evidence basis per link: the full issue
body as collected live in R02 (reports/rework1/review_r02_raw_github.json
/ review_r02_raw_hn.json, 2026-11-05) plus live re-reads of the
load-bearing issues on 2026-11-06 (NeuroKit #1176/#1236, wfdb #538,
MNE #14321, edgartools #1848, OpenBB #7744, yfinance #3012,
langchain #41708 — see reports/rework2/r2_03.md §1).  No link needed
UNKNOWN: all 76 bodies were readable.

Run from the project root:
    .venv/bin/python reports/rework2/assess_r2_03.py
Idempotent (upserts).  Writes reports/rework2/evidence_assessment.csv
from the DB and prints the recomputed DIRECT-only counts.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from demand_radar import db as dbmod
from demand_radar.evidence_assessment import (
    ADJACENT,
    DIRECT,
    DUPLICATE,
    OUT_OF_SCOPE,
    assessment_counts,
    direct_only_counts,
    upsert_assessment,
    upsert_problem_signature,
)

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "demand_radar.sqlite"
CSV_OUT = ROOT / "reports" / "rework2" / "evidence_assessment.csv"
ASSESSED_AT = "2026-11-06T00:30:00Z"

# pain_id -> problem_signature (see r2_03.md §2 for the granularity rule).
SIGNATURES = {
    "0b7adcf63ec0f2075fab": {
        "actor": "investor/researcher using a financial research tool to compare institutional holdings",
        "input_artifact": "two 13F-HR filings for the same manager (Bank of America Q2/Q3 2024) with compare_holdings()/holding_history()",
        "operation": "cross-match equity, Put and Call positions on the same CUSIP across periods",
        "observed_failure": "position identity (Cusip, PutCall) is lost in the join: 10,878 rows instead of 8,753 union position keys; Value sums to ~2.10x the filed Q3 total; new option positions shown DECREASED instead of NEW",
        "expected_output": "8,753 union position keys with like-designation pairs; Value sums match the filed information-table totals; a missing position is flagged, never silently merged",
        "affected_product": "edgartools (edgar.thirteenf)",
        "version_or_environment": "edgartools upstream main @ 5ae0f6352, Python 3.13.17, pandas 3.1.0, Windows 11 Pro",
    },
    "4bb734fac7245033d327": {
        "actor": "researcher processing a real physiological recording (ECG, EMG, PPG or RSP)",
        "input_artifact": "a physiological recording (or simulated signal with known ground truth) passed to a NeuroKit signal-processing function",
        "operation": "run a NeuroKit signal-processing function (emg_process, hrv_rsa, fractal_dfa, rsp_process, signal_power, signal_recompose, hrv, ...) on the recording",
        "observed_failure": "the function crashes (IndexError/KeyError/AttributeError/TypeError) or returns a silently wrong numeric value (unit-dependent DFA exponent, negative RSA, 4x-shifted EMG filter, 99%-too-small phase durations)",
        "expected_output": "correct numeric values (unit-invariant, computed on heart period, rate-aware filtering) and no crash",
        "affected_product": "NeuroKit2 (neurokit2)",
        "version_or_environment": "NeuroKit2 0.2.12-0.2.13 / dev @ f40486992, Python 3.11-3.13, NumPy 2.x",
    },
    "6513d051954cbe1b5027": {
        "actor": "developer calling an LLM API or driving an AI agent",
        "input_artifact": "an LLM API call: a token-count request, or a Responses API stream carrying a function_call",
        "operation": "invoke the API and consume its result (token count; streamed function-call completion)",
        "observed_failure": "the result the caller receives is silently wrong or silently missing: a substituted tokenizer inflates the count (up to +108% on CJK), or the completion event for a function_call is never emitted so the caller cannot know the call finished",
        "expected_output": "a result faithful to the model/API actually used: token count within 2% of the true tokenizer; exactly one completed chunk when response.output_item.done arrives, none when it does not",
        "affected_product": "LLM API client / agent framework (AgentLab, langchain-openai)",
        "version_or_environment": "AgentLab current main; langchain-openai 1.7.4, langchain-core 1.7.x, Python 3.14",
    },
    "cd021eac3c93ed0d2de1": {
        "actor": "researcher working with biosignal files",
        "input_artifact": "a biosignal file: a WFDB record/annotation set, an EDF file, or a FIFF forward solution",
        "operation": "read the file and write it back (round trip) with the same library",
        "observed_failure": "the read or write crashes (OverflowError, HeaderSyntaxError, TypeError, IndexError) or the round trip loses/changes data (wrong checksums, lost subcortical source spaces, wrong defaults, split-file names the reader cannot find)",
        "expected_output": "the file reads and writes back without crashing and without the data changing",
        "affected_product": "biosignal file I/O libraries (wfdb-python, MNE-Python)",
        "version_or_environment": "wfdb-python 4.1.2; MNE-Python 1.13.x; NumPy 2.2; Python 3.9-3.12",
    },
    "e3091fb34139fdf57dbd": {
        "actor": "investor/researcher fetching market and financial data for a symbol",
        "input_artifact": "a market/financial data request for a symbol (daily history, option chain, SEC company facts, Form 4 filings, news)",
        "operation": "fetch the data through the library's fetcher (yfinance Ticker/download, openbb-sec/openbb-cboe fetchers)",
        "observed_failure": "the fetcher returns wrong values (IV 500-2000%, valuations disagreeing with the source), silently missing values (a trading session absent, get_news [] on a 404), or leaks/corrupts resources under concurrent use (CLOSE_WAIT sockets, shared cache corruption, a cache that never caches)",
        "expected_output": "complete, correct values for the requested symbol and session; missing data flagged explicitly; no socket or cache corruption under concurrent use",
        "affected_product": "market/financial data fetchers (yfinance, openbb-sec, openbb-cboe)",
        "version_or_environment": "yfinance 1.7.0-1.8.0; openbb 4.7.2 / openbb-sec 1.6.7 / openbb-cboe 2.0.0; Python 3.12-3.13",
    },
}

# (pain_id, link key) -> (classification, reason).
# Link key: "owner/repo#number" for GitHub, "hn:<id>" for Hacker News.
ASSESSMENTS = {
    # --- 0b7a FIN workspace (6) ---
    ("0b7adcf63ec0f2075fab", "dgunning/edgartools#1848"): (
        DIRECT,
        "13F compare_holdings/holding_history loses (Cusip, PutCall) identity: 10,878 rows vs 8,753 keys, Value 2.10x the filed Q3 total. Matches every signature field.",
    ),
    ("0b7adcf63ec0f2075fab", "openbq-org/OpenBB#7640"): (
        OUT_OF_SCOPE,
        "Vendor promotion for the ViBo memory product (already REJECTED in R02); not a user problem report.",
    ),
    ("0b7adcf63ec0f2075fab", "openbq-org/OpenBB#7641"): (
        OUT_OF_SCOPE,
        "Vendor promotion for the NeuForge Pay spend firewall (already REJECTED in R02); not a user problem report.",
    ),
    ("0b7adcf63ec0f2075fab", "openbq-org/OpenBB#7744"): (
        OUT_OF_SCOPE,
        "RFC/feature proposal for pluggable chart renderers; no observed failure and no reproducer; different product (OpenBB Workspace frontend) and different task (renderer configurability). Live-confirmed 2026-11-06.",
    ),
    ("0b7adcf63ec0f2075fab", "ranaroussi/yfinance#3011"): (
        DUPLICATE,
        "Same CVE-2026-111497 report as #3012; its own body states 'Superseded by #3012'.",
    ),
    ("0b7adcf63ec0f2075fab", "ranaroussi/yfinance#3012"): (
        OUT_OF_SCOPE,
        "CVE dependency-vulnerability tracking for Brotli in the curl_cffi backend; body states explicitly 'not incorrect Yahoo Finance data'; no market-data failure observed. Live-confirmed 2026-11-06.",
    ),
    # --- 4bb7 BIO signals (19) ---
    ("4bb734fac7245033d327", "MIT-LCP/wfdb-python#538"): (
        ADJACENT,
        "GDF file read fails with a uint8 out-of-bounds error; file reading in a different product, not a NeuroKit signal-computation failure. A live maintainer reply (2026-11-06) questions whether it is a wfdb issue at all (stack trace looks like MNE).",
    ),
    ("4bb734fac7245033d327", "mne-tools/mne-python#14321"): (
        ADJACENT,
        "EDF loading with mixed sampling frequencies warns of edge artefacts when preload=False; a load-time warning in a different product, not a signal-processing function returning a wrong value or crashing. Live-confirmed 2026-11-06.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1160"): (
        OUT_OF_SCOPE,
        "conda installs 0.2.10 while pip installs 0.2.12; package-version availability, not a signal-computation failure.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1163"): (
        DIRECT,
        "bio_process demo crashes with ChainedAssignmentError in epochs_create; a NeuroKit processing function crashing on real input.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1176"): (
        OUT_OF_SCOPE,
        "GitHub Actions documentation publishing setup; CI/docs, no signal computation involved. Live-confirmed 2026-11-06.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1182"): (
        DIRECT,
        "read_acqknowledge returns a float sampling rate (2000.0) while eda_intervalrelated/signal_autocor require int for indexing; the wrong-typed value breaks downstream processing. Borderline: the failure surfaces in a read function; counted DIRECT because the observed failure is a processing break.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1183"): (
        DIRECT,
        "signal_power calls the removed np.trapz on NumPy 2.x and raises AttributeError; a processing function crashing.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1196"): (
        DIRECT,
        "rsp_intervalrelated computes phase durations from the index, returning values ~99% too small on epoched data; silently wrong values.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1200"): (
        DIRECT,
        "signal_recompose crashes with AttributeError (scipy.cluster.hierarchy has no attribute 'distance') on the homepage example.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1202"): (
        OUT_OF_SCOPE,
        "Feature request to add the Elgendi 2013 R-peak detection method; no observed failure.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1208"): (
        DIRECT,
        "fractal_dfa returns different scaling exponents for the same signal in different amplitude units and raises on small-amplitude input; wrong values established against the scale-invariance of h(q).",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1212"): (
        DIRECT,
        "emg_process amplitude filter silently assumes 1 kHz, shifting filter frequencies 4x at 4 kHz and changing muscle-activity detection; silently wrong values.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1218"): (
        ADJACENT,
        "signal_fixpeaks artifact detection differs from Kubios HRV Scientific 4.3.0 on the same recordings, but wrongness is not established: the reporter asks whether the differences are expected (published algorithm vs proprietary implementation) and there is no ground truth. Same function family, different evidential status.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1230"): (
        DIRECT,
        "RSA_PorgesBohrer computed on heart rate instead of heart period, returning -4.50 where ln(ms^2) requires a variance-based value; wrong value established against the documented unit.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1236"): (
        OUT_OF_SCOPE,
        "setuptools<82.0.0 dependency pin blocks security fixes; a packaging constraint, not a signal-computation failure. Live check 2026-11-06: the maintainer reports the pin removed (commit 84cb59e); either way out of scope.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1238"): (
        DIRECT,
        "hrv(show=True) raises KeyError on ppg_peaks output because the plot path looks up ECG_R_Peaks; a processing function crashing on documented input.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1240"): (
        DIRECT,
        "Event-related rate means are stored as change-from-onset but labelled as the rate (e.g. ECG_Rate_Mean -2.28 bpm); wrong values in the output columns.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1241"): (
        DIRECT,
        "eog_process fails on the bundled eog_100hz recording because the default blink detector requires MNE, and the error misleadingly names signal_filter(); a processing function failing on its own example data.",
    ),
    ("4bb734fac7245033d327", "neuropsychology/NeuroKit#1242"): (
        DIRECT,
        "rsp_process raises IndexError on an 8-second simulated recording (31 of 40 seeds crash); missing length check; a processing function crashing.",
    ),
    # --- 6513 AI reliability (19) ---
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#182"): (
        ADJACENT,
        "RateLimit/OpenAI timeouts with 60 s pauses per missed attempt (worst case ~16 min/step); a loud timeout/retry failure in the same user task, not a silently wrong or missing API result.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#186"): (
        OUT_OF_SCOPE,
        "agent-xray Gradio desync across multiple tabs caused by a global; an analysis-tool UI/session issue, a different task from API-call result fidelity.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#187"): (
        OUT_OF_SCOPE,
        "CAPTCHA triggered on Google search in the demo; a web-browsing interruption, not an API-call result failure.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#192"): (
        OUT_OF_SCOPE,
        "Cannot replicate benchmark leaderboard results (prompt flags unclear); benchmark documentation/reproducibility, no API failure.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#211"): (
        OUT_OF_SCOPE,
        "Question: can AgentLab run inside Docker (Python 3.13 policy); a deployment question, no observed failure.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#249"): (
        OUT_OF_SCOPE,
        "WebArena reproduced at 25 vs 31.4 reported; benchmark-score reproduction, not an API-call result failure.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#320"): (
        OUT_OF_SCOPE,
        "Benchmark name 'workarena_l3' not found; a naming/configuration question.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#323"): (
        OUT_OF_SCOPE,
        "WorkArena L3 evaluation never stops running (3 days); an evaluation-harness hang, a different operation.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#329"): (
        OUT_OF_SCOPE,
        "Qwen3 benchmark performance question ('extremely low performance', asks if anyone benchmarked it); no API failure demonstrated.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#339"): (
        OUT_OF_SCOPE,
        "Availability/use-terms question about the HTTP-trace dataset; a question, not a failure report.",
    ),
    ("6513d051954cbe1b5027", "ServiceNow/AgentLab#340"): (
        DIRECT,
        "count_tokens silently substitutes the GPT-4 tokenizer for every non-bare-OpenAI model name; measured +108.3% on Chinese, +18.5% Japanese, +11.7% English; the wrong count feeds prompt trimming.",
    ),
    ("6513d051954cbe1b5027", "langchain-ai/langchain#41672"): (
        ADJACENT,
        "HuggingFacePipeline.from_model_id moves a single-device device_map model to device 0; a silently wrong placement in model loading, not an API-call result; same broad reliability theme, different operation.",
    ),
    ("6513d051954cbe1b5027", "langchain-ai/langchain#41674"): (
        ADJACENT,
        "SentenceTransformersTokenTextSplitter loads model weights on the accelerator though only the tokenizer is used; resource waste in text-splitter loading, not a wrong or missing API result.",
    ),
    ("6513d051954cbe1b5027", "langchain-ai/langchain#41708"): (
        DIRECT,
        "Responses API streaming never emits a completed event for function_call: _convert_responses_chunk_to_generation_chunk has no function_call branch for response.output_item.done; the caller cannot know the call finished. Live-confirmed 2026-11-06.",
    ),
    ("6513d051954cbe1b5027", "langchain-ai/langchain#41709"): (
        DUPLICATE,
        "Same report as #41708 (identical title/body, same author); filed three times, counts once.",
    ),
    ("6513d051954cbe1b5027", "langchain-ai/langchain#41710"): (
        DUPLICATE,
        "Same report as #41708 (identical title/body, same author); filed three times, counts once.",
    ),
    ("6513d051954cbe1b5027", "langchain-ai/langchain#41717"): (
        OUT_OF_SCOPE,
        "HSTC feature proposal (deterministic hybrid compressor); a feature request, no observed failure.",
    ),
    ("6513d051954cbe1b5027", "langchain-ai/langchain#41718"): (
        DUPLICATE,
        "Same HSTC proposal as #41717 (identical title/body, same author).",
    ),
    ("6513d051954cbe1b5027", "hn:50382039"): (
        ADJACENT,
        "Ask HN: how to verify AI API responses quickly; the poster reports false responses and slow errors on OpenRouter, but there is no identified product/function, no reproducer and no specific failure - a discussion question, not a bug report of the same problem.",
    ),
    # --- cd02 BIO files (16) ---
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#515"): (
        DIRECT,
        "calc_adc_params off-by-one (chmax 2147483648 above the int32 max) crashes wrsamp with IndexError; a write crashing on real data.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#522"): (
        DIRECT,
        "rdann raises OverflowError on LUED annotations with NumPy 2.2; a read crashing.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#524"): (
        DIRECT,
        "rdann raises OverflowError (uint8 bounds) on NSRDB annotations; a read crashing. An independent report of the same underlying bug as #522 (different author, different dataset); both count as corroboration, not as a repost.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#528"): (
        DIRECT,
        "HeaderSyntaxError processing PTB-XL+ headers; a read failing on a real database.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#534"): (
        OUT_OF_SCOPE,
        "API design proposal (single path argument, deprecate pn_dir/file_name); no observed failure.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#543"): (
        DIRECT,
        "record.wrsamp fails with TypeError (NoneType % int) when the record has no d_signal; a write failing. Same underlying bug as #618 (different author/report); both count.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#547"): (
        OUT_OF_SCOPE,
        "Documentation request: how to access WFDB files from cloud URIs; no functional failure.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#554"): (
        DIRECT,
        "MultiRecord.wrsamp has no expanded=True option, so checksums fail on write; a write producing wrong checksums.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#568"): (
        ADJACENT,
        "dl_files authentication handling returns 403 for credentialed PhysioNet downloads; file acquisition/download, not a read/write round trip; same workflow, different operation.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#593"): (
        DIRECT,
        "csv_to_wfdb mishandles defaults, scalar broadcasting and checksums (explicit 0 treated as missing; checksum from physical values); a write producing wrong values/checksums.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#594"): (
        OUT_OF_SCOPE,
        "csv_to_wfdb docstring has incorrect parameter descriptions; a documentation error, no functional failure.",
    ),
    ("cd021eac3c93ed0d2de1", "MIT-LCP/wfdb-python#618"): (
        DIRECT,
        "Record.wrsamp fails with TypeError on a record read with physical=True (no d_signal); a write failing. Same underlying bug as #543; both count as independent reports.",
    ),
    ("cd021eac3c93ed0d2de1", "mne-tools/mne-python#14428"): (
        OUT_OF_SCOPE,
        "Proposal for a correctness benchmark and reviewed skill files for AI assistants; a process proposal, not a file I/O failure.",
    ),
    ("cd021eac3c93ed0d2de1", "mne-tools/mne-python#14431"): (
        DIRECT,
        "MNE saves split files as ..._desc-base_split-01_... while mne-bids expects split before desc, so find_matching_paths returns []; a write whose output the read side cannot find - a round-trip/interop failure.",
    ),
    ("cd021eac3c93ed0d2de1", "mne-tools/mne-python#14460"): (
        DIRECT,
        "read_forward_solution loses subcortical source spaces on a write/read round trip; data lost in the round trip.",
    ),
    ("cd021eac3c93ed0d2de1", "neuropsychology/NeuroKit#1162"): (
        ADJACENT,
        "EDA processing fails on pandas 3 (DataFrame.pad removed); a signal-processing failure, not a file read/write failure - it belongs to the 4bb7 operation class, not this theme's.",
    ),
    # --- e309 FIN fetch (16) ---
    ("e3091fb34139fdf57dbd", "dgunning/edgartools#1855"): (
        ADJACENT,
        "ixt-sec:exchnameen raises TransformError for 10 of 21 SEC exchange names; an XBRL concept-transformation failure in the same product family, but a different operation from fetching market data for a symbol (parsing a transform, not a fetch). Borderline; counted adjacent, not direct.",
    ),
    ("e3091fb34139fdf57dbd", "openbq-org/OpenBB#7645"): (
        DIRECT,
        "get_standardized_financials returns None for per-share fields (basic_eps, diluted_eps, share counts) for issuers filing only class-dimensioned facts (COKE, BRK-B, UHAL); silently missing values.",
    ),
    ("e3091fb34139fdf57dbd", "openbq-org/OpenBB#7650"): (
        DIRECT,
        "openbb_sec Form 4 fetcher leaks sockets in CLOSE_WAIT under concurrent downloads (a new ClientSession per request); a resource leak.",
    ),
    ("e3091fb34139fdf57dbd", "openbq-org/OpenBB#7651"): (
        DUPLICATE,
        "Same report as #7650 (identical title/body, same author), filed 9 minutes apart.",
    ),
    ("e3091fb34139fdf57dbd", "openbq-org/OpenBB#7655"): (
        DIRECT,
        "Company-facts fetcher never actually caches: a fresh throwaway CachedSession per call re-downloads the full multi-MB companyfacts.json for every statement type; resource waste on every fetch.",
    ),
    ("e3091fb34139fdf57dbd", "openbq-org/OpenBB#7656"): (
        DIRECT,
        "Form 4 fetcher's shared on-disk cache corrupts under concurrent calls (one call's close_db gzips/deletes the file another call is using); cache corruption, subsequent calls fail.",
    ),
    ("e3091fb34139fdf57dbd", "openbq-org/OpenBB#7813"): (
        DIRECT,
        "openbb-cboe 2.0.0 CboeOptionsChains raises TypeError (strptime on float) on live SPY payloads with digit-root option symbols; a fetcher crashing on real input.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#2930"): (
        DIRECT,
        "history() missing the 2026-07-28 session for QQQ and other tickers; silently missing values.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#2931"): (
        DIRECT,
        "yfinance.info Enterprise Value/EBITDA 9.25 vs 12.18 on the Yahoo website and 12.18 from yfinance.valuation; wrong values.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#2937"): (
        DIRECT,
        "Implied volatility 500-2000% for deep out-of-the-money options (real range 0-300%); wrong values across tickers and expiries.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#2939"): (
        DIRECT,
        "Missing XETRA 2026-07-31 data for SDF.DE though it was a trading day; silently missing values.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#2963"): (
        DIRECT,
        "Analyst upgrades/downgrades stop flowing after 8/25 with no error; silently missing values. Reporter suspects a Yahoo-side cause; the user-visible failure (silent staleness) is the same either way - attribution caveat recorded.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#2964"): (
        DIRECT,
        "Daily history missing the 2026-08-28 session across ^GSPC, ^IXIC, IWM, RSP, ANET though the market traded normally; silently missing values.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#2997"): (
        DIRECT,
        "No intraday data for ^VXN/^VXD while ^VIX works; the reporter verified Yahoo's own chart endpoint returns zero intraday timestamps, so the cause may be upstream - the user-visible failure (silent empty result) is the same; attribution caveat recorded.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#3004"): (
        DIRECT,
        "get_news() returns [] for every symbol because /xhr/ncp now answers 404; the empty list is returned without raising or logging - silently missing values.",
    ),
    ("e3091fb34139fdf57dbd", "ranaroussi/yfinance#3033"): (
        OUT_OF_SCOPE,
        "Release 1.8.0 not on PyPI because the publish job built 1.7.0; release packaging, not a fetch failure.",
    ),
}


def _url_for(conn: sqlite3.Connection, pain_id: str, key: str) -> str:
    """Resolve a link key to its canonical URL from the DB."""
    if key.startswith("hn:"):
        item_id = key[3:]
        row = conn.execute(
            "SELECT url FROM source_items WHERE platform='hackernews' "
            "AND external_id=?",
            (item_id,),
        ).fetchone()
    else:
        owner_repo, number = key.rsplit("#", 1)
        owner, repo = owner_repo.split("/", 1)
        row = conn.execute(
            "SELECT url FROM source_items WHERE platform='github' "
            "AND url LIKE ?",
            (f"%github.com/{owner}/{repo}/issues/{number}",),
        ).fetchone()
    if row is None:
        raise ValueError(f"no source_item for {pain_id} {key}")
    # Confirm this source is actually linked to this pain.
    linked = conn.execute(
        "SELECT 1 FROM evidence_links el JOIN source_items s "
        "ON s.source_id = el.source_id "
        "WHERE el.pain_id = ? AND s.url = ?",
        (pain_id, row[0]),
    ).fetchone()
    if linked is None:
        raise ValueError(f"{key} ({row[0]}) is not linked to {pain_id}")
    return row[0]


def main() -> int:
    dbmod.init_db(DB)
    with dbmod.connect(DB) as conn:
        for pain_id, sig in SIGNATURES.items():
            upsert_problem_signature(conn, pain_id, sig, ASSESSED_AT)
        for (pain_id, key), (classification, reason) in ASSESSMENTS.items():
            url = _url_for(conn, pain_id, key)
            upsert_assessment(conn, pain_id, url, classification, reason, ASSESSED_AT)
        conn.commit()
        # Every evidence link of the 5 themes must be assessed, exactly once.
        for pain_id in SIGNATURES:
            n_links = conn.execute(
                "SELECT COUNT(*) FROM evidence_links WHERE pain_id = ?",
                (pain_id,),
            ).fetchone()[0]
            n_assessed = conn.execute(
                "SELECT COUNT(*) FROM evidence_assessment WHERE pain_id = ?",
                (pain_id,),
            ).fetchone()[0]
            assert n_links == n_assessed, (
                f"{pain_id}: {n_assessed} assessed of {n_links} links"
            )
        # Export the CSV from the DB (single source of truth).
        rows = conn.execute(
            "SELECT pain_id, source_url, classification, reason, assessed_at "
            "FROM evidence_assessment ORDER BY pain_id, source_url"
        ).fetchall()
        CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
        with CSV_OUT.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                ["pain_id", "source_url", "classification", "reason", "assessed_at"]
            )
            w.writerows(rows)
        print(f"assessments: {len(rows)} rows -> {CSV_OUT}")
        for pain_id in SIGNATURES:
            c = direct_only_counts(conn, pain_id)
            print(
                f"{pain_id}: DIRECT {c['n_direct']} | orgs {c['n_orgs']} "
                f"{c['orgs']} | authors {c['n_authors']} | "
                f"all {assessment_counts(conn, pain_id)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
