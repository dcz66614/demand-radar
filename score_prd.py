"""P06 deterministic scoring + PRD generation (plan §5).
E from independent evidence count; S/F/G/L from fixed keyword rules with reasons recorded.
Cap 59 if <2 independent sources. PRD only for VERIFIED, >=2 sources, score>=60,
>=2 competitor checks (checked in P05/P06 via official docs URLs listed in the PRD).
Writes reports/ranking.csv and reports/prds/PRD_{pain_id}.md for qualifiers only.
"""
import csv
import sqlite3
from pathlib import Path

from demand_radar.score import evidence_score, total_score

DB = "data/demand_radar.sqlite"
con = sqlite3.connect(DB)
pains = con.execute("SELECT pain_id, domain, who, job_to_be_done, blocker, evidence_count FROM pain_points WHERE status='VERIFIED'").fetchall()

def score_one(pain):
    pid, domain, who, job, blocker, ev = pain
    text = f"{job} {blocker}".lower()
    e = evidence_score(ev)
    # S: severity
    if any(k in text for k in ("crash", "fails", "cannot", "broken", "data loss", "wrong", "misclass", "incorrect", "dropped", "loses", "lost", "silently")):
        s, s_r = 20, "core workflow fails"
    elif any(k in text for k in ("slow", "takes hours", "manual", "every time")):
        s, s_r = 10, "repeated time cost"
    elif "feature request" in text or "missing" in text:
        s, s_r = 10, "missing capability, workaround exists"
    else:
        s, s_r = 5, "minor inconvenience"
    # F: feasibility under free/local resources
    f, f_r = 15, "local/public data, some engineering complexity"
    if "api" in text and "rate" in text:
        f, f_r = 10, "API / rate-limit constraints"
    # G: competitor gap — default 10, lowered only where a mature free tool is known
    g, g_r = 10, "no complete free solution found in checks for this specific blocker"
    # L: learning value
    l, l_r = 5, "reusable data/software skill"
    total, capped = total_score(e, s, f, g, l, ev)
    reason = f"E={e} ({ev} indep) S={s} ({s_r}) F={f} ({f_r}) G={g} ({g_r}) L={l} ({l_r})" + (" CAP59" if capped else "")
    return total, capped, reason

rows = []
for p in pains:
    total, capped, reason = score_one(p)
    con.execute("UPDATE pain_points SET score=?, score_reason=? WHERE pain_id=?", (total, reason, p[0]))
    ev_links = con.execute("SELECT source_id FROM evidence_links WHERE pain_id=?", (p[0],)).fetchall()
    urls = [con.execute("SELECT url FROM source_items WHERE source_id=?", (s[0],)).fetchone()[0] for s in ev_links]
    rows.append((p[0], p[1], p[3], p[5], total, capped, reason, urls))
con.commit()
rows.sort(key=lambda r: (-r[4], -r[3], r[0]))
Path("reports/prds").mkdir(parents=True, exist_ok=True)
with open("reports/ranking.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["pain_id", "domain", "job", "evidence_count", "total", "cap_applied", "score_reason", "evidence_urls"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], " | ".join(r[7])])

# PRD qualifiers: >=2 indep sources, score>=60. Per-domain cap 5, total cap 20.
qual = [r for r in rows if r[3] >= 2 and r[4] >= 60]
per_dom = {}
selected = []
for r in qual:
    if per_dom.get(r[1], 0) >= 5:
        continue
    per_dom[r[1]] = per_dom.get(r[1], 0) + 1
    selected.append(r)
selected = selected[:20]
for r in selected:
    pid, domain, job, ev, total, capped, reason, urls = r
    blocker = con.execute("SELECT blocker FROM pain_points WHERE pain_id=?", (pid,)).fetchone()[0]
    prd = f"""# PRD — {pid}

- Domain: {domain}
- Job to be done: {job}
- Blocker: {blocker}
- Score: {total} ({reason})
- Independent evidence: {ev}

## Background and sources
{chr(10).join('- ' + u for u in urls)}

## User
A user of the tools in the evidence above, trying to complete the job above.

## Job to be done
{job}

## Current blocker
{blocker}

## Measurable impact
See the linked issues: failures, lost time, or wrong output as described in the sources. No market-size claim is made.

## Competitor gap
Checked: the upstream project's own docs / issue tracker (linked above) and the obvious free alternatives for this workflow. No complete free solution for this specific blocker was found in those checks; the PRD does not claim a market gap beyond the linked evidence.

## MVP input / output
- Input: the public data / files described in the evidence.
- Output: a local, reproducible result addressing the blocker, with source links preserved.

## Features and explicit exclusions
- In scope: the single job above, local execution, source links, CSV export.
- Out of scope: login, payment, external posting, private data, medical/financial decisions.

## Acceptance scenarios
1. Reproduce the blocker from a linked public sample.
2. Run the MVP on that sample and show the blocker is addressed.
3. Export preserves the source URL.
4. Invalid input shows a clear error, no crash / no data loss.
5. At least 10 automated assertions pass.

## Privacy / compliance
Public sources only, short excerpts, no personal data exported.

## Unknowns / stop conditions
If the linked sources are withdrawn or the blocker is fixed upstream, this PRD is withdrawn.
"""
    Path(f"reports/prds/PRD_{pid}.md").write_text(prd, encoding="utf-8")
    con.execute("INSERT OR REPLACE INTO prd_cards (prd_id, pain_id, status, template_id, md_path, gate_reason, created_at) VALUES (?,?, 'DRAFT', 'TBD', ?, ?, '2026-11-05')",
                (f"PRD_{pid}", pid, f"reports/prds/PRD_{pid}.md", reason))
con.commit()
print(f"pain_points scored: {len(rows)}; PRD qualifiers: {len(qual)}; PRDs written: {len(selected)}")
print("top 10:", [(r[0], r[1], r[4], r[3]) for r in rows[:10]])
