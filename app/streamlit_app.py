"""Demand Radar workbench (read-only). Run: python -m streamlit run app/streamlit_app.py"""
import sqlite3
from pathlib import Path

import streamlit as st

DB = Path(__file__).resolve().parents[1] / "data" / "demand_radar.sqlite"

st.set_page_config(page_title="Demand Radar", layout="wide")
st.title("Demand Radar — 证据驱动的问题发现")

if not DB.exists():
    st.error("数据库不存在，请先运行 python -m demand_radar init")
    st.stop()

conn = sqlite3.connect(DB)
show_rejected = st.checkbox("显示已拒绝 (REJECTED) 的来源", value=False)
domains = [r[0] for r in conn.execute("SELECT DISTINCT domain FROM source_items ORDER BY domain")]
domain = st.selectbox("领域", ["全部"] + domains)
platform = st.selectbox("来源", ["全部", "github", "hackernews", "official"])
q = st.text_input("关键词筛选", "")
sql = "SELECT domain, platform, title, url, published_at, excerpt, status FROM source_items WHERE 1=1"
params: list = []
if not show_rejected:
    # R02: default UI shows VERIFIED evidence only; REJECTED rows are hidden
    # unless the reviewer explicitly opts in.
    sql += " AND status='VERIFIED'"
if domain != "全部":
    sql += " AND domain=?"; params.append(domain)
if platform != "全部":
    sql += " AND platform=?"; params.append(platform)
if q:
    sql += " AND (title LIKE ? OR excerpt LIKE ?)"; params += [f"%{q}%", f"%{q}%"]
sql += " ORDER BY published_at DESC LIMIT 200"
rows = conn.execute(sql, params).fetchall()
st.write(f"共 {len(rows)} 条（最多显示 200）" + ("" if show_rejected else " · 仅显示 VERIFIED"))
for d, p, title, url, pub, exc, stt in rows:
    st.markdown(f"**[{d} · {p} · {stt}] {title or '(无标题)'}** — {pub or '日期未知'}")
    st.write(exc)
    st.markdown(f"[原始来源]({url})")
    st.divider()
