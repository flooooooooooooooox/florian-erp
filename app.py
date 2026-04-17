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
import re
from auth import check_login, logout, admin_panel, get_user_credentials, AVAILABLE_PAGES
import streamlit.components.v1 as components
from activity_log import log_activity, read_activity_logs

st.set_page_config(
    page_title="Floxia ERP",
    page_icon="F",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── THEME (WHITE / DARK MODE) ──────────────────────────────────────────────────
if "themes" not in st.session_state:
    st.session_state.themes = "dark"

def toggle_theme():
    st.session_state.themes = "light" if st.session_state.themes == "dark" else "dark"

if st.session_state.themes == "light":
    theme_css_vars = """
    --bg-app: #F8FAFC;
    --bg-surface: #F1F5F9;
    --bg-card: #FFFFFF;
    --bg-sidebar: #F1F5F9;
    --text-main: #0F172A;
    --text-muted: #475569;
    --text-dim: #94A3B8;
    --border: rgba(0,0,0,0.1);
    --border-hover: rgba(79,142,247,0.5);
    """
    chart_bg = "#FFFFFF"
    chart_font = "#0F172A"
    chart_grid = "#E2E8F0"
else:
    theme_css_vars = """
    --bg-app: #080f1a;
    --bg-surface: #0f1e30;
    --bg-card: #132238;
    --bg-sidebar: #0f1e30;
    --text-main: #e8f0fe;
    --text-muted: #6b84a3;
    --text-dim: #3d5473;
    --border: rgba(255,255,255,0.06);
    --border-hover: rgba(79,142,247,0.35);
    """
    chart_bg = "rgba(0,0,0,0)"
    chart_font = "#e8f0fe"
    chart_grid = "rgba(255,255,255,0.06)"

# ── CSS PREMIUM ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {{
    {theme_css_vars}
    --primary: #4f8ef7;
    --primary-glow: rgba(79,142,247,0.15);
    --success: #00d68f;
    --success-glow: rgba(0,214,143,0.12);
    --warning: #ffb84d;
    --warning-glow: rgba(255,184,77,0.12);
    --danger: #ff5c7a;
    --radius: 14px;
    --radius-sm: 8px;
}}

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg-app) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text-main);
    -webkit-font-smoothing: antialiased;
}}

[data-testid="stDataFrame"] div[role="grid"] div[role="row"]:hover {{
    background-color: rgba(79, 142, 247, 0.15) !important;
    transition: background 0.2s ease;
}}

[data-testid="stSidebar"] {{
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] > div {{ padding: 0 !important; }}

::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--text-dim); border-radius: 99px; }}

[data-testid="stMetric"] {{
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 22px !important;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
}}
[data-testid="stMetric"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary), transparent);
    opacity: 0.6;
}}
[data-testid="stMetric"]:hover {{ transform: translateY(-2px); border-color: var(--border-hover); }}
[data-testid="stMetric"] label {{
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}
[data-testid="stMetricValue"] {{
    color: var(--text-main) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: var(--bg-surface);
    border-radius: var(--radius-sm);
    padding: 4px;
    border: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 6px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 8px 18px !important;
    transition: transform 0.15s ease, background 0.15s ease, color 0.15s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    transform: scale(1.04);
    background: rgba(79,142,247,0.08) !important;
}}
.stTabs [aria-selected="true"] {{
    background: var(--primary) !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 12px rgba(79,142,247,0.3) !important;
}}

.stButton > button {{
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    padding: 8px 16px !important;
}}
.stButton > button:hover {{
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: var(--primary-glow) !important;
    transform: translateY(-1px);
}}

.stTextInput input, .stNumberInput input, .stSelectbox select,
[data-testid="stTextArea"] textarea {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-main) !important;
    font-family: 'Inter', sans-serif !important;
}}

[data-testid="stDataFrame"] {{
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
}}

hr {{ border-color: var(--border) !important; margin: 16px 0 !important; }}

[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {{
    padding: 10px 14px;
    background: transparent;
    border-radius: var(--radius-sm);
    cursor: pointer;
    margin-bottom: 2px;
    border: 1px solid transparent;
    transition: all 0.15s ease;
    width: 100%;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {{ background: var(--bg-card); border-color: var(--border); }}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover p {{ transform: scale(1.03); transform-origin: left center; }}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
    background: linear-gradient(135deg, var(--primary-glow), rgba(79,142,247,0.08)) !important;
    border-color: rgba(79,142,247,0.4) !important;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {{ color: var(--primary) !important; font-weight: 700 !important; }}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p {{ margin: 0; font-size: 0.92rem; color: var(--text-muted); }}

section.main .stRadio > div[role="radiogroup"] {{
    display: flex;
    flex-direction: row;
    gap: 6px;
    background: var(--bg-surface);
    border-radius: var(--radius-sm);
    padding: 4px;
    border: 1px solid var(--border);
    width: fit-content;
    margin-bottom: 4px;
}}
section.main .stRadio > div[role="radiogroup"] > label {{
    padding: 7px 16px !important;
    background: transparent;
    border-radius: 6px !important;
    cursor: pointer;
    border: none !important;
    transition: all 0.15s ease;
    white-space: nowrap;
}}
section.main .stRadio > div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}
section.main .stRadio > div[role="radiogroup"] > label p {{
    margin: 0 !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
}}
section.main .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
    background: var(--primary) !important;
    box-shadow: 0 2px 12px rgba(79,142,247,0.3) !important;
}}
section.main .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {{
    color: #fff !important;
    font-weight: 600 !important;
}}
section.main .stRadio > div[role="radiogroup"] > label:hover:not([data-checked="true"]) {{
    background: var(--bg-card) !important;
}}

.pulse-dot {{
    display: inline-block; width: 7px; height: 7px;
    border-radius: 50%; background: var(--success);
    animation: pulse-anim 2s ease-in-out infinite;
    margin-right: 6px; vertical-align: middle;
}}
@keyframes pulse-anim {{ 0%, 100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: 0.4; transform: scale(0.85); }} }}

