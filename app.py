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
from auth import check_login, logout, admin_panel, get_user_credentials
st.set_page_config(
    page_title="Florian AI Bâtiment – ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ── INITIALISATION THEME ───────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
def toggle_theme():
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
# ── CSS PREMIUM AVEC DARK/LIGHT MODE ───────────────────────────────────────────
def get_css(theme):
    if theme == "dark":
        return """
        <style>
        @import url('[fonts.googleapis.com](https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap)');
        :root {
            --bg-app: #080f1a;
            --bg-surface: #0f1e30;
            --bg-card: #132238;
            --bg-sidebar: #060d18;
            --bg-hover: #1a3352;
            --text-main: #e8f0fe;
            --text-muted: #6b84a3;
            --text-dim: #3d5473;
            --primary: #4f8ef7;
            --primary-glow: rgba(79,142,247,0.15);
            --success: #00d68f;
            --success-glow: rgba(0,214,143,0.12);
            --warning: #ffb84d;
            --warning-glow: rgba(255,184,77,0.12);
            --danger: #ff5c7a;
            --danger-glow: rgba(255,92,122,0.12);
            --border: rgba(255,255,255,0.06);
            --border-hover: rgba(79,142,247,0.35);
            --row-highlight: rgba(255,92,122,0.15);
            --row-highlight-border: rgba(255,92,122,0.4);
            --radius: 14px;
            --radius-sm: 8px;
        }
        """
    else:
        return """
        <style>
        @import url('[fonts.googleapis.com](https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap)');
        :root {
            --bg-app: #f5f7fa;
            --bg-surface: #ffffff;
            --bg-card: #ffffff;
            --bg-sidebar: #f0f2f5;
            --bg-hover: #e8ecf0;
            --text-main: #1a202c;
            --text-muted: #64748b;
            --text-dim: #94a3b8;
            --primary: #3b82f6;
            --primary-glow: rgba(59,130,246,0.12);
            --success: #10b981;
            --success-glow: rgba(16,185,129,0.12);
            --warning: #f59e0b;
            --warning-glow: rgba(245,158,11,0.12);
            --danger: #ef4444;
            --danger-glow: rgba(239,68,68,0.12);
            --border: rgba(0,0,0,0.08);
            --border-hover: rgba(59,130,246,0.4);
            --row-highlight: rgba(239,68,68,0.1);
            --row-highlight-border: rgba(239,68,68,0.4);
            --radius: 14px;
            --radius-sm: 8px;
        }
        """
def get_common_css():
    return """
        *, *::before, *::after { box-sizing: border-box; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: var(--bg-app) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: var(--text-main);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        [data-testid="stSidebar"] {
            background: var(--bg-sidebar) !important;
            border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] > div { padding: 0 !important; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { 
            background: var(--text-dim); 
            border-radius: 99px; 
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
        /* Metrics Cards */
        [data-testid="stMetric"] {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px 22px !important;
            position: relative;
            overflow: hidden;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        [data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), transparent);
            opacity: 0.7;
        }
        [data-testid="stMetric"]:hover { 
            transform: translateY(-3px); 
            border-color: var(--border-hover);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        [data-testid="stMetric"] label {
            color: var(--text-muted) !important;
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        [data-testid="stMetricValue"] {
            color: var(--text-main) !important;
            font-family: 'Syne', sans-serif !important;
            font-size: 1.65rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
        }
        [data-testid="stMetricDelta"] { font-size: 0.8rem !important; font-weight: 500 !important; }
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: var(--bg-surface);
            border-radius: var(--radius-sm);
            padding: 4px;
            border: 1px solid var(--border);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px !important;
            color: var(--text-muted) !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            padding: 10px 18px !important;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: var(--bg-hover) !important;
        }
        .stTabs [aria-selected="true"] {
            background: var(--primary) !important;
            color: #fff !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 12px var(--primary-glow) !important;
        }
        /* Buttons */
        .stButton > button {
            border-radius: var(--radius-sm) !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: 1px solid var(--border) !important;
            background: var(--bg-card) !important;
            color: var(--text-main) !important;
            padding: 10px 18px !important;
        }
        .stButton > button:hover {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
            background: var(--primary-glow) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--primary-glow);
        }
        /* Inputs */
        .stTextInput input, .stNumberInput input, .stSelectbox > div > div,
        [data-testid="stTextArea"] textarea {
            background: var(--bg-surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-sm) !important;
            color: var(--text-main) !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.9rem !important;
            transition: all 0.2s ease;
        }
        .stTextInput input:focus, .stNumberInput input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px var(--primary-glow) !important;
            outline: none !important;
        }
        /* DataFrames - Row Selection */
        [data-testid="stDataFrame"] {
            border-radius: var(--radius) !important;
            overflow: hidden;
            border: 1px solid var(--border) !important;
        }
        [data-testid="stDataFrame"] table {
            background: var(--bg-card) !important;
        }
        [data-testid="stDataFrame"] th {
            background: var(--bg-surface) !important;
            color: var(--text-muted) !important;
            font-weight: 600 !important;
            font-size: 0.75rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            border-bottom: 2px solid var(--border) !important;
        }
        [data-testid="stDataFrame"] td {
            color: var(--text-main) !important;
            font-size: 0.85rem !important;
            border-bottom: 1px solid var(--border) !important;
            transition: background 0.15s ease;
        }
        [data-testid="stDataFrame"] tr:hover td {
            background: var(--bg-hover) !important;
        }
        hr { border-color: var(--border) !important; margin: 20px 0 !important; }
        /* Container borders */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > div[style*="border"] {
            border-color: var(--border) !important;
            background: var(--bg-card) !important;
            border-radius: var(--radius) !important;
        }
        /* Sidebar Navigation */
        [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child { display: none !important; }
        [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
            padding: 12px 16px;
            background: transparent;
            border-radius: var(--radius-sm);
            cursor: pointer;
            margin-bottom: 2px;
            border: 1px solid transparent;
            transition: all 0.2s ease;
            width: 100%;
        }
        [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover { 
            background: var(--bg-card); 
            border-color: var(--border); 
        }
        [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
            background: var(--primary-glow) !important;
            border-color: var(--border-hover) !important;
        }
        [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p { 
            color: var(--primary) !important; 
            font-weight: 700 !important; 
        }
        [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p { 
            margin: 0; 
            font-size: 0.9rem; 
            color: var(--text-muted); 
        }
        [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] { gap: 2px; }
        /* Badges */
        .badge { 
            display: inline-flex;
            align-items: center;
            padding: 4px 12px; 
            border-radius: 99px; 
            font-size: 0.72rem; 
            font-weight: 600; 
            letter-spacing: 0.03em; 
        }
        .badge-success { background: var(--success-glow); color: var(--success); border: 1px solid rgba(0,214,143,0.25); }
        .badge-warning { background: var(--warning-glow); color: var(--warning); border: 1px solid rgba(255,184,77,0.25); }
        .badge-primary { background: var(--primary-glow); color: var(--primary); border: 1px solid rgba(79,142,247,0.25); }
        .badge-danger { background: var(--danger-glow); color: var(--danger); border: 1px solid rgba(255,92,122,0.25); }
        .badge-muted { background: rgba(107,132,163,0.1); color: var(--text-muted); border: 1px solid var(--border); }
        /* Pulse Animation */
        .pulse-dot {
            display: inline-block; 
            width: 8px; 
            height: 8px;
            border-radius: 50%; 
            background: var(--success);
            animation: pulse-anim 2s ease-in-out infinite;
            margin-right: 6px; 
            vertical-align: middle;
        }
        @keyframes pulse-anim { 
            0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(0,214,143,0.4); } 
            50% { opacity: 0.8; transform: scale(1.1); box-shadow: 0 0 0 6px rgba(0,214,143,0); } 
        }
        /* Page Header */
        .page-header { 
            padding: 12px 0 28px; 
            border-bottom: 1px solid var(--border); 
            margin-bottom: 32px; 
        }
        .page-header h1 { 
            font-family: 'Syne', sans-serif !important; 
            font-size: 2rem !important; 
            font-weight: 800 !important; 
            letter-spacing: -0.03em; 
            margin: 0 !important; 
            color: var(--text-main) !important; 
        }
        .page-header .subtitle { 
            color: var(--text-muted); 
            font-size: 0.9rem; 
            margin-top: 6px;
            font-weight: 400;
        }
        /* Alert Items */
        .alert-item {
            display: flex; 
            align-items: center; 
            gap: 14px; 
            padding: 12px 16px;
            background: var(--warning-glow); 
            border: 1px solid rgba(255,184,77,0.2);
            border-radius: var(--radius-sm); 
            margin-bottom: 10px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); 
            cursor: pointer; 
            position: relative;
        }
        .alert-item:hover {
            background: rgba(255,184,77,0.15); 
            border-color: rgba(255,184,77,0.4);
            transform: translateX(6px); 
            box-shadow: 0 4px 12px rgba(255,184,77,0.15);
        }
        .alert-item .icon { font-size: 1.2rem; flex-shrink: 0; }
        .alert-item .info { flex: 1; }
        .alert-item .info .name { font-weight: 600; font-size: 0.9rem; color: var(--text-main); }
        .alert-item .info .amount { font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; }
        /* Row with 3 relances - highlight */
        .row-relance-alert {
            background: var(--row-highlight) !important;
            border-left: 3px solid var(--danger) !important;
        }
        /* Timeline */
        .timeline-month { 
            font-family: 'Syne', sans-serif; 
            font-size: 0.85rem; 
            font-weight: 700; 
            color: var(--text-muted); 
            letter-spacing: 0.06em; 
            text-transform: uppercase; 
            padding: 14px 0 8px; 
            border-bottom: 1px solid var(--border); 
            margin-bottom: 12px; 
        }
        /* Theme Toggle Button */
        .theme-toggle {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 1.1rem;
        }
        .theme-toggle:hover {
            background: var(--bg-hover);
            border-color: var(--border-hover);
            transform: scale(1.05);
        }
        /* Calendar Day Modal */
        .day-modal {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            margin-top: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .day-modal-header {
            font-family: 'Syne', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        /* Chantier Card */
        .chantier-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 18px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
        }
        .chantier-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }
        .chantier-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        .chantier-card-title {
            font-weight: 700;
            font-size: 1rem;
            color: var(--text-main);
        }
        .chantier-card-client {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 4px;
        }
        .chantier-card-meta {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }
        .chantier-card-meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .chantier-card-meta-item .icon {
            font-size: 0.9rem;
        }
        /* Status Badges */
        .status-en-cours {
            background: var(--primary-glow);
            color: var(--primary);
            border: 1px solid rgba(79,142,247,0.3);
        }
        .status-termine {
            background: var(--success-glow);
            color: var(--success);
            border: 1px solid rgba(0,214,143,0.3);
        }
        .status-retard {
            background: var(--danger-glow);
            color: var(--danger);
            border: 1px solid rgba(255,92,122,0.3);
        }
        .status-reserve {
            background: var(--warning-glow);
            color: var(--warning);
            border: 1px solid rgba(255,184,77,0.3);
        }
        </style>
    """
st.markdown(get_css(st.session_state["theme"]) + get_common_css(), unsafe_allow_html=True)
# ── AUTH ───────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()
# ── CONFIG GOOGLE SHEETS ───────────────────────────────────────────────────────
SCOPES = [
    "[googleapis.com](https://www.googleapis.com/auth/spreadsheets)",
    "[googleapis.com](https://www.googleapis.com/auth/drive)",
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
@st.cache_data(ttl=60, show_spinner=False)
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
    if pd.isna(val):
        return False
    s = str(val).strip()
    return s in {"✅","✓","✔","TRUE","true","oui","Oui","OUI","1","x","X","yes","Yes"} or "✅" in s
def has_value(val):
    if pd.isna(val):
        return False
    s = str(val).strip()
    return s != "" and s.lower() not in {"nan", "none", "null"}
def fcol(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in str(c).strip().lower():
                return c
    return None
def fmt(v):
    return f"{v:,.0f} €".replace(",", " ")
def fmt_date(d):
    if pd.isna(d):
        return ""
    try:
        return d.strftime("%d/%m/%Y")
    except:
        return str(d)
LIMIT = 100
def show_table_with_highlight(dataframe, key_suffix="", highlight_col=None, statut_col=None, statut_exclude=None):
    """Affiche un tableau avec surlignage des lignes à 3 relances"""
    total = len(dataframe)
    if total == 0:
        st.info("Aucun dossier trouvé.")
        return
    
    show_all = st.session_state.get(f"show_all_{key_suffix}", False)
    displayed = dataframe if show_all else dataframe.head(LIMIT)
    
    # Créer le style pour le surlignage
    def highlight_rows(row):
        # Vérifier si les 3 relances sont remplies
        has_3_relances = False
        if highlight_col and isinstance(highlight_col, list) and len(highlight_col) >= 3:
            relance_values = [has_value(row.get(col, "")) for col in highlight_col if col in row.index]
            has_3_relances = len(relance_values) >= 3 and all(relance_values[:3])
        
        # Exclure si statut = "devis envoyé"
        if statut_col and statut_col in row.index:
            statut_val = str(row[statut_col]).strip().lower()
            if statut_exclude and any(exc.lower() in statut_val for exc in statut_exclude):
                has_3_relances = False
        
        if has_3_relances:
            return ['background-color: rgba(255,92,122,0.15); border-left: 3px solid #ff5c7a;'] * len(row)
        return [''] * len(row)
    
    styled_df = displayed.style.apply(highlight_rows, axis=1)
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
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
def show_table(dataframe, key_suffix=""):
    total = len(dataframe)
    if total == 0:
        st.info("Aucun dossier trouvé.")
        return
    show_all = st.session_state.get(f"show_all_{key_suffix}", False)
    displayed = dataframe if show_all else dataframe.head(LIMIT)
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
# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding: 20px 16px 8px;'>", unsafe_allow_html=True)
    
    # Logo et titre
    col_logo, col_theme = st.columns([3, 1])
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
        else:
            st.markdown("""
            <div style='display:flex;align-items:center;gap:10px;padding-bottom:8px;'>
                <div style='width:40px;height:40px;background:linear-gradient(135deg,var(--primary),#2563eb);
                    border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;
                    box-shadow: 0 4px 12px var(--primary-glow);'>⚡</div>
                <div>
                    <div style='font-family:Syne,sans-serif;font-weight:800;font-size:1rem;color:var(--text-main);'>Florian AI</div>
                    <div style='font-size:0.72rem;color:var(--text-muted);letter-spacing:0.04em;'>Bâtiment ERP</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_theme:
        theme_icon = "🌙" if st.session_state["theme"] == "light" else "☀️"
        if st.button(theme_icon, key="theme_btn", help="Changer de thème"):
            toggle_theme()
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    user = st.session_state.get("username", "")
    role = st.session_state.get("role", "viewer")
    st.markdown("<div style='padding: 0 12px;'>", unsafe_allow_html=True)
    pages = [
        "📊 Vue Générale",
        "📋 Devis",
        "💶 Factures & Paiements",
        "🏗️ Chantiers",
        "📅 Planning",
        "📁 Tous les dossiers",
        "📝 Éditeur Google Sheet"
    ]
    if role == "admin":
        pages.append("👥 Utilisateurs")
    page = st.radio("Navigation", pages, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='position:absolute;bottom:0;left:0;right:0;padding:16px;border-top:1px solid var(--border);'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:12px;margin-bottom:14px;'>
        <div style='width:36px;height:36px;background:linear-gradient(135deg,var(--bg-card),var(--bg-surface));
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:0.9rem;font-weight:700;border:2px solid var(--primary);color:var(--primary);'>
            {user[0].upper() if user else '?'}
        </div>
        <div style='flex:1;'>
            <div style='font-weight:600;font-size:0.88rem;color:var(--text-main);'>{user}</div>
            <div style='font-size:0.72rem;color:var(--text-muted);text-transform:capitalize;'>{role}</div>
        </div>
        <div>
            <span class="pulse-dot"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    col_r, col_l = st.columns(2)
    with col_r:
        if st.button("🔄 Actualiser", use_container_width=True, help="Actualiser les données"):
            st.cache_data.clear()
            st.rerun()
    with col_l:
        if st.button("🚪 Déconnexion", use_container_width=True, help="Se déconnecter"):
            logout()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
# ── SCROLL TO TOP ──────────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state["current_page"] = page
if st.session_state["current_page"] != page:
    st.session_state["current_page"] = page
    st.markdown("""
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)
# ── PAGES SPÉCIALES ────────────────────────────────────────────────────────────
if page == "👥 Utilisateurs":
    admin_panel()
    st.stop()
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
        @st.cache_data(ttl=10, show_spinner=False)
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
            st.error(f"❌ {err_p}")
            if st.button("🔄 Réessayer"):
                load_presta.clear()
                st.rerun()
        else:
            sub_p_view, sub_p_add, sub_p_edit, sub_p_del = st.tabs(["👁️ Consulter","➕ Ajouter","✏️ Modifier","🗑️ Supprimer"])
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
                c_mo, c_fourn, c_marge, c_qte = st.columns(4)
                with c_mo: val_mo = st.number_input("Prix MO HT", min_value=0.0, value=0.0, step=10.0, key="add_mo")
                with c_fourn: val_fourn = st.number_input("Prix Fourn. HT", min_value=0.0, value=0.0, step=10.0, key="add_fourn")
                with c_marge: val_marge = st.number_input("Marge (%)", min_value=0.0, value=30.0, step=5.0, key="add_marge")
                with c_qte: val_qte = st.number_input("Quantité", min_value=1.0, value=1.0, step=1.0, key="add_qte")
                calcul_total = (val_mo + (val_fourn * (1 + (val_marge / 100)))) * val_qte
                st.success(f"💶 Total HT calculé : **{calcul_total:.2f} €**")
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
                    submit_add_p = st.form_submit_button("✅ Ajouter la ligne", use_container_width=True)
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
                            st.success("✅ Ligne ajoutée avec succès !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
            with sub_p_edit:
                if len(df_p) == 0:
                    st.info("Aucune ligne à modifier.")
                else:
                    headers_p2 = list(df_p.columns)
                    row_labels = [f"Ligne {i+2} — {df_p.iloc[i,0]} / {df_p.iloc[i,1] if len(headers_p2)>1 else ''}" for i in range(len(df_p))]
                    sel_idx = st.selectbox("Sélectionner la ligne à modifier", range(len(df_p)), format_func=lambda i: row_labels[i], key="sel_mod_presta")
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
                                if "categ" in hl:
                                    mod_inputs[h] = st.selectbox(h, CATEGORIES, index=CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0, key=f"mod_p_{h}")
                                elif "type" in hl and "poste" in hl:
                                    mod_inputs[h] = st.selectbox(h, TYPES_POSTE, index=TYPES_POSTE.index(cur_val) if cur_val in TYPES_POSTE else 0, key=f"mod_p_{h}")
                                else:
                                    mod_inputs[h] = st.text_input(h, value=cur_val, key=f"mod_p_{h}")
                        submit_mod_p = st.form_submit_button("💾 Enregistrer les modifications", use_container_width=True)
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
                                st.success("✅ Modifications enregistrées !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
            with sub_p_del:
                if len(df_p) == 0:
                    st.info("Aucune ligne à supprimer.")
                else:
                    headers_p3 = list(df_p.columns)
                    row_labels2 = [f"Ligne {i+2} — {df_p.iloc[i,0]} / {df_p.iloc[i,1] if len(headers_p3)>1 else ''}" for i in range(len(df_p))]
                    del_idx = st.selectbox("Sélectionner la ligne à supprimer", range(len(df_p)), format_func=lambda i: row_labels2[i], key="sel_del_presta")
                    st.warning(f"⚠️ Cette action est irréversible : **{row_labels2[del_idx]}**")
                    if st.button("🗑️ Confirmer la suppression", key="btn_del_presta"):
                        try:
                            ws_p4, err4 = get_worksheet(user, "Feuille 1")
                            if err4: st.error(err4)
                            else:
                                ws_p4.delete_rows(del_idx+2)
                                st.cache_data.clear()
                                st.success("✅ Ligne supprimée !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
    with tab_catalogue:
        CATA_COLS = ["Catégorie","Article","Description","Prix Achat HT","% Marge","Prix Vente HT"]
        @st.cache_data(ttl=10, show_spinner=False)
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
            if st.button("🔄 Réessayer", key="btn_retry_cata"):
                load_catalogue.clear()
                st.rerun()
        else:
            sub_c_view, sub_c_add, sub_c_edit, sub_c_del = st.tabs(["👁️ Consulter","➕ Ajouter","✏️ Modifier","🗑️ Supprimer"])
            with sub_c_view:
                st.caption(f"{len(df_c)} articles dans le catalogue")
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
                            if "catég" in hl or "categ" in hl:
                                inputs_c[h] = st.selectbox(h, CATEGORIES, key=f"add_c_{h}")
                            else:
                                inputs_c[h] = st.text_input(h, key=f"add_c_{h}")
                    submit_add_c = st.form_submit_button("✅ Ajouter l'article", use_container_width=True)
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
                            st.success("✅ Article ajouté !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
            with sub_c_edit:
                if len(df_c) == 0:
                    st.info("Aucun article à modifier.")
                else:
                    headers_c2 = list(df_c.columns)
                    art_labels = [f"Ligne {i+2} — {df_c.iloc[i,0]} / {df_c.iloc[i,1] if len(headers_c2)>1 else ''}" for i in range(len(df_c))]
                    sel_idx_c = st.selectbox("Sélectionner l'article à modifier", range(len(df_c)), format_func=lambda i: art_labels[i], key="sel_mod_cata")
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
                                if "catég" in hl or "categ" in hl:
                                    mod_inputs_c[h] = st.selectbox(h, CATEGORIES, index=CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0, key=f"mod_c_{h}")
                                else:
                                    mod_inputs_c[h] = st.text_input(h, value=cur_val, key=f"mod_c_{h}")
                        submit_mod_c = st.form_submit_button("💾 Enregistrer les modifications", use_container_width=True)
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
                                st.success("✅ Modifications enregistrées !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
            with sub_c_del:
                if len(df_c) == 0:
                    st.info("Aucun article à supprimer.")
                else:
                    headers_c3 = list(df_c.columns)
                    art_labels2 = [f"Ligne {i+2} — {df_c.iloc[i,0]} / {df_c.iloc[i,1] if len(headers_c3)>1 else ''}" for i in range(len(df_c))]
                    del_idx_c = st.selectbox("Sélectionner l'article à supprimer", range(len(df_c)), format_func=lambda i: art_labels2[i], key="sel_del_cata")
                    st.warning(f"⚠️ Cette action est irréversible : **{art_labels2[del_idx_c]}**")
                    if st.button("🗑️ Confirmer la suppression", key="btn_del_cata"):
                        try:
                            ws_c4, err_c4 = get_worksheet(user, "catalogue")
                            if err_c4: st.error(err_c4)
                            else:
                                ws_c4.delete_rows(del_idx_c+2)
                                st.cache_data.clear()
                                st.success("✅ Article supprimé !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
    st.stop()
# ── CHARGEMENT DONNÉES ─────────────────────────────────────────────────────────
df_raw, error = get_sheet_data(user)
if error:
    get_sheet_data.clear()
    st.error("❌ Impossible de se connecter à Google Sheets.")
    st.info(f"Détail : {error}")
    if st.button("🔄 Réessayer"):
        st.rerun()
    st.stop()
if df_raw.empty:
    st.warning("📭 Le Google Sheet est vide ou inaccessible.")
    st.stop()
df = df_raw.copy()
# ── DÉTECTION COLONNES ─────────────────────────────────────────────────────────
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
COL_EQUIPE     = fcol(df, "équipe", "equipe", "employé", "employe", "intervenant", "technicien")
# Liste des colonnes de relance pour le surlignage
RELANCE_COLS = [COL_RELANCE1, COL_RELANCE2, COL_RELANCE3]
# ── CALCULS ────────────────────────────────────────────────────────────────────
df["_montant"]       = df[COL_MONTANT].apply(clean_amount) if COL_MONTANT else 0.0
df["_acompte1"]      = df[COL_ACOMPTE1].apply(clean_amount) if COL_ACOMPTE1 else 0.0
df["_acompte2"]      = df[COL_ACOMPTE2].apply(clean_amount) if COL_ACOMPTE2 else 0.0
df["_reste"]         = (df["_montant"] - df["_acompte1"] - df["_acompte2"]).clip(lower=0)
df["_signe"]         = df[COL_SIGN].apply(is_checked) if COL_SIGN else False
df["_fact_fin"]      = df[COL_FACT_FIN].apply(is_checked) if COL_FACT_FIN else False
df["_pv"]            = df[COL_PV].apply(is_checked) if COL_PV else False
total_ca            = df["_montant"].sum()
nb_devis            = len(df)
nb_signes           = int(df["_signe"].sum())
nb_attente          = nb_devis - nb_signes
nb_fact_ok          = int(df["_fact_fin"].sum())
ca_signe            = df[df["_signe"]]["_montant"].sum()
ca_non_s            = df[~df["_signe"]]["_montant"].sum()
taux_conv           = int((nb_signes / nb_devis) * 100) if nb_devis > 0 else 0
reste_encaissement  = df[(df["_signe"]) & (~df["_fact_fin"])]["_reste"].sum()
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
                    d2["_mois"] = d2["_date"].dt.to_period("M").astype(str)
                    d2["Statut"] = d2["_signe"].map({True: "Signé ✅", False: "En attente ⏳"})
                    cm = d2.groupby(["_mois","Statut"])["_montant"].sum().reset_index()
                    
                    colors = {"Signé ✅": "#00d68f" if st.session_state["theme"] == "dark" else "#10b981", 
                              "En attente ⏳": "#1e3a5f" if st.session_state["theme"] == "dark" else "#94a3b8"}
                    
                    fig = px.bar(cm, x="_mois", y="_montant", color="Statut",
                                 title="📈 Évolution du CA par mois",
                                 color_discrete_map=colors)
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#e8f0fe" if st.session_state["theme"] == "dark" else "#1a202c",
                        font_family="Inter",
                        title_font_size=14,
                        xaxis=dict(showgrid=False, title=""),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)" if st.session_state["theme"] == "dark" else "rgba(0,0,0,0.05)", title="CA (€)"),
                        legend=dict(bgcolor="rgba(0,0,0,0)"),
                        margin=dict(t=40, b=20, l=20, r=20),
                        bargap=0.3,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Colonne 'Date creation devis' non détectée pour le graphique.")
    with cr:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:1rem;color:var(--warning);margin-bottom:14px;'>🚨 Actions Requises</div>", unsafe_allow_html=True)
            df_alertes = df[~df["_signe"]].head(6)
            if len(df_alertes) > 0:
                for _, row in df_alertes.iterrows():
                    client = row[COL_CLIENT] if COL_CLIENT else "Inconnu"
                    montant = fmt(row["_montant"])
                    chantier = row[COL_CHANTIER] if COL_CHANTIER else ""
                    num_devis = row[COL_NUM] if COL_NUM else ""
                    date_creation = row[COL_DATE] if COL_DATE else ""
                    tooltip = f"{client}"
                    if chantier and str(chantier).strip():
                        tooltip += f" • {chantier}"
                    if num_devis and str(num_devis).strip():
                        tooltip += f" • Devis: {num_devis}"
                    if date_creation and str(date_creation).strip():
                        tooltip += f" • {date_creation}"
                    st.markdown(f"""
                    <div class="alert-item" title="{tooltip}">
                        <div class="icon">📄</div>
                        <div class="info">
                            <div class="name">{client}</div>
                            <div class="amount">{montant}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                if nb_attente > 6:
                    st.caption(f"+ {nb_attente-6} autres devis en attente...")
            else:
                st.success("✅ Aucun devis en attente !")
    st.markdown("<br>", unsafe_allow_html=True)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        with st.container(border=True):
            fig_donut = go.Figure(data=[go.Pie(
                labels=["Signés","En attente"],
                values=[nb_signes, nb_attente],
                hole=0.72,
                marker_colors=["#00d68f" if st.session_state["theme"] == "dark" else "#10b981",
                               "#1e3a5f" if st.session_state["theme"] == "dark" else "#e2e8f0"],
                textinfo="none",
            )])
            fig_donut.add_annotation(text=f"{taux_conv}%", x=0.5, y=0.5,
                                     font_size=28, 
                                     font_color="#e8f0fe" if st.session_state["theme"] == "dark" else "#1a202c",
                                     font_family="Syne", showarrow=False)
            fig_donut.update_layout(
                title="Taux de transformation",
                title_font_color="#e8f0fe" if st.session_state["theme"] == "dark" else "#1a202c",
                paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", 
                           font_color="#6b84a3" if st.session_state["theme"] == "dark" else "#64748b"),
                margin=dict(t=40, b=20, l=20, r=20), height=250,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
    with col_d2:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.95rem;color:var(--text-main);margin-bottom:18px;'>📊 Résumé financier</div>", unsafe_allow_html=True)
            items = [
                ("CA Total émis", fmt(total_ca), "var(--primary)"),
                ("CA Sécurisé", fmt(ca_signe), "var(--success)"),
                ("CA En attente", fmt(ca_non_s), "var(--warning)"),
                ("Reste à encaisser", fmt(reste_encaissement), "var(--danger)"),
                ("Chantiers terminés (PV)", f"{int(df['_pv'].sum())}", "var(--success)"),
            ]
            for label, val, color in items:
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                    padding:10px 0;border-bottom:1px solid var(--border);'>
                    <span style='color:var(--text-muted);font-size:0.85rem;'>{label}</span>
                    <span style='color:{color};font-weight:700;font-size:0.95rem;'>{val}</span>
                </div>
                """, unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Devis":
    page_header("Gestion des Devis", f"{nb_devis} devis au total")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Devis Émis", nb_devis)
    c2.metric("Taux de Transformation", f"{taux_conv} %")
    c3.metric("Volume CA Global", fmt(total_ca))
    st.markdown("<br>", unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE,
                         COL_RELANCE1, COL_RELANCE2, COL_RELANCE3, COL_STATUT] if c]
    search = st.text_input("🔍 Rechercher un devis", placeholder="Nom du client, chantier, numéro...", key="search_devis")
    df_d = df.copy()
    if search:
        mask = pd.Series([False]*len(df_d), index=df_d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col: mask |= df_d[col].astype(str).str.contains(search, case=False, na=False)
        df_d = df_d[mask]
    t1, t2 = st.tabs(["⏳ En attente de signature", "✅ Devis signés"])
    with t1:
        d = df_d[~df_d["_signe"]]
        st.caption(f"{len(d)} devis — CA potentiel : {fmt(d['_montant'].sum())}")
        st.markdown("""
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;padding:8px 12px;background:var(--danger-glow);border-radius:8px;border:1px solid rgba(255,92,122,0.2);'>
            <span style='font-size:0.8rem;color:var(--danger);font-weight:600;'>💡 Les lignes surlignées en rouge ont reçu 3 relances sans réponse</span>
        </div>
        """, unsafe_allow_html=True)
        show_table_with_highlight(
            d[cols].reset_index(drop=True) if cols else d, 
            "devis_attente",
            highlight_col=RELANCE_COLS,
            statut_col=COL_STATUT,
            statut_exclude=["devis envoyé", "envoyé"]
        )
    with t2:
        d = df_d[df_d["_signe"]]
        st.caption(f"{len(d)} devis signés — CA confirmé : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_signes")
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES & PAIEMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💶 Factures & Paiements":
    page_header("Factures & Paiements", "Suivi des encaissements")
    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Factures finales émises", nb_fact_ok)
    c2.metric("⚠️ Sans facture finale", len(df_imp))
    c3.metric("💸 CA restant à facturer", fmt(reste_encaissement))
    st.markdown("<br>", unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ACOMPTE1,
                         COL_ACOMPTE2, "_reste", COL_FACT_FIN, COL_PV,
                         COL_RESERVE, COL_MODALITE, COL_TVA, COL_STATUT] if c]
    search_f = st.text_input("🔍 Rechercher", placeholder="Client, chantier...", key="search_f")
    df_f = df.copy()
    if search_f:
        mask = pd.Series([False]*len(df_f), index=df_f.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col: mask |= df_f[col].astype(str).str.contains(search_f, case=False, na=False)
        df_f = df_f[mask]
    t1, t2 = st.tabs(["⚠️ À facturer", "✅ Factures émises"])
    with t1:
        d = df_f[df_f["_signe"] & ~df_f["_fact_fin"]]
        show_table(d[cols].reset_index(drop=True) if cols else d, "fact_attente")
    with t2:
        d = df_f[df_f["_fact_fin"]]
        show_table(d[cols].reset_index(drop=True) if cols else d, "fact_ok")
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CHANTIERS (REFONTE COMPLÈTE)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Chantiers":
    page_header("Suivi des Chantiers", "Vue d'ensemble de vos projets")
    # Calculs des statuts
    df["_statut_chantier"] = df.apply(lambda row: "Terminé" if row["_pv"] else "En cours", axis=1)
    
    # Vérifier les réserves
    def get_reserve_status(row):
        if COL_RESERVE and COL_RESERVE in row.index:
            val = str(row[COL_RESERVE]).strip().lower()
            if any(x in val for x in ["avec", "oui", "yes", "true", "1", "✅"]):
                return "Avec réserves"
            elif any(x in val for x in ["sans", "non", "no", "false", "0"]):
                return "Sans réserves"
        return ""
    
    df["_reserve_status"] = df.apply(get_reserve_status, axis=1)
    # KPIs
    nb_en_cours = int((~df["_pv"]).sum())
    nb_termines = int(df["_pv"].sum())
    ca_en_cours = df[~df["_pv"]]["_montant"].sum()
    ca_termine = df[df["_pv"]]["_montant"].sum()
    nb_avec_reserves = int((df["_reserve_status"] == "Avec réserves").sum())
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔨 En cours", nb_en_cours, f"{fmt(ca_en_cours)}")
    c2.metric("✅ Terminés", nb_termines, f"{fmt(ca_termine)}")
    c3.metric("⚠️ Avec réserves", nb_avec_reserves)
    c4.metric("💰 CA Total", fmt(ca_en_cours + ca_termine))
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filtres
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_ch = st.text_input("🔍 Rechercher un chantier", placeholder="Client, adresse, objet...", key="search_ch")
    with col_filter:
        filter_status = st.selectbox("Filtrer par statut", ["Tous", "En cours", "Terminés", "Avec réserves"], key="filter_ch")
    df_ch = df.copy()
    if search_ch:
        mask = pd.Series([False]*len(df_ch), index=df_ch.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_ADRESSE]:
            if col: mask |= df_ch[col].astype(str).str.contains(search_ch, case=False, na=False)
        df_ch = df_ch[mask]
    
    if filter_status == "En cours":
        df_ch = df_ch[~df_ch["_pv"]]
    elif filter_status == "Terminés":
        df_ch = df_ch[df_ch["_pv"]]
    elif filter_status == "Avec réserves":
        df_ch = df_ch[df_ch["_reserve_status"] == "Avec réserves"]
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Affichage en cartes
    if len(df_ch) == 0:
        st.info("Aucun chantier trouvé avec ces critères.")
    else:
        st.caption(f"{len(df_ch)} chantier(s) affiché(s)")
        
        # Afficher en grille de 2 colonnes
        for i in range(0, len(df_ch), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(df_ch):
                    row = df_ch.iloc[idx]
                    
                    client = str(row[COL_CLIENT]) if COL_CLIENT else "Client inconnu"
                    chantier = str(row[COL_CHANTIER]) if COL_CHANTIER else client
                    adresse = str(row[COL_ADRESSE]) if COL_ADRESSE and has_value(row[COL_ADRESSE]) else ""
                    montant = fmt(row["_montant"])
                    statut = row["_statut_chantier"]
                    reserve = row["_reserve_status"]
                    
                    # Dates
                    date_debut = ""
                    date_fin = ""
                    if COL_DATE_DEBUT and has_value(row[COL_DATE_DEBUT]):
                        date_debut = str(row[COL_DATE_DEBUT])
                    if COL_DATE_FIN and has_value(row[COL_DATE_FIN]):
                        date_fin = str(row[COL_DATE_FIN])
                    
                    # Équipe
                    equipe = ""
                    if COL_EQUIPE and has_value(row[COL_EQUIPE]):
                        equipe = str(row[COL_EQUIPE])
                    
                    # Status badge
                    if statut == "Terminé":
                        status_class = "status-termine"
                        status_icon = "✅"
                    else:
                        status_class = "status-en-cours"
                        status_icon = "🔨"
                    
                    with col:
                        st.markdown(f"""
                        <div class="chantier-card">
                            <div class="chantier-card-header">
                                <div>
                                    <div class="chantier-card-title">{chantier if chantier != "nan" else client}</div>
                                    <div class="chantier-card-client">👤 {client}</div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-weight:700;font-size:1.1rem;color:var(--primary);">{montant}</div>
                                    <span class="badge {status_class}" style="margin-top:6px;">{status_icon} {statut}</span>
                                </div>
                            </div>
                            <div class="chantier-card-meta">
                                {"<div class='chantier-card-meta-item'><span class='icon'>📍</span>" + adresse + "</div>" if adresse and adresse != "nan" else ""}
                                {"<div class='chantier-card-meta-item'><span class='icon'>📅</span> Début: " + date_debut + "</div>" if date_debut and date_debut != "nan" else ""}
                                {"<div class='chantier-card-meta-item'><span class='icon'>🏁</span> Fin: " + date_fin + "</div>" if date_fin and date_fin != "nan" else ""}
                                {"<div class='chantier-card-meta-item'><span class='icon'>👷</span>" + equipe + "</div>" if equipe and equipe != "nan" else ""}
                                {"<span class='badge status-reserve'>⚠️ " + reserve + "</span>" if reserve else ""}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    # Vue tableau optionnelle
    with st.expander("📋 Voir en tableau", expanded=False):
        cols_ch = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ADRESSE,
                                 COL_DATE_DEBUT, COL_DATE_FIN, COL_RESERVE, COL_EQUIPE, "_statut_chantier"] if c]
        show_table(df_ch[cols_ch].reset_index(drop=True) if cols_ch else df_ch, "ch_table")
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PLANNING — AVEC SÉLECTION DE JOUR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Planning":
    page_header("Planning des Chantiers", "Calendrier des interventions")
    if not COL_DATE_DEBUT or not COL_DATE_FIN:
        st.warning("⚠️ Colonnes de dates non détectées (début/fin des travaux).")
        with st.expander("🔍 Colonnes disponibles dans le Sheet"):
            st.write(list(df.columns))
        st.stop()
    today = datetime.now()
    df_plan = df.copy()
    df_plan["_start"] = pd.to_datetime(df_plan[COL_DATE_DEBUT], dayfirst=True, errors="coerce")
    df_plan["_end"]   = pd.to_datetime(df_plan[COL_DATE_FIN],   dayfirst=True, errors="coerce")
    df_plan = df_plan.dropna(subset=["_start", "_end"])
    df_plan = df_plan[df_plan["_end"] >= df_plan["_start"]]
    if df_plan.empty:
        st.info("ℹ️ Aucune date d'intervention valide dans vos dossiers.")
        st.stop()
    def get_statut_code(row):
        if row["_pv"]:
            return "termine"
        if row["_end"].date() < today.date():
            return "retard"
        return "en-cours"
    df_plan["_statut_code"] = df_plan.apply(get_statut_code, axis=1)
    # KPI
    nb_en_cours  = int((df_plan["_statut_code"] == "en-cours").sum())
    nb_retard    = int((df_plan["_statut_code"] == "retard").sum())
    nb_termine   = int((df_plan["_statut_code"] == "termine").sum())
    nb_this_week = int(((df_plan["_start"].dt.date >= today.date()) &
                        (df_plan["_start"].dt.date <= (today + timedelta(days=7)).date())).sum())
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🟡 En cours", nb_en_cours)
    k2.metric("🔴 En retard", nb_retard)
    k3.metric("✅ Terminés", nb_termine)
    k4.metric("📅 Cette semaine", nb_this_week)
    st.markdown("<br>", unsafe_allow_html=True)
    view_mode = st.radio(
        "Mode d'affichage",
        ["📅 Calendrier mensuel", "📊 Diagramme Gantt", "📋 Liste détaillée"],
        horizontal=True,
        key="plan_view"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    # ════════════════════════════════════════════════════════════════
    # VUE CALENDRIER MENSUEL AVEC SÉLECTION DE JOUR
    # ════════════════════════════════════════════════════════════════
    if view_mode == "📅 Calendrier mensuel":
        if "plan_year" not in st.session_state:
            st.session_state["plan_year"] = today.year
        if "plan_month" not in st.session_state:
            st.session_state["plan_month"] = today.month
        if "selected_day" not in st.session_state:
            st.session_state["selected_day"] = None
        mois_fr = ["","Janvier","Février","Mars","Avril","Mai","Juin",
                   "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("◀ Mois précédent", use_container_width=True, key="prev_month"):
                if st.session_state["plan_month"] == 1:
                    st.session_state["plan_month"] = 12
                    st.session_state["plan_year"] -= 1
                else:
                    st.session_state["plan_month"] -= 1
                st.session_state["selected_day"] = None
                st.rerun()
        with nav2:
            st.markdown(
                f"<h2 style='text-align:center;margin:0;padding:8px 0;color:var(--text-main);font-family:Syne,sans-serif;font-weight:800;'>"
                f"{mois_fr[st.session_state['plan_month']]} {st.session_state['plan_year']}</h2>",
                unsafe_allow_html=True
            )
        with nav3:
            if st.button("Mois suivant ▶", use_container_width=True, key="next_month"):
                if st.session_state["plan_month"] == 12:
                    st.session_state["plan_month"] = 1
                    st.session_state["plan_year"] += 1
                else:
                    st.session_state["plan_month"] += 1
                st.session_state["selected_day"] = None
                st.rerun()
        sel_year  = st.session_state["plan_year"]
        sel_month = st.session_state["plan_month"]
        _, last_day_num = calendar.monthrange(sel_year, sel_month)
        df_month = df_plan[
            (df_plan["_start"] <= datetime(sel_year, sel_month, last_day_num)) &
            (df_plan["_end"]   >= datetime(sel_year, sel_month, 1))
        ].copy()
        # Events par jour
        events_by_day = {}
        for _, row in df_month.iterrows():
            start_d = max(row["_start"].date(), datetime(sel_year, sel_month, 1).date())
            end_d   = min(row["_end"].date(), datetime(sel_year, sel_month, last_day_num).date())
            cur = start_d
            while cur <= end_d:
                d = cur.day
                if d not in events_by_day:
                    events_by_day[d] = []
                chantier = str(row[COL_CHANTIER]) if COL_CHANTIER else str(row[COL_CLIENT]) if COL_CLIENT else "Chantier"
                client   = str(row[COL_CLIENT]) if COL_CLIENT else ""
                statut   = row["_statut_code"]
                montant  = row["_montant"]
                adresse  = str(row[COL_ADRESSE]) if COL_ADRESSE and has_value(row[COL_ADRESSE]) else ""
                events_by_day[d].append({
                    "label": chantier[:25] if chantier != "nan" else client[:25], 
                    "client": client, 
                    "statut": statut,
                    "montant": montant,
                    "adresse": adresse,
                    "start": row["_start"],
                    "end": row["_end"]
                })
                cur += timedelta(days=1)
        # Grille du calendrier avec boutons cliquables
        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        
        st.markdown("""
        <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:12px;">
        """ + "".join(
            f'<div style="text-align:center;font-size:0.8rem;font-weight:700;color:var(--primary);'
            f'padding:12px 0;letter-spacing:0.08em;text-transform:uppercase;">{d}</div>'
            for d in days_fr
        ) + "</div>", unsafe_allow_html=True)
        cal_grid = calendar.monthcalendar(sel_year, sel_month)
        
        for week in cal_grid:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.markdown("<div style='min-height:100px;'></div>", unsafe_allow_html=True)
                    else:
                        is_today = (day == today.day and sel_year == today.year and sel_month == today.month)
                        is_selected = st.session_state.get("selected_day") == day
                        events = events_by_day.get(day, [])
                        nb_events = len(events)
                        
                        # Style du conteneur
                        if is_selected:
                            bg_style = "background:var(--primary-glow);border:2px solid var(--primary);"
                        elif is_today:
                            bg_style = "background:linear-gradient(135deg, var(--primary-glow), transparent);border:2px solid var(--primary);"
                        else:
                            bg_style = "background:var(--bg-card);border:1px solid var(--border);"
                        
                        # Bouton cliquable
                        if st.button(
                            f"{day}" + (f" ({nb_events})" if nb_events > 0 else ""),
                            key=f"day_{day}",
                            use_container_width=True,
                            help=f"{nb_events} chantier(s)" if nb_events > 0 else "Aucun chantier"
                        ):
                            st.session_state["selected_day"] = day if st.session_state.get("selected_day") != day else None
                            st.rerun()
                        
                        # Indicateur visuel des événements sous le bouton
                        if nb_events > 0:
                            colors = []
                            for ev in events[:3]:
                                if ev["statut"] == "en-cours":
                                    colors.append("var(--primary)")
                                elif ev["statut"] == "retard":
                                    colors.append("var(--danger)")
                                else:
                                    colors.append("var(--success)")
                            dots = "".join(f'<span style="width:6px;height:6px;border-radius:50%;background:{c};display:inline-block;margin:0 2px;"></span>' for c in colors)
                            if nb_events > 3:
                                dots += f'<span style="font-size:0.65rem;color:var(--text-muted);margin-left:4px;">+{nb_events-3}</span>'
                            st.markdown(f"<div style='text-align:center;margin-top:-8px;'>{dots}</div>", unsafe_allow_html=True)
        # Légende
        st.markdown("""
        <div style="display:flex;gap:24px;margin:20px 0;padding:16px;background:var(--bg-card);border-radius:12px;border:1px solid var(--border);">
            <div style="display:flex;align-items:center;gap:8px;font-size:0.85rem;color:var(--text-main);font-weight:500;">
                <div style="width:12px;height:12px;border-radius:50%;background:var(--primary);"></div> En cours
            </div>
            <div style="display:flex;align-items:center;gap:8px;font-size:0.85rem;color:var(--text-main);font-weight:500;">
                <div style="width:12px;height:12px;border-radius:50%;background:var(--danger);"></div> En retard
            </div>
            <div style="display:flex;align-items:center;gap:8px;font-size:0.85rem;color:var(--text-main);font-weight:500;">
                <div style="width:12px;height:12px;border-radius:50%;background:var(--success);"></div> Terminé
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Affichage des détails du jour sélectionné
        if st.session_state.get("selected_day"):
            sel_day = st.session_state["selected_day"]
            events_today = events_by_day.get(sel_day, [])
            
            st.markdown(f"""
            <div class="day-modal">
                <div class="day-modal-header">
                    📅 {sel_day} {mois_fr[sel_month]} {sel_year} — {len(events_today)} chantier(s)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if events_today:
                for ev in events_today:
                    statut_label = {"en-cours": "En cours", "retard": "En retard", "termine": "Terminé"}
                    statut_class = {"en-cours": "status-en-cours", "retard": "status-retard", "termine": "status-termine"}
                    
                    st.markdown(f"""
                    <div class="chantier-card" style="margin-top:12px;">
                        <div class="chantier-card-header">
                            <div>
                                <div class="chantier-card-title">{ev['label']}</div>
                                <div class="chantier-card-client">👤 {ev['client']}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-weight:700;font-size:1rem;color:var(--primary);">{fmt(ev['montant'])}</div>
                                <span class="badge {statut_class[ev['statut']]}" style="margin-top:6px;">{statut_label[ev['statut']]}</span>
                            </div>
                        </div>
                        <div class="chantier-card-meta">
                            {"<div class='chantier-card-meta-item'><span class='icon'>📍</span>" + ev['adresse'] + "</div>" if ev['adresse'] and ev['adresse'] != "nan" else ""}
                            <div class='chantier-card-meta-item'><span class='icon'>📅</span> {ev['start'].strftime('%d/%m/%Y')} → {ev['end'].strftime('%d/%m/%Y')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Aucun chantier prévu ce jour.")
    # ════════════════════════════════════════════════════════════════
    # VUE GANTT
    # ════════════════════════════════════════════════════════════════
    elif view_mode == "📊 Diagramme Gantt":
        show_all_gantt = st.toggle("Inclure les chantiers terminés", value=False, key="gantt_all")
        df_gantt = df_plan.copy()
        if not show_all_gantt:
            df_gantt = df_gantt[df_gantt["_statut_code"] != "termine"]
        if df_gantt.empty:
            st.info("Aucun chantier à afficher sur le diagramme.")
        else:
            df_gantt_sorted = df_gantt.sort_values("_start")
            nom_col = COL_CHANTIER or COL_CLIENT or df_gantt.columns[0]
            label_map = {"en-cours": "🔨 En cours", "retard": "⚠️ En retard", "termine": "✅ Terminé"}
            df_gantt_sorted["_statut_label"] = df_gantt_sorted["_statut_code"].map(label_map)
            
            if st.session_state["theme"] == "dark":
                color_map = {"🔨 En cours": "#4f8ef7", "⚠️ En retard": "#ff5c7a", "✅ Terminé": "#00d68f"}
            else:
                color_map = {"🔨 En cours": "#3b82f6", "⚠️ En retard": "#ef4444", "✅ Terminé": "#10b981"}
            fig_gantt = px.timeline(
                df_gantt_sorted,
                x_start="_start", x_end="_end", y=nom_col,
                color="_statut_label",
                color_discrete_map=color_map,
                hover_name=nom_col,
                labels={"_start": "Début", "_end": "Fin", "_statut_label": "Statut"},
            )
            fig_gantt.add_vline(
                x=today.timestamp() * 1000,
                line_width=2, line_dash="dash", 
                line_color="var(--warning)" if st.session_state["theme"] == "dark" else "#f59e0b",
                annotation_text="Aujourd'hui",
                annotation_font_color="#ffb84d" if st.session_state["theme"] == "dark" else "#d97706",
                annotation_position="top right",
            )
            fig_gantt.update_yaxes(autorange="reversed", showgrid=False)
            fig_gantt.update_xaxes(
                showgrid=True, 
                gridcolor="rgba(255,255,255,0.04)" if st.session_state["theme"] == "dark" else "rgba(0,0,0,0.05)", 
                tickformat="%d %b", 
                tickfont_color="#6b84a3" if st.session_state["theme"] == "dark" else "#64748b"
            )
            fig_gantt.update_traces(marker_line_width=0, opacity=0.9)
            fig_gantt.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,30,48,0.6)" if st.session_state["theme"] == "dark" else "rgba(248,250,252,0.8)",
                font_color="#e8f0fe" if st.session_state["theme"] == "dark" else "#1a202c",
                font_family="Inter",
                title=None, xaxis_title="", yaxis_title="",
                height=max(380, len(df_gantt_sorted) * 42 + 80),
                legend=dict(
                    bgcolor="rgba(13,30,48,0.8)" if st.session_state["theme"] == "dark" else "rgba(255,255,255,0.9)", 
                    bordercolor="rgba(255,255,255,0.08)" if st.session_state["theme"] == "dark" else "rgba(0,0,0,0.1)", 
                    borderwidth=1, 
                    font_color="#6b84a3" if st.session_state["theme"] == "dark" else "#64748b",
                    title_text=""
                ),
                margin=dict(t=20, b=20, l=10, r=10),
                bargap=0.25,
            )
            with st.container(border=True):
                st.plotly_chart(fig_gantt, use_container_width=True)
            with st.expander("📋 Détails des chantiers", expanded=False):
                detail_cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_DATE_DEBUT, COL_DATE_FIN, COL_MONTANT, COL_ADRESSE] if c]
                show_table(df_gantt_sorted[detail_cols].reset_index(drop=True), "gantt_detail")
    # ════════════════════════════════════════════════════════════════
    # VUE LISTE
    # ════════════════════════════════════════════════════════════════
    elif view_mode == "📋 Liste détaillée":
        filtre_statut = st.multiselect(
            "Filtrer par statut",
            ["En cours", "En retard", "Terminé"],
            default=["En cours", "En retard"],
            key="list_filter"
        )
        code_map = {"En cours": "en-cours", "En retard": "retard", "Terminé": "termine"}
        codes_actifs = [code_map[f] for f in filtre_statut]
        df_list = df_plan[df_plan["_statut_code"].isin(codes_actifs)].sort_values("_start").copy()
        if df_list.empty:
            st.info("Aucun chantier correspondant aux filtres sélectionnés.")
        else:
            df_list["_mois_str"] = df_list["_start"].dt.strftime("%B %Y").str.capitalize()
            df_list["_mois_ord"] = df_list["_start"].dt.to_period("M")
            label_map  = {"en-cours": "En cours", "retard": "En retard", "termine": "Terminé"}
            
            for period, group in df_list.groupby("_mois_ord", sort=True):
                mois_label = group["_mois_str"].iloc[0]
                st.markdown(f'<div class="timeline-month">📅 {mois_label} — {len(group)} chantier(s)</div>', unsafe_allow_html=True)
                for _, row in group.iterrows():
                    client   = str(row[COL_CLIENT]) if COL_CLIENT else ""
                    chantier = str(row[COL_CHANTIER]) if COL_CHANTIER else client
                    adresse  = str(row[COL_ADRESSE]) if COL_ADRESSE and has_value(row[COL_ADRESSE]) else ""
                    montant  = fmt(row["_montant"])
                    debut    = row["_start"].strftime("%d/%m/%Y")
                    fin      = row["_end"].strftime("%d/%m/%Y")
                    duree    = (row["_end"] - row["_start"]).days + 1
                    statut   = row["_statut_code"]
                    label    = label_map[statut]
                    
                    statut_class = {"en-cours": "status-en-cours", "retard": "status-retard", "termine": "status-termine"}
                    st.markdown(f"""
                    <div class="chantier-card">
                        <div class="chantier-card-header">
                            <div>
                                <div class="chantier-card-title">{chantier if chantier != "nan" else client}</div>
                                <div class="chantier-card-client">👤 {client}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-weight:700;font-size:1.1rem;color:var(--primary);">{montant}</div>
                                <span class="badge {statut_class[statut]}" style="margin-top:6px;">{label}</span>
                            </div>
                        </div>
                        <div class="chantier-card-meta">
                            {"<div class='chantier-card-meta-item'><span class='icon'>📍</span>" + adresse + "</div>" if adresse and adresse != "nan" else ""}
                            <div class='chantier-card-meta-item'><span class='icon'>📅</span> {debut} → {fin}</div>
                            <div class='chantier-card-meta-item'><span class='icon'>⏱️</span> {duree} jour(s)</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
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
    
    st.markdown("""
    <div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;padding:8px 12px;background:var(--danger-glow);border-radius:8px;border:1px solid rgba(255,92,122,0.2);'>
        <span style='font-size:0.8rem;color:var(--danger);font-weight:600;'>💡 Les lignes surlignées en rouge ont reçu 3 relances</span>
    </div>
    """, unsafe_allow_html=True)
    
    drop_cols = ["_montant","_signe","_fact_fin","_pv","_acompte1","_acompte2","_reste",
                 "_statut_ch","_start","_end","_statut","_statut_code","_mois_str","_mois_ord",
                 "_statut_chantier","_reserve_status"]
    
    display_df = d.drop(columns=drop_cols, errors="ignore").reset_index(drop=True)
    
    show_table_with_highlight(
        display_df, 
        "all",
        highlight_col=RELANCE_COLS,
        statut_col=COL_STATUT,
        statut_exclude=["devis envoyé", "envoyé"]
    )
