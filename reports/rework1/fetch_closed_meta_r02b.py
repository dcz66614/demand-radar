"""R02 Phase B retry: for closed issues still missing closed_at/state_reason,
retry search_issues using distinctive words from the live BODY (title words
proved too generic for several issues), with up to 3 attempts per issue.
Merges into reports/rework1/review_r02_raw_closed.json.
Read-only; no writes.
"""
import json
import re
import sqlite3
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/rework1/review_r02_raw_closed.json"
GH = "/opt/hatch/bin/github"
STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
        "is", "are", "when", "how", "add", "new", "bug", "fix", "error", "this",
        "that", "have", "has", "from", "not", "but", "you", "your", "please",
        "issue", "data", "using", "use", "which", "there", "here"}

raw = json.loads((ROOT / "reports/rework1/review_r02_raw_github.json").read_text())
issues = raw["issues"]
prev = json.loads(OUT.read_text())
meta = prev["meta"]
unmatched = prev["unmatched"]
con = sqlite3.connect(ROOT / "data/demand_radar.sqlite")
titles = {r[0]: r[1] for r in con.execute(
    "SELECT external_id, title FROM source_items WHERE platform='github'")}
closed = [r[0] for r in con.execute(
    "SELECT external_id FROM source_items WHERE platform='github'")
    if issues[r[0]]["state"] == "CLOSED"]
todo = [e for e in closed if e not in meta]
print(f"todo={len(todo)}", flush=True)


def keywords(text, n=6):
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9._-]{2,}", text or "")
             if w.lower() not in STOP]
    # prefer longer / distinctive words
    words.sort(key=len, reverse=True)
    return " ".join(words[:n])


still = []
for eid in todo:
    repo, num = eid.split("#")
    owner, name = repo.split("/")
    body = issues[eid].get("body") or ""
    queries = [keywords(body), keywords(titles[eid])]
    found = None
    for q in queries:
        if not q:
            continue
        for attempt in range(3):
            args = {"owner": owner, "repo": name, "query": q,
                    "fields": ["number", "title", "state", "state_reason",
                               "labels", "created_at", "updated_at",
                               "closed_at", "user"]}
            p = subprocess.run([GH, "call-read-tool", "--name", "search_issues",
                                "--arguments-json", json.dumps(args)],
                               check=False, capture_output=True, text=True, timeout=120)
            try:
                d = json.loads(p.stdout)
                data = json.loads(d["result"]["content"][0]["text"])
                for it in data.get("items", []):
                    if str(it.get("number")) == num:
                        found = it
                        break
                break  # parsed OK; stop retrying this query
            except Exception:
                time.sleep(5)
                continue
        if found:
            break
    if found:
        meta[eid] = {"closed_at": found.get("closed_at"),
                     "state_reason": found.get("state_reason"),
                     "labels": [lb.get("name") if isinstance(lb, dict) else str(lb)
                                for lb in found.get("labels", [])]}
        print(f"{eid} OK", flush=True)
    else:
        still.append({"eid": eid, "queries": queries})
        print(f"{eid} MISS", flush=True)

OUT.write_text(json.dumps({"meta": meta, "unmatched": still}, indent=1))
print(f"matched={len(meta)} still_unmatched={len(still)}", flush=True)
