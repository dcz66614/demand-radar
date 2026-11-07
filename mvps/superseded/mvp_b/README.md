# MVP B — Document Trace (T2)

Pain: FIN fin-data (score 80, 9 evidence) — reading SEC filings accurately.
Input: public filing-issue extracts as CSV (`data/sample.csv`, 5 real issues with source URLs).
Output: document list with source links, keyword filter, and a diff view between two documents, with CSV export.

## Run
```
cd <project root>
. .venv/bin/activate
python -m streamlit run mvps/mvp_b/app.py
```
Or use the core directly: `from trace import load_csv, diff_docs` (run from `mvps/mvp_b/`).

## Tests
```
python -m pytest mvps/mvp_b/tests -q
```
At least 10 assertions, covering import, bad input, diff added/removed, filters, export, source preservation.
No login, no payment, no external writes. No investment advice is given.
