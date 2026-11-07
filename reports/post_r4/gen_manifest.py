"""Generate reports/post_r4/MANIFEST.sha256 for the current tree.

Usage (from the post-r4 work dir):
    python3 reports/post_r4/gen_manifest.py

Lists every file in the tree except the MANIFEST itself and the
packaging exclusions (same rules as build_zip.py), as
"<sha256>  ./<relative-path>" lines, sorted by path. Run BEFORE
build_zip.py so the zip contains the manifest that describes it.
"""

import hashlib
from pathlib import Path

EXCLUDED_DIRS = {".venv", ".venv-real", "__pycache__", ".pytest_cache", ".ruff_cache"}
EXCLUDED_FILES = {"reports/rework1/review_r02_raw_github.json"}


def _excluded(rel) -> bool:
    # Any path part that IS an excluded dir, or a build-artifact dir
    # whose name ENDS with .egg-info (e.g. src/demand_radar.egg-info/).
    return any(part in EXCLUDED_DIRS or part.endswith(".egg-info") for part in rel.parts)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = root / "reports" / "post_r4" / "MANIFEST.sha256"
    lines = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel == manifest.relative_to(root):
            continue
        if _excluded(rel):
            continue
        if rel.as_posix() in EXCLUDED_FILES:
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{digest}  ./{rel.as_posix()}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {manifest} ({len(lines)} entries)")


if __name__ == "__main__":
    main()
