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
from auth import check_login, logout, admin_panel, get_user_credentials

st.set_page_config(
    page_title="Florian AI Bâtiment – ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── FONCTION DE CALCUL DE PLANNING ──────────────────────────────────────────
def calculer_date_fin(date_debut_obj, duree_jours):
    try:
        date_fin = date_debut_obj + timedelta(days=int(duree_jours))
        return date_fin.strftime('%d/%m/%Y')
    except:
        return ""

# ── CSS REVISITÉ (Design Florian original) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-app: #0f172a;       /* Slate 900 */
    --bg-surface: #1e293b;   /* Slate 800 */
    --bg-sidebar: #0b1120;   /* Slate 950 */
    --text-main: #f8fafc;    /* Slate 50 */
    --text-muted: #94a3b8;   /* Slate 400 */
    --primary: #3b82f6;      /* Blue 500 */
    --success: #10b981;      /* Emerald 500 */
    --warning: #f59e0b;      /* Amber 500 */
    --danger: #ef4444;       /* Red 500 */
    --border: #334155;       /* Slate 700 */
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-app) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text-main);
}

[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border);
}

h1, h2, h3 { font-weight: 700 !important; letter-spacing: -0.025em; }

[data-testid="stMetric"] {
    background-color: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
    border: 1px solid var(--border) !important;
    background-color: var(--bg-surface) !important;
    color: var(--text-main) !important;
}

.stTextInput input, .stNumberInput input, .stSelectbox select {
    background-color: #0f172a80 !important; 
    border-radius: 6px !important;
    border: 1px solid var(--border) !important;
    color: white !important;
}

.refresh-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: var(--success);
    animation: pulse 2s infinite; margin-right: 6px;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ======= MENU NAVIGATION ======= */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child { display: none !important; }
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    padding: 12px 16px;
    background-color: transparent;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 4px;
    transition: all 0.2s ease;
    width: 100%;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    background-color: var(--primary) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ──
if not check_login():
    st.stop()

# ── Config Google Sheets ──
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_worksheet(username: str, tab_name: str):
    sheet_name, gsa_json = get_user_credentials(username)
    if not sheet_name or not gsa_json: return None, "Credentials non configurés."
    try:
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(sheet_name)
        ws = sh.worksheet(tab_name)
        return ws, None
    except Exception as e: return None, str(e)

@st.cache_data(ttl=30, show_spinner=False)
def get_sheet_data(username: str):
    try:
        sheet_name, gsa_json = get_user_credentials(username)
        if not sheet_name or not gsa_json: return pd.DataFrame(), "Credentials non configurés."
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(sheet_name)
        try: ws = sh.worksheet("suivie")
        except: ws = sh.sheet1
        all_values = ws.get_all_values()
        if not all_values: return pd.DataFrame(), None
        df = pd.DataFrame(all_values[1:], columns=all_values[0])
        return df, None
    except Exception as e: return pd.DataFrame(), str(e)

# ── Helpers ──
def clean_amount(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).replace("\xa0","").replace("\u202f","").replace(" ","").replace(",",".").replace("€","").strip()
    try: return float(s)
    except: return 0.0

def is_checked(val):
    s = str(val).strip()
    return s in {"✅","✓","✔","TRUE","true","oui","Oui","OUI","1"}

