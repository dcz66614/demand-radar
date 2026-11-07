"""P03 pilot collector — real public sources only, 5 per domain, GitHub first, HN fallback.
Run from project root with the venv active. Writes data/inbox/{DOMAIN}/pilot.jsonl
and reports/source_failures.csv. Unknown fields are null, never invented."""
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, "src")
from demand_radar.collectors.github_issues import fetch_issues
from demand_radar.collectors.hackernews import fetch_items
from demand_radar.extract import from_github_issue, from_hn_item
from demand_radar.models import SourceItem

ROOT = Path(".")
SEEDS = {
    "AI": ["microsoft/markitdown", "ServiceNow/AgentLab"],
    "RES": ["jupyterlab/jupyterlab", "microsoft/markitdown"],
    "BIO": ["neuropsychology/NeuroKit", "MIT-LCP/wfdb-python"],
    "FIN": ["dgunning/edgartools", "openbb-finance/OpenBB"],
    "JOB": ["speedyapply/JobSpy"],
    "UK": ["planarnetwork/gb-transit", "opentripplanner/OpenTripPlanner"],
}
HN_KEYWORDS = {
    "AI": ("agent", "export", "api", "model"),
    "RES": ("notebook", "paper", "citation", "research"),
    "BIO": ("ECG", "signal", "health"),
    "FIN": ("SEC", "filing", "stock", "finance"),
    "JOB": ("internship", "job", "sponsorship", "hiring"),
    "UK": ("train", "bus", "GTFS", "fare", "transport"),
}
ANGLES = ["manual", "bug", "fail", "cannot", "missing", "workaround", "confusing",
          "documentation", "setup", "integration", "sync", "export", "feature request", "error"]
FETCHED = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
failures = []


def matches(text: str) -> bool:
    t = text.lower()
    return any(a in t for a in ANGLES)


def main():
    for domain, repos in SEEDS.items():
        out, seen = [], set()
        for repo in repos:
            if len(out) >= 5:
                break
            try:
                issues, _ = fetch_issues(repo, per_page=30, page=1)
            except Exception as e:
                failures.append([repo, "github", str(e), FETCHED])
                continue
            for iss in issues:
                if len(out) >= 5:
                    break
                text = f"{iss.get('title','')} {iss.get('body') or ''}"
                if not matches(text):
                    continue
                try:
                    d = from_github_issue(iss, domain, FETCHED)
                    item = SourceItem.model_validate(d)
                except Exception as e:
                    failures.append([iss.get("html_url", repo), "github-validate", str(e), FETCHED])
                    continue
                if item.source_id in seen:
                    continue
                seen.add(item.source_id)
                out.append(item.model_dump(mode="json"))
        if len(out) < 5:
            try:
                for hn in fetch_items("askstories", limit=60, keywords=HN_KEYWORDS[domain]):
                    if len(out) >= 5:
                        break
                    try:
                        d = from_hn_item(hn, domain, FETCHED)
                        if not d["url"].startswith("https://"):
                            d["url"] = f"https://news.ycombinator.com/item?id={hn['id']}"
                        item = SourceItem.model_validate(d)
                    except Exception as e:
                        failures.append([str(hn.get("id")), "hn-validate", str(e), FETCHED])
                        continue
                    if item.source_id in seen:
                        continue
                    seen.add(item.source_id)
                    out.append(item.model_dump(mode="json"))
            except Exception as e:
                failures.append([domain, "hackernews", str(e), FETCHED])
        p = ROOT / "data" / "inbox" / domain / "pilot.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + ("\n" if out else ""), encoding="utf-8")
        print(domain, len(out), "->", p)
    with open(ROOT / "reports" / "source_failures.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["host", "source", "error", "time"])
        w.writerows(failures)
    print("failures:", len(failures))


if __name__ == "__main__":
    main()
