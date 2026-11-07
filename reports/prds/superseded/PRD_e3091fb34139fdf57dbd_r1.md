# PRD (R05 rewrite) — e3091fb34139fdf57dbd

- Domain: FIN
- Job to be done: fetch market/financial data reliably
- Blocker: fetchers fail, leak resources, or return wrong values
- Score: 70 (corrected R03/R04 scoring; see score_reason below)
- Score reason: E=20 (3 indep orgs, 12 distinct authors, 16 raw URLs) job='fetch market/financial data reliably' S=20 (blocker 'fetchers fail, leak resources, or return wrong values' matches failure keywords ['wrong']) F=15 (recorded workaround exists ('see linked issues'); feasibility indicated but NOT validated — F capped at 15 of 20 max) G=10 (checked 2 alternatives, none fully solves (see competitor_checks)) L=5 (no transfer/reuse evidence in record; L capped at 5 (minimum) — no cross-domain reuse claim made) | cross-org corroborated
- Independent organisations: 3; VERIFIED evidence: 16 links (14 closed, 2 open)

## User task
As an investor or researcher fetching market and financial data for a symbol, get the right values, completely, without the fetcher leaking resources or corrupting its cache.

## Evidence (VERIFIED sources only, with quotations/paraphrases)
- [closed] [dgunning/edgartools] https://github.com/dgunning/edgartools/issues/1855
  - ixt-sec:exchnameen raises TransformError for 10 of the 21 exchange names in the SEC transformation registry
  - Quoted/paraphrased from the post: "## Issue Type <!-- Select the primary category for this issue by putting an 'x' in the brackets --> - [ ] Data Quality Issue (incorrect financial values, missing data) - [x] XBRL Parsing Issue (statement rendering, concept mapping) - [ ] Filing Access Issue (download failures, attachment problems..."
- [open] [openbq-org/OpenBB] https://github.com/openbq-org/OpenBB/issues/7645
  - SEC standardized financials: per-share fields empty for issuers that file only class-dimensioned facts (COKE, BRK-B, UHAL)
  - Quoted/paraphrased from the post: "## Describe the bug `get_standardized_financials` (openbb-sec) returns `None` for `basic_eps`, `diluted_eps`, `weighted_ave_basic_shares_os` and `weighted_ave_diluted_shares_os` for issuers that tag these concepts only with `us-gaap:StatementClassOfStockAxis`. The SEC `companyfacts` API the fetch..."
- [closed] [openbq-org/OpenBB] https://github.com/openbq-org/OpenBB/issues/7650
  - openbb_sec Form 4 (insider trading) fetcher leaks sockets in CLOSE_WAIT under concurrent downloads
  - Quoted/paraphrased from the post: "## Summary `openbb_core.provider.utils.helpers.amake_request()` opens a brand-new `aiohttp.ClientSession` for every individual HTTP request rather than reusing one across a batch. `openbb_sec`'s Form 4 (insider trading) fetcher (`openbb_sec/utils/form4.py::download_data()`) calls this once per fi..."
- [closed] [openbq-org/OpenBB] https://github.com/openbq-org/OpenBB/issues/7651
  - openbb_sec Form 4 (insider trading) fetcher leaks sockets in CLOSE_WAIT under concurrent downloads
  - Quoted/paraphrased from the post: "## Summary `openbb_core.provider.utils.helpers.amake_request()` opens a brand-new `aiohttp.ClientSession` for every individual HTTP request rather than reusing one across a batch. `openbb_sec`'s Form 4 (insider trading) fetcher (`openbb_sec/utils/form4.py::download_data()`) calls this once per fi..."
- [closed] [openbq-org/OpenBB] https://github.com/openbq-org/OpenBB/issues/7655
  - openbb_sec company facts fetcher never actually caches: re-downloads full companyfacts.json for every statement type
  - Quoted/paraphrased from the post: "## Summary `openbb_sec.utils.company_facts.get_standardized_financials()` fetches SEC's full `companyfacts` JSON per call via a fresh `aiohttp_client_cache.CachedSession(expire_after=3600 * 6)`, but since no `cache=` argument is passed, `aiohttp_client_cache` defaults to a brand-new, empty, in-pr..."
