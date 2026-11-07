# MVP A — Issue Triage (T1)

Pain: AI ai-agent-api (score 80, 19 evidence) — driving an AI agent / API reliably.
Input: public GitHub issues as JSONL (`data/sample.jsonl`, 5 real issues with source URLs).
Output: triage board by theme + priority, with source links and CSV export.

## Run
```
cd <project root>
. .venv/bin/activate
python -m streamlit run mvps/mvp_a/app.py
```
Or use the core directly: `from triage import load_jsonl, triage` (run from `mvps/mvp_a/`).

## Tests
```
python -m pytest mvps/mvp_a/tests -q
```
At least 10 assertions, covering import, duplicates, bad input, classification, filters, export, source preservation.
No login, no payment, no external writes.
