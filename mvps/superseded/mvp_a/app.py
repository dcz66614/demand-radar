"""MVP A Streamlit app. Run: python -m streamlit run mvps/mvp_a/app.py"""

import streamlit as st
from triage import export_csv, filter_items, load_jsonl, triage

st.set_page_config(page_title="Issue Triage — MVP A", layout="wide")
st.title("Issue Triage (MVP A) — AI agent / API issues")
path = st.text_input("JSONL input", "mvps/mvp_a/data/sample.jsonl")
try:
    items = triage(load_jsonl(path))
except Exception as e:
    st.error(f"Cannot load input: {e}")
    st.stop()
theme = st.selectbox("Theme", ["all"] + sorted({i["theme"] for i in items}))
platform = st.selectbox("Platform", ["all"] + sorted({i.get("platform", "") for i in items}))
shown = filter_items(items,
                     theme=None if theme == "all" else theme,
                     platform=None if platform == "all" else platform)
st.write(f"{len(shown)} of {len(items)} issues")
for i in shown:
    st.markdown(f"**[{i['priority']}] [{i['theme']}] {i['title']}**")
    st.markdown(f"[source]({i['url']}) — {i.get('published_at','')}")
    st.write((i.get("excerpt") or "")[:200])
if st.button("Export CSV"):
    out = export_csv(shown, "mvps/mvp_a/data/triage_export.csv")
    st.success(f"Exported {len(shown)} rows to {out}")
