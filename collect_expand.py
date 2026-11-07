"""P04 expansion — 3 waves, per-domain ~40 candidates, per-repo cap 35%.
GitHub first (per_page=100), HN fallback only with strict domain keywords.
Writes data/inbox/{DOMAIN}/batch1.jsonl (excluding pilot ids already in DB)."""
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
    "AI": ["microsoft/markitdown", "ServiceNow/AgentLab", "langchain-ai/langchain"],
    "RES": ["jupyterlab/jupyterlab", "microsoft/markitdown", "pandas-dev/pandas"],
    "BIO": ["neuropsychology/NeuroKit", "MIT-LCP/wfdb-python", "mne-tools/mne-python"],
    "FIN": ["dgunning/edgartools", "openbb-finance/OpenBB", "ranaroussi/yfinance"],
    "JOB": ["speedyapply/JobSpy", "microsoft/markitdown", "jupyterlab/jupyterlab"],
    "UK": ["planarnetwork/gb-transit", "opentripplanner/OpenTripPlanner", "jupyterlab/jupyterlab"],
}
# JOB/UK third repos are placeholders only if first two fail to fill; they will be
# filtered by strict domain keywords below, so off-domain issues are dropped.
DOMAIN_KW = {
    "AI": ("agent", "export", "markdown", "token", "model", "api", "convert"),
    "RES": ("notebook", "jupyter", "paper", "citation", "dataframe", "reproduc"),
    "BIO": ("ecg", "eeg", "signal", "hrv", "peak", "physio", "neuro"),
    "FIN": ("sec", "filing", "xbrl", "10-k", "concept", "ticker", "finance", "edgar"),
    "JOB": ("job", "glassdoor", "indeed", "ziprecruiter", "linkedin", "apply", "hiring", "resume"),
    "UK": ("gtfs", "transit", "trip", "route", "timetable", "fare", "transfer", "bus", "train"),
}
HN_KW = {
    "AI": ("agent", "export", "api"),
    "RES": ("notebook", "paper", "research"),
    "BIO": ("ECG", "signal", "health"),
    "FIN": ("SEC", "filing", "finance"),
    "JOB": ("job", "hiring", "internship"),
    "UK": ("train", "transit", "GTFS"),
}
ANGLES = ["manual", "bug", "fail", "cannot", "missing", "workaround", "confusing",
          "documentation", "setup", "integration", "sync", "export", "feature request", "error", "crash", "broken"]
FETCHED = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
TARGET = 40
failures = []
existing = set()
import sqlite3

con = sqlite3.connect("data/demand_radar.sqlite")
existing = {r[0] for r in con.execute("SELECT source_id FROM source_items")}
con.close()

def ok_text(text, domain):
    t = text.lower()
    if len(text.strip()) < 40:
        return False
    if not any(a in t for a in ANGLES):
        return False
    if not any(k.lower() in t for k in DOMAIN_KW[domain]):
        return False
    return True

for domain, repos in SEEDS.items():
    out, seen, per_repo = [], set(), {}
    cap = int(TARGET * 0.35)  # 14
    for repo in repos:
        if len(out) >= TARGET:
            break
        for page in (1, 2):
            if len(out) >= TARGET or per_repo.get(repo, 0) >= cap:
                break
            try:
                issues, _ = fetch_issues(repo, per_page=100, page=page)
            except Exception as e:
                failures.append([repo, "github", str(e), FETCHED]); break
            if not issues:
                break
            for iss in issues:
                if len(out) >= TARGET or per_repo.get(repo, 0) >= cap:
                    break
                text = f"{iss.get('title','')} {iss.get('body') or ''}"
                if not ok_text(text, domain):
                    continue
                try:
                    item = SourceItem.model_validate(from_github_issue(iss, domain, FETCHED))
                except Exception as e:
                    failures.append([iss.get("html_url", repo), "validate", str(e), FETCHED]); continue
                if item.source_id in existing or item.source_id in seen:
                    continue
                seen.add(item.source_id); per_repo[repo] = per_repo.get(repo, 0) + 1
                out.append(item.model_dump(mode="json"))
    # HN fallback, strict
    if len(out) < TARGET:
        try:
            for hn in fetch_items("askstories", limit=100, keywords=HN_KW[domain]):
                if len(out) >= TARGET: break
                text = f"{hn.get('title','')} {hn.get('text') or ''}"
                if not ok_text(text, domain): continue
                try:
                    d = from_hn_item(hn, domain, FETCHED)
                    if not d["url"].startswith("https://"):
                        d["url"] = f"https://news.ycombinator.com/item?id={hn['id']}"
                    item = SourceItem.model_validate(d)
                except Exception: continue
                if item.source_id in existing or item.source_id in seen: continue
                seen.add(item.source_id); out.append(item.model_dump(mode="json"))
        except Exception as e:
            failures.append([domain, "hackernews", str(e), FETCHED])
    p = ROOT / "data" / "inbox" / domain / "batch1.jsonl"
    p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out) + ("\n" if out else ""), encoding="utf-8")
    print(domain, len(out), "per_repo:", per_repo, "->", p)

with open(ROOT / "reports" / "source_failures.csv", "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerows(failures)
print("failures:", len(failures))
