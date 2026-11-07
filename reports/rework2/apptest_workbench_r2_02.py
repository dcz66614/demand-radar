"""R2-02 workbench AppTest driver (evidence script, not a pytest test).

Runs the real AppTest flow for app/streamlit_app.py and prints a
machine-checkable summary. Exit 0 only if every assertion holds.
The workbench has no pytest AppTest file of its own (only the two MVP
apps do); this script fills that gap for R2-02 and is kept in
reports/rework2/ as evidence.

Usage: python reports/rework2/apptest_workbench_r2_02.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "streamlit_app.py"

from streamlit.testing.v1 import AppTest


def _row_markdowns(at):
    """One rendered source row = a markdown starting with '**['."""
    return [m for m in at.markdown if m.value.startswith("**[")]


def _count_line(at):
    # st.write output is exposed as markdown elements in AppTest
    # (streamlit 1.67 has no at.write attribute).
    for m in at.markdown:
        if m.value.startswith("共 "):
            return m.value
    return None


def main() -> int:
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception, f"app raised: {at.exception}"
    assert any("Demand Radar" in t.value for t in at.title), "title missing"

    # 1. Default view: VERIFIED only, LIMIT 200.
    rows = _row_markdowns(at)
    print(f"default rows rendered: {len(rows)}")
    print(f"default count line: {_count_line(at)}")
    assert len(rows) == 200, f"expected 200 VERIFIED rows, got {len(rows)}"
    assert not any("REJECTED" in m.value for m in rows), "REJECTED leaked into default view"
    assert "仅显示 VERIFIED" in (_count_line(at) or "")

    # 2. Opt-in checkbox: REJECTED rows appear (still LIMIT 200).
    at.checkbox[0].set_value(True).run()
    assert not at.exception
    rows2 = _row_markdowns(at)
    print(f"show-rejected rows rendered: {len(rows2)}")
    assert len(rows2) == 200
    n_rej = sum(1 for m in rows2 if "REJECTED" in m.value)
    print(f"show-rejected REJECTED rows visible: {n_rej}")
    assert n_rej > 0, "checkbox did not reveal any REJECTED row"
    at.checkbox[0].set_value(False).run()

    # 3. Domain filter: AI -> 42 VERIFIED rows (45 total, 3 REJECTED).
    at.selectbox[0].set_value("AI").run()
    assert not at.exception
    rows_ai = _row_markdowns(at)
    print(f"domain=AI rows rendered: {len(rows_ai)}")
    assert len(rows_ai) == 42, f"expected 42 AI VERIFIED rows, got {len(rows_ai)}"
    assert all(m.value.startswith("**[AI") for m in rows_ai)
    at.selectbox[0].set_value("全部").run()

    # 4. Platform filter: github -> strictly fewer than 200, more than 0.
    at.selectbox[1].set_value("github").run()
    assert not at.exception
    rows_gh = _row_markdowns(at)
    print(f"platform=github rows rendered: {len(rows_gh)}")
    assert 0 < len(rows_gh) < 200
    assert all("· github ·" in m.value for m in rows_gh)
    at.selectbox[1].set_value("全部").run()

    # 5. Keyword filter: 'token' narrows the list. The SQL matches title OR
    # excerpt, so a row qualifies if EITHER contains the keyword. Each
    # rendered row is 3 consecutive markdowns: title, excerpt, source link.
    at.text_input[0].set_value("token").run()
    assert not at.exception
    rows_tok = _row_markdowns(at)
    print(f"keyword='token' rows rendered: {len(rows_tok)}")
    assert 0 < len(rows_tok) < 200
    all_md = list(at.markdown)
    for title_md in rows_tok:
        i = all_md.index(title_md)
        excerpt_md = all_md[i + 1]
        assert re.search(r"token", title_md.value, re.IGNORECASE) or re.search(
            r"token", excerpt_md.value, re.IGNORECASE
        ), f"row matches neither title nor excerpt: {title_md.value[:80]}"

    print("WORKBENCH APPTEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
