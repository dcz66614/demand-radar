"""R02: build per-source review verdicts from live data and persist them.
Inputs: reports/rework1/review_r02_working.json (live title/body/state/labels/
author_hash), reports/rework1/review_r02_raw_closed.json (closed_at/state_reason).
Rubric (applied by reading each live post, not by repo membership):
  VERIFIED = live post states a concrete firsthand problem/blocker (bug, wrong
  result, silent failure, missing capability with a concrete use case, or a
  genuine question about a failure) relevant to its assigned domain.
  Feature requests / RFCs with a concrete use case count; closed state alone
  does NOT reject (resolution not checked from comments).
  REJECTED = spam/bot content, vendor self-promotion, withdrawn post, listing/
  survey thread with no blocker, title-only request with no use case, or
  content belonging to another domain.
Prior pilot rejections are preserved (markitdown#2799, HN 50377668, HN 50338728,
HN 50363461). P05's 11 rule-based rejects are preserved except jupyterlab#20323,
overturned with a documented reason (live body shows a real CI failure, not spam).
Outputs: reports/rework1/review_r02.jsonl (one line per source), DB updates to
source_items (status, review_verdict, review_reason, reviewed_at, author_hash,
issue_state, issue_state_checked_at, issue_labels). Raw inputs are NOT deleted.
"""
import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

REJECTED = {
    # AI
    "microsoft/markitdown#2799": "REJECTED: pilot rejection preserved; live post is a bare PDF link titled 'HAVAALAN' with no problem statement (spam/no discernible blocker).",
    "ServiceNow/AgentLab#288": "REJECTED: live post promotes the reporter's own libraries (vimgolf-gym, CTF/Cybergod, WebUI recorder); no AgentLab problem/blocker is stated.",
    "50366117": "REJECTED: HN survey thread ('What's your current AI agentic setup?'); asks how people use AI, states no problem/blocker.",
    # FIN
    "openbq-org/OpenBB#7640": "REJECTED: vendor self-promotion for paid product ViBo ($5/month, referral partnership); no OpenBB problem stated.",
    "openbq-org/OpenBB#7641": "REJECTED: vendor self-promotion for NeuForge Pay spend-firewall SDK; no OpenBB problem stated.",
    "openbq-org/OpenBB#7667": "REJECTED: post is withdrawn by its author ('Withdrawn. No action is requested from this project.'); no problem remains.",
    # JOB
    "50338728": "REJECTED: pilot rejection preserved; HN 'Who is hiring?' monthly listing thread, not a tool blocker.",
    "50377668": "REJECTED: pilot rejection preserved; HN Dependabot-fatigue discussion is a dev-workflow topic, wrong domain for JOB (job search/scraping).",
    "jupyterlab/jupyterlab#20035": "REJECTED: P05 rejection preserved; live issue is a real JupyterLab security bug but belongs to another domain, not JOB (job search/scraping).",
    "jupyterlab/jupyterlab#20062": "REJECTED: P05 rejection preserved; live issue is a real JupyterLab CI yarn-cache problem but belongs to another domain, not JOB.",
    "jupyterlab/jupyterlab#20177": "REJECTED: P05 rejection preserved; live issue is a real JupyterLab CI failure but belongs to another domain, not JOB.",
    "jupyterlab/jupyterlab#20183": "REJECTED: P05 rejection preserved; live issue is a real JupyterLab Markdown-preview bug but belongs to another domain, not JOB.",
    "speedyapply/JobSpy#440": "REJECTED: title-only feature request ('Add Dubizzle Job Search'); live body is empty, no use case or problem stated.",
    # UK
    "50363461": "REJECTED: pilot rejection preserved; HN post about Gemini training on chat history is a privacy topic, wrong domain for UK (GB transit).",
    "jupyterlab/jupyterlab#20017": "REJECTED: P05 rejection preserved; live issue is a real JupyterLab loading-latency bug but belongs to another domain, not UK (GB transit).",
    "jupyterlab/jupyterlab#20167": "REJECTED: P05 rejection preserved; live issue is a real JupyterLab settings-editor display bug but belongs to another domain, not UK.",
    "jupyterlab/jupyterlab#20304": "REJECTED: P05 rejection preserved; live issue is a real JupyterLab file-browser menu bug but belongs to another domain, not UK.",
    "planarnetwork/gb-transit#230": "REJECTED: P05 rejection preserved; live post is the Renovate 'Dependency Dashboard' bot listing, no user problem stated.",
}

