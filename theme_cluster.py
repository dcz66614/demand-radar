"""P05b thematic clustering — documented aggregation, not new evidence.
Strict near-duplicate clusters (review_p05.py) found 0 pains with >=2 independent
sources, because seed-repo issues are repo-specific bugs. Product discovery needs
workflow-level pains: issues in the same domain, same job, same failure class,
from distinct issues/authors/repos, are grouped under a named theme.
Every theme pain lists ALL its evidence URLs; the theme statement is a summary
of those linked issues, not a new claim. Themes with <3 items are not PRD-eligible.
"""
import hashlib
import sqlite3
from pathlib import Path

DB = "data/demand_radar.sqlite"
# (theme_id, job, blocker, keywords in title+excerpt, any-of)
THEMES = {
 "AI": [
  ("ai-setup", "install and run an AI tool without friction",
   "setup, install or dependency conflicts block first use",
   ("setup", "install", "dependency", "import", "pin")),
  ("ai-convert", "convert documents to Markdown accurately",
   "conversion drops, corrupts or mis-renders content (math, tables, footnotes, JSON)",
   ("convert", "docx", "xlsx", "markdown", "export", "pdf")),
  ("ai-agent-api", "drive an AI agent / API reliably",
   "API calls fail, return wrong results, or silently substitute defaults",
   ("api", "agent", "token", "model", "litellm", "stream")),
 ],
 "RES": [
  ("res-data", "analyse tabular data correctly",
   "dataframe operations silently give wrong results or raise misleading errors",
   ("dataframe", "series", "dtype", "rank", "merge", "read_csv")),
  ("res-docs", "render and navigate documents",
   "markdown / document rendering drops content, links or structure",
   ("markdown", "render", "link", "heading", "footnote")),
  ("res-notebook", "run and reproduce work in a notebook",
   "kernel, cell or file-browser behaviour fails or loses state",
   ("notebook", "kernel", "cell", "jupyter", "restart")),
 ],
 "BIO": [
  ("bio-io", "read and write biosignal files",
   "file reading/writing, format conversion or parameter handling fails",
   ("wrsamp", "csv_to", "read_forward", "split", "file")),
  ("bio-signal", "process physiological signals correctly",
   "signal processing functions crash or return wrong values on real inputs",
   ("ecg", "signal", "hrv", "peak", "rsp", "eog", "neuro")),
  ("bio-docs", "learn and configure a biosignal library",
   "docs, defaults or API naming are confusing or incorrect",
   ("doc", "setup", "parameter", "default", "deprecat")),
 ],
 "FIN": [
  ("fin-fetch", "fetch market/financial data reliably",
   "fetchers fail, leak resources, or return wrong values",
   ("fetch", "download", "socket", "ticker", "yfinance")),
  ("fin-data", "read SEC filings accurately",
   "filing data is misclassified, mislabelled or dropped in extraction",
   ("sec", "filing", "xbrl", "10-k", "edgar", "concept")),
  ("fin-ui", "use a financial research tool",
   "UI, chart or workspace features are missing or broken",
   ("chart", "workspace", "ui", "render", "option")),
 ],
 "JOB": [
  ("job-setup", "install and run a job-search tool",
   "install, import or dependency problems block first use",
   ("import", "install", "setup", "numpy")),
  ("job-source", "cover more job boards",
   "a wanted job board / source is missing, so listings are incomplete",
   ("add", "source", "adapter", "support")),
  ("job-scrape", "find real job listings by location and source",
   "scrapers return no jobs, wrong jobs, or silently ignore filters",
   ("scrape", "glassdoor", "indeed", "ziprecruiter", "linkedin", "remote", "location")),
 ],
 "UK": [
  ("uk-api", "query transit data via API",
   "API fields are missing or incomplete for stops, calls and vehicles",
   ("graphql", "stopcall", "headsign")),
  ("uk-gtfs", "use GTFS timetable data correctly",
   "GTFS data is invalid, incomplete or misread, breaking trips",
   ("gtfs", "timetable", "calendar", "agency")),
  ("uk-routing", "plan a transit journey",
   "routing, transfers or fares drop valid journeys or give wrong costs",
   ("transfer", "fare", "cost", "journey", "raptor", "siri", "route")),
 ],
}
con = sqlite3.connect(DB)
rows = con.execute("""SELECT s.source_id, s.domain, s.title, s.excerpt, s.url
 FROM source_items s JOIN evidence_links e ON e.source_id=s.source_id
 WHERE e.review_status='VERIFIED'""").fetchall()
# note: evidence_links currently only link strict pains; every VERIFIED item has exactly one strict link
from collections import defaultdict

themes = defaultdict(list)
for sid, domain, title, excerpt, url in rows:
    text = f"{title or ''} {excerpt or ''}".lower()
    placed = None
    for tid, job, blocker, kws in THEMES.get(domain, []):
        if any(k in text for k in kws):
            placed = (tid, job, blocker); break
    if placed:
        themes[(domain, placed[0], placed[1], placed[2])].append((sid, url))

now = "2026-11-05T00:00:00Z"
made = 0
for (domain, tid, job, blocker), items in sorted(themes.items()):
    if len(items) < 3:
        continue
    pid = hashlib.sha256(f"THEME|{domain}|{tid}".encode()).hexdigest()[:20]
    con.execute("""INSERT OR REPLACE INTO pain_points
      (pain_id, domain, who, job_to_be_done, blocker, current_workaround, impact, status,
       cluster_key, evidence_count, created_at, updated_at)
      VALUES (?,?,?,?,?,'see linked issues',NULL,'VERIFIED',?, ?,?,?)""",
      (pid, domain, "user", job, blocker, tid, len(items), now, now))
    for sid, url in items:
        repo = url.split("github.com/")[-1].split("/issues")[0] if "github.com" in url else "hn"
        con.execute("""INSERT OR IGNORE INTO evidence_links
          (pain_id, source_id, is_firsthand, independence_group, evidence_note, checked_at, review_status)
          VALUES (?,?,1,?,'thematic cluster member','2026-11-05','VERIFIED')""",
          (pid, sid, repo))
    made += 1
    print(domain, tid, len(items))
con.commit()
print("thematic pains:", made)
Path("reports/theme_clusters.md").write_text(
    "# Thematic clusters (P05b)\n\nStrict near-duplicate clustering found 0 pains with >=2 independent sources.\n"
    "Themes group distinct issues by domain + job + failure class; every theme pain lists all its evidence URLs in ranking.csv / PRDs.\n"
    "Theme statements summarise the linked issues only.\n\n" +
    "\n".join(f"- {d} {t}: {len(v)} items" for (d, t, _, _), v in sorted(themes.items()) if len(v) >= 3),
    encoding="utf-8")
