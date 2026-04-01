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

# ── THEME STATE ────────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

is_dark = st.session_state["theme"] == "dark"

# ── CSS COMPLET DARK / LIGHT ───────────────────────────────────────────────────
dark_vars = """
    --bg-app: #080f1a;
    --bg-surface: #0f1e30;
    --bg-card: #132238;
    --bg-sidebar: #060d18;
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
    --border: rgba(255,255,255,0.06);
    --border-hover: rgba(79,142,247,0.35);
    --radius: 14px;
    --radius-sm: 8px;
    --row-hover: rgba(79,142,247,0.08);
    --row-selected: rgba(79,142,247,0.18);
    --row-danger: rgba(255,92,122,0.13);
    --row-danger-border: rgba(255,92,122,0.35);
    --shadow: 0 4px 24px rgba(0,0,0,0.35);
    --cal-cell: #0f1e30;
    --cal-cell-border: rgba(255,255,255,0.06);
    --cal-cell-today-bg: linear-gradient(135deg, rgba(79,142,247,0.18), rgba(79,142,247,0.06));
    --cal-cell-today-border: rgba(79,142,247,0.6);
"""

light_vars = """
    --bg-app: #f0f4fb;
    --bg-surface: #ffffff;
    --bg-card: #f7f9fd;
    --bg-sidebar: #1a2d4a;
    --text-main: #1a2636;
    --text-muted: #5a7290;
    --text-dim: #9ab0c8;
    --primary: #2563eb;
    --primary-glow: rgba(37,99,235,0.12);
    --success: #059669;
    --success-glow: rgba(5,150,105,0.10);
    --warning: #d97706;
    --warning-glow: rgba(217,119,6,0.10);
    --danger: #e11d48;
    --border: rgba(0,0,0,0.08);
    --border-hover: rgba(37,99,235,0.35);
    --radius: 14px;
    --radius-sm: 8px;
    --row-hover: rgba(37,99,235,0.06);
    --row-selected: rgba(37,99,235,0.14);
    --row-danger: rgba(225,29,72,0.07);
    --row-danger-border: rgba(225,29,72,0.3);
    --shadow: 0 4px 24px rgba(0,0,0,0.10);
    --cal-cell: #ffffff;
    --cal-cell-border: rgba(0,0,0,0.07);
    --cal-cell-today-bg: linear-gradient(135deg, rgba(37,99,235,0.12), rgba(37,99,235,0.04));
    --cal-cell-today-border: rgba(37,99,235,0.55);
"""

theme_vars = dark_vars if is_dark else light_vars

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Syne:wght@700;800&display=swap');

:root {{
    {theme_vars}
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg-app) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text-main);
    font-size: 15px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background: {'linear-gradient(180deg, var(--bg-sidebar) 0%, #0a1628 100%)' if is_dark else 'linear-gradient(180deg, #1a2d4a 0%, #132238 100%)'} !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] > div {{ padding: 0 !important; }}
[data-testid="stSidebar"] * {{ color: #e8f0fe !important; }}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--text-dim); border-radius: 99px; }}

/* ── METRICS ── */
[data-testid="stMetric"] {{
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 22px !important;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    box-shadow: var(--shadow);
}}
[data-testid="stMetric"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary), transparent);
    opacity: 0.7;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    border-color: var(--border-hover);
    box-shadow: 0 8px 32px rgba(79,142,247,0.12);
}}
[data-testid="stMetric"] label {{
    color: var(--text-muted) !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}
[data-testid="stMetricValue"] {{
    color: var(--text-main) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}}
[data-testid="stMetricDelta"] {{ font-size: 0.8rem !important; font-weight: 600 !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: var(--bg-surface);
    border-radius: var(--radius-sm);
    padding: 4px;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 6px !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    padding: 8px 18px !important;
    transition: all 0.15s ease;
    letter-spacing: 0.01em;
}}
.stTabs [aria-selected="true"] {{
    background: var(--primary) !important;
    color: #fff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 12px rgba(79,142,247,0.35) !important;
}}

/* ── BUTTONS ── */
.stButton > button {{
    border-radius: var(--radius-sm) !important;
    font-weight: 700 !important;
    font-size: 0.86rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    padding: 8px 16px !important;
    letter-spacing: 0.01em;
    font-family: 'DM Sans', sans-serif !important;
}}
.stButton > button:hover {{
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: var(--primary-glow) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79,142,247,0.2) !important;
}}

/* ── INPUTS ── */
.stTextInput input, .stNumberInput input, .stSelectbox select,
[data-testid="stTextArea"] textarea {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-main) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}}
.stTextInput input:focus, .stNumberInput input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--primary-glow) !important;
    outline: none !important;
}}
.stTextInput label, .stNumberInput label, .stSelectbox label,
[data-testid="stTextArea"] label {{
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {{
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow);
}}

/* ── HR ── */
hr {{ border-color: var(--border) !important; margin: 18px 0 !important; opacity: 0.5; }}

/* ── SIDEBAR NAV ── */
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
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {{
    background: rgba(255,255,255,0.06);
    border-color: rgba(255,255,255,0.1);
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
    background: linear-gradient(135deg, rgba(79,142,247,0.22), rgba(79,142,247,0.10)) !important;
    border-color: rgba(79,142,247,0.45) !important;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {{
    color: #7db3fa !important;
    font-weight: 700 !important;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p {{
    margin: 0;
    font-size: 0.92rem;
    color: rgba(232,240,254,0.7);
    font-weight: 500;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {{ gap: 2px; }}

/* ── BADGES ── */
.badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    font-family: 'DM Sans', sans-serif;
}}
.badge-success {{ background: var(--success-glow); color: var(--success); border: 1px solid rgba(0,214,143,0.2); }}
.badge-warning {{ background: var(--warning-glow); color: var(--warning); border: 1px solid rgba(255,184,77,0.2); }}
.badge-primary {{ background: var(--primary-glow); color: var(--primary); border: 1px solid rgba(79,142,247,0.2); }}
.badge-danger {{ background: rgba(255,92,122,0.1); color: var(--danger); border: 1px solid rgba(255,92,122,0.2); }}
.badge-muted {{ background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border); }}

/* ── PULSE ── */
.pulse-dot {{
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--success);
    animation: pulse-anim 2s ease-in-out infinite;
    margin-right: 6px;
    vertical-align: middle;
}}
@keyframes pulse-anim {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.35; transform: scale(0.8); }}
}}

