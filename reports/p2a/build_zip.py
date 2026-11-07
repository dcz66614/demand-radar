"""P2-A packaging script (deterministic zip build).

Usage (from the post-r4 work dir):
    python3 reports/p2a/build_zip.py <output-zip-path>

- Single top-level directory `demand-radar-p2a/`.
- Excludes: .venv/, .venv-real/, __pycache__/, .pytest_cache/,
  .ruff_cache/, *.egg-info, reports/rework1/review_r02_raw_github.json
  (the ~20 MB raw evidence file; documented in-package by
  reports/rework1/EVIDENCE_ARCHIVE_NOTE.md).
- Zip entries are sorted by path and carry a FIXED timestamp
  (1980-01-01 00:00:00 UTC), so a rebuild from the same tree is
  byte-identical — unlike R3/R4, where the pass-1 -> final diff had
  to be verified by per-file content comparison because entry
  timestamps differed. The MANIFEST (content hashes) is unaffected.
- MANIFEST.sha256 (reports/p2a/MANIFEST.sha256) is generated
  separately by gen_manifest.py BEFORE this script runs; it lists
  every file in the tree except itself, with paths relative to the
  project root ("./..."), so `sha256sum -c
  reports/p2a/MANIFEST.sha256` from the project root verifies it.
"""

import sys
import zipfile
from pathlib import Path

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
EXCLUDED_DIRS = {".venv", ".venv-real", "__pycache__", ".pytest_cache", ".ruff_cache"}
EXCLUDED_FILES = {"reports/rework1/review_r02_raw_github.json"}


def _excluded(rel) -> bool:
    # Any path part that IS an excluded dir, or a build-artifact dir
    # whose name ENDS with .egg-info (e.g. src/demand_radar.egg-info/).
    return any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in rel.parts)


def collect(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if _excluded(rel):
            continue
        if rel.as_posix() in EXCLUDED_FILES:
            continue
        out.append(p)
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out_path = Path(sys.argv[1])
    files = collect(root)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            rel = p.relative_to(root)
            arc = Path("demand-radar-p2a") / rel
            info = zipfile.ZipInfo(str(arc), date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, p.read_bytes())
    print(f"wrote {out_path} ({len(files)} files)")


if __name__ == "__main__":
    main()
