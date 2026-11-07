PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS source_items (
  source_id TEXT PRIMARY KEY,
  platform TEXT NOT NULL CHECK(platform IN ('github','hackernews','official','reddit_authorized')),
  external_id TEXT NOT NULL,
  url TEXT NOT NULL,
  canonical_url TEXT NOT NULL,
  author_key TEXT,
  title TEXT,
  excerpt TEXT NOT NULL,
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  source_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'FETCHED',
  UNIQUE(platform, external_id)
);
CREATE TABLE IF NOT EXISTS pain_points (
  pain_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL CHECK(domain IN ('AI','RES','BIO','FIN','JOB','UK')),
  who TEXT NOT NULL,
  job_to_be_done TEXT NOT NULL,
  blocker TEXT NOT NULL,
  current_workaround TEXT,
  impact TEXT,
  status TEXT NOT NULL DEFAULT 'CANDIDATE'
     CHECK(status IN ('CANDIDATE','PENDING_REVIEW','VERIFIED','REJECTED','SOURCE_LIMITED')),
  cluster_key TEXT,
  evidence_count INTEGER NOT NULL DEFAULT 0, -- RAW unique URLs; never independence
  independent_evidence_count INTEGER NOT NULL DEFAULT 0, -- R03: distinct author/context/org groups
  score INTEGER,
  score_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence_links (
  pain_id TEXT NOT NULL REFERENCES pain_points(pain_id),
  source_id TEXT NOT NULL REFERENCES source_items(source_id),
  is_firsthand INTEGER NOT NULL DEFAULT 0,
  independence_group TEXT NOT NULL,
  evidence_note TEXT NOT NULL,
  checked_at TEXT,
  review_status TEXT NOT NULL DEFAULT 'PENDING',
  PRIMARY KEY(pain_id, source_id)
);
CREATE TABLE IF NOT EXISTS competitor_checks (
  check_id TEXT PRIMARY KEY,
  pain_id TEXT NOT NULL REFERENCES pain_points(pain_id),
  product TEXT NOT NULL,
  checked_url TEXT NOT NULL,
  does_solve INTEGER,
  gaps TEXT,
  checked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prd_cards (
  prd_id TEXT PRIMARY KEY,
  pain_id TEXT NOT NULL UNIQUE REFERENCES pain_points(pain_id),
  status TEXT NOT NULL DEFAULT 'DRAFT',
  template_id TEXT NOT NULL,
  md_path TEXT NOT NULL,
  gate_reason TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run_events (
  event_id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL,
  agent_role TEXT NOT NULL,
  event_type TEXT NOT NULL,
  detail_json TEXT NOT NULL,
  event_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sources_domain ON source_items(domain, published_at);
CREATE INDEX IF NOT EXISTS idx_pain_domain_status ON pain_points(domain, status);
CREATE INDEX IF NOT EXISTS idx_evidence_independence ON evidence_links(independence_group);