def fcol(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in str(c).strip().lower(): return c
    return None

def fmt(v): return f"{v:,.0f} €".replace(",", " ")

def show_table(dataframe, key_suffix=""):
    total = len(dataframe)
    if total == 0:
        st.info("Aucun dossier trouvé.")
        return
    show_all = st.session_state.get(f"show_all_{key_suffix}", False)
    displayed = dataframe if show_all else dataframe.head(100)
    st.dataframe(displayed, use_container_width=True, hide_index=True)

# ── Sidebar ──
with st.sidebar:
    user = st.session_state.get("username", "")
    role = st.session_state.get("role", "viewer")
    pages = ["📊 Vue Générale", "📋 Devis", "💶 Factures & Paiements", "🏗️ Chantiers", "📁 Tous les dossiers", "📝 Éditeur Google Sheet"]
    if role == "admin": pages.append("👥 Utilisateurs")
    page = st.radio("Navigation", pages, label_visibility="collapsed")
    if st.button("🔄 Forcer l'actualisation", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 Se déconnecter", use_container_width=True):
        logout()
        st.rerun()

if page == "👥 Utilisateurs":
    admin_panel()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ÉDITEUR (AVEC NOUVEAU GÉNÉRATEUR DE PLANNING)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Éditeur Google Sheet":
    st.title("📝 Éditeur Google Sheet")
    tab_presta, tab_catalogue, tab_planning = st.tabs(["📋 Prestations", "🗂️ Catalogue", "📅 CRÉER UN PLANNING"])

    with tab_presta:
        st.write("Gestion des prestations...")
        # Ici ton code d'édition des prestations d'origine

    with tab_catalogue:
        st.write("Gestion du catalogue...")
        # Ici ton code d'édition du catalogue d'origine

    with tab_planning:
        st.subheader("🏗️ Générer un nouveau chantier (Suivi automatique)")
        with st.form("form_planning_florian"):
            c1, c2 = st.columns(2)
            with c1:
                p_client = st.text_input("Client")
                p_objet = st.text_input("Objet / Chantier")
                p_devis = st.text_input("N° Devis", value="FA-2026-")
                p_montant = st.text_input("Montant TTC (€)")
            with c2:
                p_addr = st.text_input("Addresse du chantier")
                p_debut = st.date_input("Date de début")
                p_duree = st.number_input("Durée du chantier (en jours)", min_value=1, value=10)
                p_mod = st.selectbox("Modalité", ["Acompte / Solde", "Comptant", "Échelonné"])
            
            if st.form_submit_button("⚡ Créer le planning et envoyer au Sheet"):
                date_fin_calc = calculer_date_fin(p_debut, p_duree)
                # Respect des 22 colonnes de ton fichier suivie.csv
                ligne_complete = [
                    p_client, p_objet, p_devis, p_montant, "✅", "✅", 
                    "", "", "", # Relances
                    "", "", "", # Factures
                    "", # PV
                    p_mod, "Oui", "En cours", "", "✅", 
                    p_addr, datetime.now().strftime('%d/%m/%Y'),
                    p_debut.strftime('%d/%m/%Y'),
                    date_fin_calc
                ]
                ws, err = get_worksheet(user, "suivie")
                if not err:
                    ws.append_row(ligne_complete, value_input_option="USER_ENTERED")
                    st.success(f"✅ Chantier ajouté ! Fin prévue : {date_fin_calc}")
                    st.cache_data.clear()
                    st.rerun()

# ── CHARGEMENT DONNÉES SUIVIE (Pour les autres pages) ──
df_raw, error = get_sheet_data(user)
if error or df_raw.empty: st.stop()
df = df_raw.copy()

# Extraction des colonnes
COL_CLIENT = fcol(df, "client")
COL_CHANTIER = fcol(df, "objet", "chantier")
COL_DATE_DEBUT = fcol(df, "début", "debut")
COL_DATE_FIN = fcol(df, "fin")
COL_PV = fcol(df, "pv")
COL_MONTANT = fcol(df, "montant")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : CHANTIERS (AVEC GANTT)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Chantiers":
    st.title("🏗️ Suivi des Chantiers & Planning")
    t1, t2, t3 = st.tabs(["🟡 Travaux en cours", "✅ Livrés", "📅 PLANNING GRAPHIQUE"])

    with t3:
        st.subheader("Diagramme de Gantt")
        d_plan = df.copy()
        d_plan["_start"] = pd.to_datetime(d_plan[COL_DATE_DEBUT], dayfirst=True, errors='coerce')
        d_plan["_end"] = pd.to_datetime(d_plan[COL_DATE_FIN], dayfirst=True, errors='coerce')
        d_plan = d_plan.dropna(subset=["_start", "_end"])
        if not d_plan.empty:
            fig = px.timeline(d_plan, x_start="_start", x_end="_end", y=COL_CHANTIER, color=COL_CLIENT)
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : VUE GÉNÉRALE (Garder tes stats d'origine)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Vue Générale":
    st.title("📊 Tableau de Bord")
    # Calculs métriques originaux
    df["_val"] = df[COL_MONTANT].apply(clean_amount)
    total_ca = df["_val"].sum()
    st.metric("Volume CA Global", fmt(total_ca))
    # ... Tes graphiques Plotly d'origine ici ...

# ── Auto-refresh ──
time.sleep(30)
st.rerun()
