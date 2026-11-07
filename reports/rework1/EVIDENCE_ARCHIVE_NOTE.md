# Evidence archive note — R02 raw GitHub scan (NOT shipped in the delivery ZIP)

The R02 raw live-scan file is too large to ship (19,992,213 bytes) and is
excluded from `demand-radar-rework1-2026-11-05.zip` by the R07 packaging rule.

- File (in the rework1 working tree only):
  `reports/rework1/review_r02_raw_github.json`
- Size: 19,992,213 bytes
- SHA-256: ac4a88d147c58cfa8ca07b550b10fbeb7a794dc7df07bb359b290f55593c5cbe
- Contents: raw `list_issues` responses for the 213 GitHub issues reviewed in
  R02 (6,048 issues scanned across 14 repos), as fetched 2026-11-05.
- What IS shipped instead: the 218-line review trail
  `reports/rework1/review_r02.jsonl` (one verdict + reason + live state +
  excerpt hash per source), `review_r02.md`, and the smaller raw files
  `review_r02_raw_hn.json`, `review_r02_raw_closed.json`,
  `review_r02_working.json`.
- The file is preserved unchanged in the rework1 working directory
  (`~/projects/demand-radar-rework1/`); it was not deleted, only excluded
  from the archive. Anyone with access to that working directory can verify
  the SHA-256 above against the file.