- [closed] [openbq-org/OpenBB] https://github.com/openbq-org/OpenBB/issues/7656
  - openbb_sec Form 4 fetcher's shared on-disk cache corrupts under concurrent calls
  - Quoted/paraphrased from the post: "## Summary `openbb_sec/utils/form4.py::download_data()` uses a single, shared on-disk cache file (`sec_form4.db` / `sec_form4.db.gz`, one file total, not keyed per symbol or per call) with a lifecycle that decompresses it at the start of every call and compresses-then-deletes the raw file at the ..."
- [open] [openbq-org/OpenBB] https://github.com/openbq-org/OpenBB/issues/7813
  - openbb-cboe 2.0.0 CboeOptionsChains: strptime() argument 1 must be str, not float on digit-root option symbols (live SPY payload)
  - Quoted/paraphrased from the post: "## Summary `openbb-cboe` 2.0.0's `CboeOptionsChainsFetcher.transform_data` raises `TypeError: strptime() argument 1 must be str, not float` on current live payloads from CBOE's delayed-quote endpoint, for any symbol whose chain now contains a contract with a digit-bearing option root (observed on..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/2930
  - Missing 7-28 data
  - Quoted/paraphrased from the post: "I was running session = curl_requests.Session(impersonate="chrome101") stock = yf.Ticker("QQQ", session=session) qqq = stock.history(start = start, interval=interval, raise_errors=True) with start = "2025-11-4", then when i print(qqq.index[-1], qqq.index[-2]), it returns, 2026-07-29 00:00:00-04:0..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/2931
  - Valuations greatly differ between info and valuation
  - Quoted/paraphrased from the post: "### Describe bug Valuations from yfinance.info appears to be significantly different from the web site and yfinance.valuation. According to https://finance.yahoo.com/quote/MO/key-statistics/ Current Enterprise Value/EBITDA 12.18 According to yfinance.info Enterprise Value/EBITDA 9.25 According to..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/2937
  - Implied Volatility Calculation Bug for Deep Out-of-the-Money Options
  - Quoted/paraphrased from the post: "### Describe bug When fetching option chain data for certain tickers, yfinance returns unrealistic implied volatility (IV) values for deep out-of-the-money (OTM) options. These IV values often exceed 500-2000%, which is impossible in real markets (where IV typically ranges between 0-300%). The is..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/2939
  - Missing Data
  - Quoted/paraphrased from the post: "### Describe bug Data is missing for some symbols from XETRA on 7-31. Please add a method to check Stock Exchange Trading Days. ### Simple code that reproduces your problem ```python import yfinance as yf # Define the ticker symbol ticker_symbol = "SDF.DE" print(ticker_symbol) # Create a Ticker o..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/2963
  - Analyst upgrades downgrades data not flowing after 8/25
  - Quoted/paraphrased from the post: "Hi, I use yfinance library to fetch analyst upgrades and downgrades on stocks. After 8/25, I am not seeing any new data flowing in. The APIs seem to be working fine, and there is no errors reported as such, but no new data is flowing in. So, it seems to be a Yahoo side issue. Are others also seei..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/2964
  - Missing daily session for 2026-08-28 across multiple tickers/indices (^GSPC, ^IXIC, IWM, RSP, ANET)
  - Quoted/paraphrased from the post: "### Description Historical daily data (`interval='1d'`) is missing the session for **Friday, 2026-08-28** across multiple unrelated tickers and indices. The returned data jumps straight from Thursday 2026-08-27 to Monday 2026-08-31. This is **not** a market closure — the S&P 500 traded normally t..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/2997
  - ^VXN and ^VXD return no intraday data while ^VIX works
  - Quoted/paraphrased from the post: "Description Since October 2026 I am unable to retrieve intraday data for the CBOE volatility indices ^VXN and ^VXD. ^VIX works normally at the same time. Environment: Windows 11 Python 3.13.14 yfinance 1.7.0 requests 2.34.2 Results: ^VXN: yf.download(period="1d", interval="1m") -> possibly delist..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/3004
  - get_news() returns [] for every symbol: /xhr/ncp now answers 404
  - Quoted/paraphrased from the post: "### Describe bug `Ticker.get_news()` returns an empty list for every symbol. The endpoint it posts to, `https://finance.yahoo.com/xhr/ncp?queryRef=...&serviceKey=ncp_fin`, now answers `404` with the body `{"message":"Not Found"}`. That body is valid JSON, so `get_news()` finds no `data.tickerStre..."
