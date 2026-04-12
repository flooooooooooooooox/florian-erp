import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import os
import calendar
import requests
from auth import check_login, logout, admin_panel, get_user_credentials
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Floxia – ERP Bâtiment",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── THEME ──────────────────────────────────────────────────────────────────────
if "themes" not in st.session_state:
    st.session_state.themes = "dark"

def toggle_theme():
    st.session_state.themes = "light" if st.session_state.themes == "dark" else "dark"

if st.session_state.themes == "light":
    theme_css_vars = """
    --bg-app: #F0F4F8;
    --bg-surface: #FFFFFF;
    --bg-card: #FFFFFF;
    --bg-sidebar: #1A2942;
    --text-main: #0F172A;
    --text-muted: #64748B;
    --text-dim: #94A3B8;
    --border: rgba(0,0,0,0.08);
    --border-hover: rgba(59,130,246,0.4);
    --sidebar-text: #E2E8F0;
    --sidebar-muted: #94A3B8;
    """
    chart_bg = "#FFFFFF"
    chart_font = "#0F172A"
    chart_grid = "#E2E8F0"
else:
    theme_css_vars = """
    --bg-app: #080f1a;
    --bg-surface: #0d1929;
    --bg-card: #111e30;
    --bg-sidebar: #060d18;
    --text-main: #e8f0fe;
    --text-muted: #6b84a3;
    --text-dim: #3d5473;
    --border: rgba(255,255,255,0.06);
    --border-hover: rgba(59,130,246,0.35);
    --sidebar-text: #e8f0fe;
    --sidebar-muted: #6b84a3;
    """
    chart_bg = "rgba(0,0,0,0)"
    chart_font = "#e8f0fe"
    chart_grid = "rgba(255,255,255,0.05)"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {{
    {theme_css_vars}
    --primary: #3B82F6;
    --primary-glow: rgba(59,130,246,0.12);
    --primary-dark: #2563EB;
    --success: #10B981;
    --success-glow: rgba(16,185,129,0.1);
    --warning: #F59E0B;
    --danger: #EF4444;
    --radius: 12px;
    --radius-sm: 8px;
    --radius-xs: 6px;
    --shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.15);
}}

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg-app) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text-main);
    -webkit-font-smoothing: antialiased;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background: var(--bg-sidebar) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}}
[data-testid="stSidebar"] > div {{ padding: 0 !important; }}
[data-testid="stSidebar"] * {{ color: var(--sidebar-text) !important; }}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 3px; height: 3px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 99px; }}

/* ── METRICS ── */
[data-testid="stMetric"] {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px !important;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    box-shadow: var(--shadow);
}}
[data-testid="stMetric"]::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary) 0%, transparent 100%);
}}
[data-testid="stMetric"]:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
[data-testid="stMetric"] label {{
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: 'DM Sans', sans-serif !important;
}}
[data-testid="stMetricValue"] {{
    color: var(--text-main) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    background: var(--bg-surface);
    border-radius: var(--radius-sm);
    padding: 3px;
    border: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: var(--radius-xs) !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 7px 16px !important;
    transition: all 0.15s ease;
    font-family: 'DM Sans', sans-serif !important;
}}
.stTabs [aria-selected="true"] {{
    background: var(--primary) !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.35) !important;
}}

/* ── BUTTONS ── */
.stButton > button {{
    border-radius: var(--radius-xs) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.15s ease !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    padding: 7px 14px !important;
}}
.stButton > button:hover {{
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: var(--primary-glow) !important;
    transform: translateY(-1px);
}}

/* ── INPUTS ── */
.stTextInput input, .stNumberInput input,
[data-testid="stTextArea"] textarea {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-xs) !important;
    color: var(--text-main) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    transition: border-color 0.15s ease;
}}
.stTextInput input:focus, .stNumberInput input:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--primary-glow) !important;
}}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {{
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow);
}}
[data-testid="stDataFrame"] div[role="grid"] div[role="row"]:hover {{
    background-color: rgba(59,130,246,0.08) !important;
}}

hr {{ border-color: var(--border) !important; margin: 14px 0 !important; }}

/* ── SIDEBAR RADIO (nav) ── */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {{
    padding: 9px 12px;
    background: transparent;
    border-radius: var(--radius-xs);
    cursor: pointer;
    margin-bottom: 1px;
    border: 1px solid transparent;
    transition: all 0.15s ease;
    width: 100%;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {{
    background: rgba(255,255,255,0.06);
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
    background: rgba(59,130,246,0.15) !important;
    border-color: rgba(59,130,246,0.3) !important;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {{
    color: #60A5FA !important;
    font-weight: 700 !important;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p {{
    margin: 0;
    font-size: 0.88rem;
    color: var(--sidebar-muted);
    font-family: 'DM Sans', sans-serif;
}}

/* ── MAIN RADIO (horizontal) ── */
section.main .stRadio > div[role="radiogroup"] {{
    display: flex;
    flex-direction: row;
    gap: 4px;
    background: var(--bg-surface);
    border-radius: var(--radius-sm);
    padding: 3px;
    border: 1px solid var(--border);
    width: fit-content;
    margin-bottom: 4px;
}}
section.main .stRadio > div[role="radiogroup"] > label {{
    padding: 6px 14px !important;
    background: transparent;
    border-radius: var(--radius-xs) !important;
    cursor: pointer;
    border: none !important;
    transition: all 0.15s ease;
    white-space: nowrap;
}}
section.main .stRadio > div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}
section.main .stRadio > div[role="radiogroup"] > label p {{
    margin: 0 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    font-family: 'DM Sans', sans-serif !important;
}}
section.main .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
    background: var(--primary) !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
}}
section.main .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {{
    color: #fff !important;
    font-weight: 600 !important;
}}

/* ── PULSE DOT ── */
.pulse-dot {{
    display: inline-block; width: 6px; height: 6px;
    border-radius: 50%; background: var(--success);
    animation: pulse-anim 2s ease-in-out infinite;
    margin-right: 5px; vertical-align: middle;
}}
@keyframes pulse-anim {{ 0%,100% {{ opacity:1; transform:scale(1); }} 50% {{ opacity:0.4; transform:scale(0.8); }} }}

/* ── PAGE HEADER ── */
.page-header {{ padding: 6px 0 22px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }}
.page-header h1 {{
    font-family: 'Syne', sans-serif !important;
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em;
    margin: 0 !important;
    color: var(--text-main) !important;
}}
.page-header .subtitle {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 3px; }}

/* ── NOTIFICATION BADGE ── */
.nav-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    background: #EF4444;
    color: #fff;
    border-radius: 99px;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 0 5px;
    margin-left: 6px;
    vertical-align: middle;
    line-height: 1;
    box-shadow: 0 2px 6px rgba(239,68,68,0.4);
    animation: badge-pop 0.3s cubic-bezier(0.34,1.56,0.64,1);
}}
@keyframes badge-pop {{ 0% {{ transform: scale(0); }} 100% {{ transform: scale(1); }} }}

/* ── CALENDAR STYLES ── */
.cal-grid {{ display: grid; grid-template-columns: 60px repeat(7,1fr); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; background: var(--bg-card); }}
.cal-header {{ background: var(--bg-surface); border-bottom: 1px solid var(--border); padding: 10px 0; text-align: center; font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }}
.cal-header.today {{ color: var(--primary); }}
.cal-time {{ font-size: 0.7rem; color: var(--text-dim); text-align: right; padding: 0 8px 0 4px; border-right: 1px solid var(--border); }}
.cal-cell {{ border-right: 1px solid var(--border); border-bottom: 1px solid rgba(255,255,255,0.03); min-height: 40px; position: relative; }}
.cal-event {{
    position: absolute; left: 2px; right: 2px;
    border-radius: 4px;
    padding: 2px 5px;
    font-size: 0.68rem;
    font-weight: 600;
    overflow: hidden;
    cursor: pointer;
    z-index: 1;
    white-space: nowrap;
    text-overflow: ellipsis;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}}
.cal-now-line {{
    position: absolute;
    left: 0; right: 0;
    height: 2px;
    background: #EF4444;
    z-index: 10;
}}
.cal-now-dot {{
    position: absolute;
    left: -4px; top: -4px;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #EF4444;
}}

/* ── CARD ── */
.erp-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin-bottom: 10px;
    box-shadow: var(--shadow);
    transition: border-color 0.15s ease, transform 0.15s ease;
}}
.erp-card:hover {{ border-color: var(--border-hover); transform: translateY(-1px); }}

/* ── SELECT ── */
[data-testid="stSelectbox"] > div > div {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-xs) !important;
    color: var(--text-main) !important;
}}
</style>
""", unsafe_allow_html=True)

# ── AUTH ───────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()

# ── CONFIG ─────────────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_worksheet(username: str, tab_name: str):
    sheet_name, gsa_json = get_user_credentials(username)
    if not sheet_name or not gsa_json:
        return None, "Credentials non configurés."
    try:
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(sheet_name)
        ws = sh.worksheet(tab_name)
        return ws, None
    except gspread.exceptions.WorksheetNotFound:
        return None, f"Onglet '{tab_name}' introuvable."
    except Exception as e:
        return None, str(e)

def _dedup_headers(headers):
    seen, out = {}, []
    for i, h in enumerate(headers):
        h = h.strip() or f"_col_{i}"
        if h in seen:
            seen[h] += 1
            out.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            out.append(h)
    return out

@st.cache_data(ttl=90, show_spinner=False)
def get_sheet_data(username: str):
    try:
        sheet_name, gsa_json = get_user_credentials(username)
        if not sheet_name or not gsa_json:
            return pd.DataFrame(), "Credentials non configurés."
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(sheet_name)
        try:
            ws = sh.worksheet("suivie")
        except Exception:
            ws = sh.sheet1
        all_values = ws.get_all_values()
        if not all_values:
            return pd.DataFrame(), None
        raw_headers = all_values[0]
        clean_headers = _dedup_headers(raw_headers)
        rows = all_values[1:]
        n = len(clean_headers)
        padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
        df = pd.DataFrame(padded, columns=clean_headers)
        df = df.loc[:, ~df.columns.str.startswith("_col_")]
        df = df.replace("", pd.NA).dropna(how="all").fillna("")
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ── HELPERS ────────────────────────────────────────────────────────────────────
def clean_amount(val):
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    s = str(val).replace("\xa0","").replace("\u202f","").replace(" ","").replace(",",".").replace("€","").strip()
    try:
        return float(s)
    except:
        return 0.0

def is_checked(val):
    if pd.isna(val): return False
    s = str(val).strip()
    return s in {"✅","✓","✔","TRUE","true","oui","Oui","OUI","1","x","X","yes","Yes"} or "✅" in s

def fcol(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in str(c).strip().lower():
                return c
    return None

def fmt(v):
    return f"{v:,.0f} €".replace(",", " ")

def style_relances(row):
    r3_col = next((c for c in row.index if "relance 3" in str(c).lower()), None)
    st_col = next((c for c in row.index if "statut" in str(c).lower()), None)
    if r3_col and st_col:
        r3_val = str(row.get(r3_col, "")).strip()
        st_val = str(row.get(st_col, "")).lower()
        if r3_val != "" and "envoyé" not in st_val:
            return ['background-color: rgba(239,68,68,0.12); color: #EF4444; font-weight: 600;'] * len(row)
    return [''] * len(row)

LIMIT = 100

def show_table(dataframe, key_suffix=""):
    total = len(dataframe)
    if total == 0:
        st.info("Aucun dossier trouvé.")
        return
    show_all = st.session_state.get(f"show_all_{key_suffix}", False)
    displayed = dataframe if show_all else dataframe.head(LIMIT)
    if isinstance(displayed, pd.DataFrame):
        styled_df = displayed.style.apply(style_relances, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(displayed, use_container_width=True, hide_index=True)
    if total > LIMIT:
        if not show_all:
            st.caption(f"Affichage des {LIMIT} premiers sur {total}.")
            if st.button(f"📂 Voir les {total - LIMIT} suivants", key=f"btn_more_{key_suffix}"):
                st.session_state[f"show_all_{key_suffix}"] = True
                st.rerun()
        else:
            st.caption(f"{total} dossiers affichés.")
            if st.button("🔼 Réduire", key=f"btn_less_{key_suffix}"):
                st.session_state[f"show_all_{key_suffix}"] = False
                st.rerun()

def page_header(title, subtitle=""):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        {"<div class='subtitle'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)

# ── NOTIFICATION COUNT (cached séparément pour le badge) ──────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def _get_notif_count(u):
    ws, err = get_worksheet(u, "notifications")
    if err or not ws:
        return 0
    try:
        vals = ws.get_all_values()
        if not vals or len(vals) < 2:
            return 0
        headers = [h.strip().lower() for h in vals[0]]
        if "statut" not in headers:
            return 0
        idx = headers.index("statut")
        return sum(1 for r in vals[1:] if len(r) > idx and r[idx].strip() == "en_attente")
    except:
        return 0

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
user = st.session_state.get("username", "")
role = st.session_state.get("role", "viewer")
nb_notif_badge = _get_notif_count(user)

with st.sidebar:
    st.markdown("<div style='padding: 18px 14px 6px;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)
    else:
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;padding-bottom:6px;'>
            <div style='width:34px;height:34px;background:linear-gradient(135deg,#3B82F6,#1D4ED8);
                border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:1rem;'>⚡</div>
            <div>
                <div style='font-family:Syne,sans-serif;font-weight:800;font-size:1rem;color:#E8F0FE;letter-spacing:-0.02em;'>Floxia</div>
                <div style='font-size:0.68rem;color:#6B84A3;letter-spacing:0.05em;text-transform:uppercase;'>ERP Bâtiment</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.button("🌓 Thème", on_click=toggle_theme, use_container_width=True)
    st.markdown("<hr style='margin:8px 0;border-color:rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    st.markdown("<div style='padding: 0 10px;'>", unsafe_allow_html=True)

    pages = [
        "📊 Vue Générale",
        "📄 Créer un devis",
        "📋 Devis",
        "💶 Factures & Paiements",
        "🏗️ Chantiers",
        "📅 Planning",
        "🔔 Notifications",
        "🗂️ Espace Clients",
        "📁 Tous les dossiers",
        "📝 Éditeur Google Sheet",
        "📞 Coordonnées & RGPD"
    ]
    if role == "admin":
        pages.append("👥 Utilisateurs")

    # Pages avec badge
    pages_display = []
    for p in pages:
        if p == "🔔 Notifications" and nb_notif_badge > 0:
            pages_display.append(f"🔔 Notifications [{nb_notif_badge}]")
        else:
            pages_display.append(p)

    if "nav_override" in st.session_state:
        _override = st.session_state.pop("nav_override")
        if _override in pages:
            st.session_state["_page_index"] = pages.index(_override)

    if "_page_index" not in st.session_state:
        st.session_state["_page_index"] = 0
    if st.session_state["_page_index"] >= len(pages):
        st.session_state["_page_index"] = 0

    def _on_nav_change():
        val = st.session_state.get("nav_radio")
        if val and val in pages_display:
            st.session_state["_page_index"] = pages_display.index(val)

    page_display = st.radio(
        "Navigation",
        pages_display,
        label_visibility="collapsed",
        index=st.session_state["_page_index"],
        key="nav_radio",
        on_change=_on_nav_change,
    )
    # Résoudre page réelle
    page = pages[pages_display.index(page_display)] if page_display in pages_display else pages[0]
    if page_display in pages_display:
        st.session_state["_page_index"] = pages_display.index(page_display)

    st.markdown("</div>", unsafe_allow_html=True)

    # Badge JS injection pour le styling
    if nb_notif_badge > 0:
        st.markdown(f"""
        <script>
        (function() {{
            const labels = window.parent.document.querySelectorAll('[data-testid="stSidebar"] label p');
            labels.forEach(el => {{
                if(el.textContent.includes('Notifications')) {{
                    if(!el.querySelector('.nav-badge')) {{
                        const badge = document.createElement('span');
                        badge.className = 'nav-badge';
                        badge.textContent = '{nb_notif_badge}';
                        el.appendChild(badge);
                    }}
                }}
            }});
        }})();
        </script>
        """, unsafe_allow_html=True)

    st.markdown("<div style='position:absolute;bottom:0;left:0;right:0;padding:14px;border-top:1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:9px;margin-bottom:10px;'>
        <div style='width:30px;height:30px;background:linear-gradient(135deg,#1E3A5F,#2563EB);
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:0.8rem;color:#fff;font-weight:700;'>
            {user[0].upper() if user else '?'}
        </div>
        <div>
            <div style='font-weight:600;font-size:0.82rem;color:#E8F0FE;'>{user}</div>
            <div style='font-size:0.68rem;color:#6B84A3;'>{role}</div>
        </div>
        <div style='margin-left:auto;'><span class="pulse-dot"></span></div>
    </div>
    """, unsafe_allow_html=True)

    col_r, col_l = st.columns(2)
    with col_r:
        if st.button("🔄", use_container_width=True, help="Actualiser"):
            st.cache_data.clear()
            st.rerun()
    with col_l:
        if st.button("🚪", use_container_width=True, help="Déconnexion"):
            logout()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── PAGES SPÉCIALES ────────────────────────────────────────────────────────────
