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

# ── CSS PREMIUM ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');

:root {
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
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-app) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text-main);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg-sidebar) 0%, #0a1628 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--text-dim); border-radius: 99px; }

[data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 22px !important;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary), transparent);
    opacity: 0.6;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: var(--border-hover); }
[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: var(--text-main) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.7rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

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
    font-size: 0.88rem !important;
    padding: 8px 18px !important;
    transition: all 0.15s ease;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 12px rgba(79,142,247,0.3) !important;
}

.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    padding: 8px 16px !important;
}
.stButton > button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: var(--primary-glow) !important;
    transform: translateY(-1px);
}

.stTextInput input, .stNumberInput input, .stSelectbox select,
[data-testid="stTextArea"] textarea {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-main) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stNumberInput input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--primary-glow) !important;
}

[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
}

hr { border-color: var(--border) !important; margin: 16px 0 !important; }

[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > div[style*="border"] {
    border-color: var(--border) !important;
    background: var(--bg-card) !important;
    border-radius: var(--radius) !important;
}

[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child { display: none !important; }
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    padding: 10px 14px;
    background: transparent;
    border-radius: var(--radius-sm);
    cursor: pointer;
    margin-bottom: 2px;
    border: 1px solid transparent;
    transition: all 0.15s ease;
    width: 100%;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover { background: var(--bg-card); border-color: var(--border); }
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, var(--primary-glow), rgba(79,142,247,0.08)) !important;
    border-color: rgba(79,142,247,0.4) !important;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p { color: var(--primary) !important; font-weight: 700 !important; }
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p { margin: 0; font-size: 0.92rem; color: var(--text-muted); }
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] { gap: 2px; }

.badge { display: inline-block; padding: 3px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.03em; }
.badge-success { background: var(--success-glow); color: var(--success); border: 1px solid rgba(0,214,143,0.2); }
.badge-warning { background: var(--warning-glow); color: var(--warning); border: 1px solid rgba(255,184,77,0.2); }
.badge-primary { background: var(--primary-glow); color: var(--primary); border: 1px solid rgba(79,142,247,0.2); }
.badge-danger { background: rgba(255,92,122,0.1); color: var(--danger); border: 1px solid rgba(255,92,122,0.2); }
.badge-muted { background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border); }

.pulse-dot {
    display: inline-block; width: 7px; height: 7px;
    border-radius: 50%; background: var(--success);
    animation: pulse-anim 2s ease-in-out infinite;
    margin-right: 6px; vertical-align: middle;
}
@keyframes pulse-anim { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } }

.page-header { padding: 8px 0 24px; border-bottom: 1px solid var(--border); margin-bottom: 28px; }
.page-header h1 { font-family: 'Syne', sans-serif !important; font-size: 1.9rem !important; font-weight: 800 !important; letter-spacing: -0.03em; margin: 0 !important; color: var(--text-main) !important; }
.page-header .subtitle { color: var(--text-muted); font-size: 0.88rem; margin-top: 4px; }

.alert-item {
    display: flex; align-items: center; gap: 12px; padding: 10px 14px;
    background: rgba(255,184,77,0.06); border: 1px solid rgba(255,184,77,0.15);
    border-radius: var(--radius-sm); margin-bottom: 8px;
    transition: all 0.2s ease; cursor: pointer; position: relative;
}
.alert-item:hover {
    background: rgba(255,184,77,0.12); border-color: rgba(255,184,77,0.35);
    transform: translateX(4px); box-shadow: 0 2px 8px rgba(255,184,77,0.2);
}
.alert-item::after {
    content: attr(title); position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%);
    background: #0a1628; color: #ffb84d; padding: 8px 12px; border-radius: 6px;
    font-size: 0.75rem; white-space: nowrap; opacity: 0; pointer-events: none;
    transition: opacity 0.2s ease; margin-bottom: 6px; border: 1px solid rgba(255,184,77,0.3);
    z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
