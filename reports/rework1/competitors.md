# R04 — Real competitor evidence (2026-11-05)

Status: DONE. 34 checks, 17 PRD candidates × 2, 0 UNKNOWN, all gates met.
Machine-readable trail: `reports/rework1/competitor_checks.jsonl` (one line per check).
DB: `data/demand_radar.sqlite`, table `competitor_checks` = 34 rows.
Code: `src/demand_radar/competitors.py` (insert / count / gate helpers).
Tests: `tests/test_competitors.py` — 7 passed (fail on old code: no `competitors` module).

## Method

Each alternative was checked against its official home/docs/repo page on
2026-11-05 by direct fetch (curl GET, HTTP status + page title recorded in
the JSONL; two pages needed a browser fetch — see verification notes).
Version is recorded only where obtainable (GitHub `releases/latest`
redirect tag, or a version string in the docs page title); otherwise the
record honestly says "not stated on checked page". `does_solve=1` would mean
the alternative fully solves the pain — **no check has does_solve=1**.
Every gap is a concrete, observed limitation, not a generic sentence.

## Verification notes (all URLs re-checked against the exact URLs in the JSONL)

- 29/31 distinct URLs returned HTTP 200 by curl on the final pass.
- SEC EDGAR API docs (`sec.gov/edgar/sec-api-documentation`): curl got
  403 "Request Rate Threshold Exceeded" (SEC bot protection), but the page
  was fetched and read in full via browser (title "EDGAR Application
  Programming Interfaces (APIs)", XBRL endpoints documented). Recorded
  http_status 200 with verified_via noting the browser fetch.
- Bus Open Data Service (`bus-data.dft.gov.uk`): curl 200 on first pass,
  403 on re-check (rate-limit flap); page fetched and read via browser
  (title "Bus Open Data Service", timetables/bus location/fares across
  England, free open data). Same note in the record.
- Valhalla: `valhalla.openstreetmap.org` was unreachable from this VM
  (curl exit 000, retried twice), so the official GitHub Pages docs
  `valhalla.github.io/valhalla/` (HTTP 200, "Valhalla Docs") are the
  verified source. The unreachable host is recorded, not hidden.
- JobSpy: repo moved from `cullenwatson/JobSpy` to `speedyapply/JobSpy`
  (curl followed the redirect); the final URL is the recorded one, v1.4.1.
- Redirects followed and recorded: LangSmith docs
  (`docs.smith.langchain.com` → `docs.langchain.com/langsmith/observability`),
  pipx (`pipx.pypa.io` → `/stable/`), TfL API (`api.tfl.gov.uk` →
  `api-portal.tfl.gov.uk`), pandas-datareader (→ `/en/latest/`).
- DuckDB docs pages are JS redirects, so the official GitHub repo
  `github.com/duckdb/duckdb` (HTTP 200) is the recorded source.
- LiteLLM docs are JS-rendered (empty title); capability grounded by
  grepping the fetched HTML: "retries, fallbacks, and the cost of each call".

## Per-candidate checks

### 0b7adcf63ec0f2075fab — FIN, use a financial research tool (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| OpenBB | not stated on checked page | https://openbb.co/ | "Build your own financial workspace" — free investment research platform | The reported UI/workspace failures are filed against OpenBB itself; same bug class, not a fix | 0 |
| TradingView | not stated (web app) | https://www.tradingview.com/ | "Track All Markets" — charting, screeners, market data | Charting/screener, not an open research workbench; advanced features are paid tiers | 0 |

### 28ccf8f8701bb84bf95b — FIN, read SEC filings accurately (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| Arelle | not stated on checked page | https://arelle.org/ | Open-source XBRL validator/processor | Validates XBRL; does not fix misclassification/mislabelling/dropped data in extraction pipelines | 0 |
| SEC EDGAR APIs (data.sec.gov) | not versioned (REST API) | https://www.sec.gov/edgar/sec-api-documentation | Official REST JSON APIs: submissions history + XBRL facts (companyconcept/companyfacts/frames), no auth | Raw facts JSON only; no classification/labelling layer — consumer must build the extraction that gets it wrong | 0 |

### 3955670369ee96d7b5d6 — JOB, find real job listings by location and source (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| JobSpy | v1.4.1 | https://github.com/speedyapply/JobSpy | Jobs scraper library for LinkedIn, Indeed, Glassdoor, ZipRecruiter, etc. | Same failure class as the pain: scrapers break / return no or wrong jobs when sites change | 0 |
| Adzuna API | not stated on checked page | https://developer.adzuna.com/ | Job search API | API coverage + free-tier limits; a data source, not a scraper fix; paid beyond free tier | 0 |

### 46c4f297fe1033b95248 — RES, render and navigate documents (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| MarkItDown | v0.1.9 | https://github.com/microsoft/markitdown | Python tool converting files/office docs to Markdown | Converter, not a viewer/navigator; conversion dropping content is the pain class itself | 0 |
| Pandoc | not stated on checked page | https://pandoc.org/ | Universal document converter | Converter, not a viewer/navigator; math/table/footnote fidelity limits remain | 0 |

### 4bb734fac7245033d327 — BIO, process physiological signals correctly (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| NeuroKit2 | 0.2.14.dev115 | https://neuropsychology.github.io/NeuroKit/ | Neurophysiological data analysis library | The reported crashes/wrong values are filed against NeuroKit itself — it is the failing tool | 0 |
| HeartPy | 1.2.5 | https://github.com/paulvangentcom/heartrate_analysis_python | Python heart-rate analysis package (PPG/ECG) | Narrow scope (heart rate only), not a general physiological-signal processor | 0 |

### 5d10a3095668d0928fe2 — UK, use GTFS timetable data correctly (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| MobilityData GTFS Validator | v8.0.1 | https://github.com/MobilityData/gtfs-validator | Canonical GTFS validator for schedule (static) files | Validation only: reports bad data, does not fix it or stop consumers misreading it | 0 |
| Transitland | not stated on checked page | https://www.transit.land/ | Aggregates bus/train/subway feeds for software builders | Aggregation, not validation/repair: invalid GTFS still reaches consumers | 0 |

### 6513d051954cbe1b5027 — AI, drive an AI agent / API reliably (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| LiteLLM | not stated on checked page | https://docs.litellm.ai/ | Retries, fallbacks and cost tracking across LLM providers (verified in fetched HTML) | Retries do not fix wrong results or silent substitution of model defaults; no result validation | 0 |
| LangSmith | not stated on checked page | https://docs.langchain.com/langsmith/observability | Tracing, monitoring and evaluation of LLM calls | Observability only: records failures after they happen, does not prevent them | 0 |

### 6a7abaf0c0655b39aa36 — AI, install and run an AI tool without friction (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| uv | not stated on checked page | https://docs.astral.sh/uv/ | Fast Python package/project manager (Astral) | General env management; does not fix a specific tool's own install/import conflicts | 0 |
| pipx | not stated on checked page | https://pipx.pypa.io/stable/ | Installs Python apps in isolated environments | Isolation helps generally; does not repair the tool's own install/import problems | 0 |

### 908f662d8a749944fb20 — RES, run and reproduce work in a notebook (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| JupyterLab | not stated on checked page | https://jupyter.org/ | Notebook UI + kernel ecosystem | The reported kernel/cell/file-browser failures are filed against Jupyter itself | 0 |
| Marimo | not stated on checked page | https://docs.marimo.io/ | Reactive Python notebook | Different execution model; requires migrating notebooks, does not fix Jupyter failures for existing work | 0 |

### bdef2d35b09f45a0e94a — RES, analyse tabular data correctly (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| Polars | not stated on checked page | https://docs.pola.rs/ | DataFrame library (user guide) | Different API, not a pandas drop-in; wrong-result/misleading-error classes can occur in any engine | 0 |
| DuckDB | not stated on checked page | https://github.com/duckdb/duckdb | In-process analytical SQL database | SQL engine, not a pandas drop-in; different semantics rather than a fix for dataframe behaviour | 0 |

### c37a39eaf9fb6a9805a2 — AI, convert documents to Markdown accurately (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| Docling | not stated on checked page | https://docling-project.github.io/docling/ | Document conversion library (IBM) | Conversion fidelity (tables/math/footnotes/JSON) is the pain class; another converter, same failure mode | 0 |
| Pandoc | not stated on checked page | https://pandoc.org/ | Universal document converter | Own math/table/footnote fidelity limits; does not fix conversion that drops/corrupts content | 0 |

### cd021eac3c93ed0d2de1 — BIO, read and write biosignal files (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| pyEDFlib | v0.1.42 | https://github.com/holgern/pyedflib | Read/write EDF+/BDF+ files | EDF+/BDF+ only; other biosignal formats and parameter-handling failures remain | 0 |
| MNE-Python | 1.13.2 | https://mne.tools/stable/index.html | EEG/MEG data I/O and analysis ("MNE 1.13.2 documentation") | Heavy dependency, limited format coverage; reported file I/O failures are partly against MNE itself | 0 |

### da75a85dbf1cb9f121cc — UK, plan a transit journey (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| OpenTripPlanner | not stated on checked page | https://www.opentripplanner.org/ | Open-source multimodal journey planner consuming GTFS | Needs valid GTFS/correct data; does not fix routing that drops valid journeys or wrong fares | 0 |
| Valhalla | not stated on checked page | https://valhalla.github.io/valhalla/ | Open-source routing engine (docs) | Routing engine consuming transit data; transfer/fare logic limited, does not repair bad input data | 0 |

### df72dcf35dc9db2c24b5 — JOB, install and run a job-search tool (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| pipx | not stated on checked page | https://pipx.pypa.io/stable/ | Isolated Python app installs | Does not fix the tool's own install/import/dependency problems | 0 |
| Docker | not stated on checked page | https://docs.docker.com/ | Container platform | Containerising wraps the failure rather than fixing import/dependency bugs inside the image; adds Docker setup friction | 0 |

### e3091fb34139fdf57dbd — FIN, fetch market/financial data reliably (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| yfinance | 1.8.0 | https://github.com/ranaroussi/yfinance | Download market data from Yahoo! Finance API | The reported fetcher failures, leaks and wrong values are filed against yfinance itself | 0 |
| pandas-datareader | 0.11.2.dev2 | https://pandas-datareader.readthedocs.io/en/latest/ | Remote data readers for pandas | Many sources deprecated/broken; same failure class as the pain | 0 |

### e5fd57ab0f0c20381e36 — JOB, cover more job boards (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| JobSpy | v1.4.1 | https://github.com/speedyapply/JobSpy | Multi-board jobs scraper library | A library to build with, not board coverage for an existing tool; shares scraper-breakage class | 0 |
| SerpApi Google Jobs API | not stated on checked page | https://serpapi.com/google-jobs-api | Google Jobs API (paid) | Provides Google Jobs results, not the missing board itself; adds a paid dependency | 0 |

### fcaac0fde92e53b85f19 — UK, query transit data via API (gate: PASS, 2/2)

| Product | Version | URL | Observed capability | Gap vs pain | Solves? |
|---|---|---|---|---|---|
| TfL Unified API | not stated on checked page | https://api-portal.tfl.gov.uk/ | Unified API for London transport | London-only; cannot supply UK-wide transit API fields | 0 |
| Bus Open Data Service (BODS) | not stated on checked page | https://www.bus-data.dft.gov.uk/ | UK bus open data: timetables, bus location, fares across England | Bus only; data quality varies by operator; does not fix missing/incomplete API fields across modes | 0 |

## Score impact (CLI re-run, exit 0)

`python -m demand_radar score` — scored 221 pains. Exactly the 17
candidates changed, each G 0 → 10 (+10), except the two capped at 59:

| pain_id | before | after |
|---|---|---|
| 0b7adcf63ec0f2075fab | 60 | 70 |
| 4bb734fac7245033d327 | 60 | 70 |
| 6513d051954cbe1b5027 | 60 | 70 |
| cd021eac3c93ed0d2de1 | 60 | 70 |
| e3091fb34139fdf57dbd | 60 | 70 |
| 28ccf8f8701bb84bf95b | 55 | 65 |
| 3955670369ee96d7b5d6 | 55 | 65 |
| da75a85dbf1cb9f121cc | 55 | 65 |
| 6a7abaf0c0655b39aa36 | 50 | 60 |
| 908f662d8a749944fb20 | 50 | 59 (CAP59, <2 indep groups) |
| bdef2d35b09f45a0e94a | 50 | 59 (CAP59, <2 indep groups) |
| 5d10a3095668d0928fe2 | 40 | 50 |
| c37a39eaf9fb6a9805a2 | 40 | 50 |
| e5fd57ab0f0c20381e36 | 40 | 50 |
| fcaac0fde92e53b85f19 | 40 | 50 |
| 46c4f297fe1033b95248 | 35 | 45 |
| df72dcf35dc9db2c24b5 | 35 | 45 |

204 non-candidate pains unchanged (G=0, no competitor checks — R05 must
not treat them as G=10). Top 5 after re-score: 70 (five pains).

## Flag for R05 (scoring limitation, not fixed here — R03 owns scoring)

`score_components` awards G=10 for >=2 `competitor_checks` rows
regardless of `does_solve`. All 34 checks here are does_solve=0, so this
limitation had no effect on these scores — but if a future check records
does_solve=1 (an alternative fully solves the pain), the current scorer
would still award G=10. R05/R03 should make G depend on does_solve before
relying on it for qualification.

## UNKNOWN cases

None. Every candidate found two verifiable real alternatives; no
failed-search trail was needed. If R05 re-ranks and new candidates appear,
they must get the same treatment (or an UNKNOWN trail that blocks the gate).
