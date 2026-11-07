"""R02 Phase A: fetch live GitHub issue data via authenticated GitHub MCP
(call-read-tool list_issues, per repo OPEN+CLOSED, cursor pagination, stops
as soon as all needed issue numbers for that repo are found, max 15 pages
per state) and HN items via Firebase.
Writes reports/rework1/review_r02_raw_github.json and review_r02_raw_hn.json.
NOTE: `github call-read-tool issue_read` is NOT in the reviewed read-only set
(it errors: use call-tool so it receives write-capable approval). list_issues
is the reviewed read-only path returning number/title/body/state/user/labels/
created_at/updated_at. closed_at/state_reason are fetched in Phase B via
search_issues (title-keyword query, filtered by issue number).
Read-only towards GitHub/HN; no writes, no posts.
"""
import json
import sqlite3
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_GH = ROOT / "reports/rework1/review_r02_raw_github.json"
OUT_HN = ROOT / "reports/rework1/review_r02_raw_hn.json"
GH = "/opt/hatch/bin/github"

con = sqlite3.connect(ROOT / "data/demand_radar.sqlite")
needed = {}
for (eid,) in con.execute("SELECT external_id FROM source_items WHERE platform='github'"):
    repo, num = eid.split("#")
    needed.setdefault(repo, set()).add(int(num))
repos = sorted(needed)
print(f"repos={len(repos)} needed={sum(len(v) for v in needed.values())}", flush=True)

all_issues = {}
errors = []
for repo in repos:
    owner, name = repo.split("/")
    missing = set(needed[repo])
    for state in ("OPEN", "CLOSED"):
        if not missing:
            break
        after = None
        pages = 0
        while missing and pages < 15:
            args = {"owner": owner, "repo": name, "state": state, "perPage": 100,
                    "fields": ["number", "title", "body", "state", "user", "labels",
                               "created_at", "updated_at"]}
            if after:
                args["after"] = after
            p = subprocess.run([GH, "call-read-tool", "--name", "list_issues",
                                "--arguments-json", json.dumps(args)],
                               check=False, capture_output=True, text=True, timeout=120)
            pages += 1
            if p.returncode != 0:
                errors.append({"repo": repo, "state": state, "stderr": p.stderr[:300]})
                break
            d = json.loads(p.stdout)
            if not d.get("ok") or d.get("result", {}).get("isError"):
                errors.append({"repo": repo, "state": state, "result": str(d)[:300]})
                break
            data = json.loads(d["result"]["content"][0]["text"])
            for it in data["issues"]:
                all_issues[f"{repo}#{it['number']}"] = it
                missing.discard(it["number"])
            pi = data.get("pageInfo", {})
            if not pi.get("hasNextPage"):
                break
            after = pi.get("endCursor")
        print(f"{repo} {state}: pages={pages} still_missing={sorted(missing)[:8]}", flush=True)
    if missing:
        errors.append({"repo": repo, "missing_after_15_pages": sorted(missing)})
print(f"fetched issues={len(all_issues)} errors={len(errors)}", flush=True)
OUT_GH.write_text(json.dumps({"issues": all_issues, "errors": errors}, indent=1))
print("wrote", OUT_GH, flush=True)

hn_ids = [r[0] for r in con.execute(
    "SELECT external_id FROM source_items WHERE platform='hackernews'")]
hn = {}
for hid in hn_ids:
    with urllib.request.urlopen(
            f"https://hacker-news.firebaseio.com/v0/item/{hid}.json",
            timeout=30) as resp:
        hn[hid] = json.loads(resp.read())
    print("HN", hid, hn[hid].get("type"), (hn[hid].get("title") or "")[:50], flush=True)
OUT_HN.write_text(json.dumps(hn, indent=1))
print("wrote", OUT_HN, flush=True)
