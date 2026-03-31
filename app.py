import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
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

# ── CSS REVISITÉ (Design plus fluide, moderne et aéré) ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-app: #0f172a;       /* Slate 900 - Fond principal plus profond */
    --bg-surface: #1e293b;   /* Slate 800 - Cartes et éléments */
    --bg-sidebar: #0b1120;   /* Slate 950 - Sidebar très sombre */
    --text-main: #f8fafc;    /* Slate 50 - Texte principal */
    --text-muted: #94a3b8;   /* Slate 400 - Texte secondaire */
    --primary: #3b82f6;      /* Blue 500 - Couleur principale d'accentuation */
    --success: #10b981;      /* Emerald 500 - Succès/Validation */
    --danger: #ef4444;       /* Red 500 - Suppression */
    --border: #334155;       /* Slate 700 - Bordures discrètes */
}

/* Base de l'application */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-app) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text-main);
}

[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border);
}

/* Titres plus élégants */
h1, h2, h3 { 
    font-weight: 700 !important; 
    letter-spacing: -0.025em;
}

/* Cartes Métriques (KPIs) - Look Dashboard Pro */
[data-testid="stMetric"] {
    background-color: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
}
[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-size: 0.85rem;
    font-weight: 500;
}
[data-testid="stMetricValue"] {
    color: var(--text-main) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* Onglets (Tabs) plus lisibles */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 4px 4px 0px 0px;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom-color: var(--primary) !important;
}

/* Boutons d'action */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
    border: 1px solid var(--border) !important;
    background-color: var(--bg-surface) !important;
    color: var(--text-main) !important;
}
.stButton > button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
}

/* Inputs form */
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background-color: #0f172a80 !important; /* Lége transparence */
    border-radius: 6px !important;
    border: 1px solid var(--border) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 1px var(--primary) !important;
}

/* Dot de synchronisation */
.refresh-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: var(--success);
    animation: pulse 2s infinite; margin-right: 6px;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ======= SUPER MENU DE NAVIGATION LATÉRAL ======= */