/* ── PAGE HEADER ── */
.page-header {{
    padding: 4px 0 22px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 26px;
}}
.page-header h1 {{
    font-family: 'Syne', sans-serif !important;
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em;
    margin: 0 !important;
    color: var(--text-main) !important;
    line-height: 1.15 !important;
}}
.page-header .subtitle {{
    color: var(--text-muted);
    font-size: 0.86rem;
    margin-top: 5px;
    font-weight: 500;
}}

/* ── ALERT ITEMS ── */
.alert-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: rgba(255,184,77,0.06);
    border: 1px solid rgba(255,184,77,0.15);
    border-radius: var(--radius-sm);
    margin-bottom: 7px;
    transition: all 0.2s ease;
    cursor: pointer;
    position: relative;
}}
.alert-item:hover {{
    background: rgba(255,184,77,0.12);
    border-color: rgba(255,184,77,0.35);
    transform: translateX(4px);
    box-shadow: 0 2px 10px rgba(255,184,77,0.18);
}}
.alert-item .icon {{ font-size: 1.1rem; flex-shrink: 0; }}
.alert-item .info {{ flex: 1; }}
.alert-item .info .name {{ font-weight: 700; font-size: 0.88rem; color: var(--text-main); }}
.alert-item .info .amount {{ font-size: 0.78rem; color: var(--text-muted); margin-top: 1px; }}

/* ── TIMELINE ── */
.timeline-month {{
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 800;
    color: var(--text-muted);
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 12px 0 7px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 9px;
}}

/* ── SELECTED DAY ── */
.cal-day-selected {{
    background: linear-gradient(135deg, rgba(79,142,247,0.22), rgba(79,142,247,0.10)) !important;
    border-color: rgba(79,142,247,0.6) !important;
    box-shadow: 0 0 0 2px rgba(79,142,247,0.3) !important;
}}

/* ── ROW CARDS (pour les dossiers custom) ── */
.dossier-row {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 13px 16px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}}
.dossier-row:hover {{
    border-color: var(--border-hover);
    background: var(--row-hover);
    transform: translateX(3px);
    box-shadow: 0 2px 12px rgba(79,142,247,0.12);
}}
.dossier-row.danger {{
    background: var(--row-danger);
    border-color: var(--row-danger-border);
    border-left: 3px solid var(--danger);
}}
.dossier-row.danger:hover {{
    box-shadow: 0 2px 12px rgba(255,92,122,0.18);
}}
.dossier-row.selected {{
    border-color: var(--primary);
    background: var(--row-selected);
    box-shadow: 0 0 0 2px var(--primary-glow), 0 4px 16px rgba(79,142,247,0.15);
}}
.dossier-row .row-title {{
    font-weight: 700;
    font-size: 0.91rem;
    color: var(--text-main);
    margin-bottom: 2px;
    font-family: 'DM Sans', sans-serif;
}}
.dossier-row .row-sub {{
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 500;
}}
.dossier-row .row-amount {{
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--primary);
    text-align: right;
    font-family: 'Syne', sans-serif;
}}
.dossier-row .relance-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.7rem;
    font-weight: 700;
    background: rgba(255,92,122,0.15);
    color: var(--danger);
    border: 1px solid rgba(255,92,122,0.3);
    margin-top: 4px;
    letter-spacing: 0.03em;
}}

/* ── DETAIL PANEL ── */
.detail-panel {{
    background: linear-gradient(135deg, var(--bg-card), var(--bg-surface));
    border: 1px solid var(--border-hover);
    border-radius: var(--radius);
    padding: 20px 22px;
    margin: 8px 0 16px;
    animation: slideDown 0.2s ease;
    box-shadow: 0 8px 32px rgba(79,142,247,0.10);
}}
@keyframes slideDown {{
    from {{ opacity: 0; transform: translateY(-8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
.detail-panel .detail-title {{
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1rem;
    color: var(--primary);
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}}
.detail-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
}}
.detail-field {{
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
}}
.detail-field .field-label {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--text-dim);
    margin-bottom: 4px;
}}
.detail-field .field-value {{
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-main);
}}

/* ── SECTION LABEL ── */
.section-label {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}}

/* ── CAPTION override ── */
[data-testid="stCaptionContainer"] p {{
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}}

/* ── EXPANDER ── */
[data-testid="stExpander"] {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}}
[data-testid="stExpander"] summary {{
    color: var(--text-main) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}}

/* ── INFO / WARNING / SUCCESS ── */
[data-testid="stAlert"] {{
    border-radius: var(--radius-sm) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}}