- [closed] [ranaroussi/yfinance] https://github.com/ranaroussi/yfinance/issues/3033
  - 1.8.0 is not on PyPI: the upload built 1.7.0
  - Quoted/paraphrased from the post: "The 1.8.0 release's publish run failed: https://github.com/ranaroussi/yfinance/actions/runs/41703874919 `yfinance/version.py` at tag 1.8.0 still says `version = "1.7.0"`, so the job built `yfinance-1.7.0.tar.gz` and `yfinance-1.7.0-py3-none-any.whl`, and PyPI rejected the upload with `400 Bad Req..."

## Actual workaround and impact
No workaround is documented in the record. Reporters file the bug; for the worst case there is nothing to work around with — yfinance get_news() returns [] for every symbol because the Yahoo endpoint it posts to now answers 404 (#3004), and analyst upgrades/downgrades simply stop flowing after 8/25 with no error reported (#2963).

Measured in the evidence: the daily session for Friday 2026-08-28 is missing across ^GSPC, ^IXIC, IWM, RSP and ANET although the S&P 500 traded normally that day — the series jumps straight from 2026-08-27 to 2026-08-31 (#2964); valuations differ between yfinance.info and the Yahoo website (Enterprise Value/EBITDA 12.18 on the site vs 9.25 from info, #2931); the openbb_sec Form 4 fetcher leaks sockets in CLOSE_WAIT under concurrent downloads (#7650, filed twice by one author and counted once); the company-facts fetcher never actually caches — it re-downloads the full companyfacts.json for every statement type (#7655); the shared on-disk Form 4 cache corrupts under concurrent calls (#7656); ^VXN and ^VXD return no intraday data while ^VIX works (#2997); implied volatility for deep out-of-the-money options comes back at 500–2000%, impossible in real markets (#2937).

## Competitor checks (R04, checked 2026-11-05, 0 solve the pain)
- pandas-datareader (0.11.2.dev2) — https://pandas-datareader.readthedocs.io/en/latest/ (checked 2026-11-05)
  - Observed capability: pandas-datareader docs: 'pandas-datareader 0.11.2.dev2+g9a3e2fe documentation' - remote data readers. HTTP 200, 2026-11-05.
  - Gap vs this pain: Many of its data sources are deprecated or broken; same failure class (fetchers fail or return wrong values) as the reported pain.
- yfinance (1.8.0) — https://github.com/ranaroussi/yfinance (checked 2026-11-05)
  - Observed capability: GitHub repo: 'Download market data from Yahoo! Finance's API'. HTTP 200, 2026-11-05.
  - Gap vs this pain: Does not solve the pain: the reported fetcher failures, resource leaks and wrong values are filed against yfinance itself. It is the failing tool, not a fix.

## Sample input
Two recorded reproducers. (1) yfinance #2964: yf download of ^GSPC at interval 1d spanning 2026-08-27 to 2026-08-31. (2) OpenBB #7650: concurrent Form 4 (insider trading) downloads for one symbol.

## Expected output
(1) The 2026-08-28 session is present in the returned frame — or, if the source omits it, the result flags the session as missing from the source instead of silently jumping 08-27 to 08-31. (2) Concurrent Form 4 downloads complete and the process socket count returns to its pre-run baseline (no CLOSE_WAIT leak).

## Acceptance tests
1. ^GSPC 1d history spanning 2026-08-27 to 2026-08-31 contains the 2026-08-28 session; if the source omits it, the result flags the missing session instead of silently jumping 08-27 to 08-31 (#2964).
2. Concurrent Form 4 downloads for one symbol complete and the process socket count returns to its pre-run baseline — no CLOSE_WAIT leak (#7650).
3. Two consecutive company-facts fetches for the same symbol issue one network download of companyfacts.json, not two (#7655).
4. Concurrent calls sharing the Form 4 on-disk cache each return correct data, with no corruption (#7656).
5. get_news() for a symbol either returns items or reports the endpoint failure explicitly; an empty list with no error is a failure (#3004).

## Caveats and stop conditions
- 14 of 16 VERIFIED evidence items are CLOSED — the most closed-heavy of the five qualifying pains. Closed does not mean solved; R06 must re-check the live state of the cited issues before building on any one of them.
- OpenBB #7650/#7651 are the same report filed twice by one author, 9 minutes apart; counted once.
- yfinance #3033 (release 1.8.0 not on PyPI because the publish built 1.7.0) is a release-packaging report inside the theme, not a fetch failure.
- Closed evidence items are counted as evidence of a real problem, not as proof the problem is solved: R02 did not check resolution from comments.
- If the linked sources are withdrawn or the blocker is fixed upstream, this PRD is withdrawn.
