"""Hacker News collector — official Firebase API, bounded window, local keyword filter."""
from __future__ import annotations

import requests

UA = "DemandRadarResearch/1.0"
BASE = "https://hacker-news.firebaseio.com/v0"


def fetch_items(story_kind: str = "askstories", limit: int = 30, keywords: tuple[str, ...] = (),
                session: requests.Session | None = None):
    s = session or requests.Session()
    ids = s.get(f"{BASE}/{story_kind}.json", headers={"User-Agent": UA}, timeout=(5, 20)).json()[:limit]
    out = []
    for i in ids:
        item = s.get(f"{BASE}/item/{i}.json", headers={"User-Agent": UA}, timeout=(5, 20)).json()
        if not item or item.get("deleted") or item.get("dead"):
            continue
        text = f"{item.get('title','')} {item.get('text','')}".lower()
        if keywords and not any(k.lower() in text for k in keywords):
            continue
        out.append(item)
    return out
