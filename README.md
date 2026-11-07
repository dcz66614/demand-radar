# Demand Radar

Evidence-driven product-opportunity discovery + local MVP incubation.
Standalone project — not part of the P series, no P number.
Local Python/SQLite/Streamlit, zero extra paid infrastructure.
Sources: public GitHub Issues + Hacker News (+ official docs for competitor checks). Reddit disabled by default.

## Run (exact commands — verified from a fresh extract in REWORK1 R01)
```
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m demand_radar init
python -m demand_radar score
python -m demand_radar report --stage final
python -m pytest -q
python -m streamlit run app/streamlit_app.py
```
`python -m pip install -e .` is required: this is a `src/`-layout project.
`score` recomputes every VERIFIED pain from the DB and writes `reports/ranking.csv`.
`export` is VERIFIED-only by default; add `--all` to include REJECTED rows.

## REWORK1
Original delivery (2026-11-05) was audited REWORK_REQUIRED / NOT_ADOPTED.
Rework lives in `~/projects/demand-radar-rework1/`, original preserved unchanged
at `~/projects/demand-radar/` (ZIP SHA-256 963568deaff04e778123d17cd4f5cdaba7f9957212d248079240c12588f2b261).
See `reports/rework1/STATUS.md` and `Demand_Radar_Muse_Rework_2026-11-05.md` (R01–R07).

See `Demand_Radar_Execution_Plan_v1.0.md` for the frozen execution plan (P00–P10).
