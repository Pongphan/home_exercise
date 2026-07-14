"""Shared Streamlit styling and small presentation helpers."""

from __future__ import annotations

from html import escape

import streamlit as st


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
:root { --forest:#14332b; --mint:#d9f36a; --cream:#f7f5ef; --coral:#ff8066; --muted:#65736e; }
.stApp { background: linear-gradient(150deg, #fbfaf6 0%, #f2f7f3 55%, #faf7ef 100%); }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.035em; color:var(--forest); }
[data-testid="stSidebar"] { background:#14332b; }
[data-testid="stSidebar"] * { color:#edf5f1; }
[data-testid="stSidebar"] [aria-selected="true"] { background:rgba(217,243,106,.16); }
.hero { padding:2.3rem; border-radius:24px; color:white; background:linear-gradient(125deg,#14332b,#285f50); margin:.4rem 0 1.5rem; position:relative; overflow:hidden; }
.hero:after { content:''; position:absolute; width:180px; height:180px; border-radius:50%; right:-35px; top:-75px; background:#d9f36a; opacity:.9; }
.hero h1 { color:white; margin:0 0 .35rem; max-width:75%; font-size:clamp(2rem,5vw,3.8rem); }
.hero p { color:#dfeae6; margin:0; max-width:650px; font-size:1.05rem; }
.eyebrow { text-transform:uppercase; letter-spacing:.16em; font-weight:700; font-size:.75rem; color:#8bffca; margin-bottom:.55rem; }
.metric-card { background:rgba(255,255,255,.88); border:1px solid #e1e8e4; padding:1.1rem 1.2rem; border-radius:18px; min-height:115px; box-shadow:0 8px 30px rgba(20,51,43,.055); }
.metric-card .value { color:#14332b; font:800 1.8rem 'Manrope'; }
.metric-card .label { color:#65736e; font-size:.86rem; }
.exercise-card { background:white; border:1px solid #e2e9e5; padding:1rem; border-radius:18px; margin-bottom:.75rem; box-shadow:0 6px 24px rgba(20,51,43,.045); }
.pill { display:inline-block; padding:.25rem .55rem; border-radius:999px; background:#edf3ef; color:#2d574b; font-size:.76rem; margin:.12rem; }
.safety { border-left:4px solid #ff8066; background:#fff3ef; border-radius:8px; padding:.8rem 1rem; color:#70473e; }
.stButton>button, .stDownloadButton>button { border-radius:12px; font-weight:700; }
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] { background:#14332b; color:white; border-color:#14332b; }
[data-testid="stForm"] { background:rgba(255,255,255,.72); border-radius:18px; padding:1rem; border:1px solid #e2e9e5; }
@media (max-width: 700px) { .hero { padding:1.35rem; border-radius:18px; } .hero:after{width:100px;height:100px;} .hero h1{max-width:90%;} [data-testid="column"] { min-width:100% !important; } }
</style>
"""


def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, eyebrow: str = "FITJOURNEY") -> None:
    st.markdown(
        f'<section class="hero"><div class="eyebrow">{escape(eyebrow)}</div>'
        f'<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></section>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="label">{escape(label)}</div><div class="value">{escape(value)}</div>'
        f'<div class="label">{escape(caption)}</div></div>', unsafe_allow_html=True,
    )
