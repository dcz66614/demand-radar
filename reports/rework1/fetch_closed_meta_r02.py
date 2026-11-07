"""R02 Phase B: for each CLOSED GitHub issue, get closed_at/state_reason via
authenticated GitHub MCP search_issues (title-keyword query, filtered by
issue number). list_issues does not expose closed_at/state_reason.
Writes reports/rework1/review_r02_raw_closed.json.
Read-only; no writes.
"""
import json
import re
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/rework1/review_r02_raw_closed.json"
GH = "/opt/hatch/bin/github"

raw = json.loads((ROOT / "reports/rework1/review_r02_raw_github.json").read_text())
issues = raw["issues"]
con = sqlite3.connect(ROOT / "data/demand_radar.sqlite")
rows = con.execute(
    "SELECT external_id, title FROM source_items WHERE platform='github'").fetchall()
closed = [(eid, title) for eid, title in rows if issues[eid]["state"] == "CLOSED"]
print(f"closed={len(closed)}", flush=True)

STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
        "is", "are", "when", "how", "add", "new", "bug", "fix", "error"}
meta = {}
unmatched = []
for eid, title in closed:
    repo, num = eid.split("#")
    owner, name = repo.split("/")
    words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]*", title or "")
             if w.lower() not in STOP][:5]
    q = " ".join(words) if words else title
    args = {"owner": owner, "repo": name, "query": q,
            "fields": ["number", "title", "state", "state_reason", "labels",
                       "created_at", "updated_at", "closed_at", "user"]}
    p = subprocess.run([GH, "call-read-tool", "--name", "search_issues",
                        "--arguments-json", json.dumps(args)],
                       check=False, capture_output=True, text=True, timeout=120)
    found = None
    try:
        d = json.loads(p.stdout)
        data = json.loads(d["result"]["content"][0]["text"])
        for it in data.get("items", []):
            if str(it.get("number")) == num:
                found = it
                break
    except Exception as exc:
        unmatched.append({"eid": eid, "error": str(exc)[:200]})
        continue
    if found is None:
        unmatched.append({"eid": eid, "query": q})
    else:
        meta[eid] = {"closed_at": found.get("closed_at"),
                     "state_reason": found.get("state_reason"),
                     "labels": [lb.get("name") for lb in found.get("labels", [])]}
    print(f"{eid} {'OK' if found else 'MISS'}", flush=True)

OUT.write_text(json.dumps({"meta": meta, "unmatched": unmatched}, indent=1))
print(f"matched={len(meta)} unmatched={len(unmatched)}", flush=True)
print("wrote", OUT, flush=True)
