import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trace import diff_docs, export_csv, filter_docs, load_csv, paragraphs

import pytest

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample.csv"


def test_load_sample():
    docs = load_csv(SAMPLE)
    assert len(docs) == 5
    assert all(d["source_url"].startswith("https://") for d in docs)


def test_load_missing():
    with pytest.raises(FileNotFoundError):
        load_csv("nope.csv")


def test_load_empty(tmp_path):
    p = tmp_path / "e.csv"; p.write_text("doc_id,title,source_url,version,text\n")
    with pytest.raises(ValueError):
        load_csv(p)


def test_load_missing_source(tmp_path):
    p = tmp_path / "b.csv"; p.write_text("doc_id,title,source_url,version,text\n1,x,,v1,hello\n")
    with pytest.raises(ValueError):
        load_csv(p)


def test_paragraphs():
    assert paragraphs("a\n\n  b \n") == ["a", "b"]


def test_diff_added_removed():
    d = diff_docs("alpha\nbeta", "alpha\ngamma")
    kinds = [k for k, _ in d]
    assert "removed" in kinds and "added" in kinds


def test_diff_identical():
    d = diff_docs("same\nlines", "same\nlines")
    assert all(k == "unchanged" for k, _ in d) and len(d) == 2


def test_diff_empty():
    assert diff_docs("", "") == []


def test_filter_keyword():
    docs = load_csv(SAMPLE)
    f = filter_docs(docs, keyword="SEC")
    assert f and all("sec" in (d["title"] + d["text"]).lower() for d in f)


def test_filter_no_match():
    docs = load_csv(SAMPLE)
    assert filter_docs(docs, keyword="zzz-no-such-word") == []


def test_filter_source():
    docs = load_csv(SAMPLE)
    f = filter_docs(docs, source="github.com/dgunning")
    assert f and all("dgunning" in d["source_url"] for d in f)


def test_export_csv(tmp_path):
    d = diff_docs("a\nb", "a\nc")
    p = export_csv(d, tmp_path / "diff.csv")
    text = p.read_text()
    assert "added" in text and "removed" in text
    assert text.count("\n") == len(d) + 1