/* Cache le cercle des boutons radio */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
/* Style des boutons du menu */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    padding: 12px 16px;
    background-color: transparent;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 4px;
    border: 1px solid transparent;
    transition: all 0.2s ease;
    width: 100%;
}
/* Survol des boutons */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
    background-color: var(--bg-surface);
    border-color: var(--border);
}
/* Bouton actif / Sélectionné */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
}
/* Alignement du texte */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p {
    margin: 0;
    font-size: 1rem;
}
/* Espacement du conteneur radio */
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {
    gap: 4px;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()

# ── Config Google Sheets ───────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_gc(username: str):
    _, gsa_json = get_user_credentials(username)
    if not gsa_json:
        return None, "GOOGLE_SERVICE_ACCOUNT non configuré."
    creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
    return gspread.authorize(creds), None

def get_worksheet(username: str, tab_name: str):
    sheet_name, gsa_json = get_user_credentials(username)
    if not sheet_name or not gsa_json:
        return None, "Credentials non configurés."
    try:
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        gc    = gspread.authorize(creds)
        sh    = gc.open(sheet_name)
        ws    = sh.worksheet(tab_name)
        return ws, None
    except Exception as e:
        return None, str(e)

# ── Cache données suivie ───────────────────────────────────────────────────────
@st.cache_resource(ttl=30)
def get_sheet_data(username: str):
    try:
        sheet_name, gsa_json = get_user_credentials(username)
        if not sheet_name or not gsa_json:
            return pd.DataFrame(), "Credentials non configurés."
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        gc    = gspread.authorize(creds)
        sh    = gc.open(sheet_name)
        try:
            ws = sh.worksheet("suivie")
        except Exception:
            ws = sh.sheet1

        all_values = ws.get_all_values()
        if not all_values:
            return pd.DataFrame(), None

        raw_headers = all_values[0]
        seen = {}
        clean_headers = []
        for i, h in enumerate(raw_headers):
            h = h.strip()
            if h == "":
                h = f"_col_{i}"
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 0
            clean_headers.append(h)

        rows  = all_values[1:]
        n     = len(clean_headers)
        padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
        df    = pd.DataFrame(padded, columns=clean_headers)
        df    = df.loc[:, ~df.columns.str.startswith("_col_")]
        df    = df.replace("", pd.NA).dropna(how="all").fillna("")
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ── Helpers ────────────────────────────────────────────────────────────────────
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
    if s in {"✅","✓","✔","TRUE","true","oui","Oui","OUI","1","x","X","yes","Yes"}:
        return True
    return "✅" in s

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
    show_all  = st.session_state.get(f"show_all_{key_suffix}", False)
    displayed = dataframe if show_all else dataframe.head(LIMIT)
    st.dataframe(displayed, use_container_width=True, hide_index=True)
    if total > LIMIT:
        if not show_all:
            st.caption(f"Affichage des {LIMIT} premiers sur {total}.")
            if st.button(f"📂 Voir les {total-LIMIT} suivants", key=f"btn_more_{key_suffix}"):
                st.session_state[f"show_all_{key_suffix}"] = True
                st.rerun()
        else:
            st.caption(f"{total} dossiers affichés.")
            if st.button("🔼 Réduire l'affichage", key=f"btn_less_{key_suffix}"):
                st.session_state[f"show_all_{key_suffix}"] = False
                st.rerun()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=130)
    else:
        st.markdown("<div style='text-align:center;font-size:2.5rem;padding:10px 0;color:#3b82f6;'>⚡</div>", unsafe_allow_html=True)

    user = st.session_state.get("username", "")
    role = st.session_state.get("role", "viewer")

    st.markdown("<br>", unsafe_allow_html=True)
    
    pages = [
        "📊 Vue Générale", "📋 Devis",
        "💶 Factures & Paiements", "🏗️ Chantiers",
        "📁 Tous les dossiers", "📝 Éditeur Google Sheet",
    ]
    if role == "admin":
        pages.append("👥 Utilisateurs")

    # On utilise st.radio qui affiche tous les choix d'un coup, 
    # mais le CSS plus haut le transforme en boutons modernes !
    page = st.radio("Navigation", pages, label_visibility="collapsed")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<span class="refresh-dot"></span><span style="font-size:0.8rem;color:#94a3b8;">Synchronisation auto (30s)</span>', unsafe_allow_html=True)
    if st.button("🔄 Forcer l'actualisation", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
        
    st.divider()
    st.markdown(f'<div style="font-size:0.85rem;color:#94a3b8;text-align:center;">Connecté en tant que<br><b style="color:#f8fafc;font-size:1rem;">{user}</b> ({role})</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Se déconnecter", use_container_width=True):
        logout()
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ADMIN USERS
# ══════════════════════════════════════════════════════════════════════════════
if page == "👥 Utilisateurs":
    admin_panel()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ÉDITEUR GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Éditeur Google Sheet":
    st.title("📝 Éditeur Google Sheet")
    st.markdown("Gérez votre base de données en temps réel directement depuis cette interface.")

    tab_presta, tab_catalogue = st.tabs(["📋 Base de données Prestations", "🗂️ Base de données Catalogue"])

    # ── ONGLET PRESTATIONS ─────────────────────────────────────────────────────
    with tab_presta:
        PRESTA_COLS = [
            "categorie", "Type de poste", "Sous-prestation", "Description",
            "Prix MO HT", "Prix Fourn. HT", "Marge (%)", "Quantité", "Total HT"
        ]
        CATEGORIES  = ["Salle de bain", "Cuisine", "Chambre", "Salon", "WC / Toilettes", "Entrée / Couloir", "Garage", "Cave / Sous-sol", "Combles / Grenier", "Buanderie", "Bureau / Bibliothèque", "Terrasse / Balcon", "Jardin / Extérieur", "Façade", "Toiture", "Escalier", "Piscine", "Véranda / Pergola", "Parties communes", "Local technique", "Autre"]
        TYPES_POSTE = ["Préparation / Démolition", "Gros œuvre", "Charpente / Couverture", "Isolation", "Plâtrerie / Cloisons", "Menuiserie intérieure", "Menuiserie extérieure", "Plomberie / Sanitaire", "Chauffage / VMC / Climatisation", "Électricité", "Domotique / Alarme", "Carrelage / Revêtement sol", "Peinture / Revêtement mur", "Parquet / Stratifié", "Faïence", "Finition", "Installation", "Mobilier / Agencement", "Serrurerie / Métallerie", "Terrassement / VRD", "Maçonnerie", "Enduit / Ravalement", "Étanchéité / Hydrofuge", "Nettoyage / Évacuation", "Autre"]

        def _dedup(headers):
            seen, out = {}, []
            for h in headers:
                h = h.strip() or "_col"
                if h in seen:
                    seen[h] += 1
                    out.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 0
                    out.append(h)
            return out

        @st.cache_resource(ttl=10)
        def load_presta(u):
            ws, err = get_worksheet(u, "Feuille 1")
            if err: return None, err, pd.DataFrame()
            try:
                all_vals = ws.get_all_values()
                if not all_vals: return ws, None, pd.DataFrame()
                headers = _dedup(all_vals[0])
                rows    = all_vals[1:]
                n       = len(headers)
                padded  = [r + [""]*(n-len(r)) if len(r)<n else r[:n] for r in rows]
                df      = pd.DataFrame(padded, columns=headers)
                df      = df.replace("", pd.NA).dropna(how="all").fillna("")
                useful = [c for c in df.columns if not c.startswith("_col")]
                return ws, None, df[useful]
            except Exception as e:
                return None, str(e), pd.DataFrame()

        ws_p, err_p, df_p = load_presta(user)

        if err_p:
            st.error(f"❌ {err_p}")
        else:
            # Création de sous-onglets pour une UX fluide
            sub_p_view, sub_p_add, sub_p_edit, sub_p_del = st.tabs(["👁️ Voir les données", "➕ Ajouter une ligne", "✏️ Modifier", "🗑️ Supprimer"])

            # -- VUE --
            with sub_p_view:
                st.caption(f"Base de données actuelle ({len(df_p)} lignes)")
                with st.container(border=True):
                    search_p = st.text_input("🔍 Rechercher une prestation", placeholder="Taper un mot-clé...", key="search_presta")
                    df_show  = df_p.copy()
                    if search_p:
                        mask = pd.Series([False]*len(df_show), index=df_show.index)
                        for c in df_show.columns:
                            mask |= df_show[c].astype(str).str.contains(search_p, case=False, na=False)
                        df_show = df_show[mask]
                    show_table(df_show.reset_index(drop=True), "presta_view")

            # -- AJOUTER --
            with sub_p_add:
                st.subheader("Nouvelle prestation")
                with st.container(border=True):
                    c_mo, c_fourn, c_marge, c_qte = st.columns(4)
                    with c_mo: val_mo = st.number_input("Prix MO HT", min_value=0.0, value=0.0, step=10.0, key="add_mo")
                    with c_fourn: val_fourn = st.number_input("Prix Fourn. HT", min_value=0.0, value=0.0, step=10.0, key="add_fourn")
                    with c_marge: val_marge = st.number_input("Marge (%)", min_value=0.0, value=30.0, step=5.0, key="add_marge")
                    with c_qte: val_qte = st.number_input("Quantité", min_value=1.0, value=1.0, step=1.0, key="add_qte")
                    
                    calcul_total = (val_mo + (val_fourn * (1 + (val_marge / 100)))) * val_qte
                    st.success(f"💶 **Total HT Calculé : {calcul_total:.2f} €**")

                    with st.form("form_add_presta"):
                        headers_p = list(df_p.columns) if len(df_p) > 0 else PRESTA_COLS
                        inputs_p  = {}
                        cols1     = st.columns(3)
                        for i, h in enumerate(headers_p):
                            hl = h.lower()
                            if "mo ht" in hl or "fourn. ht" in hl or "marge" in hl or "quantit" in hl or "total ht" in hl:
                                continue
                            with cols1[i % 3]:
                                if "categ" in hl or "colonne" in hl:
                                    inputs_p[h] = st.selectbox(h, CATEGORIES, key=f"add_p_{h}")
                                elif "type" in hl and "poste" in hl:
                                    inputs_p[h] = st.selectbox(h, TYPES_POSTE, key=f"add_p_{h}")
                                else:
                                    inputs_p[h] = st.text_input(h, key=f"add_p_{h}")
                                    
                        submit_add_p = st.form_submit_button("✅ Ajouter au tableur", use_container_width=True)

                    if submit_add_p:
                        for h in headers_p:
                            hl = h.lower()
                            if "mo ht" in hl: inputs_p[h] = str(val_mo)
                            elif "fourn. ht" in hl: inputs_p[h] = str(val_fourn)
                            elif "marge" in hl: inputs_p[h] = str(val_marge)
                            elif "quantit" in hl: inputs_p[h] = str(val_qte)
                            elif "total ht" in hl: inputs_p[h] = str(round(calcul_total, 2))

                        try:
                            ws_p2, err2 = get_worksheet(user, "Feuille 1")
                            if err2: st.error(err2)
                            else:
                                new_row = [inputs_p.get(h, "") for h in headers_p]
                                next_row = len(df_p) + 2
                                ws_p2.insert_row(new_row, index=next_row, value_input_option="USER_ENTERED")
                                st.cache_resource.clear()
                                st.success("✅ Ligne ajoutée avec succès !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            # -- MODIFIER --
            with sub_p_edit:
                st.subheader("Modifier une prestation existante")
                if len(df_p) == 0:
                    st.info("Aucune ligne à modifier.")
                else:
                    headers_p2 = list(df_p.columns)
                    row_labels = [f"Ligne {i+2} — {df_p.iloc[i, 0]} / {df_p.iloc[i, 1] if len(headers_p2)>1 else ''}" for i in range(len(df_p))]
                    sel_idx = st.selectbox("Sélectionner la ligne", range(len(df_p)), format_func=lambda i: row_labels[i], key="sel_mod_presta")

                    with st.container(border=True):
                        cur_mo = 0.0; cur_fourn = 0.0; cur_marge = 30.0; cur_qte = 1.0
                        for h in headers_p2:
                            hl = h.lower()
                            val = df_p.iloc[sel_idx][h]
                            if "mo ht" in hl: cur_mo = clean_amount(val)
                            elif "fourn. ht" in hl: cur_fourn = clean_amount(val)
                            elif "marge" in hl: cur_marge = clean_amount(val)
                            elif "quantit" in hl: cur_qte = clean_amount(val)
                        
                        c_mo_m, c_fourn_m, c_marge_m, c_qte_m = st.columns(4)
                        with c_mo_m: mod_mo = st.number_input("Prix MO HT", min_value=0.0, value=float(cur_mo), step=10.0, key="mod_mo")
                        with c_fourn_m: mod_fourn = st.number_input("Prix Fourn. HT", min_value=0.0, value=float(cur_fourn), step=10.0, key="mod_fourn")
                        with c_marge_m: mod_marge = st.number_input("Marge (%)", min_value=0.0, value=float(cur_marge), step=5.0, key="mod_marge")
                        with c_qte_m: mod_qte = st.number_input("Quantité", min_value=1.0, value=float(cur_qte) if float(cur_qte) > 0 else 1.0, step=1.0, key="mod_qte")

                        mod_calcul_total = (mod_mo + (mod_fourn * (1 + (mod_marge / 100)))) * mod_qte
                        st.success(f"💶 **Nouveau Total HT : {mod_calcul_total:.2f} €**")

                        with st.form("form_mod_presta"):
                            mod_inputs = {}
                            cols2 = st.columns(3)
                            for i, h in enumerate(headers_p2):
                                hl = h.lower()
                                if "mo ht" in hl or "fourn. ht" in hl or "marge" in hl or "quantit" in hl or "total ht" in hl:
                                    continue
                                with cols2[i % 3]:
                                    cur_val = str(df_p.iloc[sel_idx][h])
                                    if "categ" in hl or "colonne" in hl:
                                        idx_cat = CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0
                                        mod_inputs[h] = st.selectbox(h, CATEGORIES, index=idx_cat, key=f"mod_p_{h}")
                                    elif "type" in hl and "poste" in hl:
                                        idx_tp = TYPES_POSTE.index(cur_val) if cur_val in TYPES_POSTE else 0
                                        mod_inputs[h] = st.selectbox(h, TYPES_POSTE, index=idx_tp, key=f"mod_p_{h}")
                                    else:
                                        mod_inputs[h] = st.text_input(h, value=cur_val, key=f"mod_p_{h}")
                                        
                            submit_mod_p = st.form_submit_button("💾 Enregistrer les modifications", use_container_width=True)

                        if submit_mod_p:
                            for h in headers_p2:
                                hl = h.lower()
                                if "mo ht" in hl: mod_inputs[h] = str(mod_mo)
                                elif "fourn. ht" in hl: mod_inputs[h] = str(mod_fourn)
                                elif "marge" in hl: mod_inputs[h] = str(mod_marge)
                                elif "quantit" in hl: mod_inputs[h] = str(mod_qte)
                                elif "total ht" in hl: mod_inputs[h] = str(round(mod_calcul_total, 2))

                            try:
                                ws_p3, err3 = get_worksheet(user, "Feuille 1")
                                if err3: st.error(err3)
                                else:
                                    sheet_row = sel_idx + 2 
                                    for col_idx, h in enumerate(headers_p2, start=1):
                                        ws_p3.update_cell(sheet_row, col_idx, mod_inputs[h])
                                    st.cache_resource.clear()
                                    st.success("✅ Ligne modifiée avec succès !")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

            # -- SUPPRIMER --
            with sub_p_del:
                st.subheader("Supprimer une prestation")
                if len(df_p) == 0:
                    st.info("Aucune ligne à supprimer.")
                else:
                    headers_p3 = list(df_p.columns)
                    row_labels2 = [f"Ligne {i+2} — {df_p.iloc[i, 0]} / {df_p.iloc[i, 1] if len(headers_p3)>1 else ''}" for i in range(len(df_p))]
                    del_idx = st.selectbox("Sélectionner la ligne à détruire", range(len(df_p)), format_func=lambda i: row_labels2[i], key="sel_del_presta")
                    
                    with st.container(border=True):
                        st.warning(f"⚠️ Action irréversible. Vous allez supprimer :\n\n**{row_labels2[del_idx]}**")
                        if st.button("🗑️ Confirmer la suppression", key="btn_del_presta"):
                            try:
                                ws_p4, err4 = get_worksheet(user, "Feuille 1")
                                if err4: st.error(err4)
                                else:
                                    ws_p4.delete_rows(del_idx + 2)
                                    st.cache_resource.clear()
                                    st.success("✅ Ligne supprimée !")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    # ── ONGLET CATALOGUE ───────────────────────────────────────────────────────
    with tab_catalogue:
        CATA_COLS = ["Catégorie", "Article", "Description", "Prix Achat HT", "% Marge", "Prix Vente HT"]
        CATEGORIES_CATA = ["Salle de bain", "Cuisine", "Chambre", "Salon", "WC / Toilettes", "Entrée / Couloir", "Garage", "Cave / Sous-sol", "Combles / Grenier", "Buanderie", "Bureau / Bibliothèque", "Terrasse / Balcon", "Jardin / Extérieur", "Façade", "Toiture", "Escalier", "Piscine", "Véranda / Pergola", "Parties communes", "Local technique", "Autre"]

        @st.cache_resource(ttl=10)
        def load_catalogue(u):
            ws, err = get_worksheet(u, "catalogue")
            if err: return None, err, pd.DataFrame()
            try:
                all_vals = ws.get_all_values()
                if not all_vals: return ws, None, pd.DataFrame()
                headers = _dedup(all_vals[0])
                rows    = all_vals[1:]
                n       = len(headers)
                padded  = [r + [""]*(n-len(r)) if len(r)<n else r[:n] for r in rows]
                df      = pd.DataFrame(padded, columns=headers)
                df      = df.replace("", pd.NA).dropna(how="all").fillna("")
                return ws, None, df
            except Exception as e:
                return None, str(e), pd.DataFrame()

        ws_c, err_c, df_c = load_catalogue(user)

        if err_c:
            st.error(f"❌ {err_c}")
        else:
            sub_c_view, sub_c_add, sub_c_edit, sub_c_del = st.tabs(["👁️ Voir les articles", "➕ Ajouter un article", "✏️ Modifier", "🗑️ Supprimer"])

            # -- VUE --
            with sub_c_view:
                st.caption(f"Catalogue actuel ({len(df_c)} articles)")
                with st.container(border=True):
                    search_c = st.text_input("🔍 Rechercher dans le catalogue", placeholder="Taper un mot-clé...", key="search_cata")
                    df_show_c = df_c.copy()
                    if search_c:
                        mask = pd.Series([False]*len(df_show_c), index=df_show_c.index)
                        for c in df_show_c.columns:
                            mask |= df_show_c[c].astype(str).str.contains(search_c, case=False, na=False)
                        df_show_c = df_show_c[mask]
                    show_table(df_show_c.reset_index(drop=True), "cata_view")

            # -- AJOUTER --
            with sub_c_add:
                st.subheader("Nouvel article")
                with st.container(border=True):
                    c_achat, c_marge_c = st.columns(2)
                    with c_achat: val_achat = st.number_input("Prix Achat HT", min_value=0.0, value=0.0, step=10.0, key="add_c_achat")
                    with c_marge_c: val_marge_c = st.number_input("% Marge", min_value=0.0, value=30.0, step=5.0, key="add_c_marge")
                    
                    calcul_vente = val_achat * (1 + (val_marge_c / 100))
                    st.success(f"💶 **Prix Vente HT Calculé : {calcul_vente:.2f} €**")

                    with st.form("form_add_cata"):
                        headers_c  = list(df_c.columns) if len(df_c) > 0 else CATA_COLS
                        inputs_c   = {}
                        cols3      = st.columns(3)
                        
                        for i, h in enumerate(headers_c):
                            hl = h.lower()
                            if "achat ht" in hl or "marge" in hl or "vente ht" in hl:
                                continue
                            with cols3[i % 3]:
                                if "catégorie" in hl or "categorie" in hl:
                                    inputs_c[h] = st.selectbox(h, CATEGORIES_CATA, key=f"add_c_{h}")
                                else:
                                    inputs_c[h] = st.text_input(h, key=f"add_c_{h}")
                                    
                        submit_add_c = st.form_submit_button("✅ Ajouter au catalogue", use_container_width=True)

                    if submit_add_c:
                        for h in headers_c:
                            hl = h.lower()
                            if "achat ht" in hl: inputs_c[h] = str(val_achat)
                            elif "marge" in hl: inputs_c[h] = str(val_marge_c)
                            elif "vente ht" in hl: inputs_c[h] = str(round(calcul_vente, 2))

                        try:
                            ws_c2, err_c2 = get_worksheet(user, "catalogue")
                            if err_c2: st.error(err_c2)
                            else:
                                new_row = [inputs_c.get(h, "") for h in headers_c]
                                next_row_c = len(df_c) + 2
                                ws_c2.insert_row(new_row, index=next_row_c, value_input_option="USER_ENTERED")
                                st.cache_resource.clear()
                                st.success("✅ Article ajouté avec succès !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            # -- MODIFIER --
            with sub_c_edit:
                st.subheader("Modifier un article")
                if len(df_c) == 0:
                    st.info("Aucun article à modifier.")
                else:
                    headers_c2  = list(df_c.columns)
                    art_labels  = [f"Ligne {i+2} — {df_c.iloc[i, 0]} / {df_c.iloc[i, 1] if len(headers_c2)>1 else ''}" for i in range(len(df_c))]
                    sel_idx_c   = st.selectbox("Sélectionner l'article", range(len(df_c)), format_func=lambda i: art_labels[i], key="sel_mod_cata")

                    with st.container(border=True):
                        cur_achat = 0.0; cur_marge_c = 30.0
                        for h in headers_c2:
                            hl = h.lower()
                            val = df_c.iloc[sel_idx_c][h]
                            if "achat ht" in hl: cur_achat = clean_amount(val)
                            elif "marge" in hl: cur_marge_c = clean_amount(val)
                        
                        c_achat_m, c_marge_m = st.columns(2)
                        with c_achat_m: mod_achat = st.number_input("Prix Achat HT", min_value=0.0, value=float(cur_achat), step=10.0, key="mod_c_achat")
                        with c_marge_m: mod_marge_c = st.number_input("% Marge", min_value=0.0, value=float(cur_marge_c), step=5.0, key="mod_c_marge")

                        mod_calcul_vente = mod_achat * (1 + (mod_marge_c / 100))
                        st.success(f"💶 **Nouveau Prix Vente HT : {mod_calcul_vente:.2f} €**")

                        with st.form("form_mod_cata"):
                            mod_inputs_c = {}
                            cols4        = st.columns(3)
                            for i, h in enumerate(headers_c2):
                                hl = h.lower()
                                if "achat ht" in hl or "marge" in hl or "vente ht" in hl:
                                    continue
                                with cols4[i % 3]:
                                    cur_val = str(df_c.iloc[sel_idx_c][h])
                                    if "catégorie" in hl or "categorie" in hl:
                                        idx_cat = CATEGORIES_CATA.index(cur_val) if cur_val in CATEGORIES_CATA else 0
                                        mod_inputs_c[h] = st.selectbox(h, CATEGORIES_CATA, index=idx_cat, key=f"mod_c_{h}")
                                    else:
                                        mod_inputs_c[h] = st.text_input(h, value=cur_val, key=f"mod_c_{h}")
                                        
                            submit_mod_c = st.form_submit_button("💾 Enregistrer les modifications", use_container_width=True)

                        if submit_mod_c:
                            for h in headers_c2:
                                hl = h.lower()
                                if "achat ht" in hl: mod_inputs_c[h] = str(mod_achat)
                                elif "marge" in hl: mod_inputs_c[h] = str(mod_marge_c)
                                elif "vente ht" in hl: mod_inputs_c[h] = str(round(mod_calcul_vente, 2))

                            try:
                                ws_c3, err_c3 = get_worksheet(user, "catalogue")
                                if err_c3: st.error(err_c3)
                                else:
                                    sheet_row_c = sel_idx_c + 2
                                    for col_idx, h in enumerate(headers_c2, start=1):
                                        ws_c3.update_cell(sheet_row_c, col_idx, mod_inputs_c[h])
                                    st.cache_resource.clear()
                                    st.success("✅ Article modifié avec succès !")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

            # -- SUPPRIMER --
            with sub_c_del:
                st.subheader("Supprimer un article")
                if len(df_c) == 0:
                    st.info("Aucun article à supprimer.")
                else:
                    headers_c3  = list(df_c.columns)
                    art_labels2 = [f"Ligne {i+2} — {df_c.iloc[i, 0]} / {df_c.iloc[i, 1] if len(headers_c3)>1 else ''}" for i in range(len(df_c))]
                    del_idx_c   = st.selectbox("Sélectionner l'article à détruire", range(len(df_c)), format_func=lambda i: art_labels2[i], key="sel_del_cata")
                    
                    with st.container(border=True):
                        st.warning(f"⚠️ Action irréversible. Vous allez supprimer :\n\n**{art_labels2[del_idx_c]}**")
                        if st.button("🗑️ Confirmer la suppression", key="btn_del_cata"):
                            try:
                                ws_c4, err_c4 = get_worksheet(user, "catalogue")
                                if err_c4: st.error(err_c4)
                                else:
                                    ws_c4.delete_rows(del_idx_c + 2)
                                    st.cache_resource.clear()
                                    st.success("✅ Article supprimé !")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    st.stop()

# ── Chargement données suivie ──────────────────────────────────────────────────
df_raw, error = get_sheet_data(user)

if error:
    st.error(f"❌ Impossible de charger le Google Sheet : {error}")
    st.stop()
if df_raw.empty:
    st.warning("📭 Le Google Sheet est vide ou inaccessible.")
    st.stop()

df = df_raw.copy()

COL_CLIENT   = fcol(df, "client")
COL_CHANTIER = fcol(df, "objet", "chantier")
COL_NUM      = fcol(df, "n° devis", "n°", "num")
COL_MONTANT  = fcol(df, "montant")
COL_SIGN     = fcol(df, "devis signé", "signé")
COL_FACT_FIN = fcol(df, "facture finale", "finale", "final")
COL_PV       = fcol(df, "pv signé", "pv")
COL_STATUT   = fcol(df, "statut")
COL_DATE     = fcol(df, "date")
COL_MODALITE = fcol(df, "modalit")
COL_TVA      = fcol(df, "tva")
COL_RELANCE1 = fcol(df, "relance 1")
COL_RELANCE2 = fcol(df, "relance 2")
COL_RELANCE3 = fcol(df, "relance 3")
COL_ACOMPTE1 = fcol(df, "acompte 1")
COL_ACOMPTE2 = fcol(df, "acompte 2")
COL_RESERVE  = fcol(df, "réserve", "reserve")

df["_montant"]  = df[COL_MONTANT].apply(clean_amount)  if COL_MONTANT  else 0.0
df["_signe"]    = df[COL_SIGN].apply(is_checked)        if COL_SIGN     else False
df["_fact_fin"] = df[COL_FACT_FIN].apply(is_checked)   if COL_FACT_FIN else False
df["_pv"]       = df[COL_PV].apply(is_checked)          if COL_PV       else False

total_ca   = df["_montant"].sum()
nb_devis   = len(df)
nb_signes  = int(df["_signe"].sum())
nb_attente = nb_devis - nb_signes
nb_fact_ok = int(df["_fact_fin"].sum())
ca_signe   = df[df["_signe"]]["_montant"].sum()
ca_non_s   = df[~df["_signe"]]["_montant"].sum()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : VUE GÉNÉRALE
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Vue Générale":
    st.title("📊 Vue Générale")
    st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 CA Total TTC", fmt(total_ca))
    c2.metric("📋 Devis créés", nb_devis, f"{nb_signes} signés")
    c3.metric("⏳ En attente signature", nb_attente)
    c4.metric("🏁 Factures finales", nb_fact_ok)

    st.markdown("<br>", unsafe_allow_html=True)
    
    cl, cr = st.columns([3, 2])
    with cl:
        with st.container(border=True):
            if COL_DATE:
                d2 = df.copy()
                d2["_date"] = pd.to_datetime(d2[COL_DATE], dayfirst=True, errors="coerce")
                d2 = d2.dropna(subset=["_date"])
                if not d2.empty:
                    d2["_mois"] = d2["_date"].dt.to_period("M").astype(str)
                    cm = d2.groupby("_mois")["_montant"].sum().reset_index()
                    cm.columns = ["Mois", "CA (€)"]
                    fig = px.bar(cm, x="Mois", y="CA (€)", title="📈 Évolution du CA par mois",
                                 color_discrete_sequence=["#3b82f6"])
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font_color="#f8fafc", title_font_family="Inter",
                                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#334155"))
                    st.plotly_chart(fig, use_container_width=True)
    with cr:
        with st.container(border=True):
            pct  = int(nb_signes / nb_devis * 100) if nb_devis else 0
            fig2 = go.Figure(go.Pie(
                labels=["Signés", "En attente"],
                values=[max(nb_signes, 0), max(nb_attente, 0)],
                hole=0.65, marker_colors=["#10b981", "#334155"], textinfo="none",
            ))
            fig2.update_layout(
                title="📋 Taux de conversion devis", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#f8fafc", title_font_family="Inter", showlegend=True,
                legend=dict(font=dict(color="#94a3b8"), orientation="h", y=-0.1),
                annotations=[dict(text=f"<b>{pct}%</b>", x=0.5, y=0.5,
                                   font_size=32, showarrow=False, font_color="#f8fafc")],
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🕐 Derniers dossiers enregistrés")
    with st.container(border=True):
        cols_show = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_STATUT] if c]
        show_table(df[cols_show].tail(10).iloc[::-1] if cols_show else df.tail(10), "home")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Devis":
    st.title("📋 Gestion des Devis")
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE,
                         COL_RELANCE1, COL_RELANCE2, COL_RELANCE3, COL_STATUT] if c]
    
    with st.container(border=True):
        search = st.text_input("🔍 Rechercher un devis", placeholder="Nom du client, nom du chantier, numéro de devis...")
        df_d   = df.copy()
        if search:
            mask = pd.Series([False]*len(df_d), index=df_d.index)
            for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
                if col: mask |= df_d[col].astype(str).str.contains(search, case=False, na=False)
            df_d = df_d[mask]
            
    t1, t2 = st.tabs(["⏳ Devis en attente de signature", "✅ Devis validés"])
    with t1:
        d = df_d[~df_d["_signe"]]
        st.caption(f"{len(d)} devis en attente — CA potentiel : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_attente")
    with t2:
        d = df_d[df_d["_signe"]]
        st.caption(f"{len(d)} devis signés — CA confirmé : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_signes")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES & PAIEMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💶 Factures & Paiements":
    st.title("💶 Factures & Paiements")
    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Factures finales émises", nb_fact_ok)
    c2.metric("⚠️ Dossiers sans facture finale", len(df_imp))
    c3.metric("💸 CA restant à facturer", fmt(df_imp["_montant"].sum()))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ACOMPTE1,
                         COL_ACOMPTE2, COL_FACT_FIN, COL_PV, COL_RESERVE,
                         COL_MODALITE, COL_TVA, COL_STATUT] if c]
                         
    with st.container(border=True):
        search_f = st.text_input("🔍 Rechercher une facture", placeholder="Client, chantier...", key="search_f")
        df_f = df.copy()
        if search_f:
            mask = pd.Series([False]*len(df_f), index=df_f.index)
            for col in [COL_CLIENT, COL_CHANTIER]:
                if col: mask |= df_f[col].astype(str).str.contains(search_f, case=False, na=False)
            df_f = df_f[mask]
            
    t1, t2 = st.tabs(["⚠️ Factures à émettre", "✅ Factures payées/réglées"])
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
    st.title("🏗️ Suivi des Chantiers")
    df["_statut_ch"] = df["_pv"].apply(lambda x: "✅ Terminé" if x else "🟡 En cours")
    
    c1, c2, c3, c4  = st.columns(4)
    c1.metric("🏗️ Chantiers en cours", int((~df["_pv"]).sum()))
    c2.metric("💰 Trésorerie en cours", fmt(df[~df["_pv"]]["_montant"].sum()))
    c3.metric("✅ Chantiers terminés", int(df["_pv"].sum()))
    c4.metric("💰 CA réalisé & clôturé", fmt(df[df["_pv"]]["_montant"].sum()))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        search_ch = st.text_input("🔍 Filtrer les chantiers", placeholder="Client, lieu...", key="search_ch")
        df_ch = df.copy()
        if search_ch:
            mask = pd.Series([False]*len(df_ch), index=df_ch.index)
            for col in [COL_CLIENT, COL_CHANTIER]:
                if col: mask |= df_ch[col].astype(str).str.contains(search_ch, case=False, na=False)
            df_ch = df_ch[mask]
            
    cols_ch = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_DATE, COL_RESERVE, "_statut_ch"] if c]
    t1, t2  = st.tabs(["🟡 Travaux en cours", "✅ Livrés (PV signé)"])
    with t1:
        d = df_ch[~df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) actif(s) — {fmt(d['_montant'].sum())}")
        show_table(d[cols_ch].reset_index(drop=True) if cols_ch else d, "ch_cours")
    with t2:
        d = df_ch[df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) livré(s) — {fmt(d['_montant'].sum())}")
        show_table(d[cols_ch].reset_index(drop=True) if cols_ch else d, "ch_termines")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : TOUS LES DOSSIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Tous les dossiers":
    st.title("📁 Tous les dossiers")
    
    with st.container(border=True):
        search = st.text_input("🔍 Recherche globale", placeholder="Client, chantier, numéro...", key="search_all")
        d = df.copy()
        if search:
            mask = pd.Series([False]*len(d), index=d.index)
            for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
                if col: mask |= d[col].astype(str).str.contains(search, case=False, na=False)
            d = d[mask]
        st.caption(f"{len(d)} dossier(s) trouvé(s)")
        drop_cols = ["_montant", "_signe", "_fact_fin", "_pv", "_statut_ch"]
        show_table(d.drop(columns=drop_cols, errors="ignore").reset_index(drop=True), "all")

# ── Auto-refresh ───────────────────────────────────────────────────────────────
time.sleep(30)
st.rerun()