if page == "👥 Utilisateurs":
    admin_panel()
    st.stop()

elif page == "📞 Coordonnées & RGPD":
    page_header("📞 Coordonnées & RGPD", "Informations légales et contact")
    st.markdown(f"""
    <div class="erp-card">
        <h3 style="color:var(--primary);margin-top:0;font-family:Syne,sans-serif;">👤 Contact Développeur</h3>
        <p style="color:var(--text-main);"><strong>Email :</strong> <a href="mailto:flogagnebien611@gmail.com" style="color:var(--primary);">flogagnebien611@gmail.com</a></p>
        <p style="color:var(--text-main);"><strong>Téléphone :</strong> 06 33 79 05 42</p>
    </div>
    <div class="erp-card" style="margin-top:12px;">
        <h3 style="color:var(--primary);margin-top:0;font-family:Syne,sans-serif;">🛡️ Conformité RGPD</h3>
        <p style="color:var(--text-main);">Cette application respecte le <strong>Règlement Général sur la Protection des Données (RGPD)</strong>.</p>
        <ul style="color:var(--text-muted);line-height:1.7;margin-top:8px;">
            <li><strong>Finalité :</strong> Données utilisées exclusivement pour la gestion opérationnelle.</li>
            <li><strong>Sécurité :</strong> Accès sécurisé via authentification et API Google officielle.</li>
            <li><strong>Droit d'accès :</strong> Modification et suppression via l'éditeur intégré.</li>
            <li><strong>Conservation :</strong> Aucune donnée personnelle stockée hors identifiants de session.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ESPACE CLIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗂️ Espace Clients":
    page_header("🗂️ Espace Clients", "Documents et dossiers synchronisés avec Google Drive")
    prefill_client = st.session_state.pop("_prefill_client_search", "")

    def get_google_doc_content(file_id, mime_type, drive_service):
        try:
            if 'application/vnd.google-apps.document' in mime_type:
                request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
                return request.execute().decode('utf-8')
            elif 'text/plain' in mime_type:
                request = drive_service.files().get_media(fileId=file_id)
                return request.execute().decode('utf-8')
            return None
        except Exception:
            return None

    try:
        from googleapiclient.discovery import build
        sheet_name, gsa_json = get_user_credentials(user)
        if not gsa_json:
            st.error("Identifiants Google introuvables.")
            st.stop()
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        query_main = "name = 'espace clients' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_main = drive_service.files().list(q=query_main, fields="files(id, name)").execute()
        main_folders = res_main.get('files', [])
        if not main_folders:
            st.warning("⚠️ Dossier 'espace clients' introuvable.")
        else:
            main_folder_id = main_folders[0]['id']
            query_clients = f"'{main_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res_clients = drive_service.files().list(q=query_clients, fields="files(id, name)", pageSize=1000).execute()
            client_folders = sorted(res_clients.get('files', []), key=lambda x: x['name'].lower())
            if not client_folders:
                st.info("Aucun dossier client trouvé.")
            else:
                client_names = [f["name"] for f in client_folders]
                search_client = st.text_input("🔍 Rechercher un client :", placeholder="Tapez le nom...", value=prefill_client)
                filtered = [n for n in client_names if search_client.lower() in n.lower()]
                if not filtered:
                    st.warning("Aucun client ne correspond.")
                else:
                    selected_name = st.selectbox("👤 Sélectionnez un client :", filtered)
                    selected_id = next(f['id'] for f in client_folders if f['name'] == selected_name)
                    st.markdown(f"<hr><h4 style='color:var(--primary);font-family:Syne,sans-serif;'>📂 {selected_name}</h4>", unsafe_allow_html=True)
                    query_files = f"'{selected_id}' in parents and trashed = false"
                    res_files = drive_service.files().list(q=query_files, fields="files(id, name, mimeType, webViewLink)", orderBy="folder, name", pageSize=1000).execute()
                    files = res_files.get('files', [])

                    def display_file(f_dict):
                        mime = f_dict.get('mimeType', '').lower()
                        icon = "📄"
                        if "folder" in mime: icon = "📁"
                        elif "pdf" in mime: icon = "📕"
                        elif "image" in mime: icon = "🖼️"
                        elif "spreadsheet" in mime or "sheet" in mime or "excel" in mime: icon = "📊"
                        elif "document" in mime or "word" in mime: icon = "📝"
                        st.markdown(f"""
                        <a href="{f_dict.get('webViewLink','#')}" target="_blank" style="text-decoration:none;">
                            <div class="erp-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;">
                                <div style="font-size:1.1rem;">{icon}</div>
                                <div style="color:var(--text-main);font-weight:600;font-size:0.88rem;">{f_dict.get('name')}</div>
                                <div style="margin-left:auto;color:var(--primary);font-size:0.72rem;font-weight:600;">Ouvrir ↗</div>
                            </div>
                        </a>
                        """, unsafe_allow_html=True)

                    if not files:
                        st.info("Dossier vide.")
                    else:
                        for file in files:
                            mime_type = file.get('mimeType', '')
                            if mime_type == 'application/vnd.google-apps.folder':
                                with st.expander(f"📁 **{file.get('name')}**"):
                                    sub_query = f"'{file.get('id')}' in parents and trashed = false"
                                    sub_res = drive_service.files().list(q=sub_query, fields="files(id, name, mimeType, webViewLink)", orderBy="folder, name", pageSize=1000).execute()
                                    sub_files = sub_res.get('files', [])
                                    if not sub_files:
                                        st.caption("Dossier vide.")
                                    else:
                                        is_infos = file.get('name','').strip().lower() in ["infos clients","info client","infos client"]
                                        for sf in sub_files:
                                            sm = sf.get('mimeType','').lower()
                                            if is_infos and ('document' in sm or 'text' in sm):
                                                content = get_google_doc_content(sf['id'], sm, drive_service)
                                                if content:
                                                    st.markdown(f"""<div class="erp-card"><div style="font-weight:700;color:var(--primary);margin-bottom:8px;">📝 {sf.get('name')}</div><div style="white-space:pre-wrap;font-size:0.88rem;color:var(--text-main);">{content}</div></div>""", unsafe_allow_html=True)
                                                else:
                                                    display_file(sf)
                                            else:
                                                display_file(sf)
                            else:
                                display_file(file)
    except ImportError:
        st.error("🚨 'google-api-python-client' non installé.")
    except Exception as e:
        st.error(f"Erreur Google Drive : {e}")

# ══════════════════════════════════════════════════════════════════════════════
# ÉDITEUR GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Éditeur Google Sheet":
    page_header("📝 Éditeur Google Sheet", "Gérez votre base de données en temps réel")

    CATEGORIES = ["Salle de bain","Cuisine","Chambre","Salon","WC / Toilettes","Entrée / Couloir",
                  "Garage","Cave / Sous-sol","Combles / Grenier","Buanderie","Bureau / Bibliothèque",
                  "Terrasse / Balcon","Jardin / Extérieur","Façade","Toiture","Escalier","Piscine",
                  "Véranda / Pergola","Parties communes","Local technique","Autre"]
    TYPES_POSTE = ["Préparation / Démolition","Gros œuvre","Charpente / Couverture","Isolation",
                   "Plâtrerie / Cloisons","Menuiserie intérieure","Menuiserie extérieure",
                   "Plomberie / Sanitaire","Chauffage / VMC / Climatisation","Électricité",
                   "Domotique / Alarme","Carrelage / Revêtement sol","Peinture / Revêtement mur",
                   "Parquet / Stratifié","Faïence","Finition","Installation","Mobilier / Agencement",
                   "Serrurerie / Métallerie","Terrassement / VRD","Maçonnerie","Enduit / Ravalement",
                   "Étanchéité / Hydrofuge","Nettoyage / Évacuation","Autre"]

    tab_presta, tab_catalogue = st.tabs(["📋 Feuille Prestations", "🗂️ Catalogue"])

    with tab_presta:
        PRESTA_COLS = ["categorie","Type de poste","Sous-prestation","Description","Prix MO HT","Prix Fourn. HT","Marge (%)","Quantité","Total HT"]

        @st.cache_data(ttl=15, show_spinner=False)
        def load_presta(u):
            ws, err = get_worksheet(u, "Feuille 1")
            if err: return err, pd.DataFrame()
            try:
                all_vals = ws.get_all_values()
                if not all_vals: return None, pd.DataFrame()
                headers = _dedup_headers(all_vals[0])
                rows = all_vals[1:]
                n = len(headers)
                padded = [r + [""]*(n-len(r)) if len(r)<n else r[:n] for r in rows]
                df = pd.DataFrame(padded, columns=headers)
                df = df.replace("", pd.NA).dropna(how="all").fillna("")
                useful = [c for c in df.columns if not c.startswith("_col")]
                return None, df[useful]
            except Exception as e:
                return str(e), pd.DataFrame()

        err_p, df_p = load_presta(user)
        if err_p:
            st.error(f"❌ {err_p}")
        else:
            sub_p_view, sub_p_add, sub_p_edit, sub_p_del = st.tabs(["👁️ Voir","➕ Ajouter","✏️ Modifier","🗑️ Supprimer"])
            with sub_p_view:
                st.caption(f"{len(df_p)} lignes")
                search_p = st.text_input("🔍 Rechercher", placeholder="Mot-clé...", key="search_presta")
                df_show = df_p.copy()
                if search_p:
                    mask = pd.Series([False]*len(df_show), index=df_show.index)
                    for c in df_show.columns:
                        mask |= df_show[c].astype(str).str.contains(search_p, case=False, na=False)
                    df_show = df_show[mask]
                show_table(df_show.reset_index(drop=True), "presta_view")

            with sub_p_add:
                c_mo, c_fourn, c_marge, c_qte = st.columns(4)
                with c_mo: val_mo = st.number_input("Prix MO HT", min_value=0.0, value=0.0, step=10.0, key="add_mo")
                with c_fourn: val_fourn = st.number_input("Prix Fourn. HT", min_value=0.0, value=0.0, step=10.0, key="add_fourn")
                with c_marge: val_marge = st.number_input("Marge (%)", min_value=0.0, value=30.0, step=5.0, key="add_marge")
                with c_qte: val_qte = st.number_input("Quantité", min_value=1.0, value=1.0, step=1.0, key="add_qte")
                calcul_total = (val_mo + (val_fourn * (1 + (val_marge / 100)))) * val_qte
                st.success(f"💶 Total HT : **{calcul_total:.2f} €**")
                with st.form("form_add_presta"):
                    headers_p = list(df_p.columns) if len(df_p) > 0 else PRESTA_COLS
                    inputs_p = {}
                    cols1 = st.columns(3)
                    for i, h in enumerate(headers_p):
                        hl = h.lower()
                        if any(mot in hl for mot in ["mo ht","fourn","marge","quantit","total"]): continue
                        with cols1[i % 3]:
                            if "categ" in hl: inputs_p[h] = st.selectbox(h, CATEGORIES, key=f"add_p_{h}")
                            elif "type" in hl and "poste" in hl: inputs_p[h] = st.selectbox(h, TYPES_POSTE, key=f"add_p_{h}")
                            else: inputs_p[h] = st.text_input(h, key=f"add_p_{h}")
                    submit_add_p = st.form_submit_button("✅ Ajouter", use_container_width=True)
                if submit_add_p:
                    for h in (list(df_p.columns) if len(df_p) > 0 else PRESTA_COLS):
                        hl = h.lower()
                        if "mo ht" in hl: inputs_p[h] = str(val_mo)
                        elif "fourn" in hl: inputs_p[h] = str(val_fourn)
                        elif "marge" in hl: inputs_p[h] = str(val_marge)
                        elif "quantit" in hl: inputs_p[h] = str(val_qte)
                        elif "total" in hl: inputs_p[h] = str(round(calcul_total, 2))
                    try:
                        ws_p2, err2 = get_worksheet(user, "Feuille 1")
                        if err2: st.error(err2)
                        else:
                            new_row = [inputs_p.get(h, "") for h in (list(df_p.columns) if len(df_p) > 0 else PRESTA_COLS)]
                            ws_p2.insert_row(new_row, index=len(df_p)+2, value_input_option="USER_ENTERED")
                            st.cache_data.clear()
                            st.success("✅ Ajouté !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            with sub_p_edit:
                if len(df_p) == 0:
                    st.info("Aucune ligne.")
                else:
                    headers_p2 = list(df_p.columns)
                    def _lbl(i):
                        for h in headers_p2:
                            if any(k in h.lower() for k in ["sous","prestation","designation","désignation"]):
                                val = str(df_p.iloc[i][h]).strip()
                                if val: return f"Ligne {i+2} — {val}"
                        return f"Ligne {i+2} — {df_p.iloc[i,0]}"
                    row_labels = [_lbl(i) for i in range(len(df_p))]
                    sel_idx = st.selectbox("Ligne à modifier", range(len(df_p)), format_func=lambda i: row_labels[i], key="sel_mod_presta")
                    cur_mo = cur_fourn = 0.0; cur_marge = 30.0; cur_qte = 1.0
                    for h in headers_p2:
                        hl = h.lower(); val = df_p.iloc[sel_idx][h]
                        if "mo ht" in hl: cur_mo = clean_amount(val)
                        elif "fourn" in hl: cur_fourn = clean_amount(val)
                        elif "marge" in hl: cur_marge = clean_amount(val)
                        elif "quantit" in hl: cur_qte = clean_amount(val)
                    c_mo_m, c_fourn_m, c_marge_m, c_qte_m = st.columns(4)
                    with c_mo_m: mod_mo = st.number_input("Prix MO HT", min_value=0.0, value=float(cur_mo), step=10.0, key="mod_mo")
                    with c_fourn_m: mod_fourn = st.number_input("Prix Fourn. HT", min_value=0.0, value=float(cur_fourn), step=10.0, key="mod_fourn")
                    with c_marge_m: mod_marge = st.number_input("Marge (%)", min_value=0.0, value=float(cur_marge), step=5.0, key="mod_marge")
                    with c_qte_m: mod_qte = st.number_input("Quantité", min_value=1.0, value=max(float(cur_qte),1.0), step=1.0, key="mod_qte")
                    mod_total = (mod_mo + (mod_fourn * (1 + (mod_marge/100)))) * mod_qte
                    st.success(f"💶 Nouveau Total HT : **{mod_total:.2f} €**")
                    with st.form("form_mod_presta"):
                        mod_inputs = {}; cols2 = st.columns(3)
                        for i, h in enumerate(headers_p2):
                            hl = h.lower()
                            if any(mot in hl for mot in ["mo ht","fourn","marge","quantit","total"]): continue
                            with cols2[i % 3]:
                                cur_val = str(df_p.iloc[sel_idx][h])
                                if "categ" in hl: mod_inputs[h] = st.selectbox(h, CATEGORIES, index=CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0, key=f"mod_p_{h}")
                                elif "type" in hl and "poste" in hl: mod_inputs[h] = st.selectbox(h, TYPES_POSTE, index=TYPES_POSTE.index(cur_val) if cur_val in TYPES_POSTE else 0, key=f"mod_p_{h}")
                                else: mod_inputs[h] = st.text_input(h, value=cur_val, key=f"mod_p_{h}")
                        submit_mod_p = st.form_submit_button("💾 Enregistrer", use_container_width=True)
                    if submit_mod_p:
                        for h in headers_p2:
                            hl = h.lower()
                            if "mo ht" in hl: mod_inputs[h] = str(mod_mo)
                            elif "fourn" in hl: mod_inputs[h] = str(mod_fourn)
                            elif "marge" in hl: mod_inputs[h] = str(mod_marge)
                            elif "quantit" in hl: mod_inputs[h] = str(mod_qte)
                            elif "total" in hl: mod_inputs[h] = str(round(mod_total, 2))
                        try:
                            ws_p3, err3 = get_worksheet(user, "Feuille 1")
                            if err3: st.error(err3)
                            else:
                                for col_idx, h in enumerate(headers_p2, start=1):
                                    ws_p3.update_cell(sel_idx+2, col_idx, mod_inputs.get(h,""))
                                st.cache_data.clear()
                                st.success("✅ Modifié !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            with sub_p_del:
                if len(df_p) == 0:
                    st.info("Aucune ligne.")
                else:
                    headers_p3 = list(df_p.columns)
                    def _lbl2(i):
                        for h in headers_p3:
                            if any(k in h.lower() for k in ["sous","prestation","designation","désignation"]):
                                val = str(df_p.iloc[i][h]).strip()
                                if val: return f"Ligne {i+2} — {val}"
                        return f"Ligne {i+2} — {df_p.iloc[i,0]}"
                    row_labels2 = [_lbl2(i) for i in range(len(df_p))]
                    del_idx = st.selectbox("Ligne à supprimer", range(len(df_p)), format_func=lambda i: row_labels2[i], key="sel_del_presta")
                    st.warning(f"⚠️ Suppression irréversible : **{row_labels2[del_idx]}**")
                    if st.button("🗑️ Confirmer la suppression", key="btn_del_presta"):
                        try:
                            ws_p4, err4 = get_worksheet(user, "Feuille 1")
                            if err4: st.error(err4)
                            else:
                                ws_p4.delete_rows(del_idx+2)
                                st.cache_data.clear()
                                st.success("✅ Supprimé !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

    with tab_catalogue:
        CATA_COLS = ["Catégorie","Article","Description","Prix Achat HT","% Marge","Prix Vente HT"]

        @st.cache_data(ttl=15, show_spinner=False)
        def load_catalogue(u):
            ws, err = get_worksheet(u, "catalogue")
            if err: return err, pd.DataFrame()
            try:
                all_vals = ws.get_all_values()
                if not all_vals: return None, pd.DataFrame()
                headers = _dedup_headers(all_vals[0])
                rows = all_vals[1:]
                n = len(headers)
                padded = [r + [""]*(n-len(r)) if len(r)<n else r[:n] for r in rows]
                df = pd.DataFrame(padded, columns=headers)
                df = df.replace("", pd.NA).dropna(how="all").fillna("")
                return None, df
            except Exception as e:
                return str(e), pd.DataFrame()

        err_c, df_c = load_catalogue(user)
        if err_c:
            st.error(f"❌ {err_c}")
        else:
            sub_c_view, sub_c_add, sub_c_edit, sub_c_del = st.tabs(["👁️ Voir","➕ Ajouter","✏️ Modifier","🗑️ Supprimer"])
            with sub_c_view:
                st.caption(f"{len(df_c)} articles")
                search_c = st.text_input("🔍 Rechercher", placeholder="Mot-clé...", key="search_cata")
                df_show_c = df_c.copy()
                if search_c:
                    mask = pd.Series([False]*len(df_show_c), index=df_show_c.index)
                    for c in df_show_c.columns:
                        mask |= df_show_c[c].astype(str).str.contains(search_c, case=False, na=False)
                    df_show_c = df_show_c[mask]
                show_table(df_show_c.reset_index(drop=True), "cata_view")

            with sub_c_add:
                c_achat, c_marge_c = st.columns(2)
                with c_achat: val_achat = st.number_input("Prix Achat HT", min_value=0.0, value=0.0, step=10.0, key="add_c_achat")
                with c_marge_c: val_marge_c = st.number_input("% Marge", min_value=0.0, value=30.0, step=5.0, key="add_c_marge")
                calcul_vente = val_achat * (1 + (val_marge_c / 100))
                st.success(f"💶 Prix Vente HT : **{calcul_vente:.2f} €**")
                with st.form("form_add_cata"):
                    headers_c = list(df_c.columns) if len(df_c) > 0 else CATA_COLS
                    inputs_c = {}; cols3 = st.columns(3)
                    for i, h in enumerate(headers_c):
                        hl = h.lower()
                        if any(mot in hl for mot in ["achat","marge","vente"]): continue
                        with cols3[i % 3]:
                            if "catég" in hl or "categ" in hl: inputs_c[h] = st.selectbox(h, CATEGORIES, key=f"add_c_{h}")
                            else: inputs_c[h] = st.text_input(h, key=f"add_c_{h}")
                    submit_add_c = st.form_submit_button("✅ Ajouter", use_container_width=True)
                if submit_add_c:
                    for h in headers_c:
                        hl = h.lower()
                        if "achat" in hl: inputs_c[h] = str(val_achat)
                        elif "marge" in hl: inputs_c[h] = str(val_marge_c)
                        elif "vente" in hl: inputs_c[h] = str(round(calcul_vente, 2))
                    try:
                        ws_c2, err_c2 = get_worksheet(user, "catalogue")
                        if err_c2: st.error(err_c2)
                        else:
                            ws_c2.insert_row([inputs_c.get(h,"") for h in headers_c], index=len(df_c)+2, value_input_option="USER_ENTERED")
                            st.cache_data.clear()
                            st.success("✅ Ajouté !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            with sub_c_edit:
                if len(df_c) == 0:
                    st.info("Aucun article.")
                else:
                    headers_c2 = list(df_c.columns)
                    art_labels = [f"Ligne {i+2} — {df_c.iloc[i,0]} / {df_c.iloc[i,1] if len(headers_c2)>1 else ''}" for i in range(len(df_c))]
                    sel_idx_c = st.selectbox("Article à modifier", range(len(df_c)), format_func=lambda i: art_labels[i], key="sel_mod_cata")
                    cur_achat = cur_marge_c2 = 0.0
                    for h in headers_c2:
                        hl = h.lower(); val = df_c.iloc[sel_idx_c][h]
                        if "achat" in hl: cur_achat = clean_amount(val)
                        elif "marge" in hl: cur_marge_c2 = clean_amount(val)
                    c_achat_m, c_marge_m = st.columns(2)
                    with c_achat_m: mod_achat = st.number_input("Prix Achat HT", min_value=0.0, value=float(cur_achat), step=10.0, key="mod_c_achat")
                    with c_marge_m: mod_marge_c = st.number_input("% Marge", min_value=0.0, value=float(cur_marge_c2), step=5.0, key="mod_c_marge")
                    mod_vente = mod_achat * (1 + (mod_marge_c / 100))
                    st.success(f"💶 Prix Vente HT : **{mod_vente:.2f} €**")
                    with st.form("form_mod_cata"):
                        mod_inputs_c = {}; cols4 = st.columns(3)
                        for i, h in enumerate(headers_c2):
                            hl = h.lower()
                            if any(mot in hl for mot in ["achat","marge","vente"]): continue
                            with cols4[i % 3]:
                                cur_val = str(df_c.iloc[sel_idx_c][h])
                                if "catég" in hl or "categ" in hl: mod_inputs_c[h] = st.selectbox(h, CATEGORIES, index=CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0, key=f"mod_c_{h}")
                                else: mod_inputs_c[h] = st.text_input(h, value=cur_val, key=f"mod_c_{h}")
                        submit_mod_c = st.form_submit_button("💾 Enregistrer", use_container_width=True)
                    if submit_mod_c:
                        for h in headers_c2:
                            hl = h.lower()
                            if "achat" in hl: mod_inputs_c[h] = str(mod_achat)
                            elif "marge" in hl: mod_inputs_c[h] = str(mod_marge_c)
                            elif "vente" in hl: mod_inputs_c[h] = str(round(mod_vente, 2))
                        try:
                            ws_c3, err_c3 = get_worksheet(user, "catalogue")
                            if err_c3: st.error(err_c3)
                            else:
                                for col_idx, h in enumerate(headers_c2, start=1):
                                    ws_c3.update_cell(sel_idx_c+2, col_idx, mod_inputs_c.get(h,""))
                                st.cache_data.clear()
                                st.success("✅ Modifié !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            with sub_c_del:
                if len(df_c) == 0:
                    st.info("Aucun article.")
                else:
                    headers_c3 = list(df_c.columns)
                    art_labels2 = [f"Ligne {i+2} — {df_c.iloc[i,0]} / {df_c.iloc[i,1] if len(headers_c3)>1 else ''}" for i in range(len(df_c))]
                    del_idx_c = st.selectbox("Article à supprimer", range(len(df_c)), format_func=lambda i: art_labels2[i], key="sel_del_cata")
                    st.warning(f"⚠️ Suppression irréversible : **{art_labels2[del_idx_c]}**")
                    if st.button("🗑️ Confirmer", key="btn_del_cata"):
                        try:
                            ws_c4, err_c4 = get_worksheet(user, "catalogue")
                            if err_c4: st.error(err_c4)
                            else:
                                ws_c4.delete_rows(del_idx_c+2)
                                st.cache_data.clear()
                                st.success("✅ Supprimé !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Notifications":
    page_header("🔔 Notifications", "Devis signés en attente de planification")
    WEBHOOK_REPONSE = f"https://n8n.florianai.fr/webhook-test/reponse-{user}"

    @st.cache_data(ttl=60, show_spinner=False)
    def _load_salaries(u):
        ws, err = get_worksheet(u, "liste")
        if err: return []
        try:
            vals = ws.get_all_values()
            if not vals or len(vals) < 2: return []
            headers = [h.strip().lower() for h in vals[0]]
            sal_col = next((h for h in headers if "salar" in h), headers[0] if headers else None)
            if not sal_col: return []
            idx = headers.index(sal_col)
            return [r[idx].strip() for r in vals[1:] if len(r) > idx and r[idx].strip()]
        except Exception: return []

    @st.cache_data(ttl=15, show_spinner=False)
    def _load_notifications(u):
        ws, err = get_worksheet(u, "notifications")
        if err: return err, pd.DataFrame()
        try:
            vals = ws.get_all_values()
            if not vals or len(vals) < 2: return None, pd.DataFrame()
            headers = _dedup_headers(vals[0])
            rows = vals[1:]
            n = len(headers)
            padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
            df_n = pd.DataFrame(padded, columns=headers)
            df_n = df_n.replace("", pd.NA).dropna(how="all").fillna("")
            return None, df_n
        except Exception as e: return str(e), pd.DataFrame()

    salaries = _load_salaries(user)
    err_n, df_notif = _load_notifications(user)

    if err_n:
        st.error(f"❌ Onglet 'notifications' introuvable : {err_n}")
        st.stop()

    df_attente = df_notif[df_notif.get("statut", pd.Series(dtype=str)).astype(str).str.strip() == "en_attente"] if "statut" in df_notif.columns else df_notif
    nb_attente_notif = len(df_attente)

    col_n1, col_n2 = st.columns(2)
    col_n1.metric("🔔 En attente", nb_attente_notif)
    col_n2.metric("✅ Planifiés", len(df_notif) - nb_attente_notif)

    if st.button("🔄 Actualiser", key="btn_refresh_notif"):
        _load_notifications.clear()
        _get_notif_count.clear()
        st.rerun()

    st.markdown("---")

    if nb_attente_notif == 0:
        st.success("✅ Aucune notification en attente !")
    else:
        for idx, (row_idx, row) in enumerate(df_attente.iterrows()):
            numero  = str(row.get("numero_devis", "")).strip()
            client  = str(row.get("nom_client", "")).strip()
            objet   = str(row.get("objet", "")).strip()
            montant = str(row.get("montant", "")).strip()
            date_r  = str(row.get("date_reception", "")).strip()

            with st.container(border=True):
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                  <div>
                    <span style="background:var(--primary);color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:700;">{numero}</span>
                    <strong style="margin-left:8px;font-size:0.92rem;font-family:Syne,sans-serif;">{client}</strong>
                  </div>
                  <div style="font-size:0.75rem;color:var(--text-dim);">{date_r}</div>
                </div>
                <div style="color:var(--text-muted);font-size:0.83rem;margin-bottom:3px;">🏗️ {objet}</div>
                <div style="color:var(--primary);font-weight:700;font-size:0.88rem;margin-bottom:10px;">💶 {montant} €</div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    date_debut_notif = st.date_input("📅 Date début", value=datetime.today(), key=f"notif_date_{idx}")
                with c2:
                    heure_intervention = st.time_input("🕐 Heure début", value=datetime.strptime("08:00", "%H:%M").time(), key=f"notif_heure_{idx}")
                with c3:
                    heure_fin = st.time_input("🕔 Heure fin", value=datetime.strptime("17:00", "%H:%M").time(), key=f"notif_heure_fin_{idx}")
                with c4:
                    salarie_sel = st.selectbox("👷 Salarié(e)", ["— Choisir —"] + salaries, key=f"notif_sal_{idx}")

                col_send, col_del = st.columns([3, 1])
                with col_send:
                    if st.button("📤 Confirmer et envoyer à n8n", key=f"notif_send_{idx}", use_container_width=True, type="primary"):
                        if salarie_sel == "— Choisir —":
                            st.error("❌ Sélectionne un(e) salarié(e)")
                        else:
                            payload_notif = {
                                "numero_devis": numero, "nom_client": client, "objet": objet,
                                "montant": montant, "date_debut_travaux": date_debut_notif.strftime("%Y-%m-%d"),
                                "heure_intervention": heure_intervention.strftime("%H:%M"),
                                "heure_fin": heure_fin.strftime("%H:%M"), "salarie": salarie_sel,
                                "planifie_par": user, "planifie_le": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            }
                            try:
                                resp = requests.post(WEBHOOK_REPONSE, json=payload_notif, timeout=30, headers={"Content-Type": "application/json"})
                                if resp.status_code in (200, 201):
                                    ws_n, _ = get_worksheet(user, "notifications")
                                    if ws_n:
                                        statut_col = list(df_notif.columns).index("statut") + 1 if "statut" in df_notif.columns else None
                                        if statut_col:
                                            ws_n.update_cell(row_idx + 2, statut_col, "planifie")
                                    _load_notifications.clear()
                                    _get_notif_count.clear()
                                    st.success(f"✅ Planification envoyée pour {client} !")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erreur n8n : {resp.status_code}")
                            except Exception as ex:
                                st.error(f"Erreur : {ex}")

                with col_del:
                    if st.button("🗑️ Supprimer", key=f"notif_del_{idx}", use_container_width=True):
                        st.session_state[f"confirm_del_{idx}"] = True
                    if st.session_state.get(f"confirm_del_{idx}"):
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Oui", key=f"yes_del_{idx}"):
                                try:
                                    ws_n2, _ = get_worksheet(user, "notifications")
                                    if ws_n2:
                                        ws_n2.delete_rows(row_idx + 2)
                                    _load_notifications.clear()
                                    _get_notif_count.clear()
                                    st.session_state.pop(f"confirm_del_{idx}", None)
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Erreur : {ex}")
                        with col_no:
                            if st.button("❌ Non", key=f"no_del_{idx}"):
                                st.session_state.pop(f"confirm_del_{idx}", None)
                                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CRÉER UN DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Créer un devis":
    page_header("📄 Créer un devis", "Remplis le formulaire — n8n génère le PDF et met à jour Sheets")
    WEBHOOK_URL = f"https://n8n.florianai.fr/webhook-test/{user}"

    @st.cache_data(ttl=60, show_spinner=False)
    def _load_catalogue_devis(u):
        ws, err = get_worksheet(u, "catalogue")
        if err: return []
        try:
            vals = ws.get_all_values()
            if not vals or len(vals) < 2: return []
            headers = [h.strip().lower() for h in vals[0]]
            items = []
            for r in vals[1:]:
                if not any(r): continue
                row_d = dict(zip(headers, r + [""] * max(0, len(headers) - len(r))))
                article = row_d.get("article", row_d.get("sous-prestation", "")).strip()
                prix = row_d.get("prix vente ht", row_d.get("total ht", "")).strip()
                desc = row_d.get("description", "").strip()
                cat = row_d.get("catégorie", row_d.get("categorie", "")).strip()
                items.append({"article": article, "description": desc, "prix_ht": prix, "categorie": cat, "source": "catalogue"})
            return items
        except Exception: return []

    @st.cache_data(ttl=60, show_spinner=False)
    def _load_prestations_devis(u):
        ws, err = get_worksheet(u, "Feuille 1")
        if err: return []
        try:
            vals = ws.get_all_values()
            if not vals or len(vals) < 2: return []
            headers = [h.strip().lower() for h in vals[0]]
            items = []
            for r in vals[1:]:
                if not any(r): continue
                row_d = dict(zip(headers, r + [""] * max(0, len(headers) - len(r))))
                article = (row_d.get("sous-prestation","") or row_d.get("sous prestation","") or row_d.get("designation","") or row_d.get("désignation","") or row_d.get("prestation","")).strip()
                if not article: continue
                prix = (row_d.get("total ht","") or row_d.get("prix vente ht","") or row_d.get("prix mo ht","")).strip()
                desc = row_d.get("description","").strip()
                cat = (row_d.get("categorie","") or row_d.get("catégorie","") or row_d.get("type de poste","")).strip()
                label = article + (f"  –  {prix} € HT" if prix else "")
                items.append({"label": label, "article": article, "description": desc, "prix_ht": prix, "categorie": cat, "source": "prestations"})
            return items
        except Exception: return []

    catalogue_items = _load_catalogue_devis(user)
    prestations_items = _load_prestations_devis(user)
    cat_labels = ["— Choisir un article —"] + [it["article"] for it in catalogue_items]
    prest_labels = ["— Choisir une prestation —"] + [it["label"] for it in prestations_items]

    def _parse_prix(val):
        try: return float(str(val).replace(",",".").replace(" ","").replace("\u202f","") or 0)
        except: return 0.0

    if "devis_lignes" not in st.session_state:
        st.session_state.devis_lignes = [{"source": "libre", "article": "", "description": "", "prix_ht": 0.0, "qte": 1.0, "categorie": ""}]
    if "devis_preview" not in st.session_state:
        st.session_state.devis_preview = False

    st.markdown("#### 👤 Informations client")
    c1, c2 = st.columns(2)
    with c1:
        client_nom = st.text_input("Nom complet *", placeholder="Jean Dupont", key="dv_nom")
        client_email = st.text_input("Email", placeholder="jean.dupont@email.com", key="dv_email")
    with c2:
        client_tel = st.text_input("Téléphone", placeholder="06 xx xx xx xx", key="dv_tel")
        client_adresse = st.text_input("Adresse du client", placeholder="12 rue de la Paix, 75001 Paris", key="dv_adr_client")

    st.markdown("---")
    st.markdown("#### 🏗️ Chantier")
    c3, c4 = st.columns(2)
    with c3:
        objet_travaux = st.text_input("Objet des travaux *", placeholder="Rénovation salle de bain", key="dv_objet")
        adresse_chantier = st.text_input("Adresse du chantier *", placeholder="108 rue de Falaise, 14000 Caen", key="dv_adr_chantier")
        categorie_operation = st.selectbox("Catégorie d'opération", ["Prestation","Service","Fourniture","Fourniture et pose","Main d'œuvre","Autre"], key="dv_cat_op")
        siren_client = st.text_input("SIREN client (optionnel)", placeholder="123 456 789", key="dv_siren")
    with c4:
        modalite_paie = st.selectbox("Modalité de paiement", ["Acompte / Solde","Paiement intégral à la commande","Paiement comptant / immédiat","Paiement échelonné / progressif","Paiement différé / à terme"], key="dv_modal")
        duree_jours = st.number_input("Durée estimée (jours ouvrés) *", min_value=1, value=5, step=1, key="dv_duree")

    pct_acompte = 30; pct_solde = 70; segments = []; jours_differe = 0; phrase_modalite = ""

    if modalite_paie == "Acompte / Solde":
        ca1, ca2 = st.columns(2)
        with ca1: pct_acompte = st.slider("Acompte (%)", min_value=10, max_value=90, value=30, step=5, key="dv_pct_acompte")
        pct_solde = 100 - pct_acompte
        with ca2: st.metric("Solde (%)", f"{pct_solde} %")
        segments = [{"etape": "À la commande", "percent": pct_acompte},{"etape": "À la réception", "percent": pct_solde}]
    elif modalite_paie == "Paiement échelonné / progressif":
        ce1, ce2, ce3 = st.columns(3)
        with ce1: pct_cmd = st.slider("À la commande (%)", 0, 100, 20, 5, key="dv_pct_cmd")
        with ce2: pct_enc = st.slider("En cours (%)", 0, 100-pct_cmd, min(30, 100-pct_cmd), 5, key="dv_pct_enc")
        pct_fin = 100 - pct_cmd - pct_enc
        with ce3: st.metric("À la réception (%)", f"{pct_fin} %")
        segments = [{"etape": "À la commande","percent": pct_cmd},{"etape": "En cours de chantier","percent": pct_enc},{"etape": "À la réception","percent": pct_fin}]
    elif modalite_paie == "Paiement différé / à terme":
        jours_differe = st.number_input("Jours après réception", min_value=1, max_value=365, value=30, step=1, key="dv_jours_differe")
        segments = [{"etape": f"À terme ({jours_differe}j)", "percent": 100}]
    elif modalite_paie == "Paiement intégral à la commande":
        segments = [{"etape": "À la commande", "percent": 100}]
    elif modalite_paie == "Paiement comptant / immédiat":
        segments = [{"etape": "À la réception", "percent": 100}]

    st.markdown("---")
    st.markdown("#### 🧾 TVA")
    c_tva1, c_tva2 = st.columns(2)
    with c_tva1:
        tva_option = st.radio("Taux TVA", ["5,5 % (amélioration énergétique)","10 % (travaux de rénovation)","20 % (travaux neufs / autres)"], key="dv_tva")
    with c_tva2:
        tva_debits_option = st.radio("Régime TVA", ["TVA sur encaissements","TVA sur débits"], key="dv_tva_debits")

    tva_taux = 0.055 if "5,5" in tva_option else (0.10 if "10 %" in tva_option else 0.20)
    tva_debits_bool = "débits" in tva_debits_option
    tva_pct_str = "5,5" if tva_taux == 0.055 else str(int(tva_taux * 100))

    st.markdown("---")
    st.markdown("#### 🛠️ Prestations")
    lignes = st.session_state.devis_lignes
    to_del = []

    for i, ligne in enumerate(lignes):
        with st.container(border=True):
            col_src, col_del = st.columns([6, 1])
            with col_src:
                src_idx = {"catalogue": 0, "prestations": 1}.get(ligne.get("source", "libre"), 2)
                src = st.radio(f"src_{i}", ["🗂️ Divers", "🔧 Prestations", "✏️ Saisie libre"], horizontal=True, key=f"src_{i}", index=src_idx, label_visibility="collapsed")
            prev_src_key = f"_prev_src_{i}"
            if st.session_state.get(prev_src_key) != src:
                st.session_state[prev_src_key] = src
                ligne["_prev_sel"] = None; ligne["article"] = ""; ligne["prix_ht"] = 0.0; ligne["qte"] = 1.0
                st.rerun()
            with col_del:
                if len(lignes) > 1 and st.button("🗑️", key=f"del_{i}"):
                    to_del.append(i)

            if src == "🗂️ Divers":
                ligne["source"] = "catalogue"
                sel = st.selectbox("Article", cat_labels, key=f"cat_{i}", label_visibility="collapsed")
                if sel != cat_labels[0]:
                    found = next((it for it in catalogue_items if it["article"] == sel), None)
                    if found and sel != ligne.get("_prev_sel"):
                        ligne.update({"article": found["article"], "description": "", "categorie": found["categorie"], "_prev_sel": sel, "prix_ht": _parse_prix(found["prix_ht"]), "qte": 1.0})
                        st.rerun()
                new_qte = st.number_input("Quantité", min_value=0.1, value=float(ligne["qte"]), step=1.0, key=f"qte_{i}")
                ligne["qte"] = new_qte
                if ligne.get("article"):
                    st.caption(f"Prix HT : **{ligne['prix_ht']:,.2f} €** — Total : **{ligne['qte'] * ligne['prix_ht']:,.2f} €**")
            elif src == "🔧 Prestations":
                ligne["source"] = "prestations"
                sel = st.selectbox("Prestation", prest_labels, key=f"prest_{i}", label_visibility="collapsed")
                if sel != prest_labels[0]:
                    found = next((it for it in prestations_items if it["label"] == sel), None)
                    if found and sel != ligne.get("_prev_sel"):
                        ligne["article"] = found["article"]; ligne["description"] = found["description"]
                        ligne["categorie"] = found["categorie"]; ligne["_prev_sel"] = sel
                        ligne["prix_ht"] = _parse_prix(found["prix_ht"]); ligne["qte"] = 1.0
                        st.session_state[f"pht2_{i}"] = float(ligne["prix_ht"])
                        st.session_state[f"qte2_{i}"] = 1.0
                        st.rerun()
                cq2, cp2 = st.columns(2)
                new_qte2 = cq2.number_input("Quantité", min_value=0.1, value=float(ligne["qte"]), step=1.0, key=f"qte2_{i}")
                new_pht2 = cp2.number_input("Prix unitaire HT (€)", min_value=0.0, value=float(ligne["prix_ht"]), step=10.0, key=f"pht2_{i}")
                ligne["qte"] = new_qte2; ligne["prix_ht"] = new_pht2
            else:
                ligne["source"] = "libre"
                ligne["article"] = st.text_input("Désignation *", value=ligne.get("article",""), key=f"art_{i}", placeholder="Ex : Pose carrelage")
                ligne["description"] = st.text_input("Description", value=ligne.get("description",""), key=f"desc_{i}")
                cq3, cp3 = st.columns(2)
                new_qte3 = cq3.number_input("Quantité", min_value=0.1, value=float(ligne["qte"]), step=1.0, key=f"qte3_{i}")
                new_pht3 = cp3.number_input("Prix unitaire HT (€)", min_value=0.0, value=float(ligne["prix_ht"]), step=10.0, key=f"pht3_{i}")
                ligne["qte"] = new_qte3; ligne["prix_ht"] = new_pht3

    for idx_d in sorted(to_del, reverse=True):
        st.session_state.devis_lignes.pop(idx_d)
    if to_del: st.rerun()

    if st.button("➕ Ajouter une ligne", key="add_ligne"):
        st.session_state.devis_lignes.append({"source": "libre", "article": "", "description": "", "prix_ht": 0.0, "qte": 1.0, "categorie": ""})
        st.rerun()

    def _get_prix(i, l): return float(l["prix_ht"])
    def _get_qte(i, l): return float(l["qte"])

    total_ht = sum(_get_prix(i, l) * _get_qte(i, l) for i, l in enumerate(lignes))
    total_tva = round(total_ht * tva_taux, 2)
    total_ttc = round(total_ht + total_tva, 2)

    if modalite_paie == "Acompte / Solde":
        phrase_modalite = f"Acompte de {pct_acompte}% à la commande ({round(total_ttc*pct_acompte/100,2):,.2f} €) — Solde de {pct_solde}% à la réception ({round(total_ttc*pct_solde/100,2):,.2f} €)"
    elif modalite_paie == "Paiement échelonné / progressif":
        parts = [f"{s['percent']}% {s['etape'].lower()} ({round(total_ttc*s['percent']/100,2):,.2f} €)" for s in segments if s["percent"] > 0]
        phrase_modalite = " — ".join(parts)
    elif modalite_paie == "Paiement différé / à terme":
        phrase_modalite = f"Paiement intégral de {total_ttc:,.2f} € sous {jours_differe} jours après réception"
    elif modalite_paie == "Paiement intégral à la commande":
        phrase_modalite = f"Paiement intégral de {total_ttc:,.2f} € à la commande"
    elif modalite_paie == "Paiement comptant / immédiat":
        phrase_modalite = f"Paiement comptant de {total_ttc:,.2f} € à la réception"

    st.markdown(f"""
    <div style="display:flex;justify-content:flex-end;margin-top:12px;">
      <div style="min-width:280px;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);">
        <div style="display:flex;justify-content:space-between;padding:7px 14px;background:var(--bg-surface);font-size:0.85rem;">
          <span style="color:var(--text-muted);">Total HT</span><strong>{total_ht:,.2f} €</strong>
        </div>
        <div style="display:flex;justify-content:space-between;padding:7px 14px;background:var(--bg-surface);font-size:0.85rem;">
          <span style="color:var(--text-muted);">TVA ({tva_pct_str} %)</span><strong>{total_tva:,.2f} €</strong>
        </div>
        <div style="display:flex;justify-content:space-between;padding:9px 14px;background:var(--primary);color:#fff;font-weight:700;font-size:1rem;">
          <span>TOTAL TTC</span><span>{total_ttc:,.2f} €</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if phrase_modalite:
        st.info(f"💬 **{phrase_modalite}**")

    st.markdown("<br>", unsafe_allow_html=True)

    def _validate():
        errs = []
        if not client_nom.strip(): errs.append("Nom client manquant")
        if not adresse_chantier.strip(): errs.append("Adresse chantier manquante")
        if not objet_travaux.strip(): errs.append("Objet des travaux manquant")
        if not any(l["article"].strip() for l in lignes): errs.append("Au moins une prestation requise")
        return errs

    def _build_payload():
        return {
            "nom_complet": client_nom.strip(), "adresse": client_adresse.strip(),
            "email": client_email.strip(), "tel": client_tel.strip(),
            "siren_client": siren_client.strip(), "objet": objet_travaux.strip(),
            "adresse_chantier": adresse_chantier.strip(), "categorie_operation": categorie_operation,
            "duree_jours": int(duree_jours), "date_debut": datetime.today().strftime("%Y-%m-%d"),
            "modalite_paiement": modalite_paie, "phrase_modalite": phrase_modalite,
            "phrase_modalité": phrase_modalite, "segments": segments, "jours_differe": jours_differe,
            "tva_choisi": float(tva_pct_str.replace(",",".")), "tva_debits": "Oui" if tva_debits_bool else "Non",
            "prestations": [{"libelle": l["article"].strip(), "description": l["description"].strip(), "quantite": _get_qte(i,l), "HT": round(_get_prix(i,l)*_get_qte(i,l),2), "TVA": round(_get_prix(i,l)*_get_qte(i,l)*tva_taux,2), "TTC": round(_get_prix(i,l)*_get_qte(i,l)*(1+tva_taux),2)} for i,l in enumerate(lignes) if l["article"].strip()],
            "totalHT": round(total_ht,2), "TVA": round(total_tva,2), "totalTTC": round(total_ttc,2),
            "cree_par": user, "cree_le": datetime.now().strftime("%Y-%m-%d %H:%M"), "source": "streamlit_erp",
        }

    if st.button("👁️ Prévisualiser le devis", use_container_width=True, key="btn_preview"):
        errs = _validate()
        if errs:
            for e in errs: st.error(f"❌ {e}")
        else:
            st.session_state.devis_preview = True

    if st.session_state.get("devis_preview"):
        st.markdown("---")
        lignes_html = ""
        for i, l in enumerate(lignes):
            if not l["article"].strip(): continue
            prix = _get_prix(i, l); qte = _get_qte(i, l)
            total_ht_l = round(qte*prix,2); tva_l = round(total_ht_l*tva_taux,2); ttc_l = round(total_ht_l+tva_l,2)
            bg = "#f8fafc" if i%2==0 else "#ffffff"
            desc_part = f"<br><span style='color:#64748b;font-size:8px;'>{l['description']}</span>" if l.get("description","").strip() else ""
            lignes_html += f"""<tr style="background:{bg};"><td style="padding:5px 6px;text-align:center;border-bottom:1px solid #e2e8f0;">{i+1}</td><td style="padding:5px 10px;border-bottom:1px solid #e2e8f0;"><strong style="font-size:9px;">{l['article']}</strong>{desc_part}</td><td style="padding:5px 6px;text-align:center;border-bottom:1px solid #e2e8f0;">{qte:g}</td><td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;">{prix:,.2f} €</td><td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;color:#64748b;">{tva_pct_str} %</td><td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;color:#64748b;">{tva_l:,.2f} €</td><td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;font-weight:700;color:#2563EB;">{ttc_l:,.2f} €</td></tr>"""

        date_fin_str = (datetime.today() + timedelta(days=int(duree_jours))).strftime("%d/%m/%Y")
        segments_html = "".join([f"<p>• {s['etape']} : <strong>{s['percent']}%</strong> — {round(total_ttc*s['percent']/100,2):,.2f} €</p>" for s in segments if s["percent"]>0])
        siren_html_preview = f"<p>SIREN : {siren_client.strip()}</p>" if siren_client.strip() else ""

        preview_html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>Devis</title><style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Segoe UI',Arial,sans-serif;font-size:9px;color:#1e293b;background:#fff;padding:15px}}header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;padding-bottom:10px;border-bottom:3px solid #2563EB}}.badge-devis{{background:#2563EB;color:#fff;font-weight:800;padding:4px 12px;border-radius:4px;letter-spacing:1px;font-size:11px}}.section-title{{font-weight:700;font-size:8px;color:#2563EB;text-transform:uppercase;margin-bottom:4px;border-bottom:1px solid #e2e8f0;padding-bottom:2px}}.two-columns{{display:flex;gap:10px;margin-bottom:12px}}.column{{flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-radius:5px;padding:7px 10px}}table{{width:100%;border-collapse:collapse;margin-top:4px}}thead{{background:#2563EB;color:#fff}}thead th{{padding:5px;text-align:left}}tbody td{{padding:5px;border-bottom:1px solid #e2e8f0}}.right{{text-align:right}}.center{{text-align:center}}.totals-wrapper{{display:flex;justify-content:flex-end;margin-top:8px}}.totals{{min-width:220px;border:1px solid #e2e8f0;border-radius:5px;overflow:hidden}}.totals table{{margin-top:0}}.totals tbody td{{padding:4px 8px}}.total-ttc{{background:#2563EB;color:#fff;font-weight:800}}.footer{{margin-top:14px;font-size:7.5px;color:#64748b;border-top:1px solid #e2e8f0;padding-top:8px}}</style></head><body>
<header><div><div style="font-weight:800;font-size:14px;color:#2563EB">Florian AI Batiment</div><div style="font-size:8px;color:#64748b">SARL - 108 rue de Falaise, 14000 Caen</div><div style="font-size:8px;color:#64748b">SIRET 812 345 678 00027 | TVA FR12 812345678</div><div style="font-size:8px;color:#64748b">06 12 34 56 78 - contact@florian-ai-batiment.fr</div></div>
<div style="text-align:right"><div class="badge-devis">DEVIS</div><div style="margin-top:6px;font-size:8px;color:#64748b">Date : {datetime.now().strftime("%d/%m/%Y")}</div><div style="font-size:8px;color:#64748b">TVA : {tva_pct_str} % | {"TVA sur débits" if tva_debits_bool else "TVA sur encaissements"}</div></div></header>
<div class="two-columns"><div class="column"><div class="section-title">Client</div><div style="font-weight:700">{client_nom}</div><div>{client_adresse}</div><div>{client_email}</div>{siren_html_preview}</div>
<div class="column"><div class="section-title">Objet des travaux</div><div style="font-weight:700">{objet_travaux}</div><div>📍 {adresse_chantier}</div><div>Catégorie : {categorie_operation}</div><div>Durée : {duree_jours} jours | Fin estimée : {date_fin_str}</div></div></div>
<div class="section-title">Détail des prestations</div>
<table><thead><tr><th>N°</th><th>Prestation</th><th class="center">Qté</th><th class="right">HT (€)</th><th class="right">TVA</th><th class="right">TVA (€)</th><th class="right">TTC (€)</th></tr></thead><tbody>{lignes_html}</tbody></table>
<div class="totals-wrapper"><div class="totals"><table><tbody><tr><td>Total HT</td><td class="right">{total_ht:,.2f} €</td></tr><tr><td>TVA {tva_pct_str}%</td><td class="right">{total_tva:,.2f} €</td></tr><tr class="total-ttc"><td><strong>TOTAL TTC</strong></td><td class="right"><strong>{total_ttc:,.2f} €</strong></td></tr></tbody></table></div></div>
<div style="margin-top:8px;padding:6px 10px;background:#eff6ff;border-left:3px solid #2563EB;font-size:8px;color:#1e40af">Modalités : {phrase_modalite}</div>
{segments_html}
<div class="footer">Florian AI Batiment — SIRET 812 345 678 00027 — contact@florian-ai-batiment.fr — Devis valable 30 jours</div></body></html>"""

        nb_lignes_valides = sum(1 for l in lignes if l["article"].strip())
        components.html(preview_html, height=850 + nb_lignes_valides*30, scrolling=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("✏️ Modifier", key="btn_close_preview", use_container_width=True):
                st.session_state.devis_preview = False; st.rerun()
        with col_b:
            if st.button("🖨️ Imprimer / PDF", key="btn_imprimer", use_container_width=True):
                payload = _build_payload(); payload["action"] = "imprimer"
                try:
                    resp = requests.post(WEBHOOK_URL, json=payload, timeout=30, headers={"Content-Type":"application/json"})
                    if resp.status_code in (200,201): st.success("✅ Envoyé pour impression !"); st.balloons()
                    else: st.error(f"❌ Erreur {resp.status_code}")
                except Exception as ex: st.error(f"Erreur : {ex}")
        with col_c:
            if st.button("📤 Envoyer au client", key="btn_envoyer_client", use_container_width=True, type="primary"):
                payload = _build_payload(); payload["action"] = "envoyer"
                try:
                    resp = requests.post(WEBHOOK_URL, json=payload, timeout=30, headers={"Content-Type":"application/json"})
                    if resp.status_code in (200,201):
                        st.success("✅ Devis envoyé !"); st.balloons()
                        st.session_state.devis_lignes = [{"source":"libre","article":"","description":"","prix_ht":0.0,"qte":1.0,"categorie":""}]
                        st.session_state.devis_preview = False; st.cache_data.clear()
                    else: st.error(f"❌ Erreur {resp.status_code}")
                except Exception as ex: st.error(f"Erreur : {ex}")
    st.stop()

# ── CHARGEMENT DONNÉES ─────────────────────────────────────────────────────────
df_raw, error = get_sheet_data(user)

if error:
    get_sheet_data.clear()
    st.error("❌ Impossible de se connecter à Google Sheets.")
    st.info(f"Détail : {error}")
    if st.button("🔄 Réessayer"): st.rerun()
    st.stop()

if df_raw.empty:
    st.warning("📭 Le Google Sheet est vide ou inaccessible.")
    st.stop()

df = df_raw.copy()

COL_CLIENT    = fcol(df, "client")
COL_CHANTIER  = fcol(df, "objet", "chantier")
COL_NUM       = fcol(df, "n° devis", "n°", "num")
COL_MONTANT   = fcol(df, "montant")
COL_SIGN      = fcol(df, "devis signé", "signé")
COL_FACT_FIN  = fcol(df, "facture finale", "finale", "final")
COL_PV        = fcol(df, "pv signé", "pv")
COL_STATUT    = fcol(df, "statut")
COL_DATE      = fcol(df, "date creation", "date créa", "date devis", "date creat")
COL_MODALITE  = fcol(df, "modalit")
COL_TVA       = fcol(df, "tva")
COL_RELANCE1  = fcol(df, "relance 1")
COL_RELANCE2  = fcol(df, "relance 2")
COL_RELANCE3  = fcol(df, "relance 3")
COL_ACOMPTE1  = fcol(df, "acompte 1")
COL_ACOMPTE2  = fcol(df, "acompte 2")
COL_RESERVE   = fcol(df, "réserve", "reserve", "avec reserve", "sans reserve")
COL_ADRESSE   = fcol(df, "address", "adresse")
COL_DATE_DEBUT = fcol(df, "début des travaux", "debut des travaux", "date début", "date debut")
COL_DATE_FIN   = fcol(df, "fin des travaux", "date fin", "date de fin")
COL_SALARIE    = fcol(df, "salarié", "salarie")
COL_HEURE_DEB  = fcol(df, "heure_debut", "heure debut", "heure_deb")
COL_HEURE_FIN  = fcol(df, "heure_fin", "heure fin")

df["_montant"]  = df[COL_MONTANT].apply(clean_amount) if COL_MONTANT else 0.0
df["_acompte1"] = df[COL_ACOMPTE1].apply(clean_amount) if COL_ACOMPTE1 else 0.0
df["_acompte2"] = df[COL_ACOMPTE2].apply(clean_amount) if COL_ACOMPTE2 else 0.0
df["_reste"]    = (df["_montant"] - df["_acompte1"] - df["_acompte2"]).clip(lower=0)
df["_signe"]    = df[COL_SIGN].apply(is_checked) if COL_SIGN else False
df["_fact_fin"] = df[COL_FACT_FIN].apply(is_checked) if COL_FACT_FIN else False
df["_pv"]       = df[COL_PV].apply(is_checked) if COL_PV else False

total_ca           = df["_montant"].sum()
nb_devis           = len(df)
nb_signes          = int(df["_signe"].sum())
nb_attente         = nb_devis - nb_signes
nb_fact_ok         = int(df["_fact_fin"].sum())
ca_signe           = df[df["_signe"]]["_montant"].sum()
ca_non_s           = df[~df["_signe"]]["_montant"].sum()
taux_conv          = int((nb_signes / nb_devis) * 100) if nb_devis > 0 else 0
reste_encaissement = df[(df["_signe"]) & (~df["_fact_fin"])]["_reste"].sum()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : VUE GÉNÉRALE
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Vue Générale":
    page_header("Tableau de Bord", f"Synchronisé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 CA Sécurisé", fmt(ca_signe), f"{nb_signes} devis signés")
    c2.metric("⏳ CA En Négociation", fmt(ca_non_s), f"{nb_attente} en cours")
    c3.metric("📈 Taux de Conversion", f"{taux_conv} %")
    c4.metric("💸 Reste à Encaisser", fmt(reste_encaissement))

    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2, 1])

    with cl:
        with st.container(border=True):
            if COL_DATE:
                d2 = df.copy()
                d2["_date"] = pd.to_datetime(d2[COL_DATE], dayfirst=True, errors="coerce")
                d2 = d2.dropna(subset=["_date"])
                if not d2.empty:
                    st.markdown("<div style='font-weight:600;font-size:0.82rem;color:var(--text-muted);margin-bottom:8px;letter-spacing:0.05em;text-transform:uppercase;'>📅 Période</div>", unsafe_allow_html=True)
                    col_dt1, col_dt2 = st.columns(2)
                    with col_dt1: start_dt = st.date_input("Du", value=d2["_date"].min().date(), key="start_dt")
                    with col_dt2: end_dt = st.date_input("Au", value=d2["_date"].max().date(), key="end_dt")
                    d2 = d2[(d2["_date"].dt.date >= start_dt) & (d2["_date"].dt.date <= end_dt)]
                    if d2.empty:
                        st.info("Aucune donnée sur cette période.")
                    else:
                        chart_mode = st.radio("Type", ["📊 Barres empilées", "📈 Courbes"], horizontal=True, key="chart_mode_toggle", label_visibility="collapsed")
                        d2["_mois_key"] = d2["_date"].dt.to_period("M").astype(str)
                        d2["_mois_label"] = d2["_date"].dt.strftime("%b %Y")
                        month_map = d2[["_mois_key","_mois_label"]].drop_duplicates().sort_values("_mois_key")
                        ca_total_m = d2.groupby("_mois_key")["_montant"].sum().reset_index().rename(columns={"_montant":"CA Total"})
                        ca_signe_m = d2[d2["_signe"]].groupby("_mois_key")["_montant"].sum().reset_index().rename(columns={"_montant":"CA Signé"})
                        ca_attente_m = d2[~d2["_signe"]].groupby("_mois_key")["_montant"].sum().reset_index().rename(columns={"_montant":"CA En attente"})
                        merged = month_map.copy()
                        for m in [ca_total_m, ca_signe_m, ca_attente_m]:
                            merged = merged.merge(m, on="_mois_key", how="left")
                        merged = merged.fillna(0)
                        x_labels = merged["_mois_label"].tolist()
                        fig = go.Figure()
                        if chart_mode == "📊 Barres empilées":
                            fig.add_trace(go.Bar(x=x_labels, y=merged["CA En attente"], name="En attente", marker_color="#1E3A5F", marker_line_width=0))
                            fig.add_trace(go.Bar(x=x_labels, y=merged["CA Signé"], name="Signé ✅", marker_color="#10B981", marker_line_width=0))
                            fig.update_layout(barmode="stack", bargap=0.3)
                        else:
                            fig.add_trace(go.Scatter(x=x_labels, y=merged["CA Total"], name="CA Total", mode="lines+markers", line=dict(color="#3B82F6", width=2.5, shape="spline"), marker=dict(size=6, color="#3B82F6"), fill="tozeroy", fillcolor="rgba(59,130,246,0.06)"))
                            fig.add_trace(go.Scatter(x=x_labels, y=merged["CA Signé"], name="CA Signé", mode="lines+markers", line=dict(color="#10B981", width=2.5, shape="spline"), marker=dict(size=6, color="#10B981"), fill="tozeroy", fillcolor="rgba(16,185,129,0.06)"))
                            fig.add_trace(go.Scatter(x=x_labels, y=merged["CA En attente"], name="En attente", mode="lines+markers", line=dict(color="#F59E0B", width=2, shape="spline", dash="dot"), marker=dict(size=5, color="#F59E0B")))
                        fig.update_layout(
                            title=dict(text="Évolution du CA mensuel", font=dict(size=13, color=chart_font, family="Syne")),
                            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                            font=dict(color=chart_font, family="DM Sans"),
                            xaxis=dict(type="category", showgrid=False, title="", tickfont=dict(color=chart_font, size=10), showline=False, zeroline=False, tickangle=-25),
                            yaxis=dict(gridcolor=chart_grid, title="CA (€)", tickfont=dict(color=chart_font, size=10), showline=False, zeroline=False, tickformat=",.0f"),
                            legend=dict(bgcolor="rgba(255,255,255,0.04)", bordercolor=chart_grid, borderwidth=1, font=dict(color=chart_font, size=10), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                            hovermode="x unified", margin=dict(t=50, b=30, l=10, r=10),
                        )
                        st.plotly_chart(fig, use_container_width=True)

    with cr:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.9rem;color:#F59E0B;margin-bottom:10px;font-family:Syne,sans-serif;'>🚨 Actions Requises</div>", unsafe_allow_html=True)
            df_alertes_all = df[~df["_signe"]]
            ALERT_PREVIEW = 6
            if "alertes_show_all" not in st.session_state: st.session_state["alertes_show_all"] = False
            df_alertes_display = df_alertes_all if st.session_state["alertes_show_all"] else df_alertes_all.head(ALERT_PREVIEW)
            if len(df_alertes_all) > 0:
                for idx, (_, row) in enumerate(df_alertes_display.iterrows()):
                    client_val = str(row[COL_CLIENT]) if COL_CLIENT else "Inconnu"
                    montant_val = fmt(row["_montant"])
                    btn_col, card_col = st.columns([0.08, 0.92])
                    with card_col:
                        st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:rgba(245,158,11,0.05);border:1px solid rgba(245,158,11,0.12);border-radius:var(--radius-xs);margin-bottom:4px;"><div style="font-size:1rem;">📄</div><div style="flex:1;min-width:0;"><div style="font-weight:600;font-size:0.85rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{client_val}</div><div style="font-size:0.75rem;color:var(--text-muted);">{montant_val}</div></div></div>""", unsafe_allow_html=True)
                    with btn_col:
                        if st.button("↗", key=f"goto_client_{idx}_{client_val}", help=f"Ouvrir {client_val}"):
                            st.session_state["_prefill_client_search"] = client_val
                            st.session_state["_page_index"] = pages.index("🗂️ Espace Clients")
                            st.session_state["nav_radio"] = pages_display[pages.index("🗂️ Espace Clients")]
                            st.rerun()
                if nb_attente > ALERT_PREVIEW:
                    if not st.session_state["alertes_show_all"]:
                        if st.button(f"📂 Voir les {nb_attente - ALERT_PREVIEW} autres", use_container_width=True, key="btn_alertes_more"):
                            st.session_state["alertes_show_all"] = True; st.rerun()
                    else:
                        if st.button("🔼 Réduire", use_container_width=True, key="btn_alertes_less"):
                            st.session_state["alertes_show_all"] = False; st.rerun()
            else:
                st.success("✅ Aucun devis en attente !")

    st.markdown("<br>", unsafe_allow_html=True)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        with st.container(border=True):
            fig_donut = go.Figure(data=[go.Pie(labels=["Signés","En attente"], values=[nb_signes, nb_attente], hole=0.72, marker_colors=["#10B981","#1E3A5F"], textinfo="none")])
            fig_donut.add_annotation(text=f"{taux_conv}%", x=0.5, y=0.5, font_size=26, font_color=chart_font, font_family="Syne", showarrow=False)
            fig_donut.update_layout(title="Taux de transformation", title_font=dict(color=chart_font, family="Syne", size=13), paper_bgcolor="rgba(0,0,0,0)", showlegend=True, legend=dict(bgcolor="rgba(0,0,0,0)", font_color=chart_font, font=dict(size=10)), margin=dict(t=40,b=10,l=10,r=10), height=240)
            st.plotly_chart(fig_donut, use_container_width=True)
    with col_d2:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.9rem;margin-bottom:14px;font-family:Syne,sans-serif;'>📊 Résumé financier</div>", unsafe_allow_html=True)
            for label, val, color in [("CA Total émis", fmt(total_ca), "#3B82F6"),("CA Sécurisé", fmt(ca_signe), "#10B981"),("CA En attente", fmt(ca_non_s), "#F59E0B"),("Reste à encaisser", fmt(reste_encaissement), "#EF4444"),("Chantiers terminés (PV)", f"{int(df['_pv'].sum())}", "#10B981")]:
                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border);'><span style='color:var(--text-muted);font-size:0.83rem;'>{label}</span><span style='color:{color};font-weight:700;font-size:0.92rem;'>{val}</span></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Devis":
    page_header("Gestion des Devis", f"{nb_devis} devis au total")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Devis", nb_devis)
    c2.metric("Taux de Conversion", f"{taux_conv} %")
    c3.metric("CA Global", fmt(total_ca))
    st.markdown("<br>", unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE, COL_RELANCE1, COL_RELANCE2, COL_RELANCE3, COL_STATUT] if c]
    search = st.text_input("🔍 Rechercher un devis", placeholder="Client, chantier, numéro...", key="search_devis")
    df_d = df.copy()
    if search:
        mask = pd.Series([False]*len(df_d), index=df_d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col: mask |= df_d[col].astype(str).str.contains(search, case=False, na=False)
        df_d = df_d[mask]
    if "devis_tab" not in st.session_state: st.session_state["devis_tab"] = "⏳ En attente de signature"
    def _on_devis_tab(): st.session_state["devis_tab"] = st.session_state["_devis_tab_radio"]
    tab_devis_choice = st.radio("", ["⏳ En attente de signature","✅ Devis signés"], horizontal=True, key="_devis_tab_radio", index=["⏳ En attente de signature","✅ Devis signés"].index(st.session_state["devis_tab"]), on_change=_on_devis_tab)
    st.markdown("---")
    if tab_devis_choice == "⏳ En attente de signature":
        d = df_d[~df_d["_signe"]]
        st.caption(f"{len(d)} devis — CA potentiel : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_attente")
    else:
        d = df_d[df_d["_signe"]]
        st.caption(f"{len(d)} devis signés — CA : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_signes")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES & PAIEMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💶 Factures & Paiements":
    page_header("Factures & Paiements", "Suivi des encaissements")
    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Factures finales", nb_fact_ok)
    c2.metric("⚠️ Sans facture finale", len(df_imp))
    c3.metric("💸 CA restant à facturer", fmt(reste_encaissement))
    st.markdown("<br>", unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ACOMPTE1, COL_ACOMPTE2, "_reste", COL_FACT_FIN, COL_PV, COL_RESERVE, COL_MODALITE, COL_TVA, COL_STATUT] if c]
    search_f = st.text_input("🔍 Rechercher", placeholder="Client, chantier...", key="search_f")
    df_f = df.copy()
    if search_f:
        mask = pd.Series([False]*len(df_f), index=df_f.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col: mask |= df_f[col].astype(str).str.contains(search_f, case=False, na=False)
        df_f = df_f[mask]
    if "fact_tab" not in st.session_state: st.session_state["fact_tab"] = "⚠️ À facturer"
    def _on_fact_tab(): st.session_state["fact_tab"] = st.session_state["_fact_tab_radio"]
    tab_fact_choice = st.radio("", ["⚠️ À facturer","✅ Factures émises"], horizontal=True, key="_fact_tab_radio", index=["⚠️ À facturer","✅ Factures émises"].index(st.session_state["fact_tab"]), on_change=_on_fact_tab)
    st.markdown("---")
    if tab_fact_choice == "⚠️ À facturer":
        d = df_f[df_f["_signe"] & ~df_f["_fact_fin"]]
        show_table(d[cols].reset_index(drop=True) if cols else d, "fact_attente")
    else:
        d = df_f[df_f["_fact_fin"]]
        show_table(d[cols].reset_index(drop=True) if cols else d, "fact_ok")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CHANTIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Chantiers":
    page_header("Suivi des Chantiers", "Vue d'ensemble des travaux")
    df["_statut_ch"] = df["_pv"].apply(lambda x: "✅ Terminé" if x else "🟡 En cours")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏗️ En cours", int((~df["_pv"]).sum()))
    c2.metric("💰 Trésorerie en cours", fmt(df[~df["_pv"]]["_montant"].sum()))
    c3.metric("✅ Terminés (PV signé)", int(df["_pv"].sum()))
    c4.metric("💰 CA réalisé", fmt(df[df["_pv"]]["_montant"].sum()))
    st.markdown("<br>", unsafe_allow_html=True)
    search_ch = st.text_input("🔍 Filtrer", placeholder="Client, lieu...", key="search_ch")
    df_ch = df.copy()
    if search_ch:
        mask = pd.Series([False]*len(df_ch), index=df_ch.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col: mask |= df_ch[col].astype(str).str.contains(search_ch, case=False, na=False)
        df_ch = df_ch[mask]
    cols_ch = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ADRESSE, COL_DATE_DEBUT, COL_DATE_FIN, COL_SALARIE, COL_RESERVE, "_statut_ch"] if c]
    valid_rename_map = {COL_CLIENT:"Client", COL_CHANTIER:"Projet / Chantier", COL_MONTANT:"Budget (€)", COL_ADRESSE:"Lieu", COL_DATE_DEBUT:"Début", COL_DATE_FIN:"Fin prévue", COL_SALARIE:"Salarié", COL_RESERVE:"Réserves", "_statut_ch":"État"}

    def has_reserve(val):
        if pd.isna(val) or str(val).strip() == "": return False
        s = str(val).strip().lower()
        if any(k in s for k in ["sans","non","aucune","aucun","no","none","0","faux","false"]): return False
        return True

    df_ch["_has_reserve"] = df_ch[COL_RESERVE].apply(has_reserve) if COL_RESERVE else False
    nb_reserves = int(df_ch["_has_reserve"].sum())
    ch_tab_opts = ["🟡 En cours","✅ Livrés (PV signé)",f"🔒 Avec réserves ({nb_reserves})"]
    if "chantier_tab" not in st.session_state: st.session_state["chantier_tab"] = "🟡 En cours"
    if st.session_state["chantier_tab"] not in ch_tab_opts: st.session_state["chantier_tab"] = ch_tab_opts[0]
    def _on_chantier_tab(): st.session_state["chantier_tab"] = st.session_state["_chantier_tab_radio"]
    tab_ch_choice = st.radio("", ch_tab_opts, horizontal=True, key="_chantier_tab_radio", index=ch_tab_opts.index(st.session_state["chantier_tab"]), on_change=_on_chantier_tab)
    st.markdown("---")
    if tab_ch_choice == "🟡 En cours":
        d = df_ch[~df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) actif(s) — {fmt(d['_montant'].sum())}")
        show_table((d[cols_ch].rename(columns=valid_rename_map) if cols_ch else d).reset_index(drop=True), "ch_cours")
    elif tab_ch_choice == "✅ Livrés (PV signé)":
        d = df_ch[df_ch["_pv"]]
        st.caption(f"{len(d)} livré(s) — {fmt(d['_montant'].sum())}")
        show_table((d[cols_ch].rename(columns=valid_rename_map) if cols_ch else d).reset_index(drop=True), "ch_termines")
    else:
        d = df_ch[df_ch["_has_reserve"]]
        if d.empty: st.success("✅ Aucun chantier avec réserves.")
        else:
            r1, r2, r3 = st.columns(3)
            r1.metric("🔒 Avec réserves", len(d))
            r2.metric("💰 CA concerné", fmt(d['_montant'].sum()))
            r3.metric("🟡 Non livrés", int((d["_has_reserve"] & ~d["_pv"]).sum()))
            show_table((d[cols_ch].rename(columns=valid_rename_map) if cols_ch else d).reset_index(drop=True), "ch_reserves")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PLANNING — CALENDRIER TYPE GOOGLE CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Planning":
    page_header("Planning des Chantiers", "Calendrier des interventions")

    if not COL_DATE_DEBUT or not COL_DATE_FIN:
        st.warning("⚠️ Colonnes de dates non détectées (Date de début / fin des travaux).")
        st.stop()

    today = datetime.now()
    df_plan = df.copy()
    df_plan["_start"] = pd.to_datetime(df_plan[COL_DATE_DEBUT], dayfirst=True, errors="coerce")
    df_plan["_end"]   = pd.to_datetime(df_plan[COL_DATE_FIN],   dayfirst=True, errors="coerce")
    df_plan = df_plan.dropna(subset=["_start","_end"])
    df_plan = df_plan[df_plan["_end"] >= df_plan["_start"]]

    # Parser heures
    def parse_heure(val, default_h=8):
        if pd.isna(val) or str(val).strip() == "":
            return default_h, 0
        s = str(val).strip()
        try:
            parts = s.replace("h",":",1).split(":")
            return int(parts[0]), int(parts[1]) if len(parts)>1 else 0
        except:
            return default_h, 0

    if COL_HEURE_DEB:
        df_plan["_h_deb"] = df_plan[COL_HEURE_DEB].apply(lambda v: parse_heure(v,8)[0] + parse_heure(v,8)[1]/60)
    else:
        df_plan["_h_deb"] = 8.0

    if COL_HEURE_FIN:
        df_plan["_h_fin"] = df_plan[COL_HEURE_FIN].apply(lambda v: parse_heure(v,17)[0] + parse_heure(v,17)[1]/60)
    else:
        df_plan["_h_fin"] = 17.0

    def get_statut_code(row):
        if row["_pv"]: return "termine"
        if row["_end"].date() < today.date(): return "retard"
        return "en-cours"

    df_plan["_statut_code"] = df_plan.apply(get_statut_code, axis=1)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🟡 En cours", int((df_plan["_statut_code"]=="en-cours").sum()))
    k2.metric("🔴 En retard", int((df_plan["_statut_code"]=="retard").sum()))
    k3.metric("✅ Terminés", int((df_plan["_statut_code"]=="termine").sum()))
    k4.metric("📅 Cette semaine", int(((df_plan["_start"].dt.date <= (today+timedelta(days=7)).date()) & (df_plan["_end"].dt.date >= today.date())).sum()))

    st.markdown("<br>", unsafe_allow_html=True)

    if "plan_view_tab" not in st.session_state: st.session_state["plan_view_tab"] = "📅 Semaine"
    _plan_opts = ["📅 Semaine", "📆 Mois", "📊 Gantt", "📋 Liste"]
    def _on_plan_view(): st.session_state["plan_view_tab"] = st.session_state["_plan_view_radio"]
    view_mode = st.radio("Vue", _plan_opts, horizontal=True, key="_plan_view_radio", index=_plan_opts.index(st.session_state["plan_view_tab"]), on_change=_on_plan_view)

    JOURS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    MOIS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    COLOR_MAP = {"en-cours": "#3B82F6", "retard": "#EF4444", "termine": "#10B981"}
    BG_MAP = {"en-cours": "rgba(59,130,246,0.15)", "retard": "rgba(239,68,68,0.15)", "termine": "rgba(16,185,129,0.15)"}

    # ── VUE SEMAINE ──────────────────────────────────────────────────────────
    if view_mode == "📅 Semaine":
        if "plan_week_offset" not in st.session_state: st.session_state["plan_week_offset"] = 0

        offset = st.session_state["plan_week_offset"]
        monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
        week_days = [monday + timedelta(days=i) for i in range(7)]

        nav1, nav2, nav3, nav4 = st.columns([1, 2, 1, 1])
        with nav1:
            if st.button("◀ Semaine préc.", use_container_width=True):
                st.session_state["plan_week_offset"] -= 1; st.rerun()
        with nav2:
            st.markdown(f"<div style='text-align:center;font-family:Syne,sans-serif;font-weight:700;font-size:1rem;padding-top:6px;'>{monday.strftime('%d %B')} – {week_days[-1].strftime('%d %B %Y')}</div>", unsafe_allow_html=True)
        with nav3:
            if st.button("Semaine suiv. ▶", use_container_width=True):
                st.session_state["plan_week_offset"] += 1; st.rerun()
        with nav4:
            if st.button("Aujourd'hui", use_container_width=True):
                st.session_state["plan_week_offset"] = 0; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Heures affichées
        HOUR_START = 7
        HOUR_END = 20
        HOUR_HEIGHT = 50  # px par heure

        total_height = (HOUR_END - HOUR_START) * HOUR_HEIGHT
        now_offset = (today.hour + today.minute/60 - HOUR_START) * HOUR_HEIGHT if HOUR_START <= today.hour < HOUR_END else -1

        # Construire le HTML du calendrier
        # Colonnes : heure + 7 jours
        col_width_pct = 100 / 8

        html_cal = f"""
        <div style="font-family:'DM Sans',sans-serif;background:var(--bg-card,#111e30);border:1px solid rgba(255,255,255,0.06);border-radius:12px;overflow:hidden;">
        <!-- HEADER -->
        <div style="display:grid;grid-template-columns:60px repeat(7,1fr);border-bottom:1px solid rgba(255,255,255,0.08);">
            <div style="padding:8px;background:rgba(0,0,0,0.1);"></div>
        """

        for d in week_days:
            is_today = d.date() == today.date()
            day_color = "#3B82F6" if is_today else "rgba(255,255,255,0.5)"
            day_bg = "rgba(59,130,246,0.12)" if is_today else "transparent"
            html_cal += f"""
            <div style="padding:8px 4px;text-align:center;background:{day_bg};border-left:1px solid rgba(255,255,255,0.05);">
                <div style="font-size:0.7rem;font-weight:600;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.05em;">{JOURS_FR[d.weekday()]}</div>
                <div style="font-size:1.1rem;font-weight:700;color:{day_color};font-family:Syne,sans-serif;">{d.day}</div>
            </div>
            """

        html_cal += "</div>"

        # BODY
        html_cal += f'<div style="position:relative;display:grid;grid-template-columns:60px repeat(7,1fr);height:{total_height}px;overflow-y:auto;">'

        # Lignes d'heures
        for h in range(HOUR_START, HOUR_END):
            top = (h - HOUR_START) * HOUR_HEIGHT
            html_cal += f"""
            <div style="position:absolute;left:0;right:0;top:{top}px;display:grid;grid-template-columns:60px repeat(7,1fr);pointer-events:none;z-index:0;">
                <div style="text-align:right;padding-right:8px;padding-top:2px;font-size:0.62rem;color:rgba(255,255,255,0.25);line-height:1;">{h:02d}h</div>
                {"".join(['<div style="border-left:1px solid rgba(255,255,255,0.04);border-top:1px solid rgba(255,255,255,0.04);height:' + str(HOUR_HEIGHT) + 'px;"></div>' for _ in range(7)])}
            </div>
            """

        # Ligne "maintenant"
        if now_offset >= 0 and week_days[0].date() <= today.date() <= week_days[-1].date():
            day_idx = today.weekday()
            col_left = 60 + day_idx * ((total_height) // (HOUR_END - HOUR_START))  # approx
            html_cal += f"""
            <div style="position:absolute;top:{now_offset}px;left:60px;right:0;height:2px;background:#EF4444;z-index:5;pointer-events:none;">
                <div style="width:8px;height:8px;border-radius:50%;background:#EF4444;position:absolute;left:-4px;top:-3px;"></div>
            </div>
            """

        # Événements
        for _, ev in df_plan.iterrows():
            ev_start = ev["_start"].date()
            ev_end   = ev["_end"].date()
            h_deb = float(ev["_h_deb"])
            h_fin = float(ev["_h_fin"])
            statut = ev["_statut_code"]
            color  = COLOR_MAP[statut]
            bg     = BG_MAP[statut]
            client_name = str(ev[COL_CLIENT]) if COL_CLIENT else ""
            chantier_name = str(ev[COL_CHANTIER]) if COL_CHANTIER else client_name
            salarie_name = str(ev[COL_SALARIE]) if COL_SALARIE and not pd.isna(ev.get(COL_SALARIE, "")) else ""

            for di, wd in enumerate(week_days):
                if ev_start <= wd.date() <= ev_end:
                    top_px = max(0, (h_deb - HOUR_START) * HOUR_HEIGHT)
                    height_px = max(20, (h_fin - h_deb) * HOUR_HEIGHT)
                    left_pct = (di + 1) / 8 * 100
                    width_pct = 1/8 * 100

                    html_cal += f"""
                    <div style="position:absolute;top:{top_px}px;left:calc({left_pct}% + 2px);width:calc({width_pct}% - 4px);height:{height_px}px;background:{bg};border-left:3px solid {color};border-radius:4px;padding:3px 5px;overflow:hidden;z-index:2;cursor:pointer;" title="{chantier_name} — {client_name}">
                        <div style="font-size:0.68rem;font-weight:700;color:{color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{chantier_name}</div>
                        <div style="font-size:0.6rem;color:rgba(255,255,255,0.5);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{client_name}{' • ' + salarie_name if salarie_name else ''}</div>
                        <div style="font-size:0.58rem;color:rgba(255,255,255,0.35);">{int(h_deb):02d}h – {int(h_fin):02d}h</div>
                    </div>
                    """

        html_cal += "</div></div>"

        components.html(html_cal, height=total_height + 80, scrolling=True)

    # ── VUE MOIS ─────────────────────────────────────────────────────────────
    elif view_mode == "📆 Mois":
        if "plan_year" not in st.session_state: st.session_state["plan_year"] = today.year
        if "plan_month" not in st.session_state: st.session_state["plan_month"] = today.month

        nav1, nav2, nav3 = st.columns([1,2,1])
        with nav1:
            if st.button("◀ Mois préc.", use_container_width=True):
                if st.session_state["plan_month"] == 1: st.session_state["plan_month"] = 12; st.session_state["plan_year"] -= 1
                else: st.session_state["plan_month"] -= 1
                st.rerun()
        with nav2:
            st.markdown(f"<h2 style='text-align:center;margin:0;font-family:Syne,sans-serif;font-size:1.3rem;'>{MOIS_FR[st.session_state['plan_month']]} {st.session_state['plan_year']}</h2>", unsafe_allow_html=True)
        with nav3:
            if st.button("Mois suiv. ▶", use_container_width=True):
                if st.session_state["plan_month"] == 12: st.session_state["plan_month"] = 1; st.session_state["plan_year"] += 1
                else: st.session_state["plan_month"] += 1
                st.rerun()

        sel_y, sel_m = st.session_state["plan_year"], st.session_state["plan_month"]
        cal_grid = calendar.monthcalendar(sel_y, sel_m)

        with st.container(border=True):
            cols_h = st.columns(7)
            for i, d_name in enumerate(JOURS_FR):
                cols_h[i].markdown(f"<div style='text-align:center;font-weight:700;font-size:0.75rem;color:var(--primary);text-transform:uppercase;letter-spacing:0.05em;padding:4px 0;'>{d_name}</div>", unsafe_allow_html=True)

            for week in cal_grid:
                cols_w = st.columns(7)
                for i, day in enumerate(week):
                    if day != 0:
                        current_date = datetime(sel_y, sel_m, day).date()
                        evs = df_plan[(df_plan["_start"].dt.date <= current_date) & (df_plan["_end"].dt.date >= current_date)]
                        is_today_day = current_date == today.date()
                        bg_day = "rgba(59,130,246,0.15)" if is_today_day else "transparent"
                        color_day = "#60A5FA" if is_today_day else "var(--text-main)"

                        ev_dots = ""
                        if not evs.empty:
                            for _, ev in evs.head(3).iterrows():
                                sc = ev["_statut_code"]
                                ev_dots += f"<div style='width:6px;height:6px;border-radius:50%;background:{COLOR_MAP[sc]};display:inline-block;margin:1px;'></div>"

                        with cols_w[i]:
                            st.markdown(f"""<div style="min-height:60px;background:{bg_day};border:1px solid var(--border);border-radius:6px;padding:4px;margin:1px;">
                                <div style="font-weight:700;font-size:0.82rem;color:{color_day};">{day}</div>
                                <div style="margin-top:3px;">{ev_dots}</div>
                                <div style="font-size:0.6rem;color:var(--text-muted);">{len(evs) if len(evs)>0 else ''}</div>
                            </div>""", unsafe_allow_html=True)
                            if len(evs) > 0:
                                if st.button("", key=f"d_{sel_y}_{sel_m}_{day}", help=f"{len(evs)} chantier(s)"):
                                    st.session_state["selected_date"] = datetime(sel_y, sel_m, day)

        if "selected_date" in st.session_state:
            sd = st.session_state["selected_date"]
            st.markdown(f"### 📋 Chantiers du {sd.strftime('%d/%m/%Y')}")
            day_events = df_plan[(df_plan["_start"].dt.date <= sd.date()) & (df_plan["_end"].dt.date >= sd.date())]
            if not day_events.empty:
                for _, row in day_events.iterrows():
                    color = COLOR_MAP[row['_statut_code']]
                    sal = str(row[COL_SALARIE]) if COL_SALARIE else ""
                    h_deb = row["_h_deb"]; h_fin = row["_h_fin"]
                    st.markdown(f"""<div style="border-left:4px solid {color};padding:10px 14px;background:var(--bg-surface);border-radius:0 8px 8px 0;margin-bottom:8px;">
                        <div style="font-weight:700;color:var(--text-main);font-family:Syne,sans-serif;">{row[COL_CHANTIER] if COL_CHANTIER else ''}</div>
                        <div style="font-size:0.82rem;color:var(--text-muted);margin-top:3px;">👤 {row[COL_CLIENT] if COL_CLIENT else ''}{' • 👷 ' + sal if sal else ''}</div>
                        <div style="font-size:0.8rem;color:{color};margin-top:3px;">🕐 {int(h_deb):02d}h{int((h_deb%1)*60):02d} – {int(h_fin):02d}h{int((h_fin%1)*60):02d}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Aucun chantier ce jour.")

    # ── GANTT ─────────────────────────────────────────────────────────────────
    elif view_mode == "📊 Gantt":
        df_gantt = df_plan.sort_values("_start")
        if df_gantt.empty:
            st.info("Aucune donnée de planning.")
        else:
            fig_gantt = px.timeline(df_gantt, x_start="_start", x_end="_end", y=COL_CHANTIER or COL_CLIENT, color="_statut_code", color_discrete_map=COLOR_MAP)
            fig_gantt.update_layout(paper_bgcolor=chart_bg, plot_bgcolor=chart_bg, font_color=chart_font, font_family="DM Sans", margin=dict(t=20,b=20,l=10,r=10), height=max(400, len(df_gantt)*42+80), xaxis=dict(gridcolor=chart_grid), yaxis=dict(gridcolor=chart_grid, autorange="reversed"))
            st.plotly_chart(fig_gantt, use_container_width=True)

    # ── LISTE ─────────────────────────────────────────────────────────────────
    elif view_mode == "📋 Liste":
        filtre_statut = st.multiselect("Filtrer", ["En cours","En retard","Terminé"], default=["En cours","En retard"], key="list_filter")
        code_map = {"En cours":"en-cours","En retard":"retard","Terminé":"termine"}
        df_list = df_plan[df_plan["_statut_code"].isin([code_map[f] for f in filtre_statut])].sort_values("_start").copy()
        if df_list.empty:
            st.info("Aucun chantier.")
        else:
            df_list["_mois_str"] = df_list["_start"].dt.strftime("%B %Y").str.capitalize()
            df_list["_mois_ord"] = df_list["_start"].dt.to_period("M")
            label_map = {"en-cours":"En cours","retard":"En retard","termine":"Terminé"}
            border_map = {"en-cours":"rgba(59,130,246,0.25)","retard":"rgba(239,68,68,0.25)","termine":"rgba(16,185,129,0.25)"}

            for period, group in df_list.groupby("_mois_ord", sort=True):
                st.markdown(f'<div style="font-size:0.75rem;font-weight:700;color:var(--text-muted);letter-spacing:0.06em;text-transform:uppercase;padding:10px 0 5px;border-bottom:1px solid var(--border);margin-bottom:6px;">📅 {group["_mois_str"].iloc[0]} — {len(group)} chantier(s)</div>', unsafe_allow_html=True)
                for _, row in group.iterrows():
                    client_v = str(row[COL_CLIENT]) if COL_CLIENT else ""
                    chantier_v = str(row[COL_CHANTIER]) if COL_CHANTIER else client_v
                    adresse_v = str(row[COL_ADRESSE]) if COL_ADRESSE else ""
                    sal_v = str(row[COL_SALARIE]) if COL_SALARIE else ""
                    h_deb = row["_h_deb"]; h_fin = row["_h_fin"]
                    montant_v = fmt(row["_montant"])
                    debut_v = row["_start"].strftime("%d/%m/%Y")
                    fin_v = row["_end"].strftime("%d/%m/%Y")
                    duree_v = (row["_end"] - row["_start"]).days + 1
                    statut = row["_statut_code"]
                    color = COLOR_MAP[statut]
                    st.markdown(f"""<div class="erp-card" style="border-left:3px solid {color};padding:12px 16px;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:0.92rem;font-family:Syne,sans-serif;">{chantier_v}</div>
                                <div style="font-size:0.78rem;color:var(--text-muted);margin-top:2px;">👤 {client_v}{' • 📍 ' + adresse_v if adresse_v and adresse_v!='nan' else ''}{' • 👷 ' + sal_v if sal_v and sal_v!='nan' else ''}</div>
                                <div style="margin-top:5px;display:flex;gap:8px;align-items:center;">
                                    <span style="display:inline-block;padding:2px 8px;border-radius:99px;font-size:0.68rem;font-weight:700;background:{color}22;color:{color};border:1px solid {color}44;">{label_map[statut]}</span>
                                    <span style="font-size:0.72rem;color:var(--text-dim);">{duree_v} jour(s)</span>
                                    <span style="font-size:0.72rem;color:var(--text-dim);">🕐 {int(h_deb):02d}h – {int(h_fin):02d}h</span>
                                </div>
                            </div>
                            <div style="text-align:right;flex-shrink:0;">
                                <div style="font-weight:700;color:{color};font-size:0.95rem;">{montant_v}</div>
                                <div style="font-size:0.72rem;color:var(--text-muted);margin-top:3px;">📅 {debut_v}</div>
                                <div style="font-size:0.72rem;color:var(--text-muted);">→ {fin_v}</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : TOUS LES DOSSIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Tous les dossiers":
    page_header("Tous les dossiers", f"{len(df)} dossiers au total")
    search = st.text_input("🔍 Recherche globale", placeholder="Client, chantier, numéro...", key="search_all")
    d = df.copy()
    if search:
        mask = pd.Series([False]*len(d), index=d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col: mask |= d[col].astype(str).str.contains(search, case=False, na=False)
        d = d[mask]
    st.caption(f"{len(d)} dossier(s) trouvé(s)")
    drop_cols = ["_montant","_signe","_fact_fin","_pv","_acompte1","_acompte2","_reste","_statut_ch","_start","_end","_statut_code","_mois_str","_mois_ord","_h_deb","_h_fin","_has_reserve"]
    show_table(d.drop(columns=drop_cols, errors="ignore").reset_index(drop=True), "all")
