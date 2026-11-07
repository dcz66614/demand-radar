"""MVP B Streamlit app. Run: python -m streamlit run mvps/mvp_b/app.py"""
from trace import diff_docs, export_csv, filter_docs, load_csv

import streamlit as st

st.set_page_config(page_title="Document Trace — MVP B", layout="wide")
st.title("Document Trace (MVP B) — SEC filing extracts")
path = st.text_input("CSV input", "mvps/mvp_b/data/sample.csv")
try:
    docs = load_csv(path)
except Exception as e:
    st.error(f"Cannot load input: {e}")
    st.stop()
kw = st.text_input("Keyword filter", "")
shown = filter_docs(docs, keyword=kw or None)
st.write(f"{len(shown)} of {len(docs)} documents")
for d in shown:
    st.markdown(f"**{d['title']}** — {d.get('version','')}")
    st.markdown(f"[source]({d['source_url']})")
    st.write((d.get("text") or "")[:250])
if len(shown) >= 2:
    st.subheader("Diff: doc 1 vs doc 2")
    diffs = diff_docs(shown[0].get("text", ""), shown[1].get("text", ""))
    for kind, line in diffs[:50]:
        st.write(f"{kind}: {line[:200]}")
    if st.button("Export diff CSV"):
        out = export_csv(diffs, "mvps/mvp_b/data/diff_export.csv")
        st.success(f"Exported {len(diffs)} diff lines to {out}")