.alert-item:hover::after { opacity: 1; }
.alert-item .icon { font-size: 1.1rem; flex-shrink: 0; }
.alert-item .info { flex: 1; }
.alert-item .info .name { font-weight: 600; font-size: 0.9rem; color: var(--text-main); }
.alert-item .info .amount { font-size: 0.8rem; color: var(--text-muted); }

.timeline-month { font-family: 'Syne', sans-serif; font-size: 0.8rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.06em; text-transform: uppercase; padding: 10px 0 6px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
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

def fcol(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in str(c).strip().lower():
                return c
    return None

def fmt(v):
    return f"{v:,.0f} €".replace(",", " ")

LIMIT = 100

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
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:10px;padding-bottom:8px;'>
            <div style='width:36px;height:36px;background:linear-gradient(135deg,#4f8ef7,#2563eb);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;'>⚡</div>
            <div>
                <div style='font-family:Syne,sans-serif;font-weight:800;font-size:0.95rem;color:#e8f0fe;'>Florian AI</div>
                <div style='font-size:0.72rem;color:#6b84a3;letter-spacing:0.04em;'>Bâtiment ERP</div>
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

    st.markdown("<div style='position:absolute;bottom:0;left:0;right:0;padding:16px;border-top:1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;'>
        <div style='width:32px;height:32px;background:linear-gradient(135deg,#132238,#1e3a5f);
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:0.85rem;border:1px solid rgba(79,142,247,0.3);'>
            {user[0].upper() if user else '?'}
        </div>
        <div>
            <div style='font-weight:600;font-size:0.85rem;color:#e8f0fe;'>{user}</div>
            <div style='font-size:0.72rem;color:#6b84a3;'>{role}</div>
        </div>
        <div style='margin-left:auto;'>
            <span class="pulse-dot"></span>
        </div>
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
                            st.success("✅ Ligne ajoutée !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            with sub_p_edit:
                if len(df_p) == 0:
                    st.info("Aucune ligne.")
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
                                st.success("✅ Modifié !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            with sub_p_del:
                if len(df_p) == 0:
                    st.info("Aucune ligne.")
                else:
                    headers_p3 = list(df_p.columns)
                    row_labels2 = [f"Ligne {i+2} — {df_p.iloc[i,0]} / {df_p.iloc[i,1] if len(headers_p3)>1 else ''}" for i in range(len(df_p))]
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
    c1.metric(f"💰 CA Sécurisé", fmt(ca_signe), f"{nb_signes} devis signés")
    c2.metric(f"⏳ CA En Négociation", fmt(ca_non_s), f"{nb_attente} en cours")
    c3.metric("📈 Taux de Conversion", f"{taux_conv} %")
    c4.metric(f"💸 Reste à Encaisser", fmt(reste_encaissement))

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
                    fig = px.bar(cm, x="_mois", y="_montant", color="Statut",
                                 title="📈 Évolution du CA par mois",
                                 color_discrete_map={"Signé ✅": "#00d68f", "En attente ⏳": "#1e3a5f"})
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#e8f0fe", font_family="DM Sans",
                        title_font_size=14, title_font_color="#e8f0fe",
                        xaxis=dict(showgrid=False, title=""),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="CA (€)"),
                        legend=dict(bgcolor="rgba(0,0,0,0)"),
                        margin=dict(t=40, b=20, l=20, r=20),
                        bargap=0.3,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Colonne 'Date creation devis' non détectée pour le graphique.")

    with cr:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:1rem;color:#ffb84d;margin-bottom:12px;'>🚨 Actions Requises</div>", unsafe_allow_html=True)
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
                marker_colors=["#00d68f","#1e3a5f"],
                textinfo="none",
            )])
            fig_donut.add_annotation(text=f"{taux_conv}%", x=0.5, y=0.5,
                                     font_size=28, font_color="#e8f0fe",
                                     font_family="Syne", showarrow=False)
            fig_donut.update_layout(
                title="Taux de transformation", title_font_color="#e8f0fe",
                paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#6b84a3"),
                margin=dict(t=40, b=20, l=20, r=20), height=250,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
    with col_d2:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.95rem;color:#e8f0fe;margin-bottom:16px;'>📊 Résumé financier</div>", unsafe_allow_html=True)
            items = [
                ("CA Total émis", fmt(total_ca), "#4f8ef7"),
                ("CA Sécurisé", fmt(ca_signe), "#00d68f"),
                ("CA En attente", fmt(ca_non_s), "#ffb84d"),
                ("Reste à encaisser", fmt(reste_encaissement), "#ff5c7a"),
                ("Chantiers terminés (PV)", f"{int(df['_pv'].sum())}", "#00d68f"),
            ]
            for label, val, color in items:
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                    padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);'>
                    <span style='color:#6b84a3;font-size:0.85rem;'>{label}</span>
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
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_attente")
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
# PAGE : CHANTIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Chantiers":
    page_header("Suivi des Chantiers", "Vue d'ensemble des travaux")

    df["_statut_ch"] = df["_pv"].apply(lambda x: "✅ Terminé" if x else "🟡 En cours")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏗️ En cours", int((~df["_pv"]).sum()))
    c2.metric("💰 Tréso. en cours", fmt(df[~df["_pv"]]["_montant"].sum()))
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

    cols_ch = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ADRESSE,
                             COL_DATE_DEBUT, COL_DATE_FIN, COL_RESERVE, "_statut_ch"] if c]
    t1, t2 = st.tabs(["🟡 En cours", "✅ Livrés (PV signé)"])
    with t1:
        d = df_ch[~df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) actif(s) — {fmt(d['_montant'].sum())}")
        show_table(d[cols_ch].reset_index(drop=True) if cols_ch else d, "ch_cours")
    with t2:
        d = df_ch[df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) livré(s) — {fmt(d['_montant'].sum())}")
        show_table(d[cols_ch].reset_index(drop=True) if cols_ch else d, "ch_termines")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PLANNING — STYLE GOOGLE CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Planning":
    page_header("Planning des Chantiers", "Vue calendrier des interventions")

    if not COL_DATE_DEBUT or not COL_DATE_FIN:
        st.warning("⚠️ Colonnes de dates non détectées.")
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

        if "plan_year" not in st.session_state:
            st.session_state["plan_year"] = today.year
        if "plan_month" not in st.session_state:
            st.session_state["plan_month"] = today.month

        mois_fr = ["","Janvier","Février","Mars","Avril","Mai","Juin",
                   "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("◀", use_container_width=True, key="prev_month"):
                if st.session_state["plan_month"] == 1:
                    st.session_state["plan_month"] = 12
                    st.session_state["plan_year"] -= 1
                else:
                    st.session_state["plan_month"] -= 1
                st.rerun()
        with nav2:
            st.markdown(
                f"<h2 style='text-align:center;margin:0;padding:8px 0;color:#e8f0fe;font-family:Syne,sans-serif;font-weight:800;'>"
                f"{mois_fr[st.session_state['plan_month']]} {st.session_state['plan_year']}</h2>",
                unsafe_allow_html=True
            )
        with nav3:
            if st.button("▶", use_container_width=True, key="next_month"):
                if st.session_state["plan_month"] == 12:
                    st.session_state["plan_month"] = 1
                    st.session_state["plan_year"] += 1
                else:
                    st.session_state["plan_month"] += 1
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
                events_by_day[d].append({"label": chantier[:20], "client": client, "color": color, "bg": bg})
                cur += timedelta(days=1)

        # Grille HTML améliorée
        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        header_html = "".join(
            f'<div style="text-align:center;font-size:0.8rem;font-weight:700;color:#4f8ef7;'
            f'padding:12px 0;letter-spacing:0.08em;text-transform:uppercase;">{d}</div>'
            for d in days_fr
        )

        cal_grid = calendar.monthcalendar(sel_year, sel_month)
        cells_html = ""
        for week in cal_grid:
            for day in week:
                if day == 0:
                    cells_html += '<div style="background:rgba(0,0,0,0);border:1px solid transparent;border-radius:12px;min-height:120px;padding:10px;"></div>'
                else:
                    is_today = (day == today.day and sel_year == today.year and sel_month == today.month)
                    if is_today:
                        cell_style = "background:linear-gradient(135deg, rgba(79,142,247,0.15), rgba(79,142,247,0.05));border:2px solid rgba(79,142,247,0.6);border-radius:12px;min-height:120px;padding:10px;transition:all 0.2s ease;"
                        num_style  = "width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#4f8ef7,#2563eb);display:flex;align-items:center;justify-content:center;font-size:0.9rem;font-weight:800;color:#fff;margin-bottom:6px;box-shadow:0 2px 8px rgba(79,142,247,0.4);"
                    else:
                        cell_style = "background:linear-gradient(135deg, #0f1e30, #132238);border:1px solid rgba(255,255,255,0.06);border-radius:12px;min-height:120px;padding:10px;transition:all 0.2s ease;cursor:default;"
                        num_style  = "font-size:0.9rem;font-weight:700;color:#6b84a3;margin-bottom:6px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;"

                    events = events_by_day.get(day, [])
                    events_html = ""
                    for ev in events[:2]:
                        events_html += (
                            f'<div style="background:{ev["bg"]};border-left:3px solid {ev["color"]};'
                            f'border-radius:0 6px 6px 0;padding:4px 8px;font-size:0.7rem;'
                            f'color:{ev["color"]};margin-bottom:3px;white-space:nowrap;overflow:hidden;'
                            f'text-overflow:ellipsis;font-weight:700;" title="{ev["label"]} — {ev["client"]}">'
                            f'{ev["label"]}</div>'
                        )
                    if len(events) > 2:
                        events_html += f'<div style="font-size:0.68rem;color:#ffb84d;padding:2px 6px;font-weight:600;">+{len(events)-2} autres</div>'

                    cells_html += f'<div style="{cell_style}"><div style="{num_style}">{day}</div>{events_html}</div>'

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #0a1628, #0f1e30);border:1px solid rgba(79,142,247,0.2);border-radius:16px;padding:24px;margin-bottom:24px;box-shadow:0 4px 20px rgba(0,0,0,0.3);">
            <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin-bottom:12px;">
                {header_html}
            </div>
            <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;">
                {cells_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Légende améliorée
        st.markdown("""
        <div style="display:flex;gap:24px;margin-bottom:20px;padding:16px;background:rgba(13,30,48,0.4);border-radius:12px;border:1px solid rgba(255,255,255,0.06);">
            <div style="display:flex;align-items:center;gap:8px;font-size:0.85rem;color:#e8f0fe;font-weight:600;">
                <div style="width:14px;height:14px;border-radius:4px;background:#4f8ef7;box-shadow:0 2px 6px rgba(79,142,247,0.4);"></div> En cours
            </div>
            <div style="display:flex;align-items:center;gap:8px;font-size:0.85rem;color:#e8f0fe;font-weight:600;">
                <div style="width:14px;height:14px;border-radius:4px;background:#ff5c7a;box-shadow:0 2px 6px rgba(255,92,122,0.4);"></div> En retard
            </div>
            <div style="display:flex;align-items:center;gap:8px;font-size:0.85rem;color:#e8f0fe;font-weight:600;">
                <div style="width:14px;height:14px;border-radius:4px;background:#00d68f;box-shadow:0 2px 6px rgba(0,214,143,0.4);"></div> Terminé
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not df_month.empty:
            st.caption(f"{len(df_month)} chantier(s) ce mois")
            detail_cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_DATE_DEBUT, COL_DATE_FIN, COL_MONTANT] if c]
            show_table(df_month[detail_cols].reset_index(drop=True), "cal_detail")

    # ════════════════════════════════════════════════════════════════
    # VUE GANTT
    # ════════════════════════════════════════════════════════════════
    elif view_mode == "📊 Gantt":
        show_all_gantt = st.toggle("Inclure les terminés", value=False, key="gantt_all")
        df_gantt = df_plan.copy()
        if not show_all_gantt:
            df_gantt = df_gantt[df_gantt["_statut_code"] != "termine"]

        if df_gantt.empty:
            st.info("Aucun chantier à afficher.")
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
            fig_gantt.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickformat="%d %b", tickfont_color="#6b84a3")
            fig_gantt.update_traces(marker_line_width=0, opacity=0.9)
            fig_gantt.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,30,48,0.6)",
                font_color="#e8f0fe", font_family="DM Sans",
                title=None, xaxis_title="", yaxis_title="",
                height=max(380, len(df_gantt_sorted) * 42 + 80),
                legend=dict(bgcolor="rgba(13,30,48,0.8)", bordercolor="rgba(255,255,255,0.08)", borderwidth=1, font_color="#6b84a3", title_text=""),
                margin=dict(t=20, b=20, l=10, r=10),
                bargap=0.25,
            )
            with st.container(border=True):
                st.plotly_chart(fig_gantt, use_container_width=True)

            with st.expander("📋 Détail", expanded=False):
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
            st.info("Aucun chantier correspondant.")
        else:
            df_list["_mois_str"] = df_list["_start"].dt.strftime("%B %Y").str.capitalize()
            df_list["_mois_ord"] = df_list["_start"].dt.to_period("M")

            color_map  = {"en-cours": "#4f8ef7", "retard": "#ff5c7a", "termine": "#00d68f"}
            bg_map     = {"en-cours": "rgba(79,142,247,0.08)", "retard": "rgba(255,92,122,0.08)", "termine": "rgba(0,214,143,0.08)"}
            label_map  = {"en-cours": "En cours", "retard": "En retard", "termine": "Terminé"}
            border_map = {"en-cours": "rgba(79,142,247,0.3)", "retard": "rgba(255,92,122,0.3)", "termine": "rgba(0,214,143,0.3)"}

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

                    st.markdown(f"""
                    <div style="background:{bg};border:1px solid {border};border-left:3px solid {color};border-radius:10px;padding:14px 18px;margin-bottom:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:0.95rem;color:#e8f0fe;margin-bottom:3px;">{chantier}</div>
                                <div style="font-size:0.8rem;color:#6b84a3;">
                                    👤 {client}{"  •  📍 " + adresse if adresse and adresse != "nan" else ""}
                                </div>
                                <div style="margin-top:8px;">
                                    <span style="display:inline-block;padding:2px 10px;border-radius:99px;font-size:0.72rem;font-weight:700;background:rgba(255,255,255,0.05);color:{color};border:1px solid {border};">{label}</span>
                                    <span style="font-size:0.75rem;color:#3d5473;margin-left:8px;">{duree} jour(s)</span>
                                </div>
                            </div>
                            <div style="text-align:right;flex-shrink:0;">
                                <div style="font-weight:700;color:{color};font-size:1rem;">{montant}</div>
                                <div style="font-size:0.78rem;color:#6b84a3;margin-top:4px;">📅 {debut}</div>
                                <div style="font-size:0.78rem;color:#6b84a3;">→ {fin}</div>
                            </div>
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
    drop_cols = ["_montant","_signe","_fact_fin","_pv","_acompte1","_acompte2","_reste",
                 "_statut_ch","_start","_end","_statut","_statut_code","_mois_str","_mois_ord"]
    show_table(d.drop(columns=drop_cols, errors="ignore").reset_index(drop=True), "all")

