import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from triage import classify, export_csv, filter_items, load_jsonl, triage

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample.jsonl"


def test_load_sample():
    items = load_jsonl(SAMPLE)
    assert len(items) == 5
    assert all(i["url"].startswith("https://") for i in items)


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_jsonl("nope.jsonl")


def test_load_bad_item(tmp_path):
    p = tmp_path / "bad.jsonl"; p.write_text('{"title": "x"}\n')
    with pytest.raises(ValueError):
        load_jsonl(p)


def test_load_empty(tmp_path):
    p = tmp_path / "empty.jsonl"; p.write_text("")
    with pytest.raises(ValueError):
        load_jsonl(p)


def test_dedupe_by_url(tmp_path):
    p = tmp_path / "d.jsonl"
    p.write_text('{"title":"a","url":"https://example.com/1"}\n{"title":"a","url":"https://example.com/1"}\n')
    assert len(load_jsonl(p)) == 1


def test_classify_api_high():
    c = classify({"title": "API crashes", "excerpt": "call fails"})
    assert c["priority"] == "high" and c["theme"] == "api-agent"


def test_classify_convert():
    c = classify({"title": "convert DOCX fails", "excerpt": ""})
    assert c["theme"] == "convert"


def test_triage_adds_fields():
    out = triage(load_jsonl(SAMPLE))
    assert all("theme" in i and "priority" in i for i in out)


def test_filter_theme():
    out = triage(load_jsonl(SAMPLE))
    f = filter_items(out, theme="api-agent")
    assert f and all(i["theme"] == "api-agent" for i in f)


def test_filter_no_match():
    out = triage(load_jsonl(SAMPLE))
    assert filter_items(out, theme="nonexistent") == []


def test_export_csv(tmp_path):
    out = triage(load_jsonl(SAMPLE))
    p = export_csv(out, tmp_path / "out.csv")
    text = p.read_text()
    assert "https://github.com" in text and text.count("\n") == len(out) + 1


def test_source_preserved_in_export(tmp_path):
    out = triage(load_jsonl(SAMPLE))
    p = export_csv(out, tmp_path / "out.csv")
    assert out[0]["url"] in p.read_text()
