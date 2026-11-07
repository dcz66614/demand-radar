"""MVP B — T2 doc_trace. Filing/document extracts in, diff + source trace out."""
import csv
import difflib
from pathlib import Path


def load_csv(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"input not found: {path}")
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("empty input: no documents")
    for r in rows:
        if not r.get("title") or not r.get("source_url"):
            raise ValueError("each document needs title and source_url")
    return rows


def paragraphs(text):
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def diff_docs(a_text, b_text):
    """Returns list of (kind, line): kind in added/removed/unchanged."""
    a, b = paragraphs(a_text), paragraphs(b_text)
    if a == b:
        return [("unchanged", line) for line in a]
    out = []
    for line in difflib.unified_diff(a, b, lineterm=""):
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("+"):
            out.append(("added", line[1:]))
        elif line.startswith("-"):
            out.append(("removed", line[1:]))
        else:
            out.append(("unchanged", line.removeprefix(" ")))
    return out


def filter_docs(docs, keyword=None, source=None):
    return [d for d in docs
            if (keyword is None or keyword.lower() in f"{d.get('title','')} {d.get('text','')}".lower())
            and (source is None or source in d.get("source_url", ""))]


def export_csv(diffs, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kind", "line"])
        w.writerows(diffs)
    return Path(path)