</style>
""", unsafe_allow_html=True)

# ── AUTH ───────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()

# ── CONFIG GOOGLE SHEETS ───────────────────────────────────────────────────────
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
        return None, f"Onglet « {tab_name} » introuvable dans le Google Sheet."
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

def is_filled(val):
    """Retourne True si la cellule est remplie (non vide, non NA)."""
    if pd.isna(val):
        return False
    s = str(val).strip()
    return s != "" and s != "nan"

def fcol(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in str(c).strip().lower():
                return c
    return None

def fmt(v):
    return f"{v:,.0f} €".replace(",", " ")

LIMIT = 100

def page_header(title, subtitle=""):
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        {"<div class='subtitle'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)

# ── COMPOSANT TABLEAU INTERACTIF ───────────────────────────────────────────────
def show_interactive_table(dataframe, key_suffix="", highlight_relances=False,
                            col_relance1=None, col_relance2=None, col_relance3=None,
                            col_statut=None, detail_cols_order=None):
    """
    Affiche un tableau de lignes cliquables avec :
    - surlignage rouge si 3 relances remplies ET statut ≠ devis envoyé
    - affichage du détail de la ligne sélectionnée
    """
    total = len(dataframe)
    if total == 0:
        st.info("Aucun dossier trouvé.")
        return

    # Session pour la ligne sélectionnée et show_all
    sel_key = f"sel_{key_suffix}"
    all_key = f"show_all_{key_suffix}"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = None
    if all_key not in st.session_state:
        st.session_state[all_key] = False

    show_all = st.session_state[all_key]
    df_display = dataframe if show_all else dataframe.head(LIMIT)

    # Colonnes à afficher dans le tableau résumé
    if detail_cols_order:
        display_cols = [c for c in detail_cols_order if c in df_display.columns]
    else:
        display_cols = [c for c in df_display.columns if not c.startswith("_")]

    # Rendu des lignes
    for idx in df_display.index:
        row = df_display.loc[idx]

        # Déterminer si ligne "danger" (3 relances remplies + statut ≠ devis envoyé)
        is_danger = False
        if highlight_relances:
            r1 = is_filled(row.get(col_relance1, "")) if col_relance1 else False
            r2 = is_filled(row.get(col_relance2, "")) if col_relance2 else False
            r3 = is_filled(row.get(col_relance3, "")) if col_relance3 else False
            statut_val = str(row.get(col_statut, "")).strip().lower() if col_statut else ""
            statut_is_envoye = "envoy" in statut_val
            if r1 and r2 and r3 and not statut_is_envoye:
                is_danger = True

        is_selected = (st.session_state[sel_key] == idx)

        # Classes CSS
        css_class = "dossier-row"
        if is_danger:
            css_class += " danger"
        if is_selected:
            css_class += " selected"

        # Récupérer quelques colonnes clés pour le résumé
        client_val  = ""
        montant_val = ""
        sub_parts   = []
        for c in display_cols[:6]:
            v = str(row.get(c, "")).strip()
            if not v or v == "nan":
                continue
            if "client" in c.lower() and not client_val:
                client_val = v
            elif any(k in c.lower() for k in ["montant","total"]) and not montant_val:
                try:
                    montant_val = fmt(float(v.replace(" ","").replace("€","").replace(",",".")))
                except:
                    montant_val = v
            elif len(sub_parts) < 3:
                sub_parts.append(v[:30])

        sub_text = "  ·  ".join(sub_parts) if sub_parts else ""
        danger_badge = '<span class="relance-badge">⚠ 3 relances envoyées</span>' if is_danger else ""

        # Afficher la ligne
        st.markdown(f"""
        <div class="{css_class}" id="row_{key_suffix}_{idx}">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;">
                <div style="flex:1;min-width:0;">
                    <div class="row-title">{client_val or "—"}</div>
                    <div class="row-sub" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{sub_text}</div>
                    {danger_badge}
                </div>
                <div class="row-amount" style="flex-shrink:0;">{montant_val}</div>
                <div style="color:var(--text-dim);font-size:0.8rem;flex-shrink:0;">{"▼" if is_selected else "▶"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Bouton invisible pour le clic
        if st.button(
            "Voir / Masquer le détail",
            key=f"btn_{key_suffix}_{idx}",
            help="Cliquez pour voir le détail de ce dossier"
        ):
            if st.session_state[sel_key] == idx:
                st.session_state[sel_key] = None
            else:
                st.session_state[sel_key] = idx
            st.rerun()

        # Panneau de détail
        if is_selected:
            all_display = detail_cols_order if detail_cols_order else [c for c in row.index if not c.startswith("_")]
            fields_html = ""
            for c in all_display:
                if c not in row.index:
                    continue
                v = str(row.get(c, "")).strip()
                if not v or v == "nan":
                    continue
                # Essayer de formater les montants
                if any(k in c.lower() for k in ["montant","total","acompte","reste"]):
                    try:
                        v = fmt(float(v.replace(" ","").replace("€","").replace(",",".")))
                    except:
                        pass
                fields_html += f"""
                <div class="detail-field">
                    <div class="field-label">{c}</div>
                    <div class="field-value">{v}</div>
                </div>"""

            st.markdown(f"""
            <div class="detail-panel">
                <div class="detail-title">📋 Détail du dossier — {client_val or "Inconnu"}</div>
                <div class="detail-grid">{fields_html}</div>
            </div>
            """, unsafe_allow_html=True)

    # Pagination
    if total > LIMIT:
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        if not show_all:
            st.caption(f"Affichage des {LIMIT} premiers sur {total} dossiers.")
            if st.button(f"📂 Charger les {total - LIMIT} suivants", key=f"btn_more_{key_suffix}"):
                st.session_state[all_key] = True
                st.rerun()
        else:
            st.caption(f"{total} dossiers affichés.")
            if st.button("🔼 Réduire", key=f"btn_less_{key_suffix}"):
                st.session_state[all_key] = False
                st.rerun()

def show_table(dataframe, key_suffix=""):
    """Version simple sans interactivité (pour l'éditeur, etc.)"""
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

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding: 20px 16px 8px;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:10px;padding-bottom:8px;'>
            <div style='width:38px;height:38px;background:linear-gradient(135deg,#4f8ef7,#2563eb);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.15rem;
                box-shadow:0 4px 12px rgba(79,142,247,0.35);'>⚡</div>
            <div>
                <div style='font-family:Syne,sans-serif;font-weight:800;font-size:0.97rem;color:#e8f0fe;letter-spacing:-0.01em;'>Florian AI</div>
                <div style='font-size:0.71rem;color:rgba(232,240,254,0.5);letter-spacing:0.05em;text-transform:uppercase;'>Bâtiment ERP</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
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

    # Footer sidebar
    st.markdown("""
    <div style='position:absolute;bottom:0;left:0;right:0;padding:16px;
        border-top:1px solid rgba(255,255,255,0.06);background:rgba(0,0,0,0.15);'>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;'>
        <div style='width:33px;height:33px;background:linear-gradient(135deg,#132238,#1e3a5f);
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:0.85rem;border:1px solid rgba(79,142,247,0.35);font-weight:700;color:#7db3fa;'>
            {user[0].upper() if user else '?'}
        </div>
        <div>
            <div style='font-weight:700;font-size:0.84rem;color:#e8f0fe;'>{user}</div>
            <div style='font-size:0.71rem;color:rgba(232,240,254,0.45);text-transform:uppercase;letter-spacing:0.05em;'>{role}</div>
        </div>
        <div style='margin-left:auto;'>
            <span class="pulse-dot"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_theme, col_r, col_l = st.columns(3)
    with col_theme:
        theme_icon = "☀️" if is_dark else "🌙"
        if st.button(theme_icon, use_container_width=True, help="Changer le thème"):
            st.session_state["theme"] = "light" if is_dark else "dark"
            st.rerun()
    with col_r:
        if st.button("🔄", use_container_width=True, help="Actualiser les données"):
            st.cache_data.clear()
            st.rerun()
    with col_l:
        if st.button("🚪", use_container_width=True, help="Se déconnecter"):
            logout()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── SCROLL TO TOP ──────────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state["current_page"] = page
if st.session_state["current_page"] != page:
    st.session_state["current_page"] = page
    st.markdown("""
        <script>window.parent.document.querySelector('section.main').scrollTo(0, 0);</script>
    """, unsafe_allow_html=True)

# ── PAGES SPÉCIALES ────────────────────────────────────────────────────────────
if page == "👥 Utilisateurs":
    admin_panel()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# ÉDITEUR GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Éditeur Google Sheet":
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
            if st.button("🔄 Retenter"):
                load_presta.clear()
                st.rerun()
        else:
            sub_p_view, sub_p_add, sub_p_edit, sub_p_del = st.tabs(["👁️ Voir","➕ Ajouter","✏️ Modifier","🗑️ Supprimer"])

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
                            st.success("✅ Ligne ajoutée avec succès !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            with sub_p_edit:
                if len(df_p) == 0:
                    st.info("Aucune ligne disponible.")
                else:
                    headers_p2 = list(df_p.columns)
                    row_labels = [f"Ligne {i+2} — {df_p.iloc[i,0]} / {df_p.iloc[i,1] if len(headers_p2)>1 else ''}" for i in range(len(df_p))]
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
                                st.cache_data.clear()
                                st.success("✅ Modifications enregistrées !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            with sub_p_del:
                if len(df_p) == 0:
                    st.info("Aucune ligne disponible.")
                else:
                    headers_p3 = list(df_p.columns)
                    row_labels2 = [f"Ligne {i+2} — {df_p.iloc[i,0]} / {df_p.iloc[i,1] if len(headers_p3)>1 else ''}" for i in range(len(df_p))]
                    del_idx = st.selectbox("Ligne à supprimer", range(len(df_p)), format_func=lambda i: row_labels2[i], key="sel_del_presta")
                    st.warning(f"⚠️ Cette suppression est **irréversible** : **{row_labels2[del_idx]}**")
                    if st.button("🗑️ Confirmer la suppression", key="btn_del_presta"):
                        try:
                            ws_p4, err4 = get_worksheet(user, "Feuille 1")
                            if err4: st.error(err4)
                            else:
                                ws_p4.delete_rows(del_idx+2)
                                st.cache_data.clear()
                                st.success("✅ Ligne supprimée.")
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
            if st.button("🔄 Retenter", key="btn_retry_cata"):
                load_catalogue.clear()
                st.rerun()
        else:
            sub_c_view, sub_c_add, sub_c_edit, sub_c_del = st.tabs(["👁️ Voir","➕ Ajouter","✏️ Modifier","🗑️ Supprimer"])

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
                            st.success("✅ Article ajouté !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            with sub_c_edit:
                if len(df_c) == 0:
                    st.info("Aucun article dans le catalogue.")
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
                                st.cache_data.clear()
                                st.success("✅ Article modifié !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            with sub_c_del:
                if len(df_c) == 0:
                    st.info("Aucun article dans le catalogue.")
                else:
                    headers_c3 = list(df_c.columns)
                    art_labels2 = [f"Ligne {i+2} — {df_c.iloc[i,0]} / {df_c.iloc[i,1] if len(headers_c3)>1 else ''}" for i in range(len(df_c))]
                    del_idx_c = st.selectbox("Article à supprimer", range(len(df_c)), format_func=lambda i: art_labels2[i], key="sel_del_cata")
                    st.warning(f"⚠️ Suppression irréversible : **{art_labels2[del_idx_c]}**")
                    if st.button("🗑️ Confirmer la suppression", key="btn_del_cata"):
                        try:
                            ws_c4, err_c4 = get_worksheet(user, "catalogue")
                            if err_c4: st.error(err_c4)
                            else:
                                ws_c4.delete_rows(del_idx_c+2)
                                st.cache_data.clear()
                                st.success("✅ Article supprimé.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
    st.stop()

# ── CHARGEMENT DONNÉES ─────────────────────────────────────────────────────────
df_raw, error = get_sheet_data(user)

if error:
    get_sheet_data.clear()
    st.error("❌ Impossible de se connecter à Google Sheets.")
    st.info(f"Détail de l'erreur : {error}")
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
# VUE GÉNÉRALE
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
                    plot_bg = "rgba(0,0,0,0)"
                    fig = px.bar(cm, x="_mois", y="_montant", color="Statut",
                                 title="Évolution du CA par mois",
                                 color_discrete_map={"Signé ✅": "#00d68f", "En attente ⏳": "#1e3a5f"})
                    fig.update_layout(
                        paper_bgcolor=plot_bg, plot_bgcolor=plot_bg,
                        font_color=("#e8f0fe" if is_dark else "#1a2636"),
                        font_family="DM Sans",
                        title_font_size=13, title_font_color=("#e8f0fe" if is_dark else "#1a2636"),
                        xaxis=dict(showgrid=False, title=""),
                        yaxis=dict(gridcolor=("rgba(255,255,255,0.05)" if is_dark else "rgba(0,0,0,0.06)"), title="CA (€)"),
                        legend=dict(bgcolor="rgba(0,0,0,0)"),
                        margin=dict(t=40, b=20, l=20, r=20),
                        bargap=0.3,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Colonne « Date creation devis » non détectée pour le graphique.")

    with cr:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.95rem;color:var(--warning);margin-bottom:12px;'>🚨 Devis en attente</div>", unsafe_allow_html=True)
            df_alertes = df[~df["_signe"]].head(6)
            if len(df_alertes) > 0:
                for _, row in df_alertes.iterrows():
                    client   = row[COL_CLIENT] if COL_CLIENT else "Inconnu"
                    montant  = fmt(row["_montant"])
                    chantier = row[COL_CHANTIER] if COL_CHANTIER else ""
                    num_devis = row[COL_NUM] if COL_NUM else ""
                    date_creation = row[COL_DATE] if COL_DATE else ""
                    parts = [str(client)]
                    if chantier and str(chantier).strip(): parts.append(str(chantier))
                    if num_devis and str(num_devis).strip(): parts.append(f"N°{num_devis}")
                    if date_creation and str(date_creation).strip(): parts.append(str(date_creation))
                    tooltip = " · ".join(parts)
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
                    st.caption(f"+ {nb_attente-6} autres devis en attente")
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
                marker_colors=["#00d68f","#1e3a5f"],
                textinfo="none",
            )])
            fig_donut.add_annotation(
                text=f"{taux_conv}%", x=0.5, y=0.5,
                font_size=28, font_color=("#e8f0fe" if is_dark else "#1a2636"),
                font_family="Syne", showarrow=False
            )
            fig_donut.update_layout(
                title="Taux de transformation",
                title_font_color=("#e8f0fe" if is_dark else "#1a2636"),
                paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", font_color=("#6b84a3" if is_dark else "#5a7290")),
                margin=dict(t=40, b=20, l=20, r=20), height=250,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
    with col_d2:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.93rem;color:var(--text-main);margin-bottom:14px;'>Résumé financier</div>", unsafe_allow_html=True)
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
                    padding:9px 0;border-bottom:1px solid var(--border);'>
                    <span style='color:var(--text-muted);font-size:0.84rem;font-weight:500;'>{label}</span>
                    <span style='color:{color};font-weight:700;font-size:0.93rem;'>{val}</span>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Devis":
    page_header("Gestion des Devis", f"{nb_devis} devis au total")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Devis Émis", nb_devis)
    c2.metric("Taux de Transformation", f"{taux_conv} %")
    c3.metric("Volume CA Global", fmt(total_ca))

    st.markdown("<br>", unsafe_allow_html=True)

    detail_cols_devis = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE,
                                      COL_RELANCE1, COL_RELANCE2, COL_RELANCE3, COL_STATUT,
                                      COL_ADRESSE, COL_MODALITE, COL_TVA] if c]

    search = st.text_input("🔍 Rechercher un devis", placeholder="Nom du client, chantier, numéro...", key="search_devis")
    df_d = df.copy()
    if search:
        mask = pd.Series([False]*len(df_d), index=df_d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col: mask |= df_d[col].astype(str).str.contains(search, case=False, na=False)
        df_d = df_d[mask]

    t1, t2 = st.tabs(["⏳ En attente de signature", "✅ Devis signés"])
    with t1:
        d = df_d[~df_d["_signe"]].copy().reset_index(drop=True)
        st.caption(f"{len(d)} devis · CA potentiel : {fmt(d['_montant'].sum())}")
        show_interactive_table(
            d, key_suffix="devis_attente",
            highlight_relances=True,
            col_relance1=COL_RELANCE1, col_relance2=COL_RELANCE2, col_relance3=COL_RELANCE3,
            col_statut=COL_STATUT,
            detail_cols_order=detail_cols_devis
        )
    with t2:
        d = df_d[df_d["_signe"]].copy().reset_index(drop=True)
        st.caption(f"{len(d)} devis signés · CA confirmé : {fmt(d['_montant'].sum())}")
        show_interactive_table(
            d, key_suffix="devis_signes",
            highlight_relances=False,
            detail_cols_order=detail_cols_devis
        )

# ══════════════════════════════════════════════════════════════════════════════
# FACTURES & PAIEMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💶 Factures & Paiements":
    page_header("Factures & Paiements", "Suivi des encaissements")

    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Factures finales émises", nb_fact_ok)
    c2.metric("⚠️ Sans facture finale", len(df_imp))
    c3.metric("💸 CA restant à facturer", fmt(reste_encaissement))

    st.markdown("<br>", unsafe_allow_html=True)

    detail_cols_fact = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ACOMPTE1,
                                     COL_ACOMPTE2, COL_FACT_FIN, COL_PV,
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
        d = df_f[df_f["_signe"] & ~df_f["_fact_fin"]].copy().reset_index(drop=True)
        st.caption(f"{len(d)} dossier(s) en attente de facturation")
        show_interactive_table(d, key_suffix="fact_attente", detail_cols_order=detail_cols_fact)
    with t2:
        d = df_f[df_f["_fact_fin"]].copy().reset_index(drop=True)
        st.caption(f"{len(d)} facture(s) émise(s)")
        show_interactive_table(d, key_suffix="fact_ok", detail_cols_order=detail_cols_fact)

# ══════════════════════════════════════════════════════════════════════════════
# CHANTIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Chantiers":
    page_header("Suivi des Chantiers", "Vue d'ensemble des travaux en cours et terminés")

    df["_statut_ch"] = df["_pv"].apply(lambda x: "✅ Terminé" if x else "🟡 En cours")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏗️ Chantiers en cours", int((~df["_pv"]).sum()))
    c2.metric("💰 Trésorerie en cours", fmt(df[~df["_pv"]]["_montant"].sum()))
    c3.metric("✅ Chantiers terminés", int(df["_pv"].sum()))
    c4.metric("💰 CA réalisé", fmt(df[df["_pv"]]["_montant"].sum()))

    st.markdown("<br>", unsafe_allow_html=True)

    search_ch = st.text_input("🔍 Filtrer les chantiers", placeholder="Client, lieu, chantier...", key="search_ch")
    df_ch = df.copy()
    if search_ch:
        mask = pd.Series([False]*len(df_ch), index=df_ch.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_ADRESSE]:
            if col: mask |= df_ch[col].astype(str).str.contains(search_ch, case=False, na=False)
        df_ch = df_ch[mask]

    detail_cols_ch = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ADRESSE,
                                   COL_DATE_DEBUT, COL_DATE_FIN, COL_EQUIPE,
                                   COL_RESERVE, COL_STATUT, "_statut_ch"] if c]

    t1, t2 = st.tabs(["🟡 Chantiers en cours", "✅ Chantiers livrés (PV signé)"])
    with t1:
        d = df_ch[~df_ch["_pv"]].copy().reset_index(drop=True)
        st.caption(f"{len(d)} chantier(s) actif(s) · {fmt(d['_montant'].sum())}")
        show_interactive_table(d, key_suffix="ch_cours", detail_cols_order=detail_cols_ch)
    with t2:
        d = df_ch[df_ch["_pv"]].copy().reset_index(drop=True)
        st.caption(f"{len(d)} chantier(s) livré(s) · {fmt(d['_montant'].sum())}")
        show_interactive_table(d, key_suffix="ch_termines", detail_cols_order=detail_cols_ch)

# ══════════════════════════════════════════════════════════════════════════════
# PLANNING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Planning":
    page_header("Planning des Chantiers", "Vue calendrier des interventions")

    if not COL_DATE_DEBUT or not COL_DATE_FIN:
        st.warning("⚠️ Colonnes de dates de début / fin non détectées dans votre Google Sheet.")
        with st.expander("🔍 Colonnes disponibles"):
            st.write(list(df.columns))
        st.stop()

    today = datetime.now()

    df_plan = df.copy()
    df_plan["_start"] = pd.to_datetime(df_plan[COL_DATE_DEBUT], dayfirst=True, errors="coerce")
    df_plan["_end"]   = pd.to_datetime(df_plan[COL_DATE_FIN],   dayfirst=True, errors="coerce")
    df_plan = df_plan.dropna(subset=["_start", "_end"])
    df_plan = df_plan[df_plan["_end"] >= df_plan["_start"]]

    if df_plan.empty:
        st.info("ℹ️ Aucune date d'intervention valide trouvée dans vos dossiers.")
        st.stop()

    def get_statut_code(row):
        if row["_pv"]:   return "termine"
        if row["_end"].date() < today.date(): return "retard"
        return "en-cours"

    df_plan["_statut_code"] = df_plan.apply(get_statut_code, axis=1)

    nb_en_cours  = int((df_plan["_statut_code"] == "en-cours").sum())
    nb_retard    = int((df_plan["_statut_code"] == "retard").sum())
    nb_termine   = int((df_plan["_statut_code"] == "termine").sum())
    nb_this_week = int(((df_plan["_start"].dt.date >= today.date()) &
                        (df_plan["_start"].dt.date <= (today + timedelta(days=7)).date())).sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🟡 En cours", nb_en_cours)
    k2.metric("🔴 En retard", nb_retard)
    k3.metric("✅ Terminés", nb_termine)
    k4.metric("📅 Démarrent cette semaine", nb_this_week)

    st.markdown("<br>", unsafe_allow_html=True)

    view_mode = st.radio(
        "Vue",
        ["📅 Calendrier mensuel", "📊 Gantt", "📋 Liste"],
        horizontal=True,
        key="plan_view"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════
    # VUE CALENDRIER MENSUEL
    # ════════════════════════════════════════════════════════════════
    if view_mode == "📅 Calendrier mensuel":

        if "plan_year"  not in st.session_state: st.session_state["plan_year"]  = today.year
        if "plan_month" not in st.session_state: st.session_state["plan_month"] = today.month
        if "cal_sel_day" not in st.session_state: st.session_state["cal_sel_day"] = None

        mois_fr = ["","Janvier","Février","Mars","Avril","Mai","Juin",
                   "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("◀  Mois précédent", use_container_width=True, key="prev_month"):
                if st.session_state["plan_month"] == 1:
                    st.session_state["plan_month"] = 12
                    st.session_state["plan_year"] -= 1
                else:
                    st.session_state["plan_month"] -= 1
                st.session_state["cal_sel_day"] = None
                st.rerun()
        with nav2:
            st.markdown(
                f"<h2 style='text-align:center;margin:0;padding:8px 0;color:var(--text-main);"
                f"font-family:Syne,sans-serif;font-weight:800;letter-spacing:-0.02em;'>"
                f"{mois_fr[st.session_state['plan_month']]} {st.session_state['plan_year']}</h2>",
                unsafe_allow_html=True
            )
        with nav3:
            if st.button("Mois suivant  ▶", use_container_width=True, key="next_month"):
                if st.session_state["plan_month"] == 12:
                    st.session_state["plan_month"] = 1
                    st.session_state["plan_year"] += 1
                else:
                    st.session_state["plan_month"] += 1
                st.session_state["cal_sel_day"] = None
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
                color    = "#4f8ef7" if statut == "en-cours" else "#ff5c7a" if statut == "retard" else "#00d68f"
                bg       = "rgba(79,142,247,0.15)" if statut == "en-cours" else "rgba(255,92,122,0.15)" if statut == "retard" else "rgba(0,214,143,0.15)"
                events_by_day[d].append({
                    "label": chantier[:22], "client": client,
                    "color": color, "bg": bg,
                    "montant": fmt(row["_montant"]),
                    "debut": row["_start"].strftime("%d/%m/%Y"),
                    "fin": row["_end"].strftime("%d/%m/%Y"),
                })
                cur += timedelta(days=1)

        # Calendrier HTML
        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        header_html = "".join(
            f'<div style="text-align:center;font-size:0.75rem;font-weight:800;color:var(--primary);'
            f'padding:12px 0;letter-spacing:0.09em;text-transform:uppercase;">{d}</div>'
            for d in days_fr
        )

        cal_grid = calendar.monthcalendar(sel_year, sel_month)
        sel_day = st.session_state.get("cal_sel_day")
        cells_html = ""
        for week in cal_grid:
            for day in week:
                if day == 0:
                    cells_html += '<div style="background:transparent;border:1px solid transparent;border-radius:12px;min-height:110px;padding:10px;"></div>'
                else:
                    is_today   = (day == today.day and sel_year == today.year and sel_month == today.month)
                    is_sel_day = (sel_day == day)
                    evs = events_by_day.get(day, [])

                    if is_sel_day:
                        cell_style = "background:linear-gradient(135deg,rgba(79,142,247,0.22),rgba(79,142,247,0.08));border:2px solid rgba(79,142,247,0.65);border-radius:12px;min-height:110px;padding:10px;box-shadow:0 0 0 3px rgba(79,142,247,0.15);"
                        num_style  = "width:28px;height:28px;border-radius:50%;background:var(--primary);display:flex;align-items:center;justify-content:center;font-size:0.85rem;font-weight:800;color:#fff;margin-bottom:5px;box-shadow:0 2px 8px rgba(79,142,247,0.4);"
                    elif is_today:
                        cell_style = "background:linear-gradient(135deg,rgba(79,142,247,0.14),rgba(79,142,247,0.05));border:2px solid rgba(79,142,247,0.5);border-radius:12px;min-height:110px;padding:10px;"
                        num_style  = "width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#4f8ef7,#2563eb);display:flex;align-items:center;justify-content:center;font-size:0.85rem;font-weight:800;color:#fff;margin-bottom:5px;box-shadow:0 2px 8px rgba(79,142,247,0.35);"
                    elif evs:
                        cell_style = "background:var(--cal-cell);border:1px solid var(--border);border-radius:12px;min-height:110px;padding:10px;cursor:pointer;transition:all 0.15s ease;"
                        num_style  = "font-size:0.88rem;font-weight:700;color:var(--text-muted);margin-bottom:5px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;"
                    else:
                        cell_style = "background:var(--cal-cell);border:1px solid var(--border);border-radius:12px;min-height:110px;padding:10px;opacity:0.7;"
                        num_style  = "font-size:0.88rem;font-weight:600;color:var(--text-dim);margin-bottom:5px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;"

                    events_html = ""
                    for ev in evs[:2]:
                        events_html += (
                            f'<div style="background:{ev["bg"]};border-left:3px solid {ev["color"]};'
                            f'border-radius:0 6px 6px 0;padding:3px 7px;font-size:0.68rem;'
                            f'color:{ev["color"]};margin-bottom:3px;white-space:nowrap;overflow:hidden;'
                            f'text-overflow:ellipsis;font-weight:700;" title="{ev["label"]} — {ev["client"]}">'
                            f'{ev["label"]}</div>'
                        )
                    if len(evs) > 2:
                        events_html += f'<div style="font-size:0.65rem;color:var(--warning);padding:2px 6px;font-weight:700;">+{len(evs)-2} autres</div>'

                    cells_html += f'<div style="{cell_style}" id="cal_day_{day}"><div style="{num_style}">{day}</div>{events_html}</div>'

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{'#0a1628' if is_dark else '#f0f4fb'},{'#0f1e30' if is_dark else '#ffffff'});
            border:1px solid var(--border);border-radius:16px;padding:24px;margin-bottom:20px;
            box-shadow:var(--shadow);">
            <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:10px;">
                {header_html}
            </div>
            <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;">
                {cells_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Boutons de jours cliquables (jours avec événements)
        if events_by_day:
            days_with_events = sorted(events_by_day.keys())
            st.markdown('<div class="section-label">Sélectionner un jour pour voir les chantiers</div>', unsafe_allow_html=True)
            # Afficher en ligne les jours qui ont des événements
            cols_days = st.columns(min(len(days_with_events), 10))
            for ci, day in enumerate(days_with_events):
                with cols_days[ci % min(len(days_with_events), 10)]:
                    nb_ev = len(events_by_day[day])
                    is_sel = (sel_day == day)
                    btn_label = f"**{day}**" if is_sel else str(day)
                    if st.button(
                        btn_label,
                        key=f"cal_day_btn_{day}",
                        help=f"{nb_ev} chantier(s) le {day}/{sel_month}/{sel_year}",
                        use_container_width=True
                    ):
                        if st.session_state["cal_sel_day"] == day:
                            st.session_state["cal_sel_day"] = None
                        else:
                            st.session_state["cal_sel_day"] = day
                        st.rerun()

        # Affichage du détail du jour sélectionné
        if sel_day and sel_day in events_by_day:
            evs = events_by_day[sel_day]
            st.markdown(f"""
            <div class="detail-panel" style="margin-top:16px;">
                <div class="detail-title">
                    📅 Chantiers du {sel_day} {mois_fr[sel_month]} {sel_year}
                    <span style="font-size:0.8rem;font-weight:500;color:var(--text-muted);margin-left:8px;">
                        {len(evs)} intervention(s)
                    </span>
                </div>
            """, unsafe_allow_html=True)
            for ev in evs:
                st.markdown(f"""
                <div style="background:var(--bg-surface);border:1px solid {ev['color']}44;
                    border-left:3px solid {ev['color']};border-radius:8px;
                    padding:12px 14px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-weight:700;font-size:0.9rem;color:var(--text-main);">{ev['label']}</div>
                            <div style="font-size:0.78rem;color:var(--text-muted);margin-top:2px;">
                                👤 {ev['client']} &nbsp;·&nbsp; 📅 {ev['debut']} → {ev['fin']}
                            </div>
                        </div>
                        <div style="font-weight:700;color:{ev['color']};font-size:0.93rem;">{ev['montant']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Légende
        st.markdown("""
        <div style="display:flex;gap:20px;margin-top:12px;padding:14px 18px;
            background:var(--bg-surface);border-radius:10px;border:1px solid var(--border);flex-wrap:wrap;">
            <div style="display:flex;align-items:center;gap:8px;font-size:0.83rem;color:var(--text-main);font-weight:600;">
                <div style="width:12px;height:12px;border-radius:3px;background:#4f8ef7;"></div> En cours
            </div>
            <div style="display:flex;align-items:center;gap:8px;font-size:0.83rem;color:var(--text-main);font-weight:600;">
                <div style="width:12px;height:12px;border-radius:3px;background:#ff5c7a;"></div> En retard
            </div>
            <div style="display:flex;align-items:center;gap:8px;font-size:0.83rem;color:var(--text-main);font-weight:600;">
                <div style="width:12px;height:12px;border-radius:3px;background:#00d68f;"></div> Terminé
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not df_month.empty:
            with st.expander(f"📋 Tous les chantiers de ce mois ({len(df_month)})", expanded=False):
                detail_cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_DATE_DEBUT, COL_DATE_FIN, COL_MONTANT] if c]
                show_table(df_month[detail_cols].reset_index(drop=True), "cal_detail")

    # ════════════════════════════════════════════════════════════════
    # VUE GANTT
    # ════════════════════════════════════════════════════════════════
    elif view_mode == "📊 Gantt":
        show_all_gantt = st.toggle("Inclure les chantiers terminés", value=False, key="gantt_all")
        df_gantt = df_plan.copy()
        if not show_all_gantt:
            df_gantt = df_gantt[df_gantt["_statut_code"] != "termine"]

        if df_gantt.empty:
            st.info("Aucun chantier à afficher. Activez « Inclure les terminés » si besoin.")
        else:
            df_gantt_sorted = df_gantt.sort_values("_start")
            nom_col = COL_CHANTIER or COL_CLIENT or df_gantt.columns[0]
            label_map = {"en-cours": "🟡 En cours", "retard": "🔴 En retard", "termine": "✅ Terminé"}
            df_gantt_sorted["_statut_label"] = df_gantt_sorted["_statut_code"].map(label_map)
            color_map = {"🟡 En cours": "#4f8ef7", "🔴 En retard": "#ff5c7a", "✅ Terminé": "#00d68f"}

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
                line_width=2, line_dash="dash", line_color="#ffb84d",
                annotation_text="Aujourd'hui",
                annotation_font_color="#ffb84d",
                annotation_position="top right",
            )
            fig_gantt.update_yaxes(autorange="reversed", showgrid=False)
            fig_gantt.update_xaxes(
                showgrid=True,
                gridcolor=("rgba(255,255,255,0.04)" if is_dark else "rgba(0,0,0,0.06)"),
                tickformat="%d %b",
                tickfont_color=("#6b84a3" if is_dark else "#5a7290")
            )
            fig_gantt.update_traces(marker_line_width=0, opacity=0.9)
            fig_gantt.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor=("rgba(13,30,48,0.6)" if is_dark else "rgba(240,244,251,0.6)"),
                font_color=("#e8f0fe" if is_dark else "#1a2636"),
                font_family="DM Sans",
                title=None, xaxis_title="", yaxis_title="",
                height=max(380, len(df_gantt_sorted) * 42 + 80),
                legend=dict(
                    bgcolor=("rgba(13,30,48,0.85)" if is_dark else "rgba(255,255,255,0.85)"),
                    bordercolor=("rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.08)"),
                    borderwidth=1,
                    font_color=("#6b84a3" if is_dark else "#5a7290"),
                    title_text=""
                ),
                margin=dict(t=20, b=20, l=10, r=10),
                bargap=0.28,
            )
            with st.container(border=True):
                st.plotly_chart(fig_gantt, use_container_width=True)

            with st.expander("📋 Détail des chantiers", expanded=False):
                detail_cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_DATE_DEBUT, COL_DATE_FIN, COL_MONTANT, COL_ADRESSE] if c]
                show_table(df_gantt_sorted[detail_cols].reset_index(drop=True), "gantt_detail")

    # ════════════════════════════════════════════════════════════════
    # VUE LISTE
    # ════════════════════════════════════════════════════════════════
    elif view_mode == "📋 Liste":
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

            color_map  = {"en-cours": "#4f8ef7", "retard": "#ff5c7a", "termine": "#00d68f"}
            bg_map     = {"en-cours": "rgba(79,142,247,0.07)", "retard": "rgba(255,92,122,0.07)", "termine": "rgba(0,214,143,0.07)"}
            label_map  = {"en-cours": "En cours", "retard": "En retard", "termine": "Terminé"}
            border_map = {"en-cours": "rgba(79,142,247,0.28)", "retard": "rgba(255,92,122,0.28)", "termine": "rgba(0,214,143,0.28)"}

            for period, group in df_list.groupby("_mois_ord", sort=True):
                mois_label = group["_mois_str"].iloc[0]
                st.markdown(f'<div class="timeline-month">📅 {mois_label} — {len(group)} chantier(s)</div>', unsafe_allow_html=True)

                for _, row in group.iterrows():
                    client   = str(row[COL_CLIENT]) if COL_CLIENT else ""
                    chantier = str(row[COL_CHANTIER]) if COL_CHANTIER else client
                    adresse  = str(row[COL_ADRESSE]) if COL_ADRESSE else ""
                    montant  = fmt(row["_montant"])
                    debut    = row["_start"].strftime("%d/%m/%Y")
                    fin      = row["_end"].strftime("%d/%m/%Y")
                    duree    = (row["_end"] - row["_start"]).days + 1
                    statut   = row["_statut_code"]
                    color    = color_map[statut]
                    bg       = bg_map[statut]
                    border   = border_map[statut]
                    label    = label_map[statut]

                    adresse_html = f"&nbsp;·&nbsp; 📍 {adresse}" if adresse and adresse != "nan" else ""

                    st.markdown(f"""
                    <div style="background:{bg};border:1px solid {border};border-left:3px solid {color};
                        border-radius:10px;padding:14px 18px;margin-bottom:8px;
                        transition:all 0.2s ease;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;">
                            <div style="flex:1;min-width:0;">
                                <div style="font-weight:700;font-size:0.92rem;color:var(--text-main);margin-bottom:3px;">
                                    {chantier}
                                </div>
                                <div style="font-size:0.79rem;color:var(--text-muted);">
                                    👤 {client}{adresse_html}
                                </div>
                                <div style="margin-top:8px;">
                                    <span style="display:inline-block;padding:2px 10px;border-radius:99px;font-size:0.71rem;
                                        font-weight:700;background:rgba(255,255,255,0.06);color:{color};
                                        border:1px solid {border};">{label}</span>
                                    <span style="font-size:0.74rem;color:var(--text-dim);margin-left:8px;">
                                        {duree} jour(s)
                                    </span>
                                </div>
                            </div>
                            <div style="text-align:right;flex-shrink:0;">
                                <div style="font-weight:800;color:{color};font-size:0.97rem;font-family:'Syne',sans-serif;">
                                    {montant}
                                </div>
                                <div style="font-size:0.77rem;color:var(--text-muted);margin-top:4px;">
                                    Début : {debut}
                                </div>
                                <div style="font-size:0.77rem;color:var(--text-muted);">
                                    Fin : {fin}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TOUS LES DOSSIERS
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
    d = d.reset_index(drop=True)

    detail_cols_all = [c for c in [
        COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE,
        COL_SIGN, COL_FACT_FIN, COL_PV, COL_STATUT,
        COL_ACOMPTE1, COL_ACOMPTE2, COL_RELANCE1, COL_RELANCE2, COL_RELANCE3,
        COL_ADRESSE, COL_DATE_DEBUT, COL_DATE_FIN, COL_EQUIPE,
        COL_RESERVE, COL_MODALITE, COL_TVA
    ] if c]

    show_interactive_table(
        d, key_suffix="all",
        highlight_relances=True,
        col_relance1=COL_RELANCE1, col_relance2=COL_RELANCE2, col_relance3=COL_RELANCE3,
        col_statut=COL_STATUT,
        detail_cols_order=detail_cols_all
    )