.page-header {{ padding: 8px 0 24px; border-bottom: 1px solid var(--border); margin-bottom: 28px; }}
.page-header h1 {{ font-family: 'Inter', sans-serif !important; font-size: 1.9rem !important; font-weight: 800 !important; letter-spacing: -0.03em; margin: 0 !important; color: var(--text-main) !important; }}
.page-header .subtitle {{ color: var(--text-muted); font-size: 0.88rem; margin-top: 4px; }}
.page-header {{
    background: linear-gradient(180deg, rgba(79,142,247,0.06), rgba(79,142,247,0.00));
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px 12px;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.ceo-hero {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 24px 26px;
    margin: 0 0 18px 0;
    background:
        radial-gradient(circle at top right, rgba(255,184,77,0.16), transparent 24%),
        radial-gradient(circle at left center, rgba(79,142,247,0.18), transparent 28%),
        linear-gradient(135deg, rgba(19,34,56,0.98), rgba(10,17,30,0.98));
    box-shadow: 0 24px 60px rgba(0,0,0,0.22);
}
.ceo-hero-title {
    font-size: 2.15rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    color: #f8fbff;
    margin-bottom: 6px;
}
.ceo-hero-subtitle {
    font-size: 0.95rem;
    color: #9fb3cc;
    max-width: 900px;
    line-height: 1.55;
}
.ceo-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}
.ceo-chip {
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.04);
    color: #dbe8ff;
    border-radius: 999px;
    padding: 8px 12px;
    font-size: 0.8rem;
    font-weight: 600;
}
.ceo-section-title {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 10px 0 10px;
}
.ceo-actions {
    border: 1px solid var(--border);
    background: linear-gradient(135deg, rgba(79,142,247,0.10), rgba(255,184,77,0.08));
    border-radius: 18px;
    padding: 14px 16px;
    margin-bottom: 14px;
}
.ceo-kpi-card {
    border-radius: 20px;
    border: 1px solid var(--border);
    padding: 18px 18px 16px;
    min-height: 148px;
    position: relative;
    overflow: hidden;
    background: linear-gradient(160deg, rgba(18,31,50,0.98), rgba(10,19,33,0.98));
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 18px 38px rgba(0,0,0,0.16);
}
.ceo-kpi-top {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin-bottom:16px;
}
.ceo-kpi-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size: 1.1rem;
    font-weight: 800;
    color: #fff;
}
.ceo-kpi-label {
    color: var(--text-dim);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 800;
}
.ceo-kpi-value {
    color: #f8fbff;
    font-size: 2rem;
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin-bottom: 8px;
}
.ceo-kpi-delta {
    font-size: 0.84rem;
    font-weight: 700;
}
.ceo-kpi-bar {
    margin-top: 14px;
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    overflow: hidden;
}
.ceo-kpi-fill {
    height: 100%;
    border-radius: 999px;
}
.ceo-card {
    border: 1px solid var(--border);
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(19,34,56,0.98), rgba(12,23,40,0.98));
    padding: 18px;
    margin-bottom: 14px;
    box-shadow: 0 12px 28px rgba(0,0,0,0.12);
}
.ceo-card-title {
    font-size: 1rem;
    font-weight: 800;
    color: #f3f8ff;
    margin-bottom: 6px;
}
.ceo-card-subtitle {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 12px;
}
.ceo-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 0.76rem;
    font-weight: 800;
}
[data-testid="stDataFrame"] div[role="grid"] div[role="row"]:nth-child(even) {
    background-color: rgba(255,255,255,0.015) !important;
}
[data-testid="stDataFrame"] div[role="columnheader"] {
    background: linear-gradient(180deg, rgba(79,142,247,0.18), rgba(79,142,247,0.03)) !important;
    color: #eaf2ff !important;
    font-weight: 800 !important;
    border-bottom: 1px solid rgba(79,142,247,0.18) !important;
}
</style>
""", unsafe_allow_html=True)

# ── AUTH ───────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()

# ── Conditions d'utilisation ──────────────────────────────────────────────────
# Objectif : rappeler que l'accès dépend des droits utilisateur (`allowed_pages`)
# et éviter les confusions lors de la gestion des accès.
_TERMS_VERSION = "v1"
_username = st.session_state.get("username", "")
_terms_key = f"accepted_terms_{_username}"
if _username and st.session_state.get(_terms_key) != _TERMS_VERSION:
    st.markdown("<div class='page-header'><h1>Conditions d'utilisation</h1></div>", unsafe_allow_html=True)
    st.markdown(
        "En utilisant cette application, vous acceptez que : "
        "`vos droits d'accès` déterminent les pages/fonctionnalités visibles (champ `allowed_pages`), "
        "que vos actions peuvent déclencher des automatisations via `n8n` (webhooks), "
        "et que vous vous engagez à ne pas divulguer d'informations internes ou sensibles."
    )
    accept = st.checkbox(
        "J'ai lu et j'accepte les conditions d'utilisation",
        key="accept_terms_checkbox",
    )
    if accept:
        st.session_state[_terms_key] = _TERMS_VERSION
        st.rerun()
    st.stop()

# ── CONFIG GOOGLE SHEETS & DRIVE ───────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource(show_spinner=False)
def get_spreadsheet(username: str):
    sheet_name, gsa_json = get_user_credentials(username)
    if not sheet_name or not gsa_json:
        return None, "Credentials non configurés."
    try:
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(sheet_name)
        return sh, None
    except Exception as e:
        return None, str(e)

def get_worksheet(username: str, tab_name: str):
    sh, err = get_spreadsheet(username)
    if err or not sh:
        return None, err or "Impossible d'ouvrir le Google Sheet."
    try:
        ws = sh.worksheet(tab_name)
        return ws, None
    except gspread.exceptions.WorksheetNotFound:
        return None, f"Onglet '{tab_name}' introuvable dans le Google Sheet."
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

@st.cache_data(ttl=180, show_spinner=False)
def get_sheet_data(username: str):
    cache_bucket = st.session_state.setdefault("_offline_sheet_cache", {})
    st.session_state["_data_source_notice"] = ""
    try:
        sh, err = get_spreadsheet(username)
        if err or not sh:
            cached_df = cache_bucket.get(username)
            if isinstance(cached_df, pd.DataFrame) and not cached_df.empty:
                st.session_state["_data_source_notice"] = "Connexion lente/instable : affichage des dernières données locales."
                _track_sync_status("suivie", fallback_used=True)
                return cached_df.copy(), None
            return pd.DataFrame(), err or "Impossible d'ouvrir le Google Sheet."
        try:
            ws = sh.worksheet("suivie")
        except Exception:
            ws = sh.sheet1
        all_values = None
        last_exc = None
        for _ in range(2):
            try:
                all_values = ws.get_all_values()
                break
            except Exception as ex:
                last_exc = ex
                time.sleep(0.6)
        if all_values is None and last_exc is not None:
            raise last_exc
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
        cache_bucket[username] = df.copy()
        _track_sync_status("suivie", fallback_used=False)
        return df, None
    except Exception as e:
        cached_df = cache_bucket.get(username)
        if isinstance(cached_df, pd.DataFrame) and not cached_df.empty:
            st.session_state["_data_source_notice"] = "Connexion faible : données locales réutilisées temporairement."
            _track_sync_status("suivie", fallback_used=True)
            return cached_df.copy(), None
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
    if pd.isna(val):
        return False
    s = str(val).strip()
    return s in {"✅","✓","✔","TRUE","true","oui","Oui","OUI","1","x","X","yes","Yes"} or "✅" in s

def fcol(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in str(c).strip().lower():
                return c
    return None

def _normalize_date_text(value) -> str:
    raw = str(value).strip()
    if not raw or raw.lower() in ("nan", "none", "nat", "null"):
        return ""
    txt = (
        raw.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace("_", " ")
        .replace("-", "/")
    )
    txt = re.sub(r"\s+", " ", txt).strip()
    txt = (
        txt.replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("ë", "e")
        .replace("à", "a")
        .replace("â", "a")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ô", "o")
        .replace("ù", "u")
        .replace("û", "u")
        .replace("ü", "u")
        .replace("ç", "c")
    )
    txt = txt.replace("1er ", "1 ")
    month_map = {
        "janvier": "january", "janv": "january",
        "fevrier": "february", "fevr": "february", "fev": "february",
        "mars": "march",
        "avril": "april", "avr": "april",
        "mai": "may",
        "juin": "june",
        "juillet": "july", "juil": "july",
        "aout": "august",
        "septembre": "september", "sept": "september",
        "octobre": "october", "oct": "october",
        "novembre": "november", "nov": "november",
        "decembre": "december", "dec": "december",
    }
    for fr, en in month_map.items():
        txt = re.sub(rf"\b{fr}\b", en, txt)
    return txt

def parse_flexible_date(value):
    s = _normalize_date_text(value)
    if not s:
        return pd.NaT
    # Formats partiels / placeholders: on complète au 1er du mois.
    m = re.match(r"^(\d{4})/(\d{1,2})/(yyyy|yy|dd)$", s)
    if m:
        return pd.to_datetime(f"{int(m.group(1)):04d}/{int(m.group(2)):02d}/01", format="%Y/%m/%d", errors="coerce")
    m = re.match(r"^(\d{4})/(\d{1,2})$", s)
    if m:
        return pd.to_datetime(f"{int(m.group(1)):04d}/{int(m.group(2)):02d}/01", format="%Y/%m/%d", errors="coerce")
    m = re.match(r"^(\d{1,2})/(\d{4})$", s)
    if m:
        return pd.to_datetime(f"{int(m.group(2)):04d}/{int(m.group(1)):02d}/01", format="%Y/%m/%d", errors="coerce")
    m = re.match(r"^([a-z]{3,12})\s+(\d{4})$", s)
    if m:
        return pd.to_datetime(f"01 {m.group(1)} {m.group(2)}", format="%d %B %Y", errors="coerce")
    m = re.match(r"^(\d{4})\s+([a-z]{3,12})$", s)
    if m:
        return pd.to_datetime(f"01 {m.group(2)} {m.group(1)}", format="%d %B %Y", errors="coerce")
    m = re.match(r"^(\d{4})$", s)
    if m:
        return pd.to_datetime(f"{int(m.group(1)):04d}/01/01", format="%Y/%m/%d", errors="coerce")
    # Essais explicites pour couvrir un maximum de formats usuels.
    for fmt in [
        "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
        "%Y/%m/%d %H:%M", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M",
        "%Y/%m/%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S",
        "%d %B %Y", "%B %d %Y", "%d %b %Y", "%b %d %Y",
    ]:
        try:
            return pd.to_datetime(s, format=fmt, errors="raise")
        except Exception:
            pass
    dt1 = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if not pd.isna(dt1):
        return dt1
    return pd.to_datetime(s, dayfirst=False, errors="coerce")

def parse_flexible_series(series: pd.Series) -> pd.Series:
    return series.apply(parse_flexible_date)

def safe_slug(value: str) -> str:
    raw = str(value or "").strip()
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", raw)
    return cleaned or "default"

N8N_TIMEOUT_SECONDS = 30

def _log_send_event(endpoint: str, status_code=None, error_msg=None):
    logs = st.session_state.setdefault("_send_logs", [])
    logs.insert(0, {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoint": endpoint,
        "status": status_code if status_code is not None else "ERR",
        "error": (str(error_msg)[:180] if error_msg else ""),
    })
    st.session_state["_send_logs"] = logs[:30]

def post_n8n(endpoint: str, payload: dict):
    try:
        resp = requests.post(
            endpoint,
            json=payload,
            timeout=N8N_TIMEOUT_SECONDS,
            headers={"Content-Type": "application/json"},
        )
        actor = st.session_state.get("username", "inconnu")
        action_name = f"webhook_envoye_http_{resp.status_code}"
        target_name = payload.get("num_devis") or payload.get("numero_devis") or payload.get("nom_client") or endpoint
        log_activity(actor, action_name, target=str(target_name), details={"endpoint": endpoint})
        if resp.status_code not in (200, 201):
            _log_send_event(endpoint, status_code=resp.status_code, error_msg=resp.text[:180])
        return resp, None
    except requests.exceptions.Timeout:
        _log_send_event(endpoint, error_msg="timeout")
        log_activity(st.session_state.get("username", "inconnu"), "webhook_timeout", target=endpoint)
        return None, "timeout"
    except Exception as ex:
        _log_send_event(endpoint, error_msg=str(ex))
        log_activity(st.session_state.get("username", "inconnu"), "webhook_erreur", target=endpoint, details={"error": str(ex)[:180]})
        return None, str(ex)


def compute_chantier_progress(start_val, end_val, is_finished=False):
    if is_finished:
        return 100
    start_dt = parse_flexible_date(start_val)
    end_dt = parse_flexible_date(end_val)
    if pd.isna(start_dt) or pd.isna(end_dt):
        return 0
    start_date = start_dt.date()
    end_date = end_dt.date()
    today_date = datetime.now().date()
    if end_date < start_date:
        return 0
    if today_date <= start_date:
        return 0
    if today_date >= end_date:
        return 100
    total_days = max((end_date - start_date).days, 1)
    elapsed_days = max((today_date - start_date).days, 0)
    return min(100, max(0, int(round((elapsed_days / total_days) * 100))))


def chantier_status_meta(progress_pct, is_finished=False):
    if is_finished or progress_pct >= 100:
        return "Termine", "#00d68f", "rgba(0,214,143,0.14)"
    if progress_pct <= 0:
        return "A demarrer", "#94a3b8", "rgba(148,163,184,0.12)"
    return "En cours", "#4f8ef7", "rgba(79,142,247,0.14)"

def show_data_source_error(message: str, clear_fn=None, retry_key: str = "retry_data_source"):
    st.error(message)
    st.info("La source est peut-être lente/indisponible. Réessaie dans quelques secondes.")
    if st.button("Réessayer", key=retry_key):
        if clear_fn:
            clear_fn()
        st.rerun()

def clear_cache_if_exists(func_name: str):
    fn = globals().get(func_name)
    if fn and hasattr(fn, "clear"):
        fn.clear()

def _track_sync_status(source_key: str, fallback_used: bool):
    sync_meta = st.session_state.setdefault("_sync_meta", {})
    now_str = datetime.now().strftime("%H:%M:%S")
    item = sync_meta.get(source_key, {})
    item["last_attempt"] = now_str
    if fallback_used:
        item["fallback"] = True
    else:
        item["fallback"] = False
        item["last_success"] = now_str
    sync_meta[source_key] = item
    st.session_state["_sync_meta"] = sync_meta

def render_sync_badge():
    sync_meta = st.session_state.get("_sync_meta", {})
    if not sync_meta:
        return
    fallback_active = any(v.get("fallback") for v in sync_meta.values())
    latest_success = max([v.get("last_success", "") for v in sync_meta.values()] or [""])
    if fallback_active:
        st.caption(f"📶 Connexion faible — données locales (fallback). Dernière synchro: {latest_success or 'n/a'}")
    else:
        st.caption(f"✅ Synchro en ligne — dernière mise à jour: {latest_success or 'n/a'}")

def get_sheet_values_resilient(username: str, tab_name: str, cache_slot: str, retries: int = 2):
    bucket = st.session_state.setdefault("_offline_tab_values_cache", {})
    ws, err = get_worksheet(username, tab_name)
    if err or not ws:
        cached_vals = bucket.get(cache_slot)
        if cached_vals is not None:
            _track_sync_status(cache_slot, fallback_used=True)
            return None, cached_vals
        return err or f"Onglet '{tab_name}' inaccessible.", None
    last_exc = None
    values = None
    for _ in range(max(1, retries)):
        try:
            values = ws.get_all_values()
            break
        except Exception as ex:
            last_exc = ex
            time.sleep(0.5)
    if values is not None:
        bucket[cache_slot] = values
        _track_sync_status(cache_slot, fallback_used=False)
        return None, values
    cached_vals = bucket.get(cache_slot)
    if cached_vals is not None:
        _track_sync_status(cache_slot, fallback_used=True)
        return None, cached_vals
    return str(last_exc) if last_exc else f"Lecture impossible sur '{tab_name}'.", None

@st.cache_data(ttl=180, show_spinner=False)
def build_monthly_ca_aggregates(df_in: pd.DataFrame):
    if df_in.empty:
        return pd.DataFrame(columns=["_mois_key", "_mois_label", "CA Total", "CA Signé", "CA En attente", "CA Cumul"])
    work = df_in.copy()
    work["_mois_key"] = work["_date"].dt.to_period("M").astype(str)
    work["_mois_label"] = work["_date"].dt.strftime("%b %Y")
    month_map = work[["_mois_key", "_mois_label"]].drop_duplicates().sort_values("_mois_key")
    ca_total_m = work.groupby("_mois_key")["_montant"].sum().reset_index().rename(columns={"_montant": "CA Total"})
    ca_signe_m = work[work["_signe"]].groupby("_mois_key")["_montant"].sum().reset_index().rename(columns={"_montant": "CA Signé"})
    ca_attente_m = work[~work["_signe"]].groupby("_mois_key")["_montant"].sum().reset_index().rename(columns={"_montant": "CA En attente"})
    merged = month_map.merge(ca_total_m, on="_mois_key", how="left").merge(ca_signe_m, on="_mois_key", how="left").merge(ca_attente_m, on="_mois_key", how="left").fillna(0)
    merged["CA Cumul"] = merged["CA Total"].cumsum()
    return merged

@st.cache_data(ttl=120, show_spinner=False)
def get_main_dataset(username: str):
    dataset_cache = st.session_state.setdefault("_offline_main_dataset_cache", {})
    df_raw, error = get_sheet_data(username)
    if error:
        cached_dataset = dataset_cache.get(username)
        if isinstance(cached_dataset, dict) and cached_dataset.get("df") is not None:
            st.session_state["_data_source_notice"] = "Mode dégradé : dernière version des données affichée."
            return cached_dataset, None, False
        return None, error, False
    if df_raw.empty:
        return None, None, True

    df = df_raw.copy()
    col_client = fcol(df, "client")
    col_chantier = fcol(df, "objet", "chantier")
    col_num = fcol(df, "n° devis", "n°", "num")
    col_montant = fcol(df, "montant")
    col_sign = fcol(df, "devis signé", "signé")
    col_fact_fin = fcol(df, "facture finale", "finale", "final")
    col_pv = fcol(df, "pv signé", "pv")
    col_statut = fcol(df, "statut")
    col_date = fcol(df, "date creation", "date créa", "date devis", "date creat")
    col_modalite = fcol(df, "modalit")
    col_tva = fcol(df, "tva")
    col_relance1 = fcol(df, "relance 1")
    col_relance2 = fcol(df, "relance 2")
    col_relance3 = fcol(df, "relance 3")
    col_acompte1 = fcol(df, "acompte 1")
    col_acompte2 = fcol(df, "acompte 2")
    col_reserve = fcol(df, "réserve", "reserve", "avec reserve", "sans reserve")
    col_adresse = fcol(df, "address", "adresse")
    col_date_debut = fcol(df, "début des travaux", "debut des travaux", "date début", "date debut", "colonne 21")
    col_date_fin = fcol(df, "fin des travaux", "date fin", "date de fin")
    col_equipe = fcol(df, "équipe", "equipe", "employé", "employe", "intervenant", "technicien")

    df["_montant"] = df[col_montant].apply(clean_amount) if col_montant else 0.0
    df["_acompte1"] = df[col_acompte1].apply(clean_amount) if col_acompte1 else 0.0
    df["_acompte2"] = df[col_acompte2].apply(clean_amount) if col_acompte2 else 0.0
    df["_reste"] = (df["_montant"] - df["_acompte1"] - df["_acompte2"]).clip(lower=0)
    df["_signe"] = df[col_sign].apply(is_checked) if col_sign else False
    df["_fact_fin"] = df[col_fact_fin].apply(is_checked) if col_fact_fin else False
    df["_pv"] = df[col_pv].apply(is_checked) if col_pv else False
    # Pré-calcul des dates pour éviter de reparser à chaque interaction (filtres plus rapides).
    df["_date_parsed_main"] = parse_flexible_series(df[col_date]) if col_date else pd.NaT
    df["_date_fin_parsed_main"] = parse_flexible_series(df[col_date_fin]) if col_date_fin else pd.NaT
    df["_date_debut_parsed_main"] = parse_flexible_series(df[col_date_debut]) if col_date_debut else pd.NaT

    nb_signes = int(df["_signe"].sum())
    nb_devis = len(df)

    dataset = {
        "df": df,
        "COL_CLIENT": col_client,
        "COL_CHANTIER": col_chantier,
        "COL_NUM": col_num,
        "COL_MONTANT": col_montant,
        "COL_SIGN": col_sign,
        "COL_FACT_FIN": col_fact_fin,
        "COL_PV": col_pv,
        "COL_STATUT": col_statut,
        "COL_DATE": col_date,
        "COL_MODALITE": col_modalite,
        "COL_TVA": col_tva,
        "COL_RELANCE1": col_relance1,
        "COL_RELANCE2": col_relance2,
        "COL_RELANCE3": col_relance3,
        "COL_ACOMPTE1": col_acompte1,
        "COL_ACOMPTE2": col_acompte2,
        "COL_RESERVE": col_reserve,
        "COL_ADRESSE": col_adresse,
        "COL_DATE_DEBUT": col_date_debut,
        "COL_DATE_FIN": col_date_fin,
        "COL_EQUIPE": col_equipe,
        "total_ca": df["_montant"].sum(),
        "nb_devis": nb_devis,
        "nb_signes": nb_signes,
        "nb_attente": nb_devis - nb_signes,
        "nb_fact_ok": int(df["_fact_fin"].sum()),
        "ca_signe": df[df["_signe"]]["_montant"].sum(),
        "ca_non_s": df[~df["_signe"]]["_montant"].sum(),
        "taux_conv": int((nb_signes / nb_devis) * 100) if nb_devis > 0 else 0,
        "reste_encaissement": df[(df["_signe"]) & (~df["_fact_fin"])]["_reste"].sum(),
    }
    dataset_cache[username] = dataset
    return dataset, None, False

def fmt(v):
    return f"{v:,.0f} €".replace(",", " ")

def convert_df_to_csv(df_export: pd.DataFrame) -> bytes:
    return df_export.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

def style_relances(row):
    r3_col = next((c for c in row.index if "relance 3" in str(c).lower()), None)
    st_col = next((c for c in row.index if "statut" in str(c).lower()), None)
    if r3_col and st_col:
        r3_val = str(row.get(r3_col, "")).strip()
        st_val = str(row.get(st_col, "")).lower()
        if r3_val != "" and "envoyé" not in st_val:
            return ['background-color: rgba(255, 92, 122, 0.25); color: #ff5c7a; font-weight: bold;'] * len(row)
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
        formatted = displayed.copy()
        for col in formatted.columns:
            col_low = str(col).lower()
            if "%" in col_low:
                formatted[col] = formatted[col].apply(lambda v: f"{v} %" if str(v).strip() not in ("", "nan", "None") else "")
            elif any(k in col_low for k in ["montant", "budget", "reste", "ttc", "ht", "ca"]) and "%" not in col_low:
                formatted[col] = formatted[col].apply(
                    lambda v: f"{clean_amount(v):,.0f} €".replace(",", " ") if str(v).strip() not in ("", "nan", "None") else ""
                )
        styled_df = formatted.style.apply(style_relances, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(displayed, use_container_width=True, hide_index=True)
    if total > LIMIT:
        if not show_all:
            st.caption(f"Affichage des {LIMIT} premiers sur {total}.")
            if st.button(f"📂 Voir les {total - LIMIT} suivants", key=f"btn_more_{key_suffix}"):
                st.session_state[f"show_all_{key_suffix}"] = True
        else:
            st.caption(f"{total} dossiers affichés.")
            if st.button("🔼 Réduire", key=f"btn_less_{key_suffix}"):
                st.session_state[f"show_all_{key_suffix}"] = False

@st.cache_data(ttl=120, show_spinner=False)
def get_pending_notifications_count(username: str) -> int:
    ws, err = get_worksheet(username, "notifications")
    if err or not ws:
        return 0
    try:
        vals = ws.get_all_values()
        if not vals or len(vals) < 2:
            return 0
        headers = [h.strip().lower() for h in vals[0]]
        if "statut" not in headers:
            return 0
        idx_statut = headers.index("statut")
        return sum(
            1 for r in vals[1:]
            if len(r) > idx_statut and r[idx_statut].strip().lower() == "en_attente"
        )
    except Exception:
        return 0

def page_header(title, subtitle=""):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        {"<div class='subtitle'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def render_ceo_hero(title, subtitle="", chips=None):
    chips = chips or []
    chips_html = "".join([f"<div class='ceo-chip'>{c}</div>" for c in chips if c])
    st.markdown(
        f"""
        <div class="ceo-hero">
            <div class="ceo-hero-title">{title}</div>
            <div class="ceo-hero-subtitle">{subtitle}</div>
            {"<div class='ceo-chip-row'>" + chips_html + "</div>" if chips_html else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(cards):
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        accent = card.get("accent", "#4f8ef7")
        bg = card.get("accent_bg", "rgba(79,142,247,0.18)")
        fill = max(0, min(100, int(card.get("fill_pct", 0))))
        delta = card.get("delta", "")
        delta_color = card.get("delta_color", accent)
        with col:
            st.markdown(
                f"""
                <div class="ceo-kpi-card">
                    <div class="ceo-kpi-top">
                        <div>
                            <div class="ceo-kpi-label">{card.get("label", "")}</div>
                        </div>
                        <div class="ceo-kpi-icon" style="background:{bg};">{card.get("icon", "•")}</div>
                    </div>
                    <div class="ceo-kpi-value">{card.get("value", "")}</div>
                    <div class="ceo-kpi-delta" style="color:{delta_color};">{delta}</div>
                    <div class="ceo-kpi-bar"><div class="ceo-kpi-fill" style="width:{fill}%;background:{accent};"></div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_filter_banner(title, helper=""):
    st.markdown(
        f"""
        <div class="ceo-actions">
            <div class="ceo-card-title">{title}</div>
            {"<div class='ceo-card-subtitle'>" + helper + "</div>" if helper else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

def safe_radio_index(options, key, default=0):
    """Retourne l'index sécurisé pour st.radio, évite ValueError si la valeur en session est obsolète."""
    val = st.session_state.get(key)
    if val in options:
        return options.index(val)
    return default

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding: 20px 16px 8px;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:10px;padding-bottom:8px;'>
            <div style='width:36px;height:36px;background:linear-gradient(135deg,#4f8ef7,#2563eb);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;'>⚡</div>
            <div>
                <div style='font-family:Inter,sans-serif;font-weight:800;font-size:0.95rem;color:var(--text-main);'>Floxia</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.button("Basculer thème", on_click=toggle_theme, use_container_width=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    user = st.session_state.get("username", "")
    user_slug = safe_slug(user)
    role = st.session_state.get("role", "viewer")

    st.markdown("<div style='padding: 0 12px;'>", unsafe_allow_html=True)

    notif_label = "Notifications"
    pending_badge = get_pending_notifications_count(user) if user else 0
    if pending_badge > 0:
        notif_label = f"🔴 Notifications ({pending_badge})"

    st.markdown("<div class='ceo-section-title' style='padding:0 2px;'>Navigation Executive</div>", unsafe_allow_html=True)
    page_items = [
        ("Vue Générale", "◈ Vue Générale"),
        ("Créer un devis", "✦ Créer un devis"),
        ("Devis", "◉ Devis"),
        ("Factures & Paiements", "◌ Factures & Paiements"),
        ("Chantiers", "◆ Chantiers"),
        ("Planning", "▣ Planning"),
        ("Salariés", "◍ Salariés"),
        ("Notifications", f"✉ {notif_label}"),
        ("Espace Clients", "⌂ Espace Clients"),
        ("Tous les dossiers", "▤ Tous les dossiers"),
        ("Éditeur Google Sheet", "⌘ Éditeur Google Sheet"),
        ("Dépenses", "◐ Dépenses"),
        ("Retards & Avenants", "△ Retards & Avenants"),
        ("Coordonnées & RGPD", "☰ Coordonnées & RGPD"),
    ]
    if role == "admin":
        page_items.append(("Utilisateurs", "☷ Utilisateurs"))

    allowed_pages = st.session_state.get("allowed_pages", AVAILABLE_PAGES.copy())
    if role != "admin":
        page_items = [p for p in page_items if p[0] in allowed_pages]

    pages = [p[1] for p in page_items]
    page_key_map = {p[1]: p[0] for p in page_items}
    if not pages:
        st.error("Aucun onglet autorisé pour ce compte.")
        st.stop()

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
        if val and val in pages:
            st.session_state["_page_index"] = pages.index(val)

    page = st.radio(
        "Navigation",
        pages,
        label_visibility="collapsed",
        index=st.session_state["_page_index"],
        key="nav_radio",
        on_change=_on_nav_change,
    )
    if page in pages:
        st.session_state["_page_index"] = pages.index(page)
    page = page_key_map.get(page, page)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='position:absolute;bottom:0;left:0;right:0;padding:16px;border-top:1px solid rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;'>
        <div style='width:32px;height:32px;background:linear-gradient(135deg,#132238,#1e3a5f);
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:0.85rem;border:1px solid rgba(79,142,247,0.3); color:#fff;'>
            {user[0].upper() if user else '?'}
        </div>
        <div>
            <div style='font-weight:600;font-size:0.85rem;color:var(--text-main);'>{user}</div>
            <div style='font-size:0.72rem;color:var(--text-muted);'>{role}</div>
        </div>
        <div style='margin-left:auto;'>
            <span class="pulse-dot"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_r, col_l = st.columns(2)
    with col_r:
        if st.button("Actualiser", use_container_width=True, help="Actualiser"):
            st.cache_data.clear()
            st.rerun()
    with col_l:
        if st.button("🚪", use_container_width=True, help="Déconnexion"):
            logout()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if st.secrets.get("SHOW_N8N_DIAGNOSTIC", "") == "1":
    with st.expander("Diagnostic n8n (endpoints & logs)", expanded=False):
        st.caption("Endpoints actifs pour ce compte :")
        st.code(
            "\n".join([
                f"reponse: https://n8n.florianai.fr/webhook/reponse-{user_slug}",
                f"devis:    https://n8n.florianai.fr/webhook/{user_slug}",
                f"retard:   https://n8n.florianai.fr/webhook/retard-{user_slug}",
            ])
        )
        send_logs = st.session_state.get("_send_logs", [])
        if send_logs:
            st.caption("Derniers envois (sans données sensibles) :")
            logs_limit = min(50, len(send_logs))
            st.dataframe(pd.DataFrame(send_logs[:logs_limit]), use_container_width=True, hide_index=True)
            if len(send_logs) > logs_limit:
                st.caption(f"Affichage de {logs_limit} / {len(send_logs)} logs.")
        else:
            st.caption("Aucun envoi loggé dans cette session.")

render_sync_badge()

# ── PAGES SPÉCIALES ────────────────────────────────────────────────────────────
if page == "Utilisateurs":
    admin_panel()
    st.stop()
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DÉPENSES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Dépenses":
    page_header("Dépenses", "Suivi des charges et TVA récupérable")

    @st.cache_data(ttl=90, show_spinner=False)
    def _load_depenses(u):
        err, vals = get_sheet_values_resilient(u, "Depenses", f"{u}:Depenses")
        if err:
            return err, pd.DataFrame()
        try:
            if not vals or len(vals) < 2:
                return None, pd.DataFrame()
            headers = _dedup_headers(vals[0])
            rows = vals[1:]
            n = len(headers)
            padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
            df_dep = pd.DataFrame(padded, columns=headers)
            df_dep = df_dep.replace("", pd.NA).dropna(how="all").fillna("")
            return None, df_dep
        except Exception as e:
            return str(e), pd.DataFrame()

    err_dep, df_dep = _load_depenses(user)

    if err_dep:
        show_data_source_error(
            f"Onglet 'Depenses' indisponible : {err_dep}",
            clear_fn=_load_depenses.clear,
            retry_key="retry_depenses_source",
        )
        st.info("Crée un onglet 'Depenses' dans ton Google Sheet.")
        st.stop()

    if st.button("Actualiser", key="btn_refresh_dep"):
        _load_depenses.clear()
        st.rerun()

    # ── Détection colonnes dépenses ────────────────────────────────────────
    def dcol(df_d, *kws):
        for kw in kws:
            for c in df_d.columns:
                if kw.lower() in str(c).strip().lower():
                    return c
        return None

    DC_DATE      = dcol(df_dep, "transaction_date", "date")
    DC_TTC       = dcol(df_dep, "total_ttc")
    DC_HT        = dcol(df_dep, "subtotal_ht")
    DC_TVA       = dcol(df_dep, "tva_recuperable")
    DC_COMPANY   = dcol(df_dep, "company_name")
    DC_ITEM      = dcol(df_dep, "item_name")
    DC_CAT       = dcol(df_dep, "item_category")
    DC_PAYMENT   = dcol(df_dep, "payment_method")
    DC_TICKET    = dcol(df_dep, "ticket_number")

    # ── Nettoyage montants ─────────────────────────────────────────────────
    for col in [DC_TTC, DC_HT, DC_TVA]:
        if col:
            df_dep[col] = df_dep[col].apply(clean_amount)

    # ── Sélecteur de dates optionnel ───────────────────────────────────────
    df_dep_filtered = df_dep.copy()
    periode_dep = False

    with st.expander("📅 Filtrer par période", expanded=False):
        col_dep1, col_dep2, col_dep3 = st.columns([2, 2, 1])
        with col_dep1:
            dep_date_debut = st.date_input("Du", value=None, key="dep_date_debut")
        with col_dep2:
            dep_date_fin = st.date_input("Au", value=None, key="dep_date_fin")
        with col_dep3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Réinitialiser", key="dep_reset_dates", use_container_width=True):
                st.session_state.pop("dep_date_debut", None)
                st.session_state.pop("dep_date_fin", None)

    if DC_DATE and (dep_date_debut or dep_date_fin):
        df_dep_filtered["_date_dep"] = parse_flexible_series(df_dep_filtered[DC_DATE])
        if dep_date_debut:
            df_dep_filtered = df_dep_filtered[df_dep_filtered["_date_dep"].dt.date >= dep_date_debut]
        if dep_date_fin:
            df_dep_filtered = df_dep_filtered[df_dep_filtered["_date_dep"].dt.date <= dep_date_fin]
        periode_dep = True
        label_dep = ""
        if dep_date_debut and dep_date_fin:
            label_dep = f"{dep_date_debut.strftime('%d/%m/%Y')} → {dep_date_fin.strftime('%d/%m/%Y')}"
        elif dep_date_debut:
            label_dep = f"Depuis le {dep_date_debut.strftime('%d/%m/%Y')}"
        else:
            label_dep = f"Jusqu'au {dep_date_fin.strftime('%d/%m/%Y')}"
        st.info(f"📅 Période active : **{label_dep}** — {len(df_dep_filtered)} ticket(s)")

    # ── Calculs KPIs ───────────────────────────────────────────────────────
    total_dep_ttc  = df_dep_filtered[DC_TTC].sum() if DC_TTC else 0.0
    total_dep_ht   = df_dep_filtered[DC_HT].sum()  if DC_HT  else 0.0
    total_tva_rec  = df_dep_filtered[DC_TVA].sum()  if DC_TVA else 0.0

    # CA sécurisé — même filtre de date si période active
    # Chargement df si pas encore fait
    df_ref_raw, _ = get_sheet_data(user)
    ca_ref = df_ref_raw.copy()
    col_date_ref  = fcol(ca_ref, "date creation", "date créa", "date devis", "date creat")
    col_sign_ref  = fcol(ca_ref, "devis signé", "signé")
    col_mont_ref  = fcol(ca_ref, "montant")
    ca_ref["_montant"] = ca_ref[col_mont_ref].apply(clean_amount) if col_mont_ref else 0.0
    ca_ref["_signe"]   = ca_ref[col_sign_ref].apply(is_checked)  if col_sign_ref else False
    if periode_dep and col_date_ref and (dep_date_debut or dep_date_fin):
        ca_ref["_date_parsed"] = parse_flexible_series(ca_ref[col_date_ref])
        if dep_date_debut:
            ca_ref = ca_ref[ca_ref["_date_parsed"].dt.date >= dep_date_debut]
        if dep_date_fin:
            ca_ref = ca_ref[ca_ref["_date_parsed"].dt.date <= dep_date_fin]
    ca_securise_dep = ca_ref[ca_ref["_signe"]]["_montant"].sum()
    resultat_net    = ca_securise_dep - total_dep_ttc

    # ── KPIs ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Dépenses TTC", fmt(total_dep_ttc), f"{len(df_dep_filtered)} tickets")
    k2.metric("Total HT", fmt(total_dep_ht))
    k3.metric("CA Sécurisé", fmt(ca_securise_dep), "période sélectionnée" if periode_dep else "total")
    k4.metric("Résultat Net Estimé", fmt(resultat_net), delta_color="normal")

    # ── TVA récupérable bien visible ───────────────────────────────────────
    st.markdown(f"""
    <div style="margin:20px 0;padding:18px 24px;background:linear-gradient(135deg,rgba(0,214,143,0.12),rgba(0,214,143,0.04));
        border:1px solid rgba(0,214,143,0.35);border-left:5px solid #00d68f;border-radius:var(--radius);">
        <div style="font-size:0.78rem;font-weight:700;color:#00d68f;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">
            TVA Récupérable — À mettre de côté
        </div>
        <div style="font-size:2rem;font-weight:800;color:#00d68f;letter-spacing:-0.02em;">{fmt(total_tva_rec)}</div>
        <div style="font-size:0.82rem;color:var(--text-muted);margin-top:4px;">
            Montant de TVA à déduire sur votre prochaine déclaration
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Résumé financier ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.95rem;color:var(--text-main);margin-bottom:14px;'>Résumé financier</div>", unsafe_allow_html=True)
            for label, val, color in [
                ("CA Sécurisé",          fmt(ca_securise_dep),  "#00d68f"),
                ("Total Dépenses TTC",   fmt(total_dep_ttc),    "#ff5c7a"),
                ("Total Dépenses HT",    fmt(total_dep_ht),     "#ffb84d"),
                ("TVA Récupérable",      fmt(total_tva_rec),    "#00d68f"),
                ("Résultat Net Estimé",  fmt(resultat_net),     "#4f8ef7" if resultat_net >= 0 else "#ff5c7a"),
            ]:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:8px 0;border-bottom:1px solid var(--border);'>"
                    f"<span style='color:var(--text-muted);font-size:0.85rem;'>{label}</span>"
                    f"<span style='color:{color};font-weight:700;font-size:0.95rem;'>{val}</span></div>",
                    unsafe_allow_html=True,
                )

    with col_res2:
        with st.container(border=True):
            if DC_CAT and not df_dep_filtered.empty:
                cat_totals = df_dep_filtered.groupby(DC_CAT)[DC_TTC].sum().reset_index().sort_values(DC_TTC, ascending=False) if DC_TTC else pd.DataFrame()
                if not cat_totals.empty:
                    fig_dep = px.bar(
                        cat_totals, x=DC_CAT, y=DC_TTC,
                        title="Dépenses TTC par catégorie",
                        color_discrete_sequence=["#4f8ef7"],
                        labels={DC_TTC: "TTC (€)", DC_CAT: "Catégorie"},
                    )
                    fig_dep.update_layout(
                        paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                        font=dict(color=chart_font, family="Inter"),
                        xaxis=dict(showgrid=False, tickangle=-30),
                        yaxis=dict(gridcolor=chart_grid, tickformat=",.0f"),
                        margin=dict(t=40, b=40, l=10, r=10),
                        title_font_color=chart_font,
                    )
                    st.plotly_chart(fig_dep, use_container_width=True)
            else:
                st.info("Colonne 'item_category' non détectée pour le graphique.")

    # ── Tableau des tickets ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Tickets de caisse")

    search_dep = st.text_input("🔍 Rechercher", placeholder="Entreprise, article, catégorie...", key="search_dep")
    df_dep_show = df_dep_filtered.copy()
    if search_dep:
        mask_dep = pd.Series([False] * len(df_dep_show), index=df_dep_show.index)
        for c in df_dep_show.columns:
            mask_dep |= df_dep_show[c].astype(str).str.contains(search_dep, case=False, na=False)
        df_dep_show = df_dep_show[mask_dep]

    cols_dep_display = [c for c in [DC_DATE, DC_COMPANY, DC_TICKET, DC_ITEM, DC_CAT, DC_HT, DC_TTC, DC_TVA, DC_PAYMENT] if c]
    drop_internal = ["_date_dep"]
    df_dep_show_clean = df_dep_show.drop(columns=[c for c in drop_internal if c in df_dep_show.columns], errors="ignore")
    show_table(
        (df_dep_show_clean[cols_dep_display] if cols_dep_display else df_dep_show_clean).reset_index(drop=True),
        "dep_table"
    )
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ESPACE CLIENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Espace Clients":
    page_header("Espace Clients", "Documents et dossiers synchronisés avec Google Drive")

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
            st.error("Identifiants Google introuvables pour ce compte.")
            st.stop()

        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)

        query_main = "name = 'espace clients' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_main = drive_service.files().list(q=query_main, fields="files(id, name)").execute()
        main_folders = res_main.get('files', [])

        if not main_folders:
            st.warning("Dossier principal 'espace clients' introuvable sur le Google Drive.")
        else:
            main_folder_id = main_folders[0]['id']
            query_clients = f"'{main_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res_clients = drive_service.files().list(q=query_clients, fields="files(id, name)", pageSize=1000).execute()
            client_folders = res_clients.get('files', [])

            if not client_folders:
                st.info("Aucun dossier client trouvé dans 'espace clients'.")
            else:
                client_folders = sorted(client_folders, key=lambda x: x['name'].lower())
                client_names = [f["name"] for f in client_folders]

                search_client = st.text_input("🔍 Rechercher un client :", placeholder="Tapez le nom d'un client...", value=prefill_client)
                filtered_client_names = [name for name in client_names if search_client.lower() in name.lower()]

                if not filtered_client_names:
                    st.warning("Aucun client ne correspond à votre recherche.")
                else:
                    # Si on arrive ici via un clic depuis une autre page, `prefill_client`
                    # contient (normalement) le nom exact du dossier client.
                    # On force alors la `selectbox` sur le bon index.
                    prefill_norm = (prefill_client or "").strip().lower()
                    exact_match = next((n for n in filtered_client_names if n.strip().lower() == prefill_norm), None)
                    default_index = filtered_client_names.index(exact_match) if exact_match in filtered_client_names else 0
                    selected_client_name = st.selectbox(
                        "Sélectionnez un client :",
                        filtered_client_names,
                        index=default_index,
                    )
                    selected_client_id = next(f['id'] for f in client_folders if f['name'] == selected_client_name)

                    st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
                    st.subheader(f"📂 Fichiers de : {selected_client_name}")

                    query_files = f"'{selected_client_id}' in parents and trashed = false"
                    res_files = drive_service.files().list(q=query_files, fields="files(id, name, mimeType, webViewLink)", orderBy="folder, name", pageSize=1000).execute()
                    files = res_files.get('files', [])

                    def display_file(f_dict):
                        mime = f_dict.get('mimeType', '').lower()
                        icon = "Fichier"
                        if "folder" in mime: icon = "Dossier"
                        elif "pdf" in mime: icon = "📕"
                        elif "image" in mime: icon = "🖼️"
                        elif "spreadsheet" in mime or "sheet" in mime or "excel" in mime: icon = "Tableur"
                        elif "document" in mime or "word" in mime: icon = "Document"
                        st.markdown(f"""
                        <a href="{f_dict.get('webViewLink', '#')}" target="_blank" style="text-decoration:none;">
                            <div style="display:flex; align-items:center; gap:12px; padding:10px 16px; background:var(--bg-surface); border:1px solid var(--border); border-radius:8px; margin-bottom:8px;">
                                <div style="font-size:1.2rem;">{icon}</div>
                                <div style="color:var(--text-main); font-weight:600; font-size:0.9rem;">{f_dict.get('name')}</div>
                                <div style="margin-left:auto; color:var(--primary); font-size:0.75rem; font-weight:600;">Ouvrir ↗</div>
                            </div>
                        </a>
                        """, unsafe_allow_html=True)

                    if not files:
                        st.info("Ce dossier client est vide.")
                    else:
                        for file in files:
                            mime_type = file.get('mimeType', '')
                            if mime_type == 'application/vnd.google-apps.folder':
                                with st.expander(f"Dossier : **{file.get('name')}**"):
                                    sub_query = f"'{file.get('id')}' in parents and trashed = false"
                                    sub_res = drive_service.files().list(q=sub_query, fields="files(id, name, mimeType, webViewLink)", orderBy="folder, name", pageSize=1000).execute()
                                    sub_files = sub_res.get('files', [])
                                    if not sub_files:
                                        st.caption("Ce dossier est vide.")
                                    else:
                                        is_infos_clients = (file.get('name').strip().lower() in ["infos clients", "info client", "infos client"])
                                        for sub_file in sub_files:
                                            sub_mime = sub_file.get('mimeType', '').lower()
                                            if is_infos_clients and ('document' in sub_mime or 'text' in sub_mime):
                                                content = get_google_doc_content(sub_file['id'], sub_mime, drive_service)
                                                if content:
                                                    st.markdown(f"""
                                                    <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:12px;">
                                                        <div style="font-weight:700; color:var(--primary); margin-bottom:8px;">{sub_file.get('name')}</div>
                                                        <div style="white-space: pre-wrap; font-size:0.9rem; color:var(--text-main);">{content}</div>
                                                    </div>
                                                    """, unsafe_allow_html=True)
                                                else:
                                                    display_file(sub_file)
                                            else:
                                                display_file(sub_file)
                            else:
                                display_file(file)

    except ImportError:
        st.error("🚨 La bibliothèque 'google-api-python-client' n'est pas installée.")
        st.info("Ajoute `google-api-python-client>=2.0.0` dans ton fichier **requirements.txt**.")
    except Exception as e:
        st.error(f"Erreur de communication avec Google Drive : {e}")

# ══════════════════════════════════════════════════════════════════════════════
# ÉDITEUR GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Éditeur Google Sheet":
    page_header("Éditeur Google Sheet", "Gérez votre base de données en temps réel")

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

    editor_tab = st.radio(
        "",
        ["Feuille Prestations", "Catalogue"],
        horizontal=True,
        key="editor_sheet_tab",
    )

    if editor_tab == "Feuille Prestations":
        PRESTA_COLS = ["categorie", "Type de poste", "Sous-prestation", "Description", "Prix MO HT", "Prix Fourn. HT", "Marge (%)", "Quantité", "Total HT"]
        st.caption("Colonnes Feuille 1 attendues : categorie | Type de poste | Sous-prestation | Description | Prix MO HT | Prix Fourn. HT | Marge (%) | Quantité | Total HT")

        @st.cache_data(ttl=30, show_spinner=False)
        def load_presta(u):
            ws, err = get_worksheet(u, "Feuille 1")
            if err:
                return err, pd.DataFrame()
            try:
                all_vals = ws.get_all_values()
                if not all_vals:
                    return None, pd.DataFrame()
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
            show_data_source_error(f"Feuille 1 indisponible : {err_p}", clear_fn=load_presta.clear, retry_key="retry_presta")
        else:
            sub_p_view, sub_p_add, sub_p_edit, sub_p_del = st.tabs(["Voir","Ajouter","Modifier","Supprimer"])

            with sub_p_view:
                st.caption(f"{len(df_p)} lignes dans la base")
                search_p = st.text_input("🔍 Rechercher", placeholder="Mot-clé...", key="search_presta")
                df_show = df_p.copy()
                if search_p:
                    mask = pd.Series([False]*len(df_show), index=df_show.index)
                    for c in df_show.columns:
                        mask |= df_show[c].astype(str).str.contains(search_p, case=False, na=False)
                    df_show = df_show[mask]
                show_table(df_show.reset_index(drop=True), "presta_view")

            with sub_p_add:
                c_t1, c_t2, c_t3 = st.columns(3)
                with c_t1:
                    add_temps_trajet = st.number_input("Temps de trajet (h)", min_value=0.0, value=0.0, step=0.5, key="add_temps_trajet")
                with c_t2:
                    add_temps_chantier = st.number_input("Temps de chantier (h)", min_value=0.0, value=0.0, step=0.5, key="add_temps_chantier")
                with c_t3:
                    add_taux_horaire = st.number_input("Taux horaire (€)", min_value=0.0, value=50.0, step=5.0, key="add_taux_horaire")

                val_mo = (add_temps_trajet + add_temps_chantier) * add_taux_horaire
                st.text_input("Prix MO HT (calculé)", value=f"{val_mo:.2f}", disabled=True, key="add_mo_calc")

                c_fourn, c_marge, c_qte = st.columns(3)
                with c_fourn: val_fourn = st.number_input("Prix Fourn. HT", min_value=0.0, value=0.0, step=10.0, key="add_fourn")
                with c_marge: val_marge = st.number_input("Marge (%)", min_value=0.0, value=30.0, step=5.0, key="add_marge")
                with c_qte: val_qte = st.number_input("Quantité", min_value=1.0, value=1.0, step=1.0, key="add_qte")
                calcul_total = (val_mo + (val_fourn * (1 + (val_marge / 100)))) * val_qte
                st.success(f"Total HT calculé : **{calcul_total:.2f} €**")
                with st.form("form_add_presta"):
                    headers_p = list(df_p.columns) if len(df_p) > 0 else PRESTA_COLS
                    inputs_p = {}
                    cols1 = st.columns(3)
                    for i, h in enumerate(headers_p):
                        hl = h.lower()
                        if any(mot in hl for mot in ["mo ht","fourn","marge","quantit","total"]):
                            continue
                        with cols1[i % 3]:
                            if "categ" in hl:
                                inputs_p[h] = st.selectbox(h, CATEGORIES, key=f"add_p_{h}")
                            elif "type" in hl and "poste" in hl:
                                inputs_p[h] = st.selectbox(h, TYPES_POSTE, key=f"add_p_{h}")
                            else:
                                inputs_p[h] = st.text_input(h, key=f"add_p_{h}")
                    submit_add_p = st.form_submit_button("Ajouter", use_container_width=True)
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
                            load_presta.clear()
                            clear_cache_if_exists("_load_prestations_devis")
                            st.success("Ligne ajoutée.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            with sub_p_edit:
                if len(df_p) == 0:
                    st.info("Aucune ligne.")
                else:
                    headers_p2 = list(df_p.columns)
                    def _get_presta_label(i):
                        for h in headers_p2:
                            if "sous" in h.lower() or "prestation" in h.lower() or "designation" in h.lower() or "désignation" in h.lower():
                                val = str(df_p.iloc[i][h]).strip()
                                if val:
                                    return f"Ligne {i+2} — {val}"
                        return f"Ligne {i+2} — {df_p.iloc[i,0]} / {df_p.iloc[i,1] if len(headers_p2)>1 else ''}"
                    row_labels = [_get_presta_label(i) for i in range(len(df_p))]
                    sel_idx = st.selectbox("Ligne à modifier", range(len(df_p)), format_func=lambda i: row_labels[i], key="sel_mod_presta")
                    cur_mo = cur_fourn = 0.0; cur_marge = 30.0; cur_qte = 1.0
                    for h in headers_p2:
                        hl = h.lower(); val = df_p.iloc[sel_idx][h]
                        if "mo ht" in hl: cur_mo = clean_amount(val)
                        elif "fourn" in hl: cur_fourn = clean_amount(val)
                        elif "marge" in hl: cur_marge = clean_amount(val)
                        elif "quantit" in hl: cur_qte = clean_amount(val)
                    c_mt1, c_mt2, c_mt3 = st.columns(3)
                    default_taux_edit = 50.0
                    default_chantier_edit = (float(cur_mo) / default_taux_edit) if default_taux_edit > 0 else 0.0
                    with c_mt1:
                        mod_temps_trajet = st.number_input("Temps de trajet (h)", min_value=0.0, value=0.0, step=0.5, key="mod_temps_trajet")
                    with c_mt2:
                        mod_temps_chantier = st.number_input("Temps de chantier (h)", min_value=0.0, value=float(default_chantier_edit), step=0.5, key="mod_temps_chantier")
                    with c_mt3:
                        mod_taux_horaire = st.number_input("Taux horaire (€)", min_value=0.0, value=default_taux_edit, step=5.0, key="mod_taux_horaire")

                    mod_mo = (mod_temps_trajet + mod_temps_chantier) * mod_taux_horaire
                    st.text_input("Prix MO HT (calculé)", value=f"{mod_mo:.2f}", disabled=True, key="mod_mo_calc")

                    c_fourn_m, c_marge_m, c_qte_m = st.columns(3)
                    with c_fourn_m: mod_fourn = st.number_input("Prix Fourn. HT", min_value=0.0, value=float(cur_fourn), step=10.0, key="mod_fourn")
                    with c_marge_m: mod_marge = st.number_input("Marge (%)", min_value=0.0, value=float(cur_marge), step=5.0, key="mod_marge")
                    with c_qte_m: mod_qte = st.number_input("Quantité", min_value=1.0, value=max(float(cur_qte),1.0), step=1.0, key="mod_qte")
                    mod_total = (mod_mo + (mod_fourn * (1 + (mod_marge/100)))) * mod_qte
                    st.success(f"Nouveau Total HT : **{mod_total:.2f} €**")
                    with st.form("form_mod_presta"):
                        mod_inputs = {}; cols2 = st.columns(3)
                        for i, h in enumerate(headers_p2):
                            hl = h.lower()
                            if any(mot in hl for mot in ["mo ht","fourn","marge","quantit","total"]): continue
                            with cols2[i % 3]:
                                cur_val = str(df_p.iloc[sel_idx][h])
                                if "categ" in hl:
                                    mod_inputs[h] = st.selectbox(h, CATEGORIES, index=CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0, key=f"mod_p_{h}")
                                elif "type" in hl and "poste" in hl:
                                    mod_inputs[h] = st.selectbox(h, TYPES_POSTE, index=TYPES_POSTE.index(cur_val) if cur_val in TYPES_POSTE else 0, key=f"mod_p_{h}")
                                else:
                                    mod_inputs[h] = st.text_input(h, value=cur_val, key=f"mod_p_{h}")
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
                                load_presta.clear()
                                clear_cache_if_exists("_load_prestations_devis")
                                st.success("Modification enregistrée.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            with sub_p_del:
                if len(df_p) == 0:
                    st.info("Aucune ligne.")
                else:
                    headers_p3 = list(df_p.columns)
                    def _get_presta_label2(i):
                        for h in headers_p3:
                            if "sous" in h.lower() or "prestation" in h.lower() or "designation" in h.lower() or "désignation" in h.lower():
                                val = str(df_p.iloc[i][h]).strip()
                                if val:
                                    return f"Ligne {i+2} — {val}"
                        return f"Ligne {i+2} — {df_p.iloc[i,0]} / {df_p.iloc[i,1] if len(headers_p3)>1 else ''}"
                    row_labels2 = [_get_presta_label2(i) for i in range(len(df_p))]
                    del_idx = st.selectbox("Ligne à supprimer", range(len(df_p)), format_func=lambda i: row_labels2[i], key="sel_del_presta")
                    st.warning(f"Suppression irréversible : **{row_labels2[del_idx]}**")
                    if st.button("Confirmer la suppression", key="btn_del_presta"):
                        try:
                            ws_p4, err4 = get_worksheet(user, "Feuille 1")
                            if err4: st.error(err4)
                            else:
                                ws_p4.delete_rows(del_idx+2)
                                load_presta.clear()
                                clear_cache_if_exists("_load_prestations_devis")
                                st.success("Ligne supprimée.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

    if editor_tab == "Catalogue":
        CATA_COLS = ["Catégorie","Article","Description","Prix Achat HT","% Marge","Prix Vente HT"]

        @st.cache_data(ttl=30, show_spinner=False)
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
            show_data_source_error(f"Catalogue indisponible : {err_c}", clear_fn=load_catalogue.clear, retry_key="btn_retry_cata")
        else:
            sub_c_view, sub_c_add, sub_c_edit, sub_c_del = st.tabs(["Voir","Ajouter","Modifier","Supprimer"])

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
                st.success(f"Prix Vente HT : **{calcul_vente:.2f} €**")
                with st.form("form_add_cata"):
                    headers_c = list(df_c.columns) if len(df_c) > 0 else CATA_COLS
                    inputs_c = {}; cols3 = st.columns(3)
                    for i, h in enumerate(headers_c):
                        hl = h.lower()
                        if any(mot in hl for mot in ["achat","marge","vente"]): continue
                        with cols3[i % 3]:
                            if "catég" in hl or "categ" in hl:
                                inputs_c[h] = st.selectbox(h, CATEGORIES, key=f"add_c_{h}")
                            else:
                                inputs_c[h] = st.text_input(h, key=f"add_c_{h}")
                    submit_add_c = st.form_submit_button("Ajouter", use_container_width=True)
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
                            load_catalogue.clear()
                            clear_cache_if_exists("_load_catalogue_devis")
                            st.success("Article ajouté.")
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
                    st.success(f"Prix Vente HT : **{mod_vente:.2f} €**")
                    with st.form("form_mod_cata"):
                        mod_inputs_c = {}; cols4 = st.columns(3)
                        for i, h in enumerate(headers_c2):
                            hl = h.lower()
                            if any(mot in hl for mot in ["achat","marge","vente"]): continue
                            with cols4[i % 3]:
                                cur_val = str(df_c.iloc[sel_idx_c][h])
                                if "catég" in hl or "categ" in hl:
                                    mod_inputs_c[h] = st.selectbox(h, CATEGORIES, index=CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0, key=f"mod_c_{h}")
                                else:
                                    mod_inputs_c[h] = st.text_input(h, value=cur_val, key=f"mod_c_{h}")
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
                                load_catalogue.clear()
                                clear_cache_if_exists("_load_catalogue_devis")
                                st.success("Modification enregistrée.")
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
                    st.warning(f"Suppression irréversible : **{art_labels2[del_idx_c]}**")
                    if st.button("Confirmer", key="btn_del_cata"):
                        try:
                            ws_c4, err_c4 = get_worksheet(user, "catalogue")
                            if err_c4: st.error(err_c4)
                            else:
                                ws_c4.delete_rows(del_idx_c+2)
                                load_catalogue.clear()
                                clear_cache_if_exists("_load_catalogue_devis")
                                st.success("Article supprimé.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif "Notifications" in page:
    page_header("Notifications", "Devis signés en attente de planification")

    WEBHOOK_REPONSE = f"https://n8n.florianai.fr/webhook/reponse-{user_slug}"

    @st.cache_data(ttl=180, show_spinner=False)
    def _load_salaries(u):
        err, vals = get_sheet_values_resilient(u, "liste", f"{u}:liste")
        if err:
            return []
        try:
            if not vals or len(vals) < 2:
                return []
            headers = [h.strip().lower() for h in vals[0]]
            sal_col = next((h for h in headers if "salar" in h), None)
            if not sal_col:
                sal_col = headers[0]
            idx = headers.index(sal_col)
            return [r[idx].strip() for r in vals[1:] if len(r) > idx and r[idx].strip()]
        except Exception:
            return []

    @st.cache_data(ttl=60, show_spinner=False)
    def _load_notifications(u):
        err, vals = get_sheet_values_resilient(u, "notifications", f"{u}:notifications")
        if err:
            return err, pd.DataFrame()
        try:
            if not vals or len(vals) < 2:
                return None, pd.DataFrame()
            headers = _dedup_headers(vals[0])
            rows = vals[1:]
            n = len(headers)
            padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
            df_n = pd.DataFrame(padded, columns=headers)
            df_n = df_n.replace("", pd.NA).dropna(how="all").fillna("")
            return None, df_n
        except Exception as e:
            return str(e), pd.DataFrame()

    def _ensure_col(headers, row_vals, candidates):
        idx = None
        headers_l = [h.strip().lower() for h in headers]
        for cand in candidates:
            if cand in headers_l:
                idx = headers_l.index(cand)
                break
        if idx is None:
            headers.append(candidates[0])
            row_vals.append("")
            idx = len(headers) - 1
        return idx

    def _upsert_planning_liste(
        u,
        numero_devis,
        nom_client,
        objet,
        salarie,
        date_debut,
        date_fin,
        heure_debut,
        heure_fin,
        tranches_personnalisees,
    ):
        ws_liste, err_liste = get_worksheet(u, "liste")
        if err_liste or not ws_liste:
            return False, f"Impossible d'ouvrir l'onglet liste : {err_liste or 'inconnu'}"

        def _col_to_a1(col_number):
            out = ""
            n = int(col_number)
            while n > 0:
                n, rem = divmod(n - 1, 26)
                out = chr(65 + rem) + out
            return out

        all_vals = ws_liste.get_all_values()
        if not all_vals:
            headers = ["numero_devis", "nom_client", "objet", "salarie", "date_debut", "date_fin", "heure_debut", "heure_fin", "tranches_horaires"]
            ws_liste.append_row(headers, value_input_option="USER_ENTERED")
            all_vals = [headers]
        headers = all_vals[0]
        row_template = [""] * len(headers)
        idx_num = _ensure_col(headers, row_template, ["numero_devis", "n_devis", "numero"])
        idx_client = _ensure_col(headers, row_template, ["nom_client", "client"])
        idx_objet = _ensure_col(headers, row_template, ["objet", "chantier"])
        idx_sal = _ensure_col(headers, row_template, ["salarie", "salarié"])
        idx_dd = _ensure_col(headers, row_template, ["date_debut", "date début"])
        idx_df = _ensure_col(headers, row_template, ["date_fin", "date fin"])
        idx_hd = _ensure_col(headers, row_template, ["heure_debut", "heure début"])
        idx_hf = _ensure_col(headers, row_template, ["heure_fin", "heure fin"])
        idx_slots = _ensure_col(headers, row_template, ["tranches_horaires", "tranches_horaires_personnalisees"])

        row_template[idx_num] = numero_devis
        row_template[idx_client] = nom_client
        row_template[idx_objet] = objet
        row_template[idx_sal] = salarie
        row_template[idx_dd] = date_debut
        row_template[idx_df] = date_fin
        row_template[idx_hd] = heure_debut
        row_template[idx_hf] = heure_fin
        row_template[idx_slots] = tranches_personnalisees

        if headers != all_vals[0]:
            ws_liste.update("1:1", [headers], value_input_option="USER_ENTERED")

        target_row_idx = None
        for i, row_vals in enumerate(all_vals[1:], start=2):
            num_val = row_vals[idx_num].strip() if len(row_vals) > idx_num else ""
            if num_val and num_val == numero_devis:
                target_row_idx = i
                break
        if target_row_idx:
            last_col = _col_to_a1(len(headers))
            ws_liste.update(f"A{target_row_idx}:{last_col}{target_row_idx}", [row_template], value_input_option="USER_ENTERED")
        else:
            ws_liste.append_row(row_template, value_input_option="USER_ENTERED")
        return True, None

    salaries = _load_salaries(user)
    err_n, df_notif = _load_notifications(user)

    if err_n:
        show_data_source_error(
            f"Onglet 'notifications' indisponible : {err_n}",
            clear_fn=_load_notifications.clear,
            retry_key="retry_notif_source",
        )
        st.caption("Colonnes attendues : date_reception, numero_devis, nom_client, objet, montant, statut")
        st.stop()

    df_attente = df_notif[df_notif.get("statut", pd.Series(dtype=str)).astype(str).str.strip() == "en_attente"] if "statut" in df_notif.columns else df_notif
    nb_attente_notif = len(df_attente)

    col_n1, col_n2 = st.columns(2)
    col_n1.metric("En attente de planification", nb_attente_notif)
    col_n2.metric("Planifiés", len(df_notif) - nb_attente_notif)

    if st.button("Actualiser", key="btn_refresh_notif"):
        _load_notifications.clear()
        st.rerun()

    st.markdown("---")

    if nb_attente_notif == 0:
        st.success("Aucune notification en attente.")
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
                    <span style="background:#1d4ed8;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8rem;font-weight:700;">{numero}</span>
                    <strong style="margin-left:8px;font-size:0.95rem;">{client}</strong>
                  </div>
                  <div style="font-size:0.8rem;color:#64748b;">{date_r}</div>
                </div>
                <div style="color:#475569;font-size:0.85rem;margin-bottom:4px;">{objet}</div>
                <div style="color:#1d4ed8;font-weight:700;font-size:0.9rem;margin-bottom:10px;">{montant} €</div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    date_debut_notif = st.date_input(
                        "Date début travaux",
                        value=datetime.today(),
                        key=f"notif_date_{idx}"
                    )
                with c2:
                    heure_intervention = st.time_input(
                        "Heure de début",
                        value=datetime.strptime("08:00", "%H:%M").time(),
                        key=f"notif_heure_{idx}"
                    )
                with c3:
                    heure_fin = st.time_input(
                        "🕔 Heure de fin",
                        value=datetime.strptime("17:00", "%H:%M").time(),
                        key=f"notif_heure_fin_{idx}"
                    )
                with c4:
                    salarie_sel = st.selectbox(
                        "Salarié(e)",
                        ["— Choisir —"] + salaries,
                        key=f"notif_sal_{idx}"
                    )

                c_week1, c_week2 = st.columns(2)
                with c_week1:
                    duree_semaines = st.number_input(
                        "Durée (semaines)",
                        min_value=1,
                        value=1,
                        step=1,
                        key=f"notif_semaines_{idx}",
                    )
                with c_week2:
                    date_fin_notif = date_debut_notif + timedelta(days=(int(duree_semaines) * 7) - 1)
                    st.text_input(
                        "Date de fin",
                        value=date_fin_notif.strftime("%d/%m/%Y"),
                        disabled=True,
                        key=f"notif_date_fin_txt_{idx}",
                    )

                st.markdown("Tranches horaires personnalisées par jour")
                weekday_defs = [
                    ("lundi", "Lundi"),
                    ("mardi", "Mardi"),
                    ("mercredi", "Mercredi"),
                    ("jeudi", "Jeudi"),
                    ("vendredi", "Vendredi"),
                    ("samedi", "Samedi"),
                    ("dimanche", "Dimanche"),
                ]
                custom_slots = []
                for day_key, day_label in weekday_defs:
                    c_day, c_start, c_end = st.columns([2, 2, 2])
                    with c_day:
                        use_day = st.checkbox(day_label, value=day_key in ["lundi", "mardi", "mercredi", "jeudi", "vendredi"], key=f"notif_use_{idx}_{day_key}")
                    with c_start:
                        start_day = st.time_input("Début", value=heure_intervention, key=f"notif_start_{idx}_{day_key}")
                    with c_end:
                        end_day = st.time_input("Fin", value=heure_fin, key=f"notif_end_{idx}_{day_key}")
                    if use_day:
                        custom_slots.append({
                            "jour": day_key,
                            "debut": start_day.strftime("%H:%M"),
                            "fin": end_day.strftime("%H:%M"),
                        })

                col_send, col_del_notif = st.columns([4, 1])
                with col_del_notif:
                    if st.button("Supprimer", key=f"notif_del_{idx}", use_container_width=True):
                        try:
                            ws_del, _ = get_worksheet(user, "notifications")
                            if ws_del:
                                ws_del.delete_rows(row_idx + 2)
                                _load_notifications.clear()
                                st.success("Notification supprimée.")
                                st.rerun()
                        except Exception as ex:
                            st.error(f"Erreur : {ex}")
                with col_send:
                    if st.button("Confirmer et envoyer à n8n", key=f"notif_send_{idx}", use_container_width=True, type="primary"):
                        if salarie_sel == "— Choisir —":
                            st.error("Sélectionne un(e) salarié(e).")
                        elif len(custom_slots) == 0:
                            st.error("Ajoute au moins une tranche horaire personnalisée.")
                        else:
                            tranches_json = json.dumps(custom_slots, ensure_ascii=False)
                            payload_notif = {
                                "numero_devis":       numero,
                                "nom_client":         client,
                                "objet":              objet,
                                "montant":            montant,
                                "date_debut_travaux": date_debut_notif.strftime("%Y-%m-%d"),
                                "date_fin_travaux":   date_fin_notif.strftime("%Y-%m-%d"),
                                "duree_semaines":     int(duree_semaines),
                                "heure_intervention": heure_intervention.strftime("%H:%M"),
                                "heure_fin":          heure_fin.strftime("%H:%M"),
                                "tranches_horaires":  custom_slots,
                                "salarie":            salarie_sel,
                                "planifie_par":       user,
                                "planifie_le":        datetime.now().strftime("%Y-%m-%d %H:%M"),
                            }
                            try:
                                resp, send_err = post_n8n(WEBHOOK_REPONSE, payload_notif)
                                if send_err:
                                    if send_err == "timeout":
                                        st.error("Timeout — le webhook n8n ne répond pas.")
                                    else:
                                        st.error(f"Erreur réseau : {send_err}")
                                    continue
                                if resp.status_code in (200, 201):
                                    ok_liste, err_liste = _upsert_planning_liste(
                                        user,
                                        numero_devis=numero,
                                        nom_client=client,
                                        objet=objet,
                                        salarie=salarie_sel,
                                        date_debut=date_debut_notif.strftime("%Y-%m-%d"),
                                        date_fin=date_fin_notif.strftime("%Y-%m-%d"),
                                        heure_debut=heure_intervention.strftime("%H:%M"),
                                        heure_fin=heure_fin.strftime("%H:%M"),
                                        tranches_personnalisees=tranches_json,
                                    )
                                    if not ok_liste:
                                        st.warning(f"Planification envoyée, mais écriture dans liste impossible : {err_liste}")
                                    ws_n, _ = get_worksheet(user, "notifications")
                                    if ws_n:
                                        sheet_row = row_idx + 2
                                        statut_col = list(df_notif.columns).index("statut") + 1 if "statut" in df_notif.columns else None
                                        if statut_col:
                                            ws_n.update_cell(sheet_row, statut_col, "planifie")
                                    log_activity(
                                        user,
                                        "chantier_modifie",
                                        target=numero or client or objet,
                                        details={
                                            "type": "planification",
                                            "salarie": salarie_sel,
                                            "date_debut": date_debut_notif.strftime("%Y-%m-%d"),
                                            "date_fin": date_fin_notif.strftime("%Y-%m-%d"),
                                        },
                                    )
                                    _load_notifications.clear()
                                    st.success(f"Planification envoyée à n8n pour {client}.")
                                    st.rerun()
                                else:
                                    st.error(f"Erreur n8n : {resp.status_code}")
                            except Exception as ex:
                                st.error(f"Erreur : {ex}")
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CRÉER UN DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Créer un devis":
    import streamlit.components.v1 as components
    page_header("Créer un devis", "Remplis le formulaire — n8n génère le PDF, l'envoie et met à jour Sheets")

    WEBHOOK_URL = f"https://n8n.florianai.fr/webhook/{user_slug}"

    def _parse_prix(val):
        try:
            return float(str(val).replace(",",".").replace(" ","").replace("\u202f","") or 0)
        except Exception:
            return 0.0

    @st.cache_data(ttl=60, show_spinner=False)
    def _load_catalogue_devis(u):
        ws, err = get_worksheet(u, "catalogue")
        if err:
            return []
        try:
            vals = ws.get_all_values()
            if not vals or len(vals) < 2:
                return []
            headers = [h.strip().lower() for h in vals[0]]
            items = []
            for r in vals[1:]:
                if not any(r):
                    continue
                row_d = dict(zip(headers, r + [""] * max(0, len(headers) - len(r))))
                article = row_d.get("article", row_d.get("sous-prestation", "")).strip()
                prix    = row_d.get("prix vente ht", row_d.get("total ht", "")).strip()
                desc    = row_d.get("description", "").strip()
                cat     = row_d.get("catégorie", row_d.get("categorie", "")).strip()
                items.append({"article": article, "description": desc,
                               "prix_ht": prix, "categorie": cat, "source": "catalogue"})
            return items
        except Exception:
            return []

    @st.cache_data(ttl=60, show_spinner=False)
    def _load_prestations_devis(u):
        ws, err = get_worksheet(u, "Feuille 1")
        if err:
            return []
        try:
            vals = ws.get_all_values()
            if not vals or len(vals) < 2:
                return []
            headers = [h.strip().lower() for h in vals[0]]
            items = []
            for r in vals[1:]:
                if not any(r):
                    continue
                row_d = dict(zip(headers, r + [""] * max(0, len(headers) - len(r))))
                article = (row_d.get("sous-prestation","") or row_d.get("sous prestation","")).strip()
                if not article:
                    continue
                prix = (row_d.get("total ht","") or row_d.get("prix vente ht","") or
                        row_d.get("prix mo ht","")).strip()
                desc = row_d.get("description","").strip()
                cat  = (row_d.get("categorie","") or row_d.get("catégorie","") or
                        row_d.get("type de poste","")).strip()
                qte_val = (
                    row_d.get("quantité","") or row_d.get("quantite","") or
                    row_d.get("qte","") or row_d.get("qté","")
                )
                qte = _parse_prix(qte_val) if str(qte_val).strip() else 1.0
                qte = qte if qte > 0 else 1.0
                label = article + (f"  –  {prix} € HT" if prix else "")
                items.append({"label": label, "article": article, "description": desc,
                               "prix_ht": prix, "categorie": cat, "qte": qte, "source": "prestations"})
            return items
        except Exception:
            return []

    catalogue_items   = _load_catalogue_devis(user)
    prestations_items = _load_prestations_devis(user)
    cat_labels        = ["— Choisir un article —"] + [it["article"] for it in catalogue_items]
    prest_labels      = ["— Choisir une prestation —"] + [it["label"] for it in prestations_items]

    if "devis_lignes" not in st.session_state:
        st.session_state.devis_lignes = [
            {"source": "libre", "article": "", "description": "", "prix_ht": 0.0, "qte": 1.0, "categorie": ""}
        ]
    if "devis_preview" not in st.session_state:
        st.session_state.devis_preview = False

    st.markdown("#### Informations client")
    c1, c2 = st.columns(2)
    with c1:
        client_nom   = st.text_input("Nom complet *", placeholder="Jean Dupont", key="dv_nom")
        client_email = st.text_input("Email", placeholder="jean.dupont@email.com (optionnel)", key="dv_email")
    with c2:
        client_tel     = st.text_input("Téléphone", placeholder="06 xx xx xx xx", key="dv_tel")
        client_adresse = st.text_input("Adresse du client", placeholder="12 rue de la Paix, 75001 Paris", key="dv_adr_client")

    st.markdown("---")
    st.markdown("#### Chantier")
    c3, c4 = st.columns(2)
    with c3:
        objet_travaux       = st.text_input("Objet des travaux *", placeholder="Rénovation salle de bain", key="dv_objet")
        adresse_chantier    = st.text_input("Adresse du chantier *", placeholder="108 rue de Falaise, 14000 Caen", key="dv_adr_chantier")
        categorie_operation = st.selectbox("Catégorie d'opération", [
            "Prestation", "Service", "Fourniture", "Fourniture et pose", "Main d'œuvre", "Autre",
        ], key="dv_cat_op")
        siren_client        = st.text_input("SIREN client (optionnel)", placeholder="123 456 789", key="dv_siren")
    with c4:
        modalite_paie = st.selectbox("Modalité de paiement", [
            "Acompte / Solde",
            "Paiement intégral à la commande",
            "Paiement comptant / immédiat",
            "Paiement échelonné / progressif",
            "Paiement différé / à terme",
        ], key="dv_modal")
        duree_jours = st.number_input("Durée estimée (jours ouvrés) *", min_value=1, value=5, step=1, key="dv_duree")

    pct_acompte   = 30
    pct_solde     = 70
    segments      = []
    jours_differe = 0
    phrase_modalite = ""

    if modalite_paie == "Acompte / Solde":
        st.markdown("##### ⚙️ Répartition acompte / solde")
        ca1, ca2 = st.columns(2)
        with ca1:
            pct_acompte = st.slider("Acompte (%)", min_value=10, max_value=90, value=30, step=5, key="dv_pct_acompte")
        pct_solde = 100 - pct_acompte
        with ca2:
            st.metric("Solde (%)", f"{pct_solde} %")
        segments = [
            {"etape": "À la commande", "percent": pct_acompte},
            {"etape": "À la réception", "percent": pct_solde},
        ]
    elif modalite_paie == "Paiement échelonné / progressif":
        st.markdown("##### ⚙️ Répartition échelonnée")
        ce1, ce2, ce3 = st.columns(3)
        with ce1:
            pct_cmd = st.slider("À la commande (%)", min_value=0, max_value=100, value=20, step=5, key="dv_pct_cmd")
        with ce2:
            pct_enc = st.slider("En cours (%)", min_value=0, max_value=100-pct_cmd, value=min(30, 100-pct_cmd), step=5, key="dv_pct_enc")
        pct_fin = 100 - pct_cmd - pct_enc
        with ce3:
            st.metric("À la réception (%)", f"{pct_fin} %")
        if pct_fin < 0:
            st.error("Le total dépasse 100% — ajuste les pourcentages.")
        segments = [
            {"etape": "À la commande",        "percent": pct_cmd},
            {"etape": "En cours de chantier", "percent": pct_enc},
            {"etape": "À la réception",       "percent": pct_fin},
        ]
    elif modalite_paie == "Paiement différé / à terme":
        st.markdown("##### ⚙️ Délai de paiement")
        jours_differe = st.number_input("Nombre de jours après réception", min_value=1, max_value=365, value=30, step=1, key="dv_jours_differe")
        segments = [{"etape": f"À terme ({jours_differe}j)", "percent": 100}]
    elif modalite_paie == "Paiement intégral à la commande":
        segments = [{"etape": "À la commande", "percent": 100}]
    elif modalite_paie == "Paiement comptant / immédiat":
        segments = [{"etape": "À la réception", "percent": 100}]

    st.markdown("---")
    st.markdown("#### TVA")
    c_tva1, c_tva2 = st.columns([2, 2])
    with c_tva1:
        tva_option = st.radio("Taux TVA applicable", [
            "5,5 % (amélioration énergétique)",
            "10 % (travaux de rénovation)",
            "20 % (travaux neufs / autres)",
        ], key="dv_tva")
    with c_tva2:
        tva_debits_option = st.radio("Régime TVA", [
            "TVA sur encaissements",
            "TVA sur débits",
        ], key="dv_tva_debits")

    tva_taux        = 0.055 if "5,5" in tva_option else (0.10 if "10 %" in tva_option else 0.20)
    tva_debits_bool = "débits" in tva_debits_option
    tva_pct_str     = "5,5" if tva_taux == 0.055 else str(int(tva_taux * 100))

    st.markdown("---")
    st.markdown("#### Prestations")

    lignes = st.session_state.devis_lignes
    to_del = []

    for i, ligne in enumerate(lignes):
        with st.container(border=True):
            col_src, col_del = st.columns([6, 1])
            with col_src:
                src_idx = {"catalogue": 0, "prestations": 1}.get(ligne.get("source", "libre"), 2)
                src = st.radio(
                    f"src_{i}",
                    ["Divers", "Prestations", "Saisie libre"],
                    horizontal=True,
                    key=f"src_{i}",
                    index=src_idx,
                    label_visibility="collapsed",
                )
            prev_src_key = f"_prev_src_{i}"
            if st.session_state.get(prev_src_key) != src:
                st.session_state[prev_src_key] = src
                ligne["_prev_sel"] = None
                ligne["article"] = ""
                ligne["prix_ht"] = 0.0
                ligne["qte"] = 1.0
                st.rerun()
            with col_del:
                if len(lignes) > 1 and st.button("Supprimer", key=f"del_{i}"):
                    to_del.append(i)

            if src == "Divers":
                ligne["source"] = "catalogue"
                sel = st.selectbox("Article", cat_labels, key=f"cat_{i}", label_visibility="collapsed")
                if sel != cat_labels[0]:
                    found = next((it for it in catalogue_items if it["article"] == sel), None)
                    if found and sel != ligne.get("_prev_sel"):
                        ligne.update({"article": found["article"], "description": "",
                                      "categorie": found["categorie"], "_prev_sel": sel,
                                      "prix_ht": _parse_prix(found["prix_ht"]),
                                      "qte": 1.0})
                        st.rerun()
                new_qte = st.number_input("Quantité", min_value=0.1, value=float(ligne["qte"]), step=1.0, key=f"qte_{i}")
                ligne["qte"] = new_qte
                if ligne.get("article"):
                    st.caption(f"Prix HT : **{ligne['prix_ht']:,.2f} €** — Total HT : **{ligne['qte'] * ligne['prix_ht']:,.2f} €**")
            elif src == "Prestations":
                ligne["source"] = "prestations"
                sel = st.selectbox("Prestation", prest_labels, key=f"prest_{i}", label_visibility="collapsed")
                if sel != prest_labels[0]:
                    found = next((it for it in prestations_items if it["label"] == sel), None)
                    if found and sel != ligne.get("_prev_sel"):
                        ligne["article"]     = found["article"]
                        ligne["description"] = found["description"]
                        ligne["categorie"]   = found["categorie"]
                        ligne["_prev_sel"]   = sel
                        ligne["prix_ht"]     = _parse_prix(found["prix_ht"])
                        ligne["qte"]         = float(found.get("qte", 1.0))
                        st.session_state[f"pht2_{i}"] = float(ligne["prix_ht"])
                        st.session_state[f"qte2_{i}"] = float(ligne["qte"])
                        st.rerun()
                cq2, cp2 = st.columns(2)
                new_qte2 = cq2.number_input("Quantité", min_value=0.1, value=float(ligne["qte"]), step=1.0, key=f"qte2_{i}")
                new_pht2 = cp2.number_input("Prix unitaire HT (€)", min_value=0.0, value=float(ligne["prix_ht"]), step=10.0, key=f"pht2_{i}")
                ligne["qte"]     = new_qte2
                ligne["prix_ht"] = new_pht2
            else:
                ligne["source"] = "libre"
                ligne["article"] = st.text_input("Désignation *", value=ligne.get("article", ""), key=f"art_{i}", placeholder="Ex : Pose carrelage")
                ligne["description"] = st.text_input("Description", value=ligne.get("description", ""), key=f"desc_{i}")
                cq3, cp3 = st.columns(2)
                new_qte3 = cq3.number_input("Quantité", min_value=0.1, value=float(ligne["qte"]), step=1.0, key=f"qte3_{i}")
                new_pht3 = cp3.number_input("Prix unitaire HT (€)", min_value=0.0, value=float(ligne["prix_ht"]), step=10.0, key=f"pht3_{i}")
                ligne["qte"] = new_qte3
                ligne["prix_ht"] = new_pht3

    for idx in sorted(to_del, reverse=True):
        st.session_state.devis_lignes.pop(idx)
    if to_del:
        st.rerun()

    if st.button("Ajouter une ligne", key="add_ligne"):
        st.session_state.devis_lignes.append(
            {"source": "libre", "article": "", "description": "", "prix_ht": 0.0, "qte": 1.0, "categorie": ""}
        )
        st.rerun()

    def _get_prix(i, l):
        return float(l["prix_ht"])

    def _get_qte(i, l):
        return float(l["qte"])

    total_ht  = sum(_get_prix(i, l) * _get_qte(i, l) for i, l in enumerate(lignes))
    total_tva = round(total_ht * tva_taux, 2)
    total_ttc = round(total_ht + total_tva, 2)

    if modalite_paie == "Acompte / Solde":
        montant_acompte = round(total_ttc * pct_acompte / 100, 2)
        montant_solde   = round(total_ttc * pct_solde   / 100, 2)
        phrase_modalite = f"Acompte de {pct_acompte}% à la commande ({montant_acompte:,.2f} €) — Solde de {pct_solde}% à la réception ({montant_solde:,.2f} €)"
    elif modalite_paie == "Paiement échelonné / progressif":
        parts = []
        for s in segments:
            if s["percent"] > 0:
                montant_s = round(total_ttc * s["percent"] / 100, 2)
                parts.append(f"{s['percent']}% {s['etape'].lower()} ({montant_s:,.2f} €)")
        phrase_modalite = " — ".join(parts)
    elif modalite_paie == "Paiement différé / à terme":
        phrase_modalite = f"Paiement intégral de {total_ttc:,.2f} € sous {jours_differe} jours après réception"
    elif modalite_paie == "Paiement intégral à la commande":
        phrase_modalite = f"Paiement intégral de {total_ttc:,.2f} € à la commande"
    elif modalite_paie == "Paiement comptant / immédiat":
        phrase_modalite = f"Paiement comptant de {total_ttc:,.2f} € à la réception"

    st.markdown(f"""
    <div style="display:flex;justify-content:flex-end;margin-top:12px;">
      <div style="min-width:280px;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
        <div style="display:flex;justify-content:space-between;padding:6px 14px;background:var(--bg-surface);font-size:0.88rem;">
          <span style="color:var(--text-muted);">Total HT</span><strong>{total_ht:,.2f} €</strong>
        </div>
        <div style="display:flex;justify-content:space-between;padding:6px 14px;background:var(--bg-surface);font-size:0.88rem;">
          <span style="color:var(--text-muted);">TVA ({tva_pct_str} %)</span><strong>{total_tva:,.2f} €</strong>
        </div>
        <div style="display:flex;justify-content:space-between;padding:8px 14px;background:#1d4ed8;color:#fff;font-weight:700;font-size:1rem;">
          <span>TOTAL TTC</span><span>{total_ttc:,.2f} €</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if phrase_modalite:
        st.info(f"**{phrase_modalite}**")

    st.markdown("<br>", unsafe_allow_html=True)

    def _validate():
        errs = []
        if not client_nom.strip():       errs.append("Nom client manquant")
        if not objet_travaux.strip():    errs.append("Objet des travaux manquant")
        if not any(l["article"].strip() for l in lignes):
            errs.append("Au moins une prestation est requise")
        return errs

    def _build_payload():
        return {
            "nom_complet":         client_nom.strip(),
            "adresse":             client_adresse.strip(),
            "email":               client_email.strip(),
            "tel":                 client_tel.strip(),
            "siren_client":        siren_client.strip(),
            "objet":               objet_travaux.strip(),
            "adresse_chantier":    adresse_chantier.strip(),
            "categorie_operation": categorie_operation,
            "duree_jours":         int(duree_jours),
            "date_debut":          datetime.today().strftime("%Y-%m-%d"),
            "modalite_paiement":   modalite_paie,
            "phrase_modalite":     phrase_modalite,
            "phrase_modalité":     phrase_modalite,
            "segments":            segments,
            "jours_differe":       jours_differe,
            "tva_choisi":          float(tva_pct_str.replace(",", ".")),
            "tva_debits":          "Oui" if tva_debits_bool else "Non",
            "prestations": [
                {
                    "libelle":     l["article"].strip(),
                    "description": l["description"].strip(),
                    "quantite":    _get_qte(i, l),
                    "HT":          round(_get_prix(i, l) * _get_qte(i, l), 2),
                    "TVA":         round(_get_prix(i, l) * _get_qte(i, l) * tva_taux, 2),
                    "TTC":         round(_get_prix(i, l) * _get_qte(i, l) * (1 + tva_taux), 2),
                }
                for i, l in enumerate(lignes) if l["article"].strip()
            ],
            "totalHT":  round(total_ht, 2),
            "TVA":      round(total_tva, 2),
            "totalTTC": round(total_ttc, 2),
            "cree_par": user,
            "cree_le":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source":   "streamlit_erp",
        }

    if st.button("Prévisualiser le devis", use_container_width=True, key="btn_preview"):
        errs = _validate()
        if errs:
            for e in errs: st.error(f"{e}")
        else:
            st.session_state.devis_preview = True

    if st.session_state.get("devis_preview"):
        st.markdown("---")

        lignes_html = ""
        for i, l in enumerate(lignes):
            if not l["article"].strip():
                continue
            prix       = _get_prix(i, l)
            qte        = _get_qte(i, l)
            total_ht_l = round(qte * prix, 2)
            tva_l      = round(total_ht_l * tva_taux, 2)
            ttc_l      = round(total_ht_l + tva_l, 2)
            bg         = "#f8fafc" if i % 2 == 0 else "#ffffff"
            desc_part  = f"<br><span style='color:#64748b;font-size:8px;'>{l['description']}</span>" if l.get("description","").strip() else ""
            lignes_html += f"""
            <tr style="background:{bg};">
              <td style="padding:5px 6px;text-align:center;border-bottom:1px solid #e2e8f0;color:#1e293b;">{i+1}</td>
              <td style="padding:5px 10px;border-bottom:1px solid #e2e8f0;color:#1e293b;">
                <strong style="font-size:9px;">{l['article']}</strong>{desc_part}
              </td>
              <td style="padding:5px 6px;text-align:center;border-bottom:1px solid #e2e8f0;color:#1e293b;">{qte:g}</td>
              <td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;color:#1e293b;">{prix:,.2f} €</td>
              <td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;color:#64748b;">{tva_pct_str} %</td>
              <td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;color:#64748b;">{tva_l:,.2f} €</td>
              <td style="padding:5px 6px;text-align:right;border-bottom:1px solid #e2e8f0;font-weight:700;color:#1d4ed8;">{ttc_l:,.2f} €</td>
            </tr>"""

        date_fin_str = (datetime.today() + timedelta(days=int(duree_jours))).strftime("%d/%m/%Y")
        segments_html = "".join([
            f"<p>• {s['etape']} : <strong>{s['percent']}%</strong> — {round(total_ttc * s['percent'] / 100, 2):,.2f} €</p>"
            for s in segments if s["percent"] > 0
        ])
        siren_html_preview = f"<p>SIREN : {siren_client.strip()}</p>" if siren_client.strip() else ""

        preview_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Devis</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 9px; color: #1e293b; background: #fff; padding: 15px; }}
  header {{ display: flex; flex-direction: row; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 3px solid #1d4ed8; }}
  .header-left {{ display: flex; flex-direction: column; gap: 5px; }}
  .badge-devis {{ display: inline-block; background: #1d4ed8; color: #fff; font-size: 16px; font-weight: 800; letter-spacing: 3px; padding: 3px 12px; border-radius: 4px; }}
  .doc-info {{ font-size: 8px; color: #64748b; margin-top: 3px; }}
  .doc-info span {{ background: #f1f5f9; padding: 2px 6px; border-radius: 3px; margin-right: 4px; font-weight: 600; }}
  .header-right {{ display: flex; flex-direction: row; align-items: center; gap: 10px; }}
  .logo-placeholder {{ width: 45px; height: 45px; border-radius: 6px; background: #1d4ed8; display: flex; align-items: center; justify-content: center; }}
  .logo-initials {{ color: #fff; font-size: 14px; font-weight: 900; }}
  .company-info {{ text-align: right; font-size: 8px; line-height: 1.5; color: #475569; }}
  .company-info strong {{ font-size: 10px; color: #1d4ed8; display: block; }}
  .section-title {{ font-weight: 700; font-size: 8px; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; padding-bottom: 2px; border-bottom: 1px solid #e2e8f0; }}
  .two-columns {{ display: flex; flex-direction: row; gap: 10px; margin-bottom: 12px; }}
  .column {{ flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 5px; padding: 7px 10px; }}
  .column p {{ margin-top: 3px; line-height: 1.5; color: #334155; }}
  .column p strong {{ font-size: 10px; color: #0f172a; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 4px; font-size: 8.5px; }}
  thead tr {{ background: #1d4ed8; color: #fff; }}
  thead th {{ padding: 5px 6px; text-align: left; font-weight: 600; font-size: 8px; text-transform: uppercase; }}
  thead th.right {{ text-align: right; }}
  thead th.center {{ text-align: center; }}
  tbody tr:nth-child(even) {{ background: #f8fafc; }}
  tbody td {{ padding: 5px 6px; border-bottom: 1px solid #e2e8f0; color: #334155; vertical-align: top; }}
  td.right {{ text-align: right; }}
  td.center {{ text-align: center; }}
  .totals-wrapper {{ display: flex; justify-content: flex-end; margin-top: 8px; }}
  .totals {{ min-width: 200px; border: 1px solid #e2e8f0; border-radius: 5px; overflow: hidden; }}
  .totals-row {{ display: flex; justify-content: space-between; padding: 4px 10px; border-bottom: 1px solid #e2e8f0; font-size: 8.5px; }}
  .totals-row.ht, .totals-row.tva {{ background: #f8fafc; }}
  .totals-row.ttc {{ background: #1d4ed8; color: #fff; font-weight: 700; font-size: 10px; padding: 6px 10px; }}
  .delai-box {{ margin-top: 8px; padding: 5px 10px; background: #eff6ff; border-left: 3px solid #1d4ed8; border-radius: 0 4px 4px 0; font-size: 8px; color: #1e40af; }}
  .modalites-box {{ margin-top: 8px; padding: 8px 10px; border: 1px solid #bfdbfe; background: #f0f7ff; border-radius: 5px; font-size: 8px; }}
  .modalites-title {{ font-weight: 700; color: #1d4ed8; font-size: 9px; margin-bottom: 3px; }}
  .modalites-detail {{ color: #475569; margin-bottom: 6px; }}
  .info-grid {{ display: flex; flex-direction: row; gap: 10px; margin-top: 8px; }}
  .company-block, .legal-compact {{ flex: 1; font-size: 7.5px; line-height: 1.5; padding: 7px 8px; border-radius: 4px; background: #f8fafc; border: 1px solid #e2e8f0; }}
  .company-block strong, .legal-compact strong {{ display: block; font-size: 8px; color: #1d4ed8; margin-bottom: 3px; text-transform: uppercase; }}
  .company-block {{ border-left: 3px solid #1d4ed8; }}
  .legal-compact {{ border-left: 3px solid #f59e0b; }}
  .signature {{ margin-top: 8px; }}
  .signature-block {{ max-width: 250px; padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 5px; background: #fafafa; }}
  .sig-title {{ font-weight: 700; font-size: 8px; color: #1d4ed8; text-transform: uppercase; margin-bottom: 5px; }}
  .sig-date {{ font-size: 7.5px; color: #64748b; margin-bottom: 20px; }}
  .signature-line {{ border-bottom: 1px solid #94a3b8; width: 100%; }}
  footer {{ margin-top: 8px; text-align: center; font-size: 7px; color: #94a3b8; padding-top: 6px; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <div class="badge-devis">DEVIS</div>
    <div class="doc-info">
      <span>Date : {datetime.now().strftime("%d/%m/%Y")}</span>
      <span>TVA : {tva_pct_str} %</span>
      <span>{"TVA sur debits" if tva_debits_bool else "TVA sur encaissements"}</span>
      <span>{categorie_operation}</span>
    </div>
  </div>
  <div class="header-right">
    <div class="company-info">
      <strong>Florian AI Batiment</strong>
      108 rue de Falaise<br>
      14000 Caen<br>
      SIRET 812 345 678 00027<br>
      TVA FR12 812345678<br>
      06 12 34 56 78<br>
      contact@florian-ai-batiment.fr
    </div>
    <div class="logo-placeholder">
      <span class="logo-initials">FA</span>
    </div>
  </div>
</header>

<div class="two-columns">
  <div class="column">
    <div class="section-title">Client</div>
    <p><strong>{client_nom}</strong></p>
    <p>{client_adresse}</p>
    <p>{client_email}</p>
    {"<p>" + client_tel + "</p>" if client_tel.strip() else ""}
    {siren_html_preview}
  </div>
  <div class="column">
    <div class="section-title">Objet des travaux</div>
    <p><strong>{objet_travaux}</strong></p>
    <p>{adresse_chantier}</p>
    <p>Categorie : {categorie_operation}</p>
    <p>Duree : {duree_jours} jour(s) ouvre(s)</p>
    <p>Fin estimee : {date_fin_str}</p>
  </div>
</div>

<div class="section-title">Detail des prestations</div>
<table>
  <thead>
    <tr>
      <th class="center" style="width:28px;">N°</th>
      <th>Prestation</th>
      <th class="center" style="width:35px;">Qte</th>
      <th class="right" style="width:60px;">HT (€)</th>
      <th class="right" style="width:55px;">TVA (€)</th>
      <th class="right" style="width:65px;">TTC (€)</th>
    </tr>
  </thead>
  <tbody>
    {lignes_html if lignes_html else '<tr><td colspan="6" style="padding:12px;text-align:center;color:#94a3b8;font-style:italic;">Aucune prestation renseignee</td></tr>'}
  </tbody>
</table>

<div class="totals-wrapper">
  <div class="totals">
    <div class="totals-row ht"><span>Total HT</span><strong>{total_ht:,.2f} €</strong></div>
    <div class="totals-row tva"><span>TVA ({tva_pct_str} %)</span><strong>{total_tva:,.2f} €</strong></div>
    <div class="totals-row ttc"><span>TOTAL TTC</span><span>{total_ttc:,.2f} €</span></div>
  </div>
</div>

<div class="delai-box">
  Delai de prestation : <strong>{duree_jours} jours</strong> a compter de la signature du devis
</div>

<div class="modalites-box">
  <div class="modalites-title">Modalites de paiement - {modalite_paie}</div>
  <div class="modalites-detail">{phrase_modalite}</div>
  {segments_html}
  <div style="color:#b45309;margin-bottom:6px;margin-top:4px;">Paiement sous 30 jours a compter de la facturation - Tout retard entraine des penalites au taux legal en vigueur.</div>
  <div style="margin-bottom:6px; color:#475569;">Modes de paiement acceptes : Cheque, Virement bancaire, Carte bancaire</div>
</div>

<div class="info-grid">
  <div class="company-block">
    <strong>Informations societe</strong>
    Florian AI Batiment - SARL au capital de 10 000 €<br>
    SIRET 812 345 678 00027 | RCS Caen | TVA FR12 812345678<br>
    Assurance decennale : AXA France IARD - Contrat n° DEC-2025-45879
  </div>
  <div class="legal-compact">
    <strong>Conditions generales de vente</strong>
    Devis valable 30 jours. Retard de paiement - penalites legales + indemnite 40 €.<br>
    {"TVA 5,5% applicable selon art. 278-0 bis CGI (travaux economie d'energie, logement +2 ans)." if tva_taux == 0.055 else "TVA 10% applicable selon art. 279-0 bis CGI (travaux de renovation, logement +2 ans)." if tva_taux == 0.10 else "TVA 20% - Taux normal applicable."}<br>
    Retractation 14 jours (art. L221-18). Litige : Tribunal de Commerce de Caen.
  </div>
</div>

<div class="signature">
  <div class="signature-block">
    <div class="sig-title">Bon pour accord - Client</div>
    <div class="sig-date">Date : ___________________________</div>
    <div style="font-size:7px; color:#94a3b8; margin-bottom:15px;">Precede de la mention Lu et approuve</div>
    <div class="signature-line"></div>
  </div>
</div>

<footer>
  Florian AI Batiment - SIRET 812 345 678 00027 - contact@florian-ai-batiment.fr - 06 12 34 56 78 - Document valable 30 jours
</footer>

</body>
</html>"""

        nb_lignes_valides = sum(1 for l in lignes if l["article"].strip())
        preview_height = 900 + nb_lignes_valides * 32
        components.html(preview_html, height=preview_height, scrolling=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Modifier le devis", key="btn_close_preview", use_container_width=True):
                st.session_state.devis_preview = False
                st.rerun()
        with col_b:
            if st.button("Imprimer / PDF", key="btn_imprimer", use_container_width=True):
                payload = _build_payload()
                payload["action"] = "imprimer"
                try:
                    resp, send_err = post_n8n(WEBHOOK_URL, payload)
                    if send_err:
                        st.error("Timeout — n8n ne répond pas." if send_err == "timeout" else f"Erreur : {send_err}")
                        resp = None
                    if resp is not None and resp.status_code in (200, 201):
                        log_activity(user, "devis_modifie", target=str(payload.get("numero_devis", "")), details={"action": "imprimer"})
                        st.success("Envoyé à n8n pour impression.")
                    elif resp is not None:
                        st.error(f"Erreur {resp.status_code}")
                except Exception as ex:
                    st.error(f"Erreur : {ex}")
        with col_c:
            if st.button("Envoyer au client", key="btn_envoyer_client", use_container_width=True, type="primary"):
                if not client_email.strip():
                    st.error("L'email client est obligatoire pour envoyer le devis.")
                else:
                    payload = _build_payload()
                    payload["action"] = "envoyer"
                    try:
                        resp, send_err = post_n8n(WEBHOOK_URL, payload)
                        if send_err:
                            st.error("Timeout — n8n ne répond pas." if send_err == "timeout" else f"Erreur : {send_err}")
                        elif resp.status_code in (200, 201):
                            log_activity(user, "devis_modifie", target=str(payload.get("numero_devis", "")), details={"action": "envoyer_client"})
                            st.success("Devis envoyé au client.")
                            st.session_state.devis_lignes = [
                                {"source": "libre", "article": "", "description": "", "prix_ht": 0.0, "qte": 1.0, "categorie": ""}
                            ]
                            st.session_state.devis_preview = False
                            get_sheet_data.clear()
                            get_main_dataset.clear()
                            clear_cache_if_exists("get_pending_notifications_count")
                        else:
                            st.error(f"Erreur {resp.status_code}")
                    except Exception as ex:
                        st.error(f"Erreur : {ex}")

    st.stop()

# ── CHARGEMENT DONNÉES ─────────────────────────────────────────────────────────
PAGES_NEED_MAIN_DF = {
    "Vue Générale",
    "Devis",
    "Factures & Paiements",
    "Chantiers",
    "Planning",
    "Salariés",
    "Tous les dossiers",
}
if page in PAGES_NEED_MAIN_DF:
    dataset, error, is_empty_sheet = get_main_dataset(user)
    if error:
        show_data_source_error(
            f"Impossible de se connecter à Google Sheets. Détail : {error}",
            clear_fn=lambda: (get_main_dataset.clear(), get_sheet_data.clear()),
            retry_key="retry_main_dataset",
        )
        st.stop()

    if is_empty_sheet:
        st.warning("📭 Le Google Sheet est vide ou inaccessible.")
        st.stop()

    df = dataset["df"]
    COL_CLIENT = dataset["COL_CLIENT"]
    COL_CHANTIER = dataset["COL_CHANTIER"]
    COL_NUM = dataset["COL_NUM"]
    COL_MONTANT = dataset["COL_MONTANT"]
    COL_SIGN = dataset["COL_SIGN"]
    COL_FACT_FIN = dataset["COL_FACT_FIN"]
    COL_PV = dataset["COL_PV"]
    COL_STATUT = dataset["COL_STATUT"]
    COL_DATE = dataset["COL_DATE"]
    COL_MODALITE = dataset["COL_MODALITE"]
    COL_TVA = dataset["COL_TVA"]
    COL_RELANCE1 = dataset["COL_RELANCE1"]
    COL_RELANCE2 = dataset["COL_RELANCE2"]
    COL_RELANCE3 = dataset["COL_RELANCE3"]
    COL_ACOMPTE1 = dataset["COL_ACOMPTE1"]
    COL_ACOMPTE2 = dataset["COL_ACOMPTE2"]
    COL_RESERVE = dataset["COL_RESERVE"]
    COL_ADRESSE = dataset["COL_ADRESSE"]
    COL_DATE_DEBUT = dataset["COL_DATE_DEBUT"]
    COL_DATE_FIN = dataset["COL_DATE_FIN"]
    COL_EQUIPE = dataset["COL_EQUIPE"]
    total_ca = dataset["total_ca"]
    nb_devis = dataset["nb_devis"]
    nb_signes = dataset["nb_signes"]
    nb_attente = dataset["nb_attente"]
    nb_fact_ok = dataset["nb_fact_ok"]
    ca_signe = dataset["ca_signe"]
    ca_non_s = dataset["ca_non_s"]
    taux_conv = dataset["taux_conv"]
    reste_encaissement = dataset["reste_encaissement"]

    data_notice = st.session_state.get("_data_source_notice", "").strip()
    if data_notice:
        st.warning(data_notice)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : VUE GÉNÉRALE
# ══════════════════════════════════════════════════════════════════════════════
if page == "Vue Générale":
    page_header("Tableau de Bord", f"Synchronisé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    render_ceo_hero(
        "Pilotage exécutif",
        "Vision consolidée du business : revenus sécurisés, conversion commerciale, encaissements et zones de friction. "
        "Cette vue sert de cockpit principal pour décider vite.",
        chips=[
            f"{nb_devis} dossiers",
            f"{int(df['_signe'].sum())} signés",
            f"{int(df['_fact_fin'].sum())} facturés",
        ],
    )

    # ── Sélecteur de dates global ──────────────────────────────────────────
    render_filter_banner("Zone filtres", "Cadre la période d'analyse pour isoler une campagne, un mois ou une période de production.")
    with st.expander("📅 Filtrer par période", expanded=False):
        col_fd1, col_fd2, col_fd3 = st.columns([2, 2, 1])
        with col_fd1:
            date_debut_vg = st.date_input("Du", value=None, key="vg_date_debut")
        with col_fd2:
            date_fin_vg = st.date_input("Au", value=None, key="vg_date_fin")
        with col_fd3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Réinitialiser", key="vg_reset_dates", use_container_width=True):
                st.session_state.pop("vg_date_debut", None)
                st.session_state.pop("vg_date_fin", None)

    # ── Filtrage selon période ─────────────────────────────────────────────
    df_vg = df.copy()
    periode_active = False

    if COL_DATE and (date_debut_vg or date_fin_vg):
        if "_date_parsed_main" in df_vg.columns:
            df_vg["_date_parsed"] = df_vg["_date_parsed_main"]
        else:
            df_vg["_date_parsed"] = parse_flexible_series(df_vg[COL_DATE])
        if date_debut_vg:
            df_vg = df_vg[df_vg["_date_parsed"].dt.date >= date_debut_vg]
        if date_fin_vg:
            df_vg = df_vg[df_vg["_date_parsed"].dt.date <= date_fin_vg]
        periode_active = True

    # ── Recalcul KPIs sur df_vg ───────────────────────────────────────────
    vg_nb_devis    = len(df_vg)
    vg_nb_signes   = int(df_vg["_signe"].sum())
    vg_nb_attente  = vg_nb_devis - vg_nb_signes
    vg_nb_fact_ok  = int(df_vg["_fact_fin"].sum())
    vg_ca_signe    = df_vg[df_vg["_signe"]]["_montant"].sum()
    vg_ca_non_s    = df_vg[~df_vg["_signe"]]["_montant"].sum()
    vg_total_ca    = df_vg["_montant"].sum()
    vg_taux_conv   = int((vg_nb_signes / vg_nb_devis) * 100) if vg_nb_devis > 0 else 0
    vg_reste       = df_vg[(df_vg["_signe"]) & (~df_vg["_fact_fin"])]["_reste"].sum()

    if periode_active:
        label_periode = ""
        if date_debut_vg and date_fin_vg:
            label_periode = f"{date_debut_vg.strftime('%d/%m/%Y')} → {date_fin_vg.strftime('%d/%m/%Y')}"
        elif date_debut_vg:
            label_periode = f"Depuis le {date_debut_vg.strftime('%d/%m/%Y')}"
        else:
            label_periode = f"Jusqu'au {date_fin_vg.strftime('%d/%m/%Y')}"
        st.info(f"📅 Période active : **{label_periode}** — {vg_nb_devis} dossier(s)")

    render_kpi_cards([
        {"label": "CA Sécurisé", "value": fmt(vg_ca_signe), "delta": f"{vg_nb_signes} devis signés", "icon": "€", "fill_pct": 100 if vg_total_ca <= 0 else int((vg_ca_signe / max(vg_total_ca, 1)) * 100), "accent": "#00d68f", "accent_bg": "rgba(0,214,143,0.18)", "delta_color": "#00d68f"},
        {"label": "CA En Négociation", "value": fmt(vg_ca_non_s), "delta": f"{vg_nb_attente} en cours", "icon": "◔", "fill_pct": 100 if vg_total_ca <= 0 else int((vg_ca_non_s / max(vg_total_ca, 1)) * 100), "accent": "#ffb84d", "accent_bg": "rgba(255,184,77,0.18)", "delta_color": "#ffb84d"},
        {"label": "Taux de Conversion", "value": f"{vg_taux_conv} %", "delta": f"{vg_nb_signes} / {vg_nb_devis} transformés", "icon": "↗", "fill_pct": vg_taux_conv, "accent": "#4f8ef7", "accent_bg": "rgba(79,142,247,0.18)", "delta_color": "#4f8ef7"},
        {"label": "Reste à Encaisser", "value": fmt(vg_reste), "delta": "Exposition de trésorerie", "icon": "◈", "fill_pct": 100 if vg_ca_signe <= 0 else int((vg_reste / max(vg_ca_signe, 1)) * 100), "accent": "#ff5c7a", "accent_bg": "rgba(255,92,122,0.18)", "delta_color": "#ff5c7a"},
    ])

    with st.container(border=True):
        st.markdown("### Prévisions de Trésorerie à 30 jours")
        if not COL_DATE:
            st.info("Colonne 'Date' introuvable pour calculer les échéances.")
        else:
            horizon_days = st.slider(
                "Durée de la prévision (jours)",
                min_value=7,
                max_value=120,
                value=30,
                step=1,
                key="treso_horizon_days",
            )
            df_tres = df.copy()
            if "_date_parsed_main" in df_tres.columns:
                df_tres["_base_date"] = df_tres["_date_parsed_main"]
            else:
                df_tres["_base_date"] = parse_flexible_series(df_tres[COL_DATE])
            df_tres["_due_date"] = df_tres["_base_date"] + pd.Timedelta(days=30)
            if COL_DATE_FIN:
                if "_date_fin_parsed_main" in df_tres.columns:
                    fin_dt = df_tres["_date_fin_parsed_main"]
                else:
                    fin_dt = parse_flexible_series(df_tres[COL_DATE_FIN])
                df_tres["_due_date"] = fin_dt.fillna(df_tres["_due_date"])

            if COL_STATUT:
                df_tres["_statut_norm"] = (
                    df_tres[COL_STATUT]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .str.replace("é", "e", regex=False)
                    .str.replace("è", "e", regex=False)
                    .str.replace("ê", "e", regex=False)
                    .str.replace("à", "a", regex=False)
                )
                # Filtre souple: accepte les variantes ("Facturé ✅", "En attente client", etc.)
                statut_mask = (
                    df_tres["_statut_norm"].str.contains("factur", na=False)
                    | df_tres["_statut_norm"].str.contains("en facturation", na=False)
                    | df_tres["_statut_norm"].str.contains("attente", na=False)
                )
                df_tres = df_tres[statut_mask]
            else:
                st.warning("Colonne 'Statut' non détectée : prévision calculée sans filtre de statut.")

            today = datetime.now().date()
            next_30 = today + timedelta(days=int(horizon_days))
            prev_30_start = today - timedelta(days=int(horizon_days))
            prev_30_end = today - timedelta(days=1)

            df_tres = df_tres.dropna(subset=["_due_date"]).copy()
            df_tres["_due_day"] = df_tres["_due_date"].dt.date
            df_future = df_tres[(df_tres["_due_day"] >= today) & (df_tres["_due_day"] <= next_30)].copy()
            df_past = df_tres[(df_tres["_due_day"] >= prev_30_start) & (df_tres["_due_day"] <= prev_30_end)].copy()

            total_future = float(df_future["_montant"].sum()) if not df_future.empty else 0.0
            total_past = float(df_past["_montant"].sum()) if not df_past.empty else 0.0
            delta_value = total_future - total_past
            st.metric(f"Montant total à recevoir ({horizon_days} jours)", fmt(total_future), delta=f"{delta_value:,.0f} €".replace(",", " "))

            if df_future.empty:
                st.info(f"Aucune échéance attendue entre aujourd'hui et les {horizon_days} prochains jours.")
            else:
                daily = (
                    df_future.groupby("_due_day")["_montant"]
                    .sum()
                    .reset_index()
                    .sort_values("_due_day")
                )
                daily["Cumul"] = daily["_montant"].cumsum()

                fig_tres = go.Figure()
                fig_tres.add_trace(
                    go.Bar(
                        x=daily["_due_day"],
                        y=daily["_montant"],
                        name="Entrées TTC / jour",
                        marker_color="#4f8ef7",
                    )
                )
                fig_tres.add_trace(
                    go.Scatter(
                        x=daily["_due_day"],
                        y=daily["Cumul"],
                        name="Cumul progressif",
                        mode="lines+markers",
                        line=dict(color="#00d68f", width=3, shape="spline"),
                        marker=dict(size=6),
                    )
                )
                fig_tres.update_layout(
                    title=f"Prévision encaissements ({horizon_days} jours)",
                    paper_bgcolor=chart_bg,
                    plot_bgcolor=chart_bg,
                    font=dict(color=chart_font, family="Inter"),
                    xaxis=dict(title="", tickformat="%d/%m"),
                    yaxis=dict(title="Montant TTC (€)", tickformat=",.0f"),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                    margin=dict(t=60, b=30, l=20, r=20),
                )
                st.plotly_chart(fig_tres, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cl, cr = st.columns([2, 1])
    with cl:
        with st.container(border=True):
            if COL_DATE:
                d2 = df.copy()  # graphique toujours sur toutes les données (ou filtré si période)
                if periode_active:
                    d2 = df_vg.copy()
                    if "_date_parsed" not in d2.columns:
                        if "_date_parsed_main" in d2.columns:
                            d2["_date_parsed"] = d2["_date_parsed_main"]
                        else:
                            d2["_date_parsed"] = parse_flexible_series(d2[COL_DATE])
                    d2["_date"] = d2["_date_parsed"]
                else:
                    if "_date_parsed_main" in d2.columns:
                        d2["_date"] = d2["_date_parsed_main"]
                    else:
                        d2["_date"] = parse_flexible_series(d2[COL_DATE])
                d2 = d2.dropna(subset=["_date"])

                if not d2.empty:
                    st.markdown("<div style='font-weight:700;font-size:0.9rem;color:var(--text-muted);margin-bottom:10px;'>Période</div>", unsafe_allow_html=True)
                    col_dt1, col_dt2 = st.columns(2)
                    min_dt = d2["_date"].min().date()
                    max_dt = d2["_date"].max().date()
                    with col_dt1:
                        start_dt = st.date_input("Du", value=min_dt, key="start_dt")
                    with col_dt2:
                        end_dt = st.date_input("Au", value=max_dt, key="end_dt")

                    d2 = d2[(d2["_date"].dt.date >= start_dt) & (d2["_date"].dt.date <= end_dt)]

                    if d2.empty:
                        st.info("Aucune donnée sur cette période.")
                    else:
                        _chart_opts = ["Barres empilées", "Courbes"]
                        chart_mode = st.radio(
                            "Type de graphique",
                            _chart_opts,
                            horizontal=True,
                            key="chart_mode_toggle",
                            label_visibility="collapsed",
                            index=safe_radio_index(_chart_opts, "chart_mode_toggle"),
                        )

                        monthly_input = d2[["_date", "_montant", "_signe"]].copy()
                        merged = build_monthly_ca_aggregates(monthly_input)

                        x_labels = merged["_mois_label"].tolist()
                        fig = go.Figure()

                        if chart_mode == "Barres empilées":
                            fig.add_trace(go.Bar(x=x_labels, y=merged["CA En attente"], name="En attente ⏳", marker_color="#1e3a5f", marker_line_width=0))
                            fig.add_trace(go.Bar(x=x_labels, y=merged["CA Signé"], name="Signé", marker_color="#00d68f", marker_line_width=0))
                            fig.add_trace(
                                go.Scatter(
                                    x=x_labels,
                                    y=merged["CA Cumul"],
                                    name="Cumul progressif",
                                    mode="lines+markers",
                                    line=dict(color="#b794f6", width=3, shape="spline"),
                                    marker=dict(size=6, color="#b794f6"),
                                )
                            )
                            fig.update_layout(barmode="stack", bargap=0.3)
                        else:
                            fig.add_trace(go.Scatter(x=x_labels, y=merged["CA Total"], name="CA Total", mode="lines+markers", line=dict(color="#4f8ef7", width=2.5, shape="spline"), marker=dict(size=7, color="#4f8ef7", line=dict(color="#fff", width=1.5)), fill="tozeroy", fillcolor="rgba(79,142,247,0.07)"))
                            fig.add_trace(go.Scatter(x=x_labels, y=merged["CA Signé"], name="CA Signé", mode="lines+markers", line=dict(color="#00d68f", width=2.5, shape="spline"), marker=dict(size=7, color="#00d68f", line=dict(color="#fff", width=1.5)), fill="tozeroy", fillcolor="rgba(0,214,143,0.07)"))
                            fig.add_trace(go.Scatter(x=x_labels, y=merged["CA En attente"], name="CA En attente", mode="lines+markers", line=dict(color="#ffb84d", width=2, shape="spline", dash="dot"), marker=dict(size=5, color="#ffb84d")))
                            fig.add_trace(
                                go.Scatter(
                                    x=x_labels,
                                    y=merged["CA Cumul"],
                                    name="Cumul progressif",
                                    mode="lines+markers",
                                    line=dict(color="#b794f6", width=3, shape="spline"),
                                    marker=dict(size=6, color="#b794f6"),
                                )
                            )

                        fig.update_layout(
                            title=dict(text="📈 Évolution du CA par mois", font=dict(size=14, color=chart_font, family="Inter")),
                            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
                            font=dict(color=chart_font, family="Inter"),
                            xaxis=dict(type="category", showgrid=False, title="", tickfont=dict(color=chart_font, size=11), showline=False, zeroline=False, tickangle=-30),
                            yaxis=dict(gridcolor=chart_grid, title="CA (€)", tickfont=dict(color=chart_font, size=11), showline=False, zeroline=False, tickformat=",.0f"),
                            legend=dict(bgcolor="rgba(255,255,255,0.05)", bordercolor=chart_grid, borderwidth=1, font=dict(color=chart_font, size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                            hovermode="x unified",
                            margin=dict(t=60, b=40, l=20, r=20),
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Colonne 'Date creation devis' non détectée pour le graphique.")

    with cr:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:1rem;color:#ffb84d;margin-bottom:12px;'>🚨 Actions Requises</div>", unsafe_allow_html=True)

            df_alertes_all = df_vg[~df_vg["_signe"]]
            ALERT_PREVIEW = 6

            if "alertes_show_all" not in st.session_state:
                st.session_state["alertes_show_all"] = False

            df_alertes_display = df_alertes_all if st.session_state["alertes_show_all"] else df_alertes_all.head(ALERT_PREVIEW)

            if len(df_alertes_all) > 0:
                for idx, (_, row) in enumerate(df_alertes_display.iterrows()):
                    client = str(row[COL_CLIENT]) if COL_CLIENT else "Inconnu"
                    montant = fmt(row["_montant"])

                    btn_col, card_col = st.columns([0.08, 0.92])
                    with card_col:
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:12px; padding:10px 14px; background:rgba(255,184,77,0.06); border:1px solid rgba(255,184,77,0.15); border-radius:8px; margin-bottom:4px;">
                            <div style="font-size:1.1rem; flex-shrink:0;">Dossier</div>
                            <div style="flex:1; min-width:0;">
                                <div style="font-weight:600; font-size:0.88rem; color:var(--text-main); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{client}</div>
                                <div style="font-size:0.78rem; color:var(--text-muted);">{montant}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with btn_col:
                        if st.button("↗", key=f"goto_client_{idx}_{client}", help=f"Ouvrir dossier {client}"):
                            st.session_state["_prefill_client_search"] = client
                            # La sidebar affiche des labels décorés (ex: "⌂ Espace Clients").
                            # On retrouve donc l'index via `page_key_map` plutôt qu'en dur.
                            target_label = next((p for p in pages if page_key_map.get(p) == "Espace Clients"), None)
                            if target_label is not None:
                                st.session_state["_page_index"] = pages.index(target_label)
                                # Streamlit ne laisse pas toujours forcer la valeur d'un widget via
                                # `session_state` (ex: clé d'un `st.radio`). On passe donc par un
                                # mécanisme d'override déjà utilisé pour la navigation.
                                st.session_state["nav_override"] = target_label
                            else:
                                # Fallback : si jamais la structure sidebar change
                                st.session_state["nav_override"] = "Espace Clients"
                            st.rerun()

                if vg_nb_attente > ALERT_PREVIEW:
                    if not st.session_state["alertes_show_all"]:
                        remaining = vg_nb_attente - ALERT_PREVIEW
                        if st.button(f"📂 Voir les {remaining} autres", width="stretch", key="btn_alertes_more"):
                            st.session_state["alertes_show_all"] = True
                            st.rerun()
                    else:
                        if st.button("🔼 Réduire", width="stretch", key="btn_alertes_less"):
                            st.session_state["alertes_show_all"] = False
                            st.rerun()
            else:
                st.success("Aucun devis en attente.")

    st.markdown("<br>", unsafe_allow_html=True)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        with st.container(border=True):
            fig_donut = go.Figure(data=[go.Pie(labels=["Signés","En attente"], values=[vg_nb_signes, vg_nb_attente], hole=0.72, marker_colors=["#00d68f","#1e3a5f"], textinfo="none")])
            fig_donut.add_annotation(text=f"{vg_taux_conv}%", x=0.5, y=0.5, font_size=28, font_color=chart_font, font_family="Inter", showarrow=False)
            fig_donut.update_layout(title="Taux de transformation", title_font_color=chart_font, paper_bgcolor="rgba(0,0,0,0)", showlegend=True, legend=dict(bgcolor="rgba(0,0,0,0)", font_color=chart_font), margin=dict(t=40, b=20, l=20, r=20), height=250)
            st.plotly_chart(fig_donut, width="stretch")
    with col_d2:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.95rem;color:var(--text-main);margin-bottom:16px;'>Résumé financier</div>", unsafe_allow_html=True)
            for label, val, color in [
                ("CA Total émis",        fmt(vg_total_ca),    "#4f8ef7"),
                ("CA Sécurisé",          fmt(vg_ca_signe),    "#00d68f"),
                ("CA En attente",        fmt(vg_ca_non_s),    "#ffb84d"),
                ("Reste à encaisser",    fmt(vg_reste),       "#ff5c7a"),
                ("Chantiers terminés (PV)", f"{int(df_vg['_pv'].sum())}", "#00d68f"),
            ]:
                st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);'><span style='color:var(--text-muted);font-size:0.85rem;'>{label}</span><span style='color:{color};font-weight:700;font-size:0.95rem;'>{val}</span></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Devis":
    page_header("Gestion des Devis", f"{nb_devis} devis au total")
    df_devis_scope = df.copy()
    devis_nb_total = len(df_devis_scope)
    devis_nb_signes = int(df_devis_scope["_signe"].sum()) if devis_nb_total > 0 else 0
    devis_taux_conv = int((devis_nb_signes / devis_nb_total) * 100) if devis_nb_total > 0 else 0
    render_ceo_hero(
        "Pipeline commercial",
        "Lecture rapide du pipe devis, du stock en attente de signature et de la valeur déjà convertie.",
        chips=[f"{devis_nb_total} devis", f"{devis_taux_conv}% conversion", fmt(df_devis_scope['_montant'].sum())],
    )

    with st.expander("📅 Filtrer le taux de transformation par période", expanded=False):
        cd1, cd2, cd3 = st.columns([2, 2, 1])
        with cd1:
            devis_date_debut = st.date_input("Du", value=None, key="devis_date_debut")
        with cd2:
            devis_date_fin = st.date_input("Au", value=None, key="devis_date_fin")
        with cd3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Réinitialiser", key="devis_reset_dates", use_container_width=True):
                st.session_state.pop("devis_date_debut", None)
                st.session_state.pop("devis_date_fin", None)

    if COL_DATE and (devis_date_debut or devis_date_fin):
        if "_date_parsed_main" in df_devis_scope.columns:
            df_devis_scope["_date_devis"] = df_devis_scope["_date_parsed_main"]
        else:
            df_devis_scope["_date_devis"] = parse_flexible_series(df_devis_scope[COL_DATE])
        if devis_date_debut:
            df_devis_scope = df_devis_scope[df_devis_scope["_date_devis"].dt.date >= devis_date_debut]
        if devis_date_fin:
            df_devis_scope = df_devis_scope[df_devis_scope["_date_devis"].dt.date <= devis_date_fin]
        devis_nb_total = len(df_devis_scope)
        devis_nb_signes = int(df_devis_scope["_signe"].sum()) if devis_nb_total > 0 else 0
        devis_taux_conv = int((devis_nb_signes / devis_nb_total) * 100) if devis_nb_total > 0 else 0
        st.info(f"📅 Taux de transformation calculé sur {devis_nb_total} devis (période filtrée).")

    render_kpi_cards([
        {"label": "Total devis", "value": devis_nb_total, "delta": "Volume commercial total", "icon": "◉", "fill_pct": 100, "accent": "#4f8ef7", "accent_bg": "rgba(79,142,247,0.18)"},
        {"label": "Transformation", "value": f"{devis_taux_conv} %", "delta": "Taux de signature", "icon": "↗", "fill_pct": devis_taux_conv, "accent": "#00d68f", "accent_bg": "rgba(0,214,143,0.18)", "delta_color": "#00d68f"},
        {"label": "Volume global", "value": fmt(df_devis_scope["_montant"].sum()), "delta": "Valeur cumulée des devis", "icon": "€", "fill_pct": 100, "accent": "#ffb84d", "accent_bg": "rgba(255,184,77,0.18)", "delta_color": "#ffb84d"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE, COL_RELANCE1, COL_RELANCE2, COL_RELANCE3, COL_STATUT] if c]

    render_filter_banner("Zone filtres", "Recherche rapide par client, chantier ou numéro de devis.")
    search = st.text_input("🔍 Rechercher un devis", placeholder="Nom du client, chantier, numéro...", key="search_devis")
    df_d = df.copy()
    if search:
        mask = pd.Series([False]*len(df_d), index=df_d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col: mask |= df_d[col].astype(str).str.contains(search, case=False, na=False)
        df_d = df_d[mask]

    _DEVIS_OPTS = ["En attente de signature", "Devis signés"]
    if "devis_tab" not in st.session_state:
        st.session_state["devis_tab"] = _DEVIS_OPTS[0]

    def _on_devis_tab():
        st.session_state["devis_tab"] = st.session_state["_devis_tab_radio"]

    tab_devis_choice = st.radio(
        "", _DEVIS_OPTS, horizontal=True, key="_devis_tab_radio",
        index=safe_radio_index(_DEVIS_OPTS, "devis_tab"),
        on_change=_on_devis_tab,
    )
    st.markdown("---")
    if tab_devis_choice == "En attente de signature":
        d = df_d[~df_d["_signe"]]
        st.caption(f"{len(d)} devis — CA potentiel : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_attente")
    else:
        d = df_d[df_d["_signe"]]
        st.caption(f"{len(d)} devis signés — CA confirmé : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_signes")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES & PAIEMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Factures & Paiements":
    page_header("Factures & Paiements", "Suivi des encaissements")
    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    reste_fact = df_imp["_reste"].sum() if "_reste" in df_imp.columns else 0
    render_ceo_hero(
        "Santé financière",
        "Vue CEO sur les encaissements, les factures finales émises et le volume encore à sécuriser.",
        chips=[f"{nb_fact_ok} factures finales", fmt(reste_fact), f"{len(df_imp)} sans facture finale"],
    )

    render_kpi_cards([
        {"label": "Factures finales", "value": nb_fact_ok, "delta": "Dossiers totalement facturés", "icon": "◌", "fill_pct": 100 if len(df) == 0 else int((nb_fact_ok / max(len(df), 1)) * 100), "accent": "#00d68f", "accent_bg": "rgba(0,214,143,0.18)", "delta_color": "#00d68f"},
        {"label": "Sans facture finale", "value": len(df_imp), "delta": "Potentiel de facturation", "icon": "△", "fill_pct": 100 if len(df) == 0 else int((len(df_imp) / max(len(df), 1)) * 100), "accent": "#ffb84d", "accent_bg": "rgba(255,184,77,0.18)", "delta_color": "#ffb84d"},
        {"label": "Reste à facturer", "value": fmt(reste_fact), "delta": "Trésorerie à convertir", "icon": "€", "fill_pct": 100, "accent": "#ff5c7a", "accent_bg": "rgba(255,92,122,0.18)", "delta_color": "#ff5c7a"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ACOMPTE1, COL_ACOMPTE2, "_reste", COL_FACT_FIN, COL_PV, COL_RESERVE, COL_MODALITE, COL_TVA, COL_STATUT] if c]

    with st.container(border=True):
        st.markdown("### Export comptable intelligent")
        if not COL_DATE:
            st.info("Colonne 'Date' introuvable : export indisponible.")
        else:
            mois_fr = [
                "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
            ]
            df_export = df.copy()
            if "_date_parsed_main" in df_export.columns:
                df_export["_date_export"] = df_export["_date_parsed_main"]
            else:
                df_export["_date_export"] = parse_flexible_series(df_export[COL_DATE])
            df_export = df_export.dropna(subset=["_date_export"]).copy()

            if df_export.empty:
                st.info("Aucune date exploitable pour l'export comptable.")
            else:
                years = sorted(df_export["_date_export"].dt.year.dropna().astype(int).unique().tolist(), reverse=True)
                if not years:
                    years = [datetime.now().year]
                current_month = datetime.now().month
                current_year = datetime.now().year

                col_per_1, col_per_2 = st.columns(2)
                with col_per_1:
                    selected_month = st.selectbox(
                        "Mois",
                        options=list(range(1, 13)),
                        format_func=lambda m: mois_fr[m - 1],
                        index=max(0, min(11, current_month - 1)),
                        key="export_compta_month",
                    )
                with col_per_2:
                    selected_year = st.selectbox(
                        "Année",
                        options=years,
                        index=years.index(current_year) if current_year in years else 0,
                        key="export_compta_year",
                    )

                valid_mask = pd.Series(False, index=df_export.index)
                if "_pv" in df_export.columns:
                    valid_mask = valid_mask | df_export["_pv"].astype(bool)
                if COL_RESERVE:
                    valid_mask = valid_mask | df_export[COL_RESERVE].apply(is_checked)

                df_export = df_export[
                    (df_export["_date_export"].dt.month == int(selected_month))
                    & (df_export["_date_export"].dt.year == int(selected_year))
                    & valid_mask
                ].copy()

                if df_export.empty:
                    st.warning("Aucune ligne validée (PV signé / sans réserve) pour cette période.")
                else:
                    # Priorité à la nouvelle colonne TVA_choisi (taux), sinon fallback sur la TVA existante.
                    col_tva_export = fcol(df_export, "tva_choisi", "tva choisi")
                    if not col_tva_export:
                        col_tva_export = COL_TVA

                    def _parse_tva_rate(val):
                        if pd.isna(val) or str(val).strip() == "":
                            return 0.0
                        s = (
                            str(val).strip().lower()
                            .replace("%", "")
                            .replace("tva", "")
                            .replace(",", ".")
                            .replace(" ", "")
                        )
                        try:
                            num = float(s)
                        except Exception:
                            return 0.0
                        if num <= 1:
                            return max(0.0, num)
                        if num <= 100:
                            return max(0.0, num / 100)
                        return 0.0

                    montant_ttc = df_export["_montant"].apply(clean_amount)
                    tva_rates = (
                        df_export[col_tva_export].apply(_parse_tva_rate)
                        if col_tva_export else pd.Series([0.0] * len(df_export), index=df_export.index)
                    )

                    tva_amounts = []
                    ht_amounts = []
                    for ttc, rate in zip(montant_ttc.tolist(), tva_rates.tolist()):
                        rate = max(rate, 0.0)
                        ht_amt = ttc / (1 + rate) if rate > 0 else ttc
                        tva_amt = ttc - ht_amt
                        ht_amounts.append(ht_amt)
                        tva_amounts.append(tva_amt)

                    export_table = pd.DataFrame({
                        "Date": df_export["_date_export"].dt.strftime("%d/%m/%Y"),
                        "Numéro": df_export[COL_NUM] if COL_NUM else "",
                        "Client": df_export[COL_CLIENT] if COL_CLIENT else "",
                        "Objet": df_export[COL_CHANTIER] if COL_CHANTIER else "",
                        "Montant HT": ht_amounts,
                        "TVA": tva_amounts,
                        "TTC": montant_ttc,
                    })

                    csv_data = convert_df_to_csv(export_table)
                    mois_label = mois_fr[int(selected_month) - 1]
                    mois_file = mois_label.upper().replace("É", "E").replace("È", "E").replace("Ê", "E").replace("Û", "U").replace("Ù", "U").replace("À", "A").replace("Â", "A").replace("Ô", "O").replace("Î", "I").replace("Ï", "I").replace("Ç", "C")
                    filename = f"export_compta_{mois_file}_{int(selected_year)}.csv"
                    st.download_button(
                        label=f"📥 Export Comptable (PV signés - {mois_label} {selected_year})",
                        data=csv_data,
                        file_name=filename,
                        mime="text/csv",
                        use_container_width=True,
                        key="btn_export_comptable_intelligent",
                    )

    render_filter_banner("Zone filtres", "Analyse instantanée des paiements par client ou chantier.")
    search_f = st.text_input("🔍 Rechercher", placeholder="Client, chantier...", key="search_f")
    df_f = df.copy()
    if search_f:
        mask = pd.Series([False]*len(df_f), index=df_f.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col: mask |= df_f[col].astype(str).str.contains(search_f, case=False, na=False)
        df_f = df_f[mask]

    _FACT_OPTS = ["À facturer", "Factures émises"]
    if "fact_tab" not in st.session_state:
        st.session_state["fact_tab"] = _FACT_OPTS[0]

    def _on_fact_tab():
        st.session_state["fact_tab"] = st.session_state["_fact_tab_radio"]

    tab_fact_choice = st.radio(
        "", _FACT_OPTS, horizontal=True, key="_fact_tab_radio",
        index=safe_radio_index(_FACT_OPTS, "fact_tab"),
        on_change=_on_fact_tab,
    )
    st.markdown("---")
    if tab_fact_choice == "À facturer":
        d = df_f[df_f["_signe"] & ~df_f["_fact_fin"]]
        show_table(d[cols].reset_index(drop=True) if cols else d, "fact_attente")
    else:
        d = df_f[df_f["_fact_fin"]]
        show_table(d[cols].reset_index(drop=True) if cols else d, "fact_ok")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CHANTIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Chantiers":
    page_header("Suivi des Chantiers", "Vue d'ensemble des travaux")
    render_ceo_hero(
        "Portefeuille chantiers",
        "Lecture opérationnelle haut de gamme par carte : budget, jalons, réserves et état d'exécution.",
        chips=["Cartes premium", "Lecture rapide", "Pilotage terrain"],
    )

    df["_statut_ch"] = df["_pv"].apply(lambda x: "Terminé" if x else "En cours")
    df["_progress_ch"] = [
        compute_chantier_progress(start_val, end_val, is_finished=pv_done)
        for start_val, end_val, pv_done in zip(df[COL_DATE_DEBUT], df[COL_DATE_FIN], df["_pv"])
    ]
    status_meta = [chantier_status_meta(p, done) for p, done in zip(df["_progress_ch"], df["_pv"])]
    df["_status_label"] = [m[0] for m in status_meta]
    df["_status_color"] = [m[1] for m in status_meta]
    render_kpi_cards([
        {"label": "En cours", "value": int((~df["_pv"]).sum()), "delta": "Chantiers actifs", "icon": "◆", "fill_pct": 100 if len(df) == 0 else int(((~df['_pv']).sum() / max(len(df), 1)) * 100), "accent": "#4f8ef7", "accent_bg": "rgba(79,142,247,0.18)"},
        {"label": "Tréso en cours", "value": fmt(df[~df['_pv']]['_montant'].sum()), "delta": "Valeur encore ouverte", "icon": "€", "fill_pct": 100, "accent": "#ffb84d", "accent_bg": "rgba(255,184,77,0.18)", "delta_color": "#ffb84d"},
        {"label": "Terminés", "value": int(df["_pv"].sum()), "delta": "PV signés", "icon": "✓", "fill_pct": 100 if len(df) == 0 else int((df['_pv'].sum() / max(len(df), 1)) * 100), "accent": "#00d68f", "accent_bg": "rgba(0,214,143,0.18)", "delta_color": "#00d68f"},
        {"label": "CA réalisé", "value": fmt(df[df["_pv"]]["_montant"].sum()), "delta": "Production validée", "icon": "◈", "fill_pct": 100, "accent": "#7c3aed", "accent_bg": "rgba(124,58,237,0.18)", "delta_color": "#b794f6"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)
    search_ch = st.text_input("🔍 Filtrer", placeholder="Client, lieu...", key="search_ch")
    df_ch = df.copy()
    if search_ch:
        mask = pd.Series([False]*len(df_ch), index=df_ch.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col: mask |= df_ch[col].astype(str).str.contains(search_ch, case=False, na=False)
        df_ch = df_ch[mask]

    def render_chantier_cards(df_cards, empty_message):
        if df_cards.empty:
            st.info(empty_message)
            return
        for _, row in df_cards.iterrows():
            client = str(row.get(COL_CLIENT, "")).strip() if COL_CLIENT else ""
            chantier = str(row.get(COL_CHANTIER, "")).strip() if COL_CHANTIER else ""
            adresse = str(row.get(COL_ADRESSE, "")).strip() if COL_ADRESSE else ""
            budget = fmt(clean_amount(row.get(COL_MONTANT, 0))) if COL_MONTANT else "—"
            debut = str(row.get(COL_DATE_DEBUT, "")).strip() if COL_DATE_DEBUT else ""
            fin = str(row.get(COL_DATE_FIN, "")).strip() if COL_DATE_FIN else ""
            reserve_txt = str(row.get(COL_RESERVE, "")).strip() if COL_RESERVE else ""
            progress_pct = int(row.get("_progress_ch", 0))
            status_label, status_color, status_bg = chantier_status_meta(progress_pct, bool(row.get("_pv", False)))
            reserve_badge = (
                f"<span class='ceo-status-badge' style='background:rgba(255,184,77,0.14);color:#ffb84d;border:1px solid rgba(255,184,77,0.26);'>Réserves</span>"
                if reserve_txt and has_reserve(reserve_txt) else ""
            )
            with st.container(border=True):
                c_left, c_right = st.columns([5, 2])
                with c_left:
                    st.markdown(f"**{client or 'Client non renseigné'}**")
                    st.caption(chantier or "Chantier non renseigné")
                    if adresse:
                        st.caption(adresse)
                    badges_html = (
                        f"<span class='ceo-status-badge' style='background:{status_bg};color:{status_color};border:1px solid {status_color}33;'>{status_label}</span>"
                        + (f" {reserve_badge}" if reserve_badge else "")
                    )
                    st.markdown(badges_html, unsafe_allow_html=True)
                    st.caption(f"Début : {debut or '—'} | Fin : {fin or '—'}")
                    st.progress(progress_pct / 100 if progress_pct else 0)
                    st.markdown(
                        f"<div style='margin-top:6px;font-size:0.8rem;color:{status_color};font-weight:700;'>Avancement exécutif : {progress_pct}%</div>",
                        unsafe_allow_html=True,
                    )
                with c_right:
                    st.markdown("`Budget`")
                    st.markdown(f"### {budget}")

    def has_reserve(val):
        if pd.isna(val) or str(val).strip() == "": return False
        s = str(val).strip().lower()
        if any(k in s for k in ["sans", "non", "aucune", "aucun", "no", "none", "0", "faux", "false"]): return False
        return True

    df_ch["_has_reserve"] = df_ch[COL_RESERVE].apply(has_reserve) if COL_RESERVE else False
    nb_reserves = int(df_ch["_has_reserve"].sum())
    ch_tab_opts = ["En cours", "Livrés (PV signé)", f"Avec réserves ({nb_reserves})"]

    if "chantier_tab" not in st.session_state:
        st.session_state["chantier_tab"] = ch_tab_opts[0]

    def _on_chantier_tab():
        st.session_state["chantier_tab"] = st.session_state["_chantier_tab_radio"]

    tab_ch_choice = st.radio(
        "", ch_tab_opts, horizontal=True, key="_chantier_tab_radio",
        index=safe_radio_index(ch_tab_opts, "chantier_tab"),
        on_change=_on_chantier_tab,
    )
    st.markdown("---")
    if tab_ch_choice == "En cours":
        d = df_ch[~df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) actif(s) — {fmt(d['_montant'].sum())}")
        render_chantier_cards(d, "Aucun chantier en cours.")
    elif tab_ch_choice == "Livrés (PV signé)":
        d = df_ch[df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) livré(s) — {fmt(d['_montant'].sum())}")
        render_chantier_cards(d, "Aucun chantier livré.")
    else:
        d = df_ch[df_ch["_has_reserve"]]
        if d.empty:
            st.success("Aucun chantier avec réserves détecté.")
        else:
            r1, r2, r3 = st.columns(3)
            r1.metric("Avec réserves", len(d))
            r2.metric("CA concerné", fmt(d['_montant'].sum()))
            r3.metric("Non livrés", int((d["_has_reserve"] & ~d["_pv"]).sum()))
            render_chantier_cards(d, "Aucun chantier avec réserves.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PLANNING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Planning":
    page_header("Planning des Chantiers", "Vue calendrier des interventions")
    render_ceo_hero(
        "Planning stratégique",
        "Vue temporelle premium des interventions avec accent sur les ressources, la durée et la progression chantier.",
        chips=["Timeline visuelle", "Priorités terrain", "Lecture journalière"],
    )

    COL_SALARIE_P   = fcol(df, "salarié", "salarie", "salar")
    COL_HEURE_DEB_P = fcol(df, "heure_debut", "heure debut", "heure_deb")
    COL_HEURE_FIN_P = fcol(df, "heure_fin", "heure fin", "heure_fin")

    if not COL_DATE_DEBUT or not COL_DATE_FIN:
        st.warning("Colonnes de dates non détectées.")
        st.stop()

    def clean_time_val(val):
        if val is None: return ""
        s = str(val).strip()
        if not s or s.lower() in ("nan", "none", ""): return ""
        if " " in s and ":" in s:
            time_part = s.split(" ")[-1]
            parts = time_part.split(":")
            if len(parts) >= 2:
                try: return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
                except: pass
        if ":" in s:
            parts = s.split(":")
            if len(parts) >= 2:
                try: return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
                except: pass
        return s

    today = datetime.now()

    # ── Chargement colonnes utiles ─────────────────────────────────────────
    cols_utiles = [c for c in [COL_DATE_DEBUT, COL_DATE_FIN, COL_SALARIE_P, COL_HEURE_DEB_P, COL_HEURE_FIN_P, COL_NUM, COL_CLIENT, COL_CHANTIER, COL_ADRESSE, COL_MONTANT] if c]
    df_plan = df[cols_utiles].copy()

    def parse_date_flex(val):
        return parse_flexible_date(val)

    if "_date_debut_parsed_main" in df.columns and COL_DATE_DEBUT:
        df_plan["_start"] = df["_date_debut_parsed_main"]
    else:
        df_plan["_start"] = df_plan[COL_DATE_DEBUT].apply(parse_date_flex)
    if "_date_fin_parsed_main" in df.columns and COL_DATE_FIN:
        df_plan["_end"] = df["_date_fin_parsed_main"]
    else:
        df_plan["_end"] = df_plan[COL_DATE_FIN].apply(parse_date_flex)
    df_plan = df_plan.dropna(subset=["_start", "_end"])
    df_plan = df_plan[df_plan["_end"] >= df_plan["_start"]].reset_index(drop=True)

    if COL_SALARIE_P:
        df_plan["_salarie"] = df_plan[COL_SALARIE_P].apply(lambda v: "" if str(v).strip().lower() in ("nan","none","") else str(v).strip())
    else:
        df_plan["_salarie"] = ""
    df_plan["_heure_deb"] = df_plan[COL_HEURE_DEB_P].apply(clean_time_val) if COL_HEURE_DEB_P else ""
    df_plan["_heure_fin"] = df_plan[COL_HEURE_FIN_P].apply(clean_time_val) if COL_HEURE_FIN_P else ""
    df_plan["_progress_pct"] = [
        compute_chantier_progress(start_val, end_val)
        for start_val, end_val in zip(df_plan["_start"], df_plan["_end"])
    ]
    plan_status_meta = [chantier_status_meta(p, False if p < 100 else True) for p in df_plan["_progress_pct"]]
    df_plan["_status_label"] = [m[0] for m in plan_status_meta]
    df_plan["_status_color"] = [m[1] for m in plan_status_meta]

    # ── KPIs ───────────────────────────────────────────────────────────────
    render_kpi_cards([
        {"label": "Total planifiés", "value": len(df_plan), "delta": "Charge totale", "icon": "▣", "fill_pct": 100, "accent": "#4f8ef7", "accent_bg": "rgba(79,142,247,0.18)"},
        {"label": "En cours / à venir", "value": int((df_plan['_end'].dt.date >= today.date()).sum()), "delta": "Pipeline terrain", "icon": "◔", "fill_pct": 100 if len(df_plan) == 0 else int(((df_plan['_end'].dt.date >= today.date()).sum() / max(len(df_plan), 1)) * 100), "accent": "#ffb84d", "accent_bg": "rgba(255,184,77,0.18)", "delta_color": "#ffb84d"},
        {"label": "Terminés", "value": int((df_plan['_end'].dt.date < today.date()).sum()), "delta": "Interventions closes", "icon": "✓", "fill_pct": 100 if len(df_plan) == 0 else int(((df_plan['_end'].dt.date < today.date()).sum() / max(len(df_plan), 1)) * 100), "accent": "#00d68f", "accent_bg": "rgba(0,214,143,0.18)", "delta_color": "#00d68f"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    _plan_opts = ["Calendrier mensuel", "Liste"]
    view_mode = st.radio("Vue", _plan_opts, horizontal=True, key="_plan_view_radio", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

    # ══ CALENDRIER MENSUEL ════════════════════════════════════════════════
    if view_mode == "Calendrier mensuel":
        if "plan_year"  not in st.session_state: st.session_state["plan_year"]  = today.year
        if "plan_month" not in st.session_state: st.session_state["plan_month"] = today.month

        mois_fr = ["","Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("◀ Mois Précédent", use_container_width=True):
                if st.session_state["plan_month"] == 1:
                    st.session_state["plan_month"] = 12
                    st.session_state["plan_year"] -= 1
                else:
                    st.session_state["plan_month"] -= 1
                st.rerun()
        with nav2:
            st.markdown(f"<h2 style='text-align:center;margin:0;color:var(--text-main);'>{mois_fr[st.session_state['plan_month']]} {st.session_state['plan_year']}</h2>", unsafe_allow_html=True)
        with nav3:
            if st.button("Mois Suivant ▶", use_container_width=True):
                if st.session_state["plan_month"] == 12:
                    st.session_state["plan_month"] = 1
                    st.session_state["plan_year"] += 1
                else:
                    st.session_state["plan_month"] += 1
                st.rerun()

        sel_y, sel_m = st.session_state["plan_year"], st.session_state["plan_month"]
        days_fr  = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        cal_grid = calendar.monthcalendar(sel_y, sel_m)

        with st.container(border=True):
            cols_h = st.columns(7)
            for i, d_name in enumerate(days_fr):
                cols_h[i].markdown(f"<div style='text-align:center;font-weight:bold;color:var(--primary);'>{d_name}</div>", unsafe_allow_html=True)
            for week in cal_grid:
                cols_w = st.columns(7)
                for i, day in enumerate(week):
                    if day != 0:
                        current_date = datetime(sel_y, sel_m, day).date()
                        evs = df_plan[(df_plan["_start"].dt.date <= current_date) & (df_plan["_end"].dt.date >= current_date)]
                        label = str(day)
                        if not evs.empty:
                            termine = (evs["_end"].dt.date < today.date()).all()
                            label += " 🟢" if termine else " 🔵"
                        if cols_w[i].button(label, key=f"d_{sel_y}_{sel_m}_{day}", use_container_width=True):
                            st.session_state["selected_date"] = datetime(sel_y, sel_m, day)

        if "selected_date" in st.session_state:
            sd = st.session_state["selected_date"]
            st.markdown(f"### Chantiers du {sd.strftime('%d/%m/%Y')}")
            day_events = df_plan[(df_plan["_start"].dt.date <= sd.date()) & (df_plan["_end"].dt.date >= sd.date())]

            if day_events.empty:
                st.info("Aucun chantier prévu ce jour.")
            else:
                salaries_jour = sorted([s for s in day_events["_salarie"].unique() if s], key=str.lower)
                if salaries_jour:
                    st.markdown(f"<div style='margin-bottom:12px;font-size:0.85rem;color:var(--text-muted);'>Intervenants ce jour : <strong>{', '.join(salaries_jour)}</strong></div>", unsafe_allow_html=True)

                for _, row in day_events.iterrows():
                    sal   = row["_salarie"]
                    hdeb  = row["_heure_deb"]
                    hfin  = row["_heure_fin"]
                    debut = row["_start"].strftime("%d/%m/%Y")
                    fin_  = row["_end"].strftime("%d/%m/%Y")
                    duree = (row["_end"] - row["_start"]).days + 1
                    termine = row["_end"].date() < today.date()
                    color = "#00d68f" if termine else "#4f8ef7"
                    progress_pct = int(row.get("_progress_pct", 0))
                    status_label = row.get("_status_label", "En cours")

                    def _get(col):
                        if not col or col not in row.index: return ""
                        v = str(row[col]).strip()
                        return "" if v.lower() in ("nan","none","") else v

                    num     = _get(COL_NUM)
                    client  = _get(COL_CLIENT)
                    chant   = _get(COL_CHANTIER)
                    adresse = _get(COL_ADRESSE)
                    montant = _get(COL_MONTANT)

                    horaire = ""
                    if hdeb and hfin:
                        note = " · <em style='font-size:0.72rem;opacity:0.7;'>chaque jour</em>" if duree > 1 else ""
                        horaire = f"<strong>{hdeb}</strong> → <strong>{hfin}</strong>{note}"
                    elif hdeb:
                        horaire = f"Début : <strong>{hdeb}</strong>"

                    num_badge     = f'<span style="background:rgba(79,142,247,0.15);color:#4f8ef7;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;">{num}</span>' if num else ""
                    montant_badge = f'<span style="color:#00d68f;font-weight:700;font-size:1rem;">{montant} €</span>' if montant else ""

                    st.markdown(f"""
                    <div style="border-left:4px solid {color};padding:16px 18px;background:var(--bg-surface);
                        border-radius:10px;margin-bottom:12px;border:1px solid var(--border);">
                      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                        <div style="flex:1;">
                          {"<div style='margin-bottom:6px;'>" + num_badge + "</div>" if num_badge else ""}
                          {"<div style='font-weight:700;font-size:1rem;color:var(--text-main);margin-bottom:3px;'>" + client + "</div>" if client else ""}
                          {"<div style='font-size:0.88rem;color:var(--text-muted);margin-bottom:3px;'>" + chant + "</div>" if chant else ""}
                          {"<div style='font-size:0.82rem;color:var(--text-muted);margin-bottom:6px;'>" + adresse + "</div>" if adresse else ""}
                          {"<div style='font-weight:600;font-size:0.88rem;color:#4f8ef7;margin-bottom:4px;'>" + sal + "</div>" if sal else ""}
                          {"<div style='font-size:0.85rem;color:#ffb84d;'>" + horaire + "</div>" if horaire else ""}
                          <div style='margin-top:8px;font-size:0.8rem;color:{color};font-weight:700;'>{status_label} · {progress_pct}%</div>
                          <div style='margin-top:6px;background:rgba(255,255,255,0.06);border-radius:999px;height:8px;overflow:hidden;'>
                            <div style='width:{progress_pct}%;background:{color};height:100%;'></div>
                          </div>
                        </div>
                        <div style="text-align:right;flex-shrink:0;">
                          <div style="margin-bottom:8px;">{montant_badge}</div>
                          <div style="margin-bottom:4px;"><span style="background:rgba(79,142,247,0.12);padding:2px 8px;border-radius:6px;font-size:0.78rem;font-weight:600;color:#4f8ef7;">Début {debut}</span></div>
                          <div style="margin-bottom:4px;"><span style="background:rgba(255,92,122,0.12);padding:2px 8px;border-radius:6px;font-size:0.78rem;font-weight:600;color:#ff5c7a;">Fin {fin_}</span></div>
                          <div style="font-size:0.72rem;color:var(--text-dim);">{duree} jour(s)</div>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    # ══ LISTE ════════════════════════════════════════════════════════════
    elif view_mode == "Liste":
        df_list = df_plan.sort_values("_start").copy()
        df_list["_mois_str"] = df_list["_start"].dt.strftime("%B %Y").str.capitalize()
        df_list["_mois_ord"] = df_list["_start"].dt.to_period("M")

        for period, group in df_list.groupby("_mois_ord", sort=True):
            st.markdown(f'<div style="font-size:0.85rem;font-weight:700;color:var(--text-muted);letter-spacing:0.06em;text-transform:uppercase;padding:10px 0 6px;border-bottom:1px solid var(--border);margin-bottom:10px;">{group["_mois_str"].iloc[0]} — {len(group)} chantier(s)</div>', unsafe_allow_html=True)
            for _, row in group.iterrows():
                sal       = row["_salarie"]
                hdeb      = row["_heure_deb"]
                hfin_v    = row["_heure_fin"]
                debut     = row["_start"].strftime("%d/%m/%Y")
                fin_      = row["_end"].strftime("%d/%m/%Y")
                duree     = (row["_end"] - row["_start"]).days + 1
                termine   = row["_end"].date() < today.date()
                color     = "#00d68f" if termine else "#4f8ef7"
                label_st  = row.get("_status_label", "En cours / À venir")
                progress_pct = int(row.get("_progress_pct", 0))

                def _get2(col):
                    if not col or col not in row.index: return ""
                    v = str(row[col]).strip()
                    return "" if v.lower() in ("nan","none","") else v

                num     = _get2(COL_NUM)
                client  = _get2(COL_CLIENT)
                chant   = _get2(COL_CHANTIER)
                adresse = _get2(COL_ADRESSE)
                montant = _get2(COL_MONTANT)

                if hdeb and hfin_v:
                    note = " · <em style='font-size:0.72rem;opacity:0.75;'>chaque jour</em>" if duree > 1 else ""
                    horaire_html = f"<strong>{hdeb}</strong> → <strong>{hfin_v}</strong>{note}"
                elif hdeb:
                    horaire_html = f"Début : <strong>{hdeb}</strong>"
                else:
                    horaire_html = ""

                num_badge     = f'<span style="background:rgba(79,142,247,0.15);color:#4f8ef7;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;">{num}</span>' if num else ""
                montant_badge = f'<span style="color:#00d68f;font-weight:700;font-size:1rem;">{montant} €</span>' if montant else ""

                st.markdown(f"""
                <div style="border-left:4px solid {color};padding:16px 18px;background:var(--bg-surface);
                    border-radius:10px;margin-bottom:8px;border:1px solid var(--border);">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
                    <div style="flex:1;">
                      {"<div style='margin-bottom:6px;'>" + num_badge + "</div>" if num_badge else ""}
                      {"<div style='font-weight:700;font-size:1rem;color:var(--text-main);margin-bottom:3px;'>" + client + "</div>" if client else ""}
                      {"<div style='font-size:0.88rem;color:var(--text-muted);margin-bottom:3px;'>" + chant + "</div>" if chant else ""}
                      {"<div style='font-size:0.82rem;color:var(--text-muted);margin-bottom:6px;'>" + adresse + "</div>" if adresse else ""}
                      {"<div style='font-weight:600;font-size:0.88rem;color:#4f8ef7;margin-bottom:4px;'>" + sal + "</div>" if sal else "<div style='color:var(--text-muted);font-size:0.85rem;margin-bottom:4px;'>Intervenant non renseigné</div>"}
                      {"<div style='font-size:0.85rem;color:#ffb84d;margin-top:2px;'>" + horaire_html + "</div>" if horaire_html else ""}
                      <div style="margin-top:8px;"><span style="padding:2px 10px;border-radius:99px;font-size:0.75rem;font-weight:700;color:{color};border:1px solid {color};background:rgba(0,0,0,0.04);">{label_st}</span></div>
                      <div style="margin-top:8px;font-size:0.8rem;color:{color};font-weight:700;">Avancement : {progress_pct}%</div>
                      <div style="margin-top:6px;background:rgba(255,255,255,0.06);border-radius:999px;height:8px;overflow:hidden;max-width:220px;">
                        <div style="width:{progress_pct}%;background:{color};height:100%;"></div>
                      </div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;">
                      <div style="margin-bottom:8px;">{montant_badge}</div>
                      <div style="margin-bottom:4px;"><span style="background:rgba(79,142,247,0.12);padding:3px 10px;border-radius:6px;font-size:0.8rem;font-weight:600;color:#4f8ef7;">Début {debut}</span></div>
                      <div style="margin-bottom:4px;"><span style="background:rgba(255,92,122,0.12);padding:3px 10px;border-radius:6px;font-size:0.8rem;font-weight:600;color:#ff5c7a;">Fin {fin_}</span></div>
                      <div style="font-size:0.75rem;color:var(--text-dim);">{duree} jour(s)</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : TOUS LES DOSSIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Tous les dossiers":
    page_header("Tous les dossiers", "Recherche globale et vue consolidée")

    search_all = st.text_input(
        "🔍 Rechercher dans tous les dossiers",
        placeholder="Client, chantier, numéro, adresse...",
        key="search_all_dossiers",
    ).strip()

    status_opts = ["Tous", "Signés", "Non signés", "Facturés", "Non facturés"]
    status_filter = st.radio(
        "",
        status_opts,
        horizontal=True,
        key="all_dossiers_status_filter",
    )

    df_all = df.copy()
    if search_all:
        mask = pd.Series([False] * len(df_all), index=df_all.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_ADRESSE, COL_STATUT]:
            if col:
                mask |= df_all[col].astype(str).str.contains(search_all, case=False, na=False)
        df_all = df_all[mask]

    if status_filter == "Signés":
        df_all = df_all[df_all["_signe"]]
    elif status_filter == "Non signés":
        df_all = df_all[~df_all["_signe"]]
    elif status_filter == "Facturés":
        df_all = df_all[df_all["_fact_fin"]]
    elif status_filter == "Non facturés":
        df_all = df_all[~df_all["_fact_fin"]]

    c1, c2, c3 = st.columns(3)
    c1.metric("Dossiers affichés", len(df_all))
    c2.metric("CA affiché", fmt(df_all["_montant"].sum() if not df_all.empty else 0))
    c3.metric("Signés", int(df_all["_signe"].sum()) if not df_all.empty else 0)

    cols_all = [
        c for c in [
            COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_ADRESSE, COL_DATE,
            COL_DATE_DEBUT, COL_DATE_FIN, COL_STATUT, COL_SIGN, COL_FACT_FIN, COL_PV
        ] if c
    ]
    st.markdown("---")
    show_table(df_all[cols_all].reset_index(drop=True) if cols_all else df_all.reset_index(drop=True), "all_dossiers")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SALARIÉS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Salariés":
    page_header("👷 Salariés", "Vue semaine — chantiers, heures et disponibilités")

    PAUSE_H = 1.0
    JOURS_DICO = {"Lun": 0, "Mar": 1, "Mer": 2, "Jeu": 3, "Ven": 4, "Sam": 5, "Dim": 6}
    JOURS_LIST = list(JOURS_DICO.keys())

    @st.cache_data(ttl=120, show_spinner=False)
    def _load_jours_salaries(u):
        err, vals = get_sheet_values_resilient(u, "liste", f"{u}:liste")
        if err:
            return {}
        try:
            if not vals or len(vals) < 2:
                return {}
            headers = [h.strip().lower() for h in vals[0]]
            # Prend la première colonne si "salar" non trouvé
            sal_idx = next((i for i, h in enumerate(headers) if "salar" in h), 0)
            jour_idx = next((i for i, h in enumerate(headers) if "jour" in h), None)
            result = {}
            for r in vals[1:]:
                if len(r) <= sal_idx:
                    continue
                nom = r[sal_idx].strip()
                if not nom:
                    continue
                if jour_idx is not None and len(r) > jour_idx and r[jour_idx].strip():
                    jours = [j.strip() for j in r[jour_idx].replace(";", ",").split(",") if j.strip() in JOURS_DICO]
                else:
                    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven"]
                result[nom] = jours
            return result
        except Exception:
            return {}
        
    # ── Chargement planning (overrides) — NIVEAU SUPÉRIEUR ────────────────
    @st.cache_data(ttl=45, show_spinner=False)
    def _load_planning_raw(u):
        err, vals = get_sheet_values_resilient(u, "planning", f"{u}:planning")
        if err:
            return err, [], []
        try:
            if not vals:
                return None, [], []
            return None, vals[0], vals[1:]
        except Exception as e:
            return str(e), [], []

    @st.cache_data(ttl=90, show_spinner=False)
    def _load_liste_raw(u):
        err, vals = get_sheet_values_resilient(u, "liste", f"{u}:liste")
        if err:
            return err, [], []
        try:
            if not vals:
                return None, [], []
            return None, vals[0], vals[1:]
        except Exception as e:
            return str(e), [], []

    err_pl, headers_pl, rows_pl = _load_planning_raw(user)

    def _get_planning_col(sal_nom):
        for i, h in enumerate(headers_pl):
            if h.strip().lower() == sal_nom.strip().lower():
                return i
        return None

    def _get_overrides_for_sal(sal_nom):
        col_idx = _get_planning_col(sal_nom)
        if col_idx is None:
            return {}
        overrides = {}
        for row in rows_pl:
            if len(row) <= col_idx:
                continue
            cell = row[col_idx].strip()
            if not cell:
                continue
            if ":" not in cell:
                continue
            try:
                sem_part, horaires_part = cell.split(":", 1)
                sem_num = int(sem_part.replace("semaine_", "").strip())
                jours_overrides = {}
                for bloc in horaires_part.split(","):
                    bloc = bloc.strip()
                    if "_" not in bloc or "-" not in bloc:
                        continue
                    jour_k, heures = bloc.split("_", 1)
                    hd, hf = heures.split("-")
                    jours_overrides[jour_k.strip()] = {"debut": hd.strip(), "fin": hf.strip()}
                overrides[sem_num] = jours_overrides
            except Exception:
                continue
        return overrides

    def _get_horaires_pour_jour(sal_nom, jour_date, chantier_row, overrides_all):
        """
        Retourne (heure_debut_str, heure_fin_str) pour un salarié à une date donnée.
        Priorité : override planning > horaires du chantier (suivie).
        """
        num_sem = jour_date.isocalendar()[1]
        overrides_sem = overrides_all.get(num_sem, {})
        JOURS_KEYS = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
        jour_key = JOURS_KEYS[jour_date.weekday()]
        if jour_key in overrides_sem:
            ov = overrides_sem[jour_key]
            return ov["debut"], ov["fin"]
        # Fallback : horaires du chantier (colonne suivie)
        hdeb = chantier_row["_hdeb"] if "_hdeb" in chantier_row.index else ""
        hfin = chantier_row["_hfin"] if "_hfin" in chantier_row.index else ""
        return hdeb, hfin

    # ──────────────────────────────────────────────────────────────────────
    jours_salaries = _load_jours_salaries(user)

    if "sal_week_offset" not in st.session_state:
        st.session_state["sal_week_offset"] = 0

    offset = st.session_state["sal_week_offset"]
    today_s = datetime.now().date()
    lundi = today_s - timedelta(days=today_s.weekday()) + timedelta(weeks=offset)
    dimanche = lundi + timedelta(days=6)
    jours_sem = [lundi + timedelta(days=i) for i in range(7)]
    jours_noms = JOURS_LIST

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.button("◀ Semaine précédente", use_container_width=True):
            st.session_state["sal_week_offset"] -= 1
            st.rerun()
    with nav2:
        st.markdown(
            f"<h3 style='text-align:center;margin:0;color:var(--text-main);font-size:1rem;'>"
            f"Semaine du {lundi.strftime('%d/%m/%Y')} au {dimanche.strftime('%d/%m/%Y')}</h3>",
            unsafe_allow_html=True,
        )
        if offset != 0:
            if st.button("Semaine actuelle", use_container_width=True):
                st.session_state["sal_week_offset"] = 0
                st.rerun()
    with nav3:
        if st.button("Semaine suivante ▶", use_container_width=True):
            st.session_state["sal_week_offset"] += 1
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    sal_view = st.radio(
        "",
        ["📅 Planning semaine", "⚙️ Jours travaillés"],
        horizontal=True,
        key="sal_view_mode",
    )

    # ══════════════════════════════════════════════════════════════════════
    # TAB : PLANNING SEMAINE
    # ══════════════════════════════════════════════════════════════════════
    if sal_view == "📅 Planning semaine":
        COL_SAL_S   = fcol(df, "salarié", "salarie", "salar")
        COL_HDeb_S  = fcol(df, "heure_debut", "heure debut", "heure_deb")
        COL_HFin_S  = fcol(df, "heure_fin", "heure fin")

        if not COL_SAL_S:
            st.warning("⚠️ Colonne 'salarié' non détectée dans l'onglet 'suivie'.")
            st.stop()
        if not COL_DATE_DEBUT or not COL_DATE_FIN:
            st.warning("⚠️ Colonnes de dates non détectées.")
            st.stop()

        def parse_date_s(val):
            dt = parse_flexible_date(val)
            if pd.isna(dt):
                return None
            return dt.date()

        def parse_time_s(val):
            if val is None:
                return 0.0
            s = str(val).strip()
            if not s or s.lower() in ("nan", "none", ""):
                return 0.0
            if " " in s and ":" in s:
                s = s.split(" ")[-1]
            parts = s.split(":")
            if len(parts) >= 2:
                try:
                    return int(parts[0]) + int(parts[1]) / 60
                except Exception:
                    pass
            try:
                return float(s)
            except Exception:
                return 0.0

        def fmt_time_s(val):
            s = str(val).strip()
            if not s or s.lower() in ("nan", "none", ""):
                return ""
            if " " in s and ":" in s:
                s = s.split(" ")[-1]
            parts = s.split(":")
            if len(parts) >= 2:
                try:
                    return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
                except Exception:
                    pass
            return s

        df_s = df.copy()
        df_s["_start_d"] = df_s[COL_DATE_DEBUT].apply(parse_date_s)
        df_s["_end_d"]   = df_s[COL_DATE_FIN].apply(parse_date_s)
        df_s = df_s[df_s["_start_d"].notna() & df_s["_end_d"].notna()]
        df_s["_sal"] = df_s[COL_SAL_S].apply(lambda v: "" if str(v).strip().lower() in ("nan", "none", "") else str(v).strip())

# Normalisation : unifie les variantes de noms (casse, espaces, fautes légères)
        def normalize_name(n):
            return str(n).strip().lower()

        sal_canonical = {}
        for nom in jours_salaries.keys():
            sal_canonical[normalize_name(nom)] = nom

        def canonicalize(v):
            if not v:
                return v
            norm = normalize_name(v)
    #         Correspondance exacte
            if norm in sal_canonical:
                return sal_canonical[norm]
    # Correspondance partielle (ex: "florian gagnebie" → "Florian Gagnebien")
            for key, canonical in sal_canonical.items():
                if norm in key or key in norm:
                    return canonical
            return v

        df_s["_sal"] = df_s["_sal"].apply(canonicalize)
        df_s["_hdeb"]   = df_s[COL_HDeb_S].apply(fmt_time_s) if COL_HDeb_S else ""
        df_s["_hfin"]   = df_s[COL_HFin_S].apply(fmt_time_s) if COL_HFin_S else ""
        df_s["_hdeb_f"] = df_s[COL_HDeb_S].apply(parse_time_s) if COL_HDeb_S else 0.0
        df_s["_hfin_f"] = df_s[COL_HFin_S].apply(parse_time_s) if COL_HFin_S else 0.0
        df_s["_duree_h"] = (df_s["_hfin_f"] - df_s["_hdeb_f"] - PAUSE_H).clip(lower=0)

        df_sem = df_s[
            (df_s["_start_d"] <= dimanche) &
            (df_s["_end_d"] >= lundi) &
            (df_s["_sal"] != "")
        ].copy()

        salaries_sem    = sorted(df_sem["_sal"].unique(), key=str.lower)
        salaries_connus = sorted([s for s in df_s["_sal"].unique() if s], key=str.lower)
        # Ajouter aussi les salariés de l'onglet liste même sans chantier cette semaine
        salaries_liste  = sorted(jours_salaries.keys(), key=str.lower)
        all_salaries_merged = list({normalize_name(s): s for s in salaries_liste + salaries_connus}.values())
        all_salaries    = sorted(all_salaries_merged, key=str.lower)

        def jours_reels(sal_nom, start_d, end_d):
            jours_fixes = jours_salaries.get(sal_nom, ["Lun", "Mar", "Mer", "Jeu", "Ven"])
            indices_fixes = {JOURS_DICO[j] for j in jours_fixes if j in JOURS_DICO}
            result = []
            cur = start_d
            while cur <= end_d:
                if cur.weekday() in indices_fixes:
                    result.append(cur)
                cur += timedelta(days=1)
            return result

        def heures_semaine(sal_nom, chantiers_df):
            """Calcule les heures totales en tenant compte des overrides planning."""
            overrides_sal = _get_overrides_for_sal(sal_nom)
            total = 0.0
            for _, row in chantiers_df.iterrows():
                jours_r = jours_reels(sal_nom, row["_start_d"], row["_end_d"])
                for jour in jours_r:
                    if lundi <= jour <= dimanche:
                        hdeb_eff, hfin_eff = _get_horaires_pour_jour(sal_nom, jour, row, overrides_sal)
                        if hdeb_eff and hfin_eff:
                            try:
                                h_deb_f = int(hdeb_eff.split(":")[0]) + int(hdeb_eff.split(":")[1]) / 60
                                h_fin_f = int(hfin_eff.split(":")[0]) + int(hfin_eff.split(":")[1]) / 60
                                total += max(0, h_fin_f - h_deb_f - PAUSE_H)
                            except Exception:
                                total += row["_duree_h"]
                        else:
                            total += row["_duree_h"]
            return total

        surcharges = 0
        for sal in salaries_sem:
            for jour in jours_sem:
                ch_sal = df_sem[df_sem["_sal"] == sal]
                nb = sum(
                    1 for _, r in ch_sal.iterrows()
                    if r["_start_d"] <= jour <= r["_end_d"]
                    and jour in jours_reels(sal, r["_start_d"], r["_end_d"])
                )
                if nb > 1:
                    surcharges += 1

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("👷 Actifs cette semaine", len(salaries_sem))
        k2.metric("🏗️ Chantiers planifiés", len(df_sem))
        k3.metric("⚠️ Jours en surcharge", surcharges)
        k4.metric("😴 Sans mission", len([s for s in all_salaries if s not in salaries_sem]))

        st.markdown("<br>", unsafe_allow_html=True)

        for sal in all_salaries:
            chantiers_sal = df_sem[df_sem["_sal"] == sal]
            actif         = len(chantiers_sal) > 0
            jours_fixes   = jours_salaries.get(sal, ["Lun", "Mar", "Mer", "Jeu", "Ven"])
            h_total       = heures_semaine(sal, chantiers_sal) if actif else 0.0

            status_color = "#00d68f" if actif else "#6b84a3"
            status_label = f"{len(chantiers_sal)} chantier(s)" if actif else "Disponible"
            heures_info  = f" · {h_total:.1f}h cette semaine" if h_total > 0 else ""

            st.markdown(
                f'<div style="display:flex;align-items:center;gap:14px;padding:14px 18px;'
                f'background:var(--bg-card);border:1px solid var(--border);'
                f'border-left:4px solid {status_color};border-radius:12px;margin-bottom:8px;">'
                f'<div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#132238,#1e3a5f);'
                f'display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1rem;color:#fff;flex-shrink:0;">'
                f'{sal[0].upper()}</div>'
                f'<div style="flex:1;">'
                f'<div style="font-weight:700;font-size:1rem;color:var(--text-main);">{sal}</div>'
                f'<div style="font-size:0.8rem;color:var(--text-muted);">'
                f'<span style="color:{status_color};font-weight:600;">{status_label}</span>{heures_info}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            if actif:
                with st.expander("📅 Voir le détail de la semaine", expanded=False):
                    # ── Grille 7 jours ─────────────────────────────────────
                    overrides_sal = _get_overrides_for_sal(sal)
                    cols_j = st.columns(7)
                    for i, (jour, nom_j) in enumerate(zip(jours_sem, jours_noms)):
                        est_jour_fixe = nom_j in jours_fixes
                        rows_jour = [
                            r for _, r in chantiers_sal.iterrows()
                            if jour in jours_reels(sal, r["_start_d"], r["_end_d"])
                        ]
                        nb_j = len(rows_jour)

                        # Calcul heures avec override
                        h_j = 0.0
                        for r in rows_jour:
                            hdeb_eff, hfin_eff = _get_horaires_pour_jour(sal, jour, r, overrides_sal)
                            if hdeb_eff and hfin_eff:
                                try:
                                    h_deb_f = int(hdeb_eff.split(":")[0]) + int(hdeb_eff.split(":")[1]) / 60
                                    h_fin_f = int(hfin_eff.split(":")[0]) + int(hfin_eff.split(":")[1]) / 60
                                    h_j += max(0, h_fin_f - h_deb_f - PAUSE_H)
                                except Exception:
                                    h_j += r["_duree_h"]
                            else:
                                h_j += r["_duree_h"]

                        is_today    = jour == today_s
                        today_ring  = "box-shadow:0 0 0 2px #ffb84d;" if is_today else ""

                        # Affiche override horaire s'il existe
                        JOURS_KEYS = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
                        jour_key   = JOURS_KEYS[jour.weekday()]
                        num_sem_j  = jour.isocalendar()[1]
                        ov_sem     = overrides_sal.get(num_sem_j, {})
                        ov_badge   = ""
                        if jour_key in ov_sem:
                            ov_h = ov_sem[jour_key]
                            ov_badge = f"<div style='font-size:0.65rem;color:#ffb84d;margin-top:2px;'>✏️ {ov_h['debut']}–{ov_h['fin']}</div>"

                        if not est_jour_fixe:
                            bg, border, txt, txt_col = "rgba(0,0,0,0.02)", "var(--border)", "— Repos", "var(--text-dim)"
                        elif nb_j == 0:
                            bg, border, txt, txt_col = "rgba(0,214,143,0.06)", "rgba(0,214,143,0.3)", "😴 Libre", "#00d68f"
                        elif nb_j == 1:
                            bg, border, txt, txt_col = "rgba(79,142,247,0.08)", "rgba(79,142,247,0.3)", "✅ 1 chantier", "#4f8ef7"
                        else:
                            bg, border, txt, txt_col = "rgba(255,92,122,0.1)", "rgba(255,92,122,0.4)", f"⚠️ {nb_j} chantiers", "#ff5c7a"

                        heures_j_str = f"<div style='font-size:0.7rem;color:var(--text-dim);margin-top:2px;'>{h_j:.1f}h</div>" if h_j > 0 else ""

                        with cols_j[i]:
                            st.markdown(
                                f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                                f'padding:8px 6px;text-align:center;{today_ring}">'
                                f'<div style="font-weight:700;font-size:0.78rem;color:var(--text-muted);">{nom_j}</div>'
                                f'<div style="font-size:0.72rem;color:var(--text-dim);margin-bottom:4px;">{jour.strftime("%d/%m")}</div>'
                                f'<div style="font-size:0.75rem;font-weight:600;color:{txt_col};">{txt}</div>'
                                f"{heures_j_str}{ov_badge}</div>",
                                unsafe_allow_html=True,
                            )

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        "<div style='font-size:0.82rem;font-weight:700;color:var(--text-muted);"
                        "margin-bottom:8px;text-transform:uppercase;letter-spacing:0.05em;'>"
                        "🏗️ Chantiers de la semaine</div>",
                        unsafe_allow_html=True,
                    )

                    for _, row in chantiers_sal.sort_values("_start_d").iterrows():
                        def _v(col):
                            if not col:
                                return ""
                            v = str(row[col]).strip()
                            return "" if v.lower() in ("nan", "none", "") else v.replace("<", "&lt;").replace(">", "&gt;")

                        num_c    = _v(COL_NUM)
                        client_c = _v(COL_CLIENT)
                        chant_c  = _v(COL_CHANTIER)
                        adr_c    = _v(COL_ADRESSE)
                        mont_c   = _v(COL_MONTANT)
                        start_c  = row["_start_d"].strftime("%d/%m/%Y")
                        end_c    = row["_end_d"].strftime("%d/%m/%Y")

                        jours_r_sem = [
                            j for j in jours_reels(sal, row["_start_d"], row["_end_d"])
                            if lundi <= j <= dimanche
                        ]
                        nb_jours_r = len(jours_r_sem)

                        # ── Horaire effectif avec override ─────────────────
                        h_chantier = 0.0
                        horaire_c  = ""
                        for jour_r in jours_r_sem:
                            hdeb_eff, hfin_eff = _get_horaires_pour_jour(sal, jour_r, row, overrides_sal)
                            if hdeb_eff and hfin_eff:
                                try:
                                    h_deb_f = int(hdeb_eff.split(":")[0]) + int(hdeb_eff.split(":")[1]) / 60
                                    h_fin_f = int(hfin_eff.split(":")[0]) + int(hfin_eff.split(":")[1]) / 60
                                    duree_eff = max(0, h_fin_f - h_deb_f - PAUSE_H)
                                except Exception:
                                    duree_eff = row["_duree_h"]
                                h_chantier += duree_eff
                                if not horaire_c:
                                    note = " · <em style='font-size:0.72rem;opacity:0.7;'>chaque jour</em>" if nb_jours_r > 1 else ""
                                    # Badge override si horaire modifié
                                    JOURS_KEYS2 = ["lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"]
                                    jour_key2   = JOURS_KEYS2[jour_r.weekday()]
                                    num_sem2    = jour_r.isocalendar()[1]
                                    is_override = jour_key2 in overrides_sal.get(num_sem2, {})
                                    override_badge = " <span style='background:rgba(255,184,77,0.2);color:#ffb84d;padding:1px 5px;border-radius:4px;font-size:0.7rem;'>✏️ modifié</span>" if is_override else ""
                                    horaire_c = f"🕐 {hdeb_eff} → {hfin_eff} ({duree_eff:.1f}h/j, pause {PAUSE_H:.0f}h déduite){override_badge}{note}"
                            else:
                                h_chantier += row["_duree_h"]

                        jours_fixes_str = ", ".join(jours_fixes) if jours_fixes else "—"
                        num_badge    = f'<span style="background:rgba(79,142,247,0.15);color:#4f8ef7;padding:2px 7px;border-radius:5px;font-size:0.75rem;font-weight:600;margin-right:6px;">{num_c}</span>' if num_c else ""
                        client_b     = f'<strong style="color:var(--text-main);">{client_c}</strong>' if client_c else ""
                        montant_badge = f'<span style="background:rgba(0,214,143,0.1);color:#00d68f;padding:2px 8px;border-radius:5px;font-size:0.75rem;font-weight:600;">{mont_c} €</span>' if mont_c else ""

                        st.markdown(
                            f'<div style="padding:12px 14px;background:var(--bg-surface);border:1px solid var(--border);border-radius:8px;margin-bottom:6px;">'
                            f"<div style='margin-bottom:6px;'>{num_badge}{client_b}</div>"
                            + (f"<div style='font-size:0.85rem;color:var(--text-muted);margin-bottom:2px;'>{chant_c}</div>" if chant_c else "")
                            + (f"<div style='font-size:0.8rem;color:var(--text-muted);margin-bottom:2px;'>{adr_c}</div>" if adr_c else "")
                            + (f"<div style='font-size:0.82rem;color:#ffb84d;margin-bottom:4px;'>{horaire_c}</div>" if horaire_c else "")
                            + f"<div style='font-size:0.8rem;color:var(--text-muted);margin-bottom:6px;'>📆 Jours fixes : <strong>{jours_fixes_str}</strong> · Cette semaine : <strong style='color:#4f8ef7;'>{nb_jours_r} jour(s)</strong> · ⏱️ <strong style='color:#00d68f;'>{h_chantier:.1f}h</strong></div>"
                            + f"<div style='display:flex;gap:8px;flex-wrap:wrap;'>"
                            + f"<span style='background:rgba(79,142,247,0.1);color:#4f8ef7;padding:2px 8px;border-radius:5px;font-size:0.75rem;'>📅 {start_c}</span>"
                            + f"<span style='background:rgba(255,92,122,0.1);color:#ff5c7a;padding:2px 8px;border-radius:5px;font-size:0.75rem;'>🏁 {end_c}</span>"
                            + (f"{montant_badge}" if mont_c else "")
                            + "</div></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.caption(f"😴 Aucun chantier cette semaine — jours habituels : {', '.join(jours_fixes)}")

            st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # TAB : CONFIGURATION JOURS TRAVAILLÉS
    # ══════════════════════════════════════════════════════════════════════
    if sal_view == "⚙️ Jours travaillés":
        st.markdown("#### ⚙️ Jours de travail & Horaires par salarié")

        err_l, headers_l, rows_l = _load_liste_raw(user)

        if err_l:
            st.error(f"❌ Onglet 'liste' introuvable : {err_l}")
            st.stop()

        headers_low = [h.strip().lower() for h in headers_l]
        sal_idx_l   = next((i for i, h in enumerate(headers_low) if "salar" in h), None)
        jour_idx_l  = next((i for i, h in enumerate(headers_low) if "jour"  in h), None)

        if sal_idx_l is None:
            st.warning("⚠️ Colonne 'salarié' introuvable dans l'onglet 'liste'.")
            st.stop()

        salaries_config = []
        for r in rows_l:
            if len(r) > sal_idx_l and r[sal_idx_l].strip():
                nom = r[sal_idx_l].strip()
                cur_jours = ""
                if jour_idx_l is not None and len(r) > jour_idx_l:
                    cur_jours = r[jour_idx_l].strip()
                jours_cur = (
                    [j.strip() for j in cur_jours.replace(";", ",").split(",") if j.strip() in JOURS_DICO]
                    if cur_jours else ["Lun", "Mar", "Mer", "Jeu", "Ven"]
                )
                salaries_config.append({"nom": nom, "jours": jours_cur})

        if not salaries_config:
            st.info("Aucun salarié trouvé dans l'onglet 'liste'.")
            st.stop()

        num_semaine = lundi.isocalendar()[1]
        annee_sem   = lundi.isocalendar()[0]
        st.caption(f"Semaine actuelle : **S{num_semaine} {annee_sem}** — du {lundi.strftime('%d/%m/%Y')} au {dimanche.strftime('%d/%m/%Y')}")
        st.markdown("---")

        for sal_idx_cfg, sal_item in enumerate(salaries_config):
            nom_s   = sal_item["nom"]
            jours_s = sal_item["jours"]
            overrides     = _get_overrides_for_sal(nom_s)
            overrides_sem = overrides.get(num_semaine, {})

            with st.container(border=True):
                st.markdown(
                    f"<div style='font-weight:800;font-size:1rem;color:var(--primary);margin-bottom:10px;'>👷 {nom_s}</div>",
                    unsafe_allow_html=True,
                )

                # ── Jours habituels ────────────────────────────────────────
                st.markdown(
                    "<div style='font-size:0.82rem;font-weight:700;color:var(--text-muted);"
                    "text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;'>Jours habituels</div>",
                    unsafe_allow_html=True,
                )
                col_jours, col_save_j = st.columns([5, 1])
                with col_jours:
                    sel_jours = st.multiselect(
                        "Jours", JOURS_LIST,
                        default=jours_s,
                        key=f"jours_sel_{sal_idx_cfg}_{nom_s}",
                        label_visibility="collapsed",
                    )
                with col_save_j:
                    if st.button("💾 Jours", key=f"save_jours_{sal_idx_cfg}", use_container_width=True):
                        try:
                            ws_l2, _ = get_worksheet(user, "liste")
                            all_vals  = ws_l2.get_all_values()
                            h_low2    = [h.strip().lower() for h in all_vals[0]]
                            s_idx2    = next((i for i, h in enumerate(h_low2) if "salar" in h), None)
                            j_idx2    = next((i for i, h in enumerate(h_low2) if "jour"  in h), None)
                            if j_idx2 is None:
                                j_idx2 = len(all_vals[0])
                                ws_l2.update_cell(1, j_idx2 + 1, "jours_travail")
                            if s_idx2 is not None:
                                for row_i, r2 in enumerate(all_vals[1:], start=2):
                                    if len(r2) > s_idx2 and r2[s_idx2].strip() == nom_s:
                                        ws_l2.update_cell(row_i, j_idx2 + 1, ",".join(sel_jours))
                                        log_activity(user, "chantier_modifie", target=nom_s, details={"type": "jours_travail", "jours": sel_jours})
                                        break
                                _load_liste_raw.clear()
                                _load_jours_salaries.clear()
                                st.success(f"✅ Jours de {nom_s} mis à jour.")
                                st.rerun()
                        except Exception as ex:
                            st.error(f"Erreur : {ex}")

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Horaires spécifiques pour la semaine ───────────────────
                st.markdown(
                    f"<div style='font-size:0.82rem;font-weight:700;color:var(--text-muted);"
                    f"text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;'>"
                    f"Horaires spécifiques — Semaine {num_semaine}</div>",
                    unsafe_allow_html=True,
                )

                jours_actifs  = sel_jours if sel_jours else jours_s
                new_overrides = {}
                cols_h        = st.columns(len(jours_actifs)) if jours_actifs else []

                for i, jour_k in enumerate(jours_actifs):
                    cur_ov  = overrides_sem.get(jour_k.lower(), {})
                    cur_deb = cur_ov.get("debut", "08:00")
                    cur_fin = cur_ov.get("fin",   "17:00")
                    try:
                        t_deb = datetime.strptime(cur_deb, "%H:%M").time()
                    except Exception:
                        t_deb = datetime.strptime("08:00", "%H:%M").time()
                    try:
                        t_fin = datetime.strptime(cur_fin, "%H:%M").time()
                    except Exception:
                        t_fin = datetime.strptime("17:00", "%H:%M").time()

                    with cols_h[i]:
                        has_ov = jour_k.lower() in overrides_sem
                        badge  = " ✏️" if has_ov else ""
                        st.markdown(
                            f"<div style='text-align:center;font-weight:700;font-size:0.8rem;"
                            f"color:{'#ffb84d' if has_ov else 'var(--primary)'};margin-bottom:4px;'>{jour_k}{badge}</div>",
                            unsafe_allow_html=True,
                        )
                        hd = st.time_input(
                            "Début", value=t_deb,
                            key=f"hd_{sal_idx_cfg}_{jour_k}_{num_semaine}",
                            label_visibility="collapsed",
                        )
                        hf = st.time_input(
                            "Fin", value=t_fin,
                            key=f"hf_{sal_idx_cfg}_{jour_k}_{num_semaine}",
                            label_visibility="collapsed",
                        )
                        new_overrides[jour_k.lower()] = {"debut": hd.strftime("%H:%M"), "fin": hf.strftime("%H:%M")}

                # On ferme la boucle 'for' et le 'with cols_h' en s'alignant ici
                if st.button(
                    f"💾 Sauvegarder horaires S{num_semaine}",
                    key=f"save_planning_{sal_idx_cfg}",
                    use_container_width=True,
                    type="primary",
                ):
                    try:
                        ws_pl, err_pl2 = get_worksheet(user, "planning")
                        if err_pl2:
                            sheet_name, gsa_json = get_user_credentials(user)
                            creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
                            gc = gspread.authorize(creds)
                            sh = gc.open(sheet_name)
                            ws_pl = sh.add_worksheet(title="planning", rows=200, cols=50)

                        all_pl = ws_pl.get_all_values()
                        headers_pl_cur = all_pl[0] if all_pl else []

                        col_sal_pl = None
                        for i, h in enumerate(headers_pl_cur):
                            if h.strip().lower() == nom_s.strip().lower():
                                col_sal_pl = i
                                break
                        
                        if col_sal_pl is None:
                            col_sal_pl = len(headers_pl_cur)
                            ws_pl.update_cell(1, col_sal_pl + 1, nom_s)
                            all_pl = ws_pl.get_all_values()

                        horaires_str = ",".join([f"{j}_{v['debut']}-{v['fin']}" for j, v in new_overrides.items()])
                        cell_val = f"semaine_{num_semaine}:{horaires_str}"

                        target_row = None
                        for row_i, row in enumerate(all_pl[1:], start=2):
                            if len(row) > col_sal_pl and f"semaine_{num_semaine}:" in row[col_sal_pl]:
                                target_row = row_i
                                break
                        
                        if target_row:
                            ws_pl.update_cell(target_row, col_sal_pl + 1, cell_val)
                        else:
                            new_row = [""] * max(len(headers_pl_cur), col_sal_pl + 1)
                            new_row[col_sal_pl] = cell_val
                            ws_pl.append_row(new_row, value_input_option="USER_ENTERED")
                        log_activity(
                            user,
                            "chantier_modifie",
                            target=nom_s,
                            details={"type": "planning_semaine", "semaine": num_semaine, "horaires": new_overrides},
                        )
                        
                        _load_planning_raw.clear()
                        st.success(f"✅ Horaires S{num_semaine} sauvegardés.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Erreur : {ex}")

# ── ON REVIENT À LA MARGE POUR LA PAGE SUIVANTE ────────────────────────────────
# PAGE : RETARDS & AVENANTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Retards & Avenants":
    page_header("Retards & Avenants", "Signalement de retard chantier")
    # ... reste du code

    WEBHOOK_RETARD = f"https://n8n.florianai.fr/webhook/retard-{user_slug}"

    @st.cache_data(ttl=90, show_spinner=False)
    def _load_envoie_pv(u):
        cache_bucket = st.session_state.setdefault("_offline_tab_values_cache", {})
        cache_key = f"{u}:envoie_pv_external"
        try:
            creds_data = get_user_credentials(u)
            # get_user_credentials retourne (sheet_name, gsa_json)
            _, gsa_json = creds_data
            if not gsa_json:
                return "Credentials non configurés.", pd.DataFrame()
            creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
            gc = gspread.authorize(creds)
            # Ouvre le sheet spécifique
            sh = gc.open("Automatisation des relances devis par dates")
            ws = sh.worksheet("envoie pv")
            vals = ws.get_all_values()
            if not vals or len(vals) < 2:
                return None, pd.DataFrame()
            cache_bucket[cache_key] = vals
            _track_sync_status(cache_key, fallback_used=False)
            headers = _dedup_headers(vals[0])
            rows = vals[1:]
            n = len(headers)
            padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
            df_pv = pd.DataFrame(padded, columns=headers)
            df_pv = df_pv.replace("", pd.NA).dropna(how="all").fillna("")
            return None, df_pv
        except gspread.exceptions.WorksheetNotFound:
            vals = cache_bucket.get(cache_key)
            if vals:
                _track_sync_status(cache_key, fallback_used=True)
                headers = _dedup_headers(vals[0]) if vals else []
                rows = vals[1:] if vals else []
                n = len(headers)
                padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
                df_pv = pd.DataFrame(padded, columns=headers) if headers else pd.DataFrame()
                df_pv = df_pv.replace("", pd.NA).dropna(how="all").fillna("") if not df_pv.empty else df_pv
                return None, df_pv
            return "Onglet 'envoie pv' introuvable.", pd.DataFrame()
        except gspread.exceptions.SpreadsheetNotFound:
            vals = cache_bucket.get(cache_key)
            if vals:
                _track_sync_status(cache_key, fallback_used=True)
                headers = _dedup_headers(vals[0]) if vals else []
                rows = vals[1:] if vals else []
                n = len(headers)
                padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
                df_pv = pd.DataFrame(padded, columns=headers) if headers else pd.DataFrame()
                df_pv = df_pv.replace("", pd.NA).dropna(how="all").fillna("") if not df_pv.empty else df_pv
                return None, df_pv
            return "Sheet 'Automatisation des relances devis par dates' introuvable.", pd.DataFrame()
        except Exception as e:
            vals = cache_bucket.get(cache_key)
            if vals:
                _track_sync_status(cache_key, fallback_used=True)
                headers = _dedup_headers(vals[0]) if vals else []
                rows = vals[1:] if vals else []
                n = len(headers)
                padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
                df_pv = pd.DataFrame(padded, columns=headers) if headers else pd.DataFrame()
                df_pv = df_pv.replace("", pd.NA).dropna(how="all").fillna("") if not df_pv.empty else df_pv
                return None, df_pv
            return str(e), pd.DataFrame()

    err_pv, df_pv = _load_envoie_pv(user)

    if err_pv:
        show_data_source_error(
            f"Erreur chargement 'envoie pv' : {err_pv}",
            clear_fn=_load_envoie_pv.clear,
            retry_key="retry_retard_pv",
        )
        st.stop()

    if df_pv.empty:
        st.info("Aucun dossier trouvé dans l'onglet 'envoie pv'.")
        st.stop()

    if st.button("Actualiser", key="btn_refresh_retard"):
        _load_envoie_pv.clear()
        st.rerun()

    # Détection colonnes de l'onglet envoie pv
    def pvcol(df_in, *kws):
        for kw in kws:
            for c in df_in.columns:
                if kw.lower() in str(c).strip().lower():
                    return c
        return None

    PV_CLIENT   = pvcol(df_pv, "client")
    PV_EMAIL    = pvcol(df_pv, "email")
    PV_OBJET    = pvcol(df_pv, "objet")
    PV_NUM      = pvcol(df_pv, "numero devis", "numero", "num")
    PV_DATE_ENV = pvcol(df_pv, "date d'envoie", "date envoie", "date")
    PV_TYPE_PAI = pvcol(df_pv, "type_paiement", "type paiement", "paiement")
    PV_STATUT   = pvcol(df_pv, "statut")
    PV_LIEN     = pvcol(df_pv, "lien pv", "lien")

    # Filtre : uniquement les lignes avec un numéro de devis valide
    df_retard = df_pv[df_pv[PV_NUM].astype(str).str.strip().ne("") & df_pv[PV_NUM].astype(str).str.strip().ne("nan")].copy() if PV_NUM else df_pv.copy()

    if df_retard.empty:
        st.info("Aucun chantier actif dans 'envoie pv'.")
        st.stop()

    st.markdown("#### Sélectionner le chantier concerné")

    def _label_chantier_r(row):
        parts = []
        if PV_NUM    and str(row.get(PV_NUM,    "")).strip() not in ("", "nan"): parts.append(str(row[PV_NUM]).strip())
        if PV_CLIENT and str(row.get(PV_CLIENT, "")).strip() not in ("", "nan"): parts.append(str(row[PV_CLIENT]).strip())
        if PV_OBJET  and str(row.get(PV_OBJET,  "")).strip() not in ("", "nan"): parts.append(str(row[PV_OBJET]).strip())
        return " — ".join(parts) if parts else f"Ligne {row.name + 2}"

    chantier_labels_r = [_label_chantier_r(row) for _, row in df_retard.iterrows()]
    chantier_index_r  = {lbl: idx for lbl, idx in zip(chantier_labels_r, df_retard.index)}

    sel_label_r = st.selectbox("Chantier", chantier_labels_r, key="retard_chantier_sel")
    sel_row_r   = df_retard.loc[chantier_index_r[sel_label_r]]

    def _safe_r(col):
        if not col: return ""
        v = str(sel_row_r.get(col, "")).strip()
        return "" if v.lower() in ("nan", "none", "") else v

    num_devis_r   = _safe_r(PV_NUM)
    nom_client_r  = _safe_r(PV_CLIENT)
    chantier_id_r = _safe_r(PV_OBJET)
    email_client_r = _safe_r(PV_EMAIL)
    type_pai_r    = _safe_r(PV_TYPE_PAI)
    date_env_r    = _safe_r(PV_DATE_ENV)

    # ── Récap chantier ────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("<div style='font-size:0.82rem;font-weight:700;color:var(--primary);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;'>Chantier sélectionné</div>", unsafe_allow_html=True)
        rc1, rc2, rc3 = st.columns(3)
        rc1.markdown(f"**N° Devis**\n\n`{num_devis_r or '—'}`")
        rc2.markdown(f"**Client**\n\n{nom_client_r or '—'}")
        rc3.markdown(f"**Type paiement**\n\n{type_pai_r or '—'}")
        if date_env_r:
            st.markdown(f"📅 Envoyé le : **{date_env_r}**")
        if chantier_id_r:
            st.markdown(f"🏗️ Objet : **{chantier_id_r}**")

    st.markdown("---")
    st.markdown("#### Signalement du retard")

    col_f1_r, col_f2_r = st.columns(2)

    with col_f1_r:
        ancienne_date_r = st.date_input("Date de fin initiale (ancienne)", value=datetime.today().date(), key="retard_ancienne_date")
        email_r         = st.text_input("Email client", value=email_client_r, placeholder="jean.dupont@email.com", key="retard_email")

    with col_f2_r:
        nouvelle_date_r = st.date_input("Nouvelle date de fin prévue", value=datetime.today().date() + timedelta(days=14), key="retard_nouvelle_date")
        motif_r         = st.selectbox("Motif du retard", [
            "Rupture de stock matériaux",
            "Conditions météorologiques",
            "Modification des travaux par le client",
            "Retard livraison fournisseur",
            "Problème technique imprévu",
            "Absence d'un intervenant",
            "Attente validation client",
            "Autre",
        ], key="retard_motif")

    details_r = st.text_area("Détails complémentaires *", placeholder="Ex : Le fournisseur annonce 15 jours de délai supplémentaire.", height=100, key="retard_details")

    delta_r = (nouvelle_date_r - ancienne_date_r).days
    if delta_r > 0:
        st.info(f"⏱️ Décalage : **{delta_r} jour(s)** — du {ancienne_date_r.strftime('%d/%m/%Y')} au {nouvelle_date_r.strftime('%d/%m/%Y')}")
    elif delta_r == 0:
        st.warning("La nouvelle date est identique à l'ancienne.")
    else:
        st.error("La nouvelle date est antérieure à l'ancienne — vérifiez les dates.")

    payload_retard = {
        "num_devis":     num_devis_r,
        "chantier_id":   chantier_id_r,
        "nom_client":    nom_client_r,
        "email_client":  email_r,
        "ancienne_date": ancienne_date_r.strftime("%d/%m/%Y"),
        "nouvelle_date": nouvelle_date_r.strftime("%d/%m/%Y"),
        "motif":         motif_r,
        "details":       details_r.strip(),
        "type_paiement": type_pai_r,
        "entreprise":    "FLOXIA",
    }

    with st.expander("🔍 Aperçu JSON envoyé à n8n", expanded=False):
        st.json(payload_retard)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1_r, col_btn2_r = st.columns([1, 2])
    with col_btn1_r:
        st.caption(f"Webhook cible : `retard-{user_slug}`")
    with col_btn2_r:
        if st.button("📤 Envoyer le signalement à n8n", use_container_width=True, type="primary", key="btn_send_retard"):
            errors_r = []
            if not num_devis_r:
                errors_r.append("Numéro de devis introuvable.")
            if not nom_client_r:
                errors_r.append("Nom client manquant.")
            if delta_r <= 0:
                errors_r.append("La nouvelle date doit être postérieure à l'ancienne.")
            if not details_r.strip():
                errors_r.append("Les détails sont obligatoires.")

            if errors_r:
                for e in errors_r:
                    st.error(e)
            else:
                try:
                    resp, send_err = post_n8n(WEBHOOK_RETARD, payload_retard)
                    if send_err:
                        if send_err == "timeout":
                            st.error("Timeout — le webhook n8n ne répond pas.")
                        else:
                            st.error(f"Erreur réseau : {send_err}")
                    elif resp.status_code in (200, 201):
                        st.success(f"✅ Signalement envoyé pour **{nom_client_r}** — Devis `{num_devis_r}`.")
                    else:
                        st.error(f"Erreur n8n : HTTP {resp.status_code}")
                        st.caption(resp.text[:300])
                except Exception as ex:
                    st.error(f"Erreur réseau : {ex}")

elif page == "Coordonnées & RGPD":
    page_header("Coordonnées & RGPD", "Informations de contact, confidentialité et droits d'accès")

    with st.container(border=True):
        st.markdown("### Coordonnées")
        st.markdown("**Entreprise** : FLOXIA")
        st.markdown("**Responsable** : Florian")
        st.markdown("**Application** : ERP Streamlit interne")

    with st.container(border=True):
        st.markdown("### Utilisation des données")
        st.markdown(
            "Les données affichées dans cette application proviennent principalement de vos Google Sheets, "
            "des informations de compte stockées dans Supabase et des actions réalisées par les utilisateurs connectés."
        )
        st.markdown(
            "Certaines actions peuvent envoyer des informations vers des automatisations `n8n` "
            "pour générer des documents, envoyer des notifications ou signaler des retards."
        )

    with st.container(border=True):
        st.markdown("### Droits utilisateurs")
        st.markdown(
            "Les onglets visibles pour chaque utilisateur sont limités par les droits d'accès configurés dans le panneau `Utilisateurs`."
        )
        st.info(
            "Dans cette version, les droits d'accès sont enregistrés localement dans l'application "
            "car la colonne `allowed_pages` n'existe pas dans la table `users` de Supabase."
        )

    with st.container(border=True):
        st.markdown("### Bonnes pratiques RGPD")
        st.markdown("- Ne partage pas d'identifiants ou de secrets Google Service Account.")
        st.markdown("- N'envoie que les données strictement necessaires aux automatisations.")
        st.markdown("- Vérifie les informations client avant tout envoi ou toute relance.")
        st.markdown("- Déconnecte-toi en fin de session sur un poste partagé.")

