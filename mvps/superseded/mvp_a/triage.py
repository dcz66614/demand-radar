"""MVP A — T1 issue_triage. Public GitHub issues in, triage board out. No writes to GitHub."""
import csv
import json
from pathlib import Path

THEMES = {
    "api-agent": ("api", "agent", "token", "model", "stream", "litellm"),
    "convert": ("convert", "docx", "xlsx", "markdown", "export", "pdf"),
    "setup": ("setup", "install", "dependency", "import", "version"),
}


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"input not found: {path}")
    items, seen = [], set()
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if not d.get("title") or not d.get("url"):
            raise ValueError("each item needs title and url")
        if d["url"] in seen:
            continue
        seen.add(d["url"])
        items.append(d)
    if not items:
        raise ValueError("empty input: no items")
    return items


def classify(item):
    text = f"{item.get('title','')} {item.get('excerpt','')}".lower()
    theme = "other"
    for name, kws in THEMES.items():
        if any(k in text for k in kws):
            theme = name
            break
    if any(k in text for k in ("crash", "fails", "cannot", "broken", "wrong")):
        priority = "high"
    elif any(k in text for k in ("missing", "feature request", "slow")):
        priority = "medium"
    else:
        priority = "low"
    return {"theme": theme, "priority": priority}


def triage(items):
    out = []
    for it in items:
        c = classify(it)
        out.append({**it, "theme": c["theme"], "priority": c["priority"]})
    return out


def filter_items(items, theme=None, platform=None, priority=None):
    return [i for i in items
            if (theme is None or i.get("theme") == theme)
            and (platform is None or i.get("platform") == platform)
            and (priority is None or i.get("priority") == priority)]


def export_csv(items, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "url", "platform", "theme", "priority"])
        w.writeheader()
        for i in items:
            w.writerow({k: i.get(k, "") for k in ["title", "url", "platform", "theme", "priority"]})
    return Path(path)
