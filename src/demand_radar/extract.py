"""Turn a raw GitHub issue / HN item into a SourceItem dict. No invented fields."""
from __future__ import annotations

from datetime import UTC, datetime


def _excerpt(text: str) -> str:
    t = " ".join((text or "").split())
    return (t[:297] + "...") if len(t) > 300 else t


def _iso(dt_str: str | None) -> str | None:
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def from_github_issue(issue: dict, domain: str, fetched_at: str) -> dict:
    body = issue.get("body") or ""
    title = issue.get("title") or ""
    return {
        "platform": "github",
        "external_id": f"{issue['repository_url'].split('repos/')[-1]}#{issue['number']}",
        "url": issue["html_url"],
        "title": title[:200],
        "excerpt": _excerpt(body or title),
        "published_at": _iso(issue.get("created_at", "").replace("+00:00", "Z") if issue.get("created_at") else None)
        or _iso(issue.get("created_at")),
        "fetched_at": fetched_at,
        "domain": domain,
        "source_type": "firsthand_issue",
        "who": "user",
        "job_to_be_done": title[:200],
        "blocker": _excerpt(body or title),
        "current_workaround": None,
        "impact": None,
        "evidence_note": "Issue describes the exact failed output / request",
        "review_status": "PENDING",
    }


def from_hn_item(item: dict, domain: str, fetched_at: str) -> dict:
    title = item.get("title") or ""
    text = item.get("text") or ""
    published = None
    if item.get("time"):
        published = datetime.fromtimestamp(item["time"], tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "platform": "hackernews",
        "external_id": str(item["id"]),
        "url": item.get("url") or f"https://news.ycombinator.com/item?id={item['id']}",
        "title": title[:200],
        "excerpt": _excerpt(text or title),
        "published_at": published,
        "fetched_at": fetched_at,
        "domain": domain,
        "source_type": "firsthand_issue",
        "who": "user",
        "job_to_be_done": title[:200],
        "blocker": _excerpt(text or title),
        "current_workaround": None,
        "impact": None,
        "evidence_note": "HN post describes a concrete workflow blocker",
        "review_status": "PENDING",
    }