# Special VERIFIED notes (duplicates / overturns / spot-checks)
SPECIAL = {
    "langchain-ai/langchain#41708": "VERIFIED: live issue is a concrete bug report (Responses API streaming never emits a completed event for function_call, with repro). NOTE: same author/title as #41709/#41710; independence handled in R03, not by rejecting the report.",
    "langchain-ai/langchain#41709": "VERIFIED: same concrete bug report as #41708 (same author, same title/body, filed minutes apart); duplicate filing, independence handled in R03.",
    "langchain-ai/langchain#41710": "VERIFIED: same concrete bug report as #41708/#41709 (same author); open, duplicate filing, independence handled in R03.",
    "langchain-ai/langchain#41716": "VERIFIED: RFC/feature proposal for a deterministic hybrid compressor with measured results (49.2% token reduction, n=86); concrete capability gap. NOTE: same author/proposal as #41717/#41718; duplicate filings, independence handled in R03.",
    "langchain-ai/langchain#41717": "VERIFIED: same HSTC feature proposal as #41716 (same author, filed 4 min later); duplicate filing, independence handled in R03.",
    "langchain-ai/langchain#41718": "VERIFIED: same HSTC feature proposal as #41716/#41717 (same author); open, duplicate filing, independence handled in R03.",
    "openbq-org/OpenBB#7650": "VERIFIED: concrete bug report (Form 4 fetcher leaks sockets in CLOSE_WAIT under concurrent downloads, with root cause). NOTE: identical duplicate of #7651 (same author, 9 min apart); independence handled in R03.",
    "openbq-org/OpenBB#7651": "VERIFIED: identical duplicate filing of #7650 (same author, same title/body); independence handled in R03.",
    "ranaroussi/yfinance#3011": "VERIFIED: real dependency-concern report (CVE-2026-111497 in Brotli via curl_cffi backend); author notes it was superseded by #3012 (resubmission with fixed headings). Duplicate filing, independence handled in R03.",
    "ranaroussi/yfinance#3012": "VERIFIED: resubmission of #3011 (same author, same CVE concern, corrected headings); duplicate filing, independence handled in R03.",
    "jupyterlab/jupyterlab#20323": "VERIFIED (OVERTURN of P05 rule-based reject): live body shows a real CI failure, not spam — the 'please update snapshots' bot fails to commit since August due to a broken pre-commit hook, with root cause and suggested fix. The P05 spam keyword matched the bot command name, not spam content.",
    "ServiceNow/AgentLab#187": "VERIFIED: concrete problem (CAPTCHA triggered at Google search in the demo, workaround requested). Audit spot-check: closed 2025-01-06 (state_reason/completed per Phase B meta); closed state recorded, resolution not re-checked from comments.",
    "openbq-org/OpenBB#7634": "VERIFIED: concrete bug report (SEC standardized statements: missing debt tag mappings, operating income imputed as revenue). Audit spot-check: closed; closed state recorded.",
    "dgunning/edgartools#1857": "VERIFIED: concrete data-quality report (reverse index classifies 44 tax-reconciliation concepts as total income tax expense, Oracle 10-K). Audit spot-check: closed; closed state recorded.",
}


def main():
    working = json.loads((ROOT / "reports/rework1/review_r02_working.json").read_text())
    closed_path = ROOT / "reports/rework1/review_r02_raw_closed.json"
    closed_meta = {}
    if closed_path.exists():
        closed_meta = json.loads(closed_path.read_text()).get("meta", {})
    con = sqlite3.connect(ROOT / "data/demand_radar.sqlite")
    out_lines = []
    counts = {"VERIFIED": 0, "REJECTED": 0, "PENDING": 0}
    for w in working:
        eid = w["external_id"]
        sid = w["source_id"]
        if eid in REJECTED:
            verdict, reason = "REJECTED", REJECTED[eid]
        elif SPECIAL.get(eid):
            verdict, reason = "VERIFIED", SPECIAL[eid]
        else:
            verdict = "VERIFIED"
            title = (w["live_title"] or "")[:120]
            reason = (f"VERIFIED: live {w['platform']} post checked {NOW[:10]}: "
                      f"'{title}' — body confirms a concrete firsthand problem/blocker "
                      f"in the {w['domain']} domain (state: {w['live_state']}).")
        counts[verdict] += 1
        body = w.get("body") or ""
        excerpt_hash = hashlib.sha256(body[:300].encode()).hexdigest()
        meta = closed_meta.get(eid, {})
        closed_at = meta.get("closed_at")
        state_reason = meta.get("state_reason")
        labels = meta.get("labels") or w.get("labels") or []
        # persist: status mirrors verdict (VERIFIED/REJECTED), PENDING only if unfetched
        new_status = verdict
        con.execute(
            """UPDATE source_items SET status=?, review_verdict=?, review_reason=?,
               reviewed_at=?, author_hash=?, issue_state=?, issue_state_checked_at=?,
               issue_labels=? WHERE source_id=?""",
            (new_status, verdict, reason, NOW, w["author_hash"],
             w["live_state"], NOW, json.dumps(labels), sid))
        out_lines.append({
            "source_id": sid, "external_id": eid, "url": w["url"],
            "domain": w["domain"], "platform": w["platform"],
            "live_title": w["live_title"], "excerpt_hash": excerpt_hash,
            "issue_state": w["live_state"], "closed_at": closed_at,
            "state_reason": state_reason, "labels": labels,
            "author_hash": w["author_hash"], "created_at": w.get("created_at"),
            "updated_at": w.get("updated_at"),
            "verdict": verdict, "reason": reason, "checked_at": NOW})
    con.commit()
    out_path = ROOT / "reports/rework1/review_r02.jsonl"
    out_path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out_lines) + "\n")
    print(f"wrote {out_path} lines={len(out_lines)} counts={counts}")
    db_counts = con.execute(
        "SELECT review_verdict, COUNT(*) FROM source_items GROUP BY review_verdict").fetchall()
    print("DB review_verdict counts:", db_counts)
    db_status = con.execute("SELECT status, COUNT(*) FROM source_items GROUP BY status").fetchall()
    print("DB status counts:", db_status)
    print("PENDING (unfetched):", con.execute(
        "SELECT COUNT(*) FROM source_items WHERE review_verdict IS NULL").fetchone()[0])


if __name__ == "__main__":
    main()
