# Environment check — P00

- Date (UTC): 2026-11-05
- Execution surface: Muse personal Agent VM (Linux, /home/hatch)
- Python: 3.12.3
- git: 2.43.0
- Disk: 147G free of 150G
- Memory at check: ~235 MB free / 728 MB available of 8 GB (tight — noted)
- Network: GitHub API https://api.github.com/repos/microsoft/markitdown -> HTTP 200
- Network: Hacker News API https://hacker-news.firebaseio.com/v0/askstories.json -> HTTP 200
- venv: .venv created, pip upgraded
- Deps installed (pip freeze in requirements-lock.txt): requests, pydantic, pandas, streamlit, rapidfuzz, PyYAML, pytest 9.2.0, ruff 0.17.3 — all import OK
- No GitHub login assumed; public read-only API only. Reddit: DISABLED_PERMISSION.
- Project root: $HOME/projects/demand-radar (new, isolated, no P number)
