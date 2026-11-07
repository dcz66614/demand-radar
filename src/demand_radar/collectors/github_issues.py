"""GitHub Issues collector — read-only, official REST API, PRs excluded, 429 respected."""
from __future__ import annotations

import time

import requests

UA = "DemandRadarResearch/1.0"
TIMEOUT = (5, 20)


def fetch_issues(repo: str, per_page: int = 30, page: int = 1, session: requests.Session | None = None):
    """Returns (issues, rate_info). issues excludes pull_request objects."""
    s = session or requests.Session()
    url = f"https://api.github.com/repos/{repo}/issues"
    for attempt in range(4):
        r = s.get(url, params={"state": "all", "per_page": per_page, "page": page},
                  headers={"User-Agent": UA, "Accept": "application/vnd.github+json"}, timeout=TIMEOUT)
        if r.status_code == 429 or (r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0"):
            wait = int(r.headers.get("Retry-After", "60"))
            time.sleep(min(wait, 60))
            continue
        r.raise_for_status()
        rate = {"remaining": r.headers.get("X-RateLimit-Remaining"), "reset": r.headers.get("X-RateLimit-Reset")}
        items = [x for x in r.json() if "pull_request" not in x]
        return items, rate
    raise RuntimeError("github rate limited after retries")
