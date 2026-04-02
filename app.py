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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Sans:wght@300;400;500&display=swap');
:root {
    --blanc: #F8FAFC; --vert: #22C55E; --vert-dk: #16A34A;
    --bleu: #0F2942; --bleu-md: #1E3A5F; --gris: #94A3B8;
    --surface: #0D1F33; --card: #132236; --border: #1E3A5F;
}
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0F2942 0%, #0D1F33 100%) !important;
    font-family: 'DM Sans', sans-serif; color: var(--blanc);
}
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
h1, h2, h3 { font-family: 'Nunito', sans-serif !important; }
[data-testid="stMetric"] {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; padding: 16px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
[data-testid="stMetric"] label {
    color: var(--gris) !important; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 1px;
}
[data-testid="stMetricValue"] {
    color: var(--blanc) !important; font-family: 'Nunito', sans-serif;
    font-size: 1.8rem !important; font-weight: 800 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #22C55E, #16A34A) !important;
    color: #0F2942 !important; border: none !important;
    border-radius: 9px !important; font-family: 'Nunito', sans-serif !important;
    font-weight: 900 !important; transition: all 0.2s;
}
.stButton > button:hover { opacity: 0.85 !important; transform: translateY(-1px); }
button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    color: #F8FAFC !important;
    border: 1px solid #1E3A5F !important;
}
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
    background: rgba(255,255,255,0.06) !important;
    color: var(--blanc) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stTextArea label { color: var(--gris) !important; font-size: 0.85rem; }
.refresh-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: var(--vert);
    animation: pulse 2s infinite; margin-right: 6px;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
hr { border-color: var(--border) !important; }
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
    """Retourne un client gspread authentifié pour le user."""
    _, gsa_json = get_user_credentials(username)
    if not gsa_json:
        return None, "GOOGLE_SERVICE_ACCOUNT non configuré."
    creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
    return gspread.authorize(creds), None

def get_worksheet(username: str, tab_name: str):
    """Retourne un worksheet gspread pour l'onglet demandé."""
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
        st.info("Aucun dossier.")
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
            if st.button("🔼 Réduire", key=f"btn_less_{key_suffix}"):
                st.session_state[f"show_all_{key_suffix}"] = False
                st.rerun()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=130)
    else:
        st.markdown("<div style='text-align:center;font-size:2rem;padding:8px 0'>⚡</div>",
                    unsafe_allow_html=True)

    user = st.session_state.get("username", "")
    role = st.session_state.get("role", "viewer")

    pages = [
        "📊 Vue Générale", "📋 Devis",
        "💶 Factures & Paiements", "🏗️ Chantiers",
        "📁 Tous les dossiers", "📝 Éditeur Google Sheet",
        "📈 Statistiques Avancées", "🗂️ Espace Clients",
    ]
    if role == "admin":
        pages.append("👥 Utilisateurs")

    page = st.selectbox("Navigation", pages, label_visibility="collapsed")

    st.divider()
    st.markdown('<span class="refresh-dot"></span>'
                '<span style="font-size:0.75rem;color:#94A3B8;">Sync toutes les 30s</span>',
                unsafe_allow_html=True)
    if st.button("🔄 Actualiser"):
        st.cache_resource.clear()
        st.rerun()
    st.divider()
    st.markdown(f'<div style="font-size:0.8rem;color:#94A3B8;">'
                f'👤 <b style="color:#F8FAFC">{user}</b> &nbsp;·&nbsp; {role}</div>',
                unsafe_allow_html=True)
    if st.button("🚪 Déconnexion"):
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
    st.markdown('<h1 style="font-size:2rem;">📝 Éditeur Google Sheet</h1>', unsafe_allow_html=True)

    tab_presta, tab_catalogue = st.tabs(["📋 Feuille Prestations", "🗂️ Catalogue"])

    # ── ONGLET PRESTATIONS ─────────────────────────────────────────────────────
    with tab_presta:
        st.markdown("### Feuille 1 — Prestations")

        # Colonnes attendues
        PRESTA_COLS = [
            "categorie", "Type de poste", "Sous-prestation", "Description",
            "Prix MO HT", "Prix Fourn. HT", "Marge (%)", "Quantité", "Total HT"
        ]

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
            if err:
                return None, err, pd.DataFrame()
            try:
                all_vals = ws.get_all_values()
                if not all_vals:
                    return ws, None, pd.DataFrame()
                headers = _dedup(all_vals[0])
                rows    = all_vals[1:]
                n       = len(headers)
                padded  = [r + [""]*(n-len(r)) if len(r)<n else r[:n] for r in rows]
                df      = pd.DataFrame(padded, columns=headers)
                df      = df.replace("", pd.NA).dropna(how="all").fillna("")
                # Garder seulement les colonnes utiles (pas les _col_*)
                useful = [c for c in df.columns if not c.startswith("_col")]
                df = df[useful]
                return ws, None, df
            except Exception as e:
                return None, str(e), pd.DataFrame()

        ws_p, err_p, df_p = load_presta(user)

        if err_p:
            st.error(f"❌ {err_p}")
        else:
            # ── Affichage ──────────────────────────────────────────────────────
            st.caption(f"{len(df_p)} lignes")
            search_p = st.text_input("🔍 Rechercher", placeholder="Salle de bain, Installation...", key="search_presta")
            df_show  = df_p.copy()
            if search_p:
                mask = pd.Series([False]*len(df_show), index=df_show.index)
                for c in df_show.columns:
                    mask |= df_show[c].astype(str).str.contains(search_p, case=False, na=False)
                df_show = df_show[mask]
            show_table(df_show.reset_index(drop=True), "presta_view")

            st.divider()

            # ── Ajouter une ligne ──────────────────────────────────────────────
            with st.expander("➕ Ajouter une ligne"):
                CATEGORIES  = ["Salle de bain", "Cuisine", "Chambre", "Salon", "WC / Toilettes", "Entrée / Couloir", "Garage", "Cave / Sous-sol", "Combles / Grenier", "Buanderie", "Bureau / Bibliothèque", "Terrasse / Balcon", "Jardin / Extérieur", "Façade", "Toiture", "Escalier", "Piscine", "Véranda / Pergola", "Parties communes", "Local technique", "Autre"]
                TYPES_POSTE = ["Préparation / Démolition", "Gros œuvre", "Charpente / Couverture", "Isolation", "Plâtrerie / Cloisons", "Menuiserie intérieure", "Menuiserie extérieure", "Plomberie / Sanitaire", "Chauffage / VMC / Climatisation", "Électricité", "Domotique / Alarme", "Carrelage / Revêtement sol", "Peinture / Revêtement mur", "Parquet / Stratifié", "Faïence", "Finition", "Installation", "Mobilier / Agencement", "Serrurerie / Métallerie", "Terrassement / VRD", "Maçonnerie", "Enduit / Ravalement", "Étanchéité / Hydrofuge", "Nettoyage / Évacuation", "Autre"]

                with st.form("form_add_presta"):
                    headers_p = list(df_p.columns) if len(df_p) > 0 else PRESTA_COLS
                    inputs_p  = {}
                    cols1     = st.columns(3)
                    for i, h in enumerate(headers_p):
                        with cols1[i % 3]:
                            hl = h.lower()
                            if "categ" in hl or "colonne" in hl:
                                inputs_p[h] = st.selectbox(h, CATEGORIES, key=f"add_p_{h}")
                            elif "type" in hl and "poste" in hl:
                                inputs_p[h] = st.selectbox(h, TYPES_POSTE, key=f"add_p_{h}")
                            else:
                                inputs_p[h] = st.text_input(h, key=f"add_p_{h}")
                    submit_add_p = st.form_submit_button("✅ Ajouter", use_container_width=True)

                # ── Génération IA de description ──────────────────────────────
                st.markdown("---")
                st.markdown("**🤖 Générer une description avec l'IA**")
                ai_col1, ai_col2 = st.columns([3, 1])
                with ai_col1:
                    ai_prompt = st.text_input(
                        "Décrivez la prestation en quelques mots",
                        placeholder="Ex: pose douche italienne salle de bain 120x90cm",
                        key="ai_desc_prompt"
                    )
                with ai_col2:
                    ai_generate = st.button("✨ Générer", use_container_width=True, key="btn_ai_desc")

                if ai_generate and ai_prompt.strip():
                    with st.spinner("Génération en cours..."):
                        try:
                            import requests as _req
                            _resp = _req.post(
                                "https://api.anthropic.com/v1/messages",
                                headers={"Content-Type": "application/json"},
                                json={
                                    "model": "claude-sonnet-4-20250514",
                                    "max_tokens": 300,
                                    "messages": [{
                                        "role": "user",
                                        "content": f'''Tu es un expert en bâtiment. Génère une description professionnelle et précise pour cette prestation de devis : "{ai_prompt}".
La description doit être courte (1-2 phrases max), technique et claire pour un client.
Réponds UNIQUEMENT avec la description, sans introduction ni explication.'''
                                    }]
                                },
                                timeout=15
                            )
                            if _resp.ok:
                                _data = _resp.json()
                                _desc = _data["content"][0]["text"].strip()
                                st.success("✅ Description générée :")
                                st.code(_desc, language=None)
                                st.caption("💡 Copiez cette description dans le champ 'Description' du formulaire ci-dessus.")
                            else:
                                st.error("Erreur API IA.")
                        except Exception as _e:
                            st.error(f"Erreur : {_e}")
                elif ai_generate:
                    st.warning("Entrez une description de la prestation.")

                if submit_add_p:
                    try:
                        ws_p2, _, _ = load_presta.__wrapped__(user) if hasattr(load_presta, '__wrapped__') else (get_worksheet(user, "Feuille 1")[0], None, None)
                        ws_p2, err2 = get_worksheet(user, "Feuille 1")
                        if err2:
                            st.error(err2)
                        else:
                            new_row = [inputs_p.get(h, "") for h in headers_p]
                            ws_p2.append_row(new_row, value_input_option="USER_ENTERED")
                            st.cache_resource.clear()
                            st.success("✅ Ligne ajoutée !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            # ── Modifier une ligne ─────────────────────────────────────────────
            with st.expander("✏️ Modifier une ligne"):
                if len(df_p) == 0:
                    st.info("Aucune ligne à modifier.")
                else:
                    headers_p2 = list(df_p.columns)
                    # Choix de la ligne par index
                    row_labels = [f"Ligne {i+2} — {df_p.iloc[i, 0]} / {df_p.iloc[i, 1] if len(headers_p2)>1 else ''}"
                                  for i in range(len(df_p))]
                    sel_idx = st.selectbox("Sélectionner la ligne à modifier", range(len(df_p)),
                                           format_func=lambda i: row_labels[i], key="sel_mod_presta")

                    CATEGORIES  = ["Salle de bain", "Cuisine", "Chambre", "Salon", "WC / Toilettes", "Entrée / Couloir", "Garage", "Cave / Sous-sol", "Combles / Grenier", "Buanderie", "Bureau / Bibliothèque", "Terrasse / Balcon", "Jardin / Extérieur", "Façade", "Toiture", "Escalier", "Piscine", "Véranda / Pergola", "Parties communes", "Local technique", "Autre"]
                    TYPES_POSTE = ["Préparation / Démolition", "Gros œuvre", "Charpente / Couverture", "Isolation", "Plâtrerie / Cloisons", "Menuiserie intérieure", "Menuiserie extérieure", "Plomberie / Sanitaire", "Chauffage / VMC / Climatisation", "Électricité", "Domotique / Alarme", "Carrelage / Revêtement sol", "Peinture / Revêtement mur", "Parquet / Stratifié", "Faïence", "Finition", "Installation", "Mobilier / Agencement", "Serrurerie / Métallerie", "Terrassement / VRD", "Maçonnerie", "Enduit / Ravalement", "Étanchéité / Hydrofuge", "Nettoyage / Évacuation", "Autre"]

                    with st.form("form_mod_presta"):
                        mod_inputs = {}
                        cols2      = st.columns(3)
                        for i, h in enumerate(headers_p2):
                            with cols2[i % 3]:
                                hl = h.lower()
                                cur_val = str(df_p.iloc[sel_idx][h])
                                if "categ" in hl or "colonne" in hl:
                                    idx_cat = CATEGORIES.index(cur_val) if cur_val in CATEGORIES else 0
                                    mod_inputs[h] = st.selectbox(h, CATEGORIES, index=idx_cat, key=f"mod_p_{h}")
                                elif "type" in hl and "poste" in hl:
                                    idx_tp = TYPES_POSTE.index(cur_val) if cur_val in TYPES_POSTE else 0
                                    mod_inputs[h] = st.selectbox(h, TYPES_POSTE, index=idx_tp, key=f"mod_p_{h}")
                                else:
                                    mod_inputs[h] = st.text_input(h, value=cur_val, key=f"mod_p_{h}")
                        submit_mod_p = st.form_submit_button("💾 Enregistrer", use_container_width=True)

                    if submit_mod_p:
                        try:
                            ws_p3, err3 = get_worksheet(user, "Feuille 1")
                            if err3:
                                st.error(err3)
                            else:
                                sheet_row = sel_idx + 2  # +1 header, +1 base 1
                                for col_idx, h in enumerate(headers_p2, start=1):
                                    ws_p3.update_cell(sheet_row, col_idx, mod_inputs[h])
                                st.cache_resource.clear()
                                st.success("✅ Ligne modifiée !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            # ── Supprimer une ligne ────────────────────────────────────────────
            with st.expander("🗑️ Supprimer une ligne"):
                if len(df_p) == 0:
                    st.info("Aucune ligne à supprimer.")
                else:
                    headers_p3 = list(df_p.columns)
                    row_labels2 = [f"Ligne {i+2} — {df_p.iloc[i, 0]} / {df_p.iloc[i, 1] if len(headers_p3)>1 else ''}"
                                   for i in range(len(df_p))]
                    del_idx = st.selectbox("Sélectionner la ligne à supprimer", range(len(df_p)),
                                           format_func=lambda i: row_labels2[i], key="sel_del_presta")
                    st.warning(f"⚠️ Tu vas supprimer : **{row_labels2[del_idx]}**")
                    if st.button("🗑️ Confirmer la suppression", key="btn_del_presta"):
                        try:
                            ws_p4, err4 = get_worksheet(user, "Feuille 1")
                            if err4:
                                st.error(err4)
                            else:
                                ws_p4.delete_rows(del_idx + 2)
                                st.cache_resource.clear()
                                st.success("✅ Ligne supprimée !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

    # ── ONGLET CATALOGUE ───────────────────────────────────────────────────────
    with tab_catalogue:
        st.markdown("### Catalogue — Articles")

        CATA_COLS = ["Catégorie", "Article", "Description", "Prix Achat HT", "% Marge", "Prix Vente HT"]

        @st.cache_resource(ttl=10)
        def load_catalogue(u):
            ws, err = get_worksheet(u, "catalogue")
            if err:
                return None, err, pd.DataFrame()
            try:
                all_vals = ws.get_all_values()
                if not all_vals:
                    return ws, None, pd.DataFrame()
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
            st.caption(f"{len(df_c)} articles")
            search_c = st.text_input("🔍 Rechercher", placeholder="Électricité, Câble...", key="search_cata")
            df_show_c = df_c.copy()
            if search_c:
                mask = pd.Series([False]*len(df_show_c), index=df_show_c.index)
                for c in df_show_c.columns:
                    mask |= df_show_c[c].astype(str).str.contains(search_c, case=False, na=False)
                df_show_c = df_show_c[mask]
            show_table(df_show_c.reset_index(drop=True), "cata_view")

            st.divider()

            # ── Ajouter un article ─────────────────────────────────────────────
            with st.expander("➕ Ajouter un article"):
                with st.form("form_add_cata"):
                    headers_c  = list(df_c.columns) if len(df_c) > 0 else CATA_COLS
                    inputs_c   = {}
                    cols3      = st.columns(3)
                    for i, h in enumerate(headers_c):
                        with cols3[i % 3]:
                            inputs_c[h] = st.text_input(h, key=f"add_c_{h}")
                    submit_add_c = st.form_submit_button("✅ Ajouter", use_container_width=True)

                if submit_add_c:
                    try:
                        ws_c2, err_c2 = get_worksheet(user, "catalogue")
                        if err_c2:
                            st.error(err_c2)
                        else:
                            new_row = [inputs_c.get(h, "") for h in headers_c]
                            ws_c2.append_row(new_row, value_input_option="USER_ENTERED")
                            st.cache_resource.clear()
                            st.success("✅ Article ajouté !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

            # ── Modifier un article ────────────────────────────────────────────
            with st.expander("✏️ Modifier un article"):
                if len(df_c) == 0:
                    st.info("Aucun article à modifier.")
                else:
                    headers_c2  = list(df_c.columns)
                    art_labels  = [f"Ligne {i+2} — {df_c.iloc[i, 0]} / {df_c.iloc[i, 1] if len(headers_c2)>1 else ''}"
                                   for i in range(len(df_c))]
                    sel_idx_c   = st.selectbox("Sélectionner l'article à modifier", range(len(df_c)),
                                               format_func=lambda i: art_labels[i], key="sel_mod_cata")

                    with st.form("form_mod_cata"):
                        mod_inputs_c = {}
                        cols4        = st.columns(3)
                        for i, h in enumerate(headers_c2):
                            with cols4[i % 3]:
                                mod_inputs_c[h] = st.text_input(
                                    h, value=str(df_c.iloc[sel_idx_c][h]), key=f"mod_c_{h}"
                                )
                        submit_mod_c = st.form_submit_button("💾 Enregistrer", use_container_width=True)

                    if submit_mod_c:
                        try:
                            ws_c3, err_c3 = get_worksheet(user, "catalogue")
                            if err_c3:
                                st.error(err_c3)
                            else:
                                sheet_row_c = sel_idx_c + 2
                                for col_idx, h in enumerate(headers_c2, start=1):
                                    ws_c3.update_cell(sheet_row_c, col_idx, mod_inputs_c[h])
                                st.cache_resource.clear()
                                st.success("✅ Article modifié !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            # ── Supprimer un article ───────────────────────────────────────────
            with st.expander("🗑️ Supprimer un article"):
                if len(df_c) == 0:
                    st.info("Aucun article à supprimer.")
                else:
                    headers_c3  = list(df_c.columns)
                    art_labels2 = [f"Ligne {i+2} — {df_c.iloc[i, 0]} / {df_c.iloc[i, 1] if len(headers_c3)>1 else ''}"
                                   for i in range(len(df_c))]
                    del_idx_c   = st.selectbox("Sélectionner l'article à supprimer", range(len(df_c)),
                                               format_func=lambda i: art_labels2[i], key="sel_del_cata")
                    st.warning(f"⚠️ Tu vas supprimer : **{art_labels2[del_idx_c]}**")
                    if st.button("🗑️ Confirmer la suppression", key="btn_del_cata"):
                        try:
                            ws_c4, err_c4 = get_worksheet(user, "catalogue")
                            if err_c4:
                                st.error(err_c4)
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
    st.markdown('<h1 style="font-size:2rem;margin-bottom:4px;">Vue Générale</h1>', unsafe_allow_html=True)
    st.caption(f"Mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 CA Total TTC", fmt(total_ca))
    c2.metric("📋 Devis créés", nb_devis, f"{nb_signes} signés")
    c3.metric("⏳ En attente signature", nb_attente)
    c4.metric("🏁 Factures finales", nb_fact_ok)

    st.divider()
    cl, cr = st.columns([3, 2])
    with cl:
        if COL_DATE:
            d2 = df.copy()
            d2["_date"] = pd.to_datetime(d2[COL_DATE], dayfirst=True, errors="coerce")
            d2 = d2.dropna(subset=["_date"])
            if not d2.empty:
                d2["_mois"] = d2["_date"].dt.to_period("M").astype(str)
                cm = d2.groupby("_mois")["_montant"].sum().reset_index()
                cm.columns = ["Mois", "CA (€)"]
                fig = px.bar(cm, x="Mois", y="CA (€)", title="📈 CA par mois",
                             color_discrete_sequence=["#22C55E"])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font_color="#F8FAFC", title_font_family="Nunito",
                                  xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1E3A5F"))
                st.plotly_chart(fig, use_container_width=True)
    with cr:
        pct  = int(nb_signes / nb_devis * 100) if nb_devis else 0
        fig2 = go.Figure(go.Pie(
            labels=["Signés", "En attente"],
            values=[max(nb_signes, 0), max(nb_attente, 0)],
            hole=0.65, marker_colors=["#22C55E", "#1E3A5F"], textinfo="none",
        ))
        fig2.update_layout(
            title="📋 Statut des devis", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F8FAFC", title_font_family="Nunito", showlegend=True,
            legend=dict(font=dict(color="#94A3B8")),
            annotations=[dict(text=f"<b>{pct}%</b>", x=0.5, y=0.5,
                               font_size=24, showarrow=False, font_color="#F8FAFC")],
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🕐 Derniers dossiers")
    cols_show = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_STATUT] if c]
    show_table(df[cols_show].tail(10).iloc[::-1] if cols_show else df.tail(10), "home")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ESPACE CLIENTS + UPLOAD PHOTOS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗂️ Espace Clients":
    st.markdown('<h1 style="font-size:2rem;">🗂️ Espace Clients</h1>', unsafe_allow_html=True)
    st.caption("Documents et photos synchronisés avec Google Drive")

    try:
        from googleapiclient.discovery import build

        sheet_name_ec, gsa_json_ec = get_user_credentials(user)
        if not gsa_json_ec:
            st.error("Identifiants Google introuvables.")
            st.stop()

        creds_ec = Credentials.from_service_account_info(json.loads(gsa_json_ec), scopes=SCOPES)
        drive_service = build("drive", "v3", credentials=creds_ec)

        # Chercher dossier "espace clients"
        q_main = "name = 'espace clients' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_main = drive_service.files().list(q=q_main, fields="files(id, name)").execute()
        main_folders = res_main.get("files", [])

        if not main_folders:
            st.warning("⚠️ Dossier principal 'espace clients' introuvable sur Google Drive.")
        else:
            main_folder_id = main_folders[0]["id"]
            q_clients = f"'{main_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res_clients = drive_service.files().list(q=q_clients, fields="files(id, name)", pageSize=1000).execute()
            client_folders = sorted(res_clients.get("files", []), key=lambda x: x["name"].lower())

            if not client_folders:
                st.info("Aucun dossier client trouvé.")
            else:
                client_names = [f["name"] for f in client_folders]
                search_ec = st.text_input("🔍 Rechercher un client", placeholder="Tapez le nom...")
                filtered = [n for n in client_names if search_ec.lower() in n.lower()]

                if not filtered:
                    st.warning("Aucun client ne correspond.")
                else:
                    sel_name = st.selectbox("👤 Sélectionner un client", filtered)
                    sel_id = next(f["id"] for f in client_folders if f["name"] == sel_name)

                    st.markdown(f"### 📂 Dossier : {sel_name}")
                    tab_files, tab_upload = st.tabs(["📄 Fichiers", "📸 Upload Photos"])

                    with tab_files:
                        q_files = f"'{sel_id}' in parents and trashed = false"
                        res_files = drive_service.files().list(
                            q=q_files,
                            fields="files(id, name, mimeType, webViewLink)",
                            orderBy="folder, name", pageSize=1000
                        ).execute()
                        files_ec = res_files.get("files", [])

                        if not files_ec:
                            st.info("Ce dossier est vide.")
                        else:
                            for f_ec in files_ec:
                                mime = f_ec.get("mimeType", "").lower()
                                icon = "📁" if "folder" in mime else "📕" if "pdf" in mime else "🖼️" if "image" in mime else "📊" if "sheet" in mime or "excel" in mime else "📝"
                                st.markdown(f"""
                                <a href="{f_ec.get('webViewLink', '#')}" target="_blank" style="text-decoration:none;">
                                    <div style="display:flex;align-items:center;gap:12px;padding:10px 16px;
                                        background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);
                                        border-radius:8px;margin-bottom:6px;">
                                        <span style="font-size:1.2rem;">{icon}</span>
                                        <span style="color:#F8FAFC;font-weight:600;font-size:0.9rem;">{f_ec.get('name')}</span>
                                        <span style="margin-left:auto;color:#4f8ef7;font-size:0.75rem;font-weight:600;">Ouvrir ↗</span>
                                    </div>
                                </a>
                                """, unsafe_allow_html=True)

                    with tab_upload:
                        st.markdown("**📸 Envoyer des photos ou documents vers ce dossier**")
                        uploaded = st.file_uploader(
                            "Sélectionnez vos fichiers",
                            type=["jpg","jpeg","png","pdf","webp","heic"],
                            accept_multiple_files=True,
                            key=f"up_{sel_name}"
                        )
                        if uploaded:
                            st.caption(f"{len(uploaded)} fichier(s) sélectionné(s)")
                            if st.button("📤 Envoyer sur Google Drive", use_container_width=True, key="btn_upload"):
                                from googleapiclient.http import MediaIoBaseUpload
                                import io as _io
                                ok_count = 0
                                with st.progress(0):
                                    for i, uf in enumerate(uploaded):
                                        try:
                                            meta = {"name": uf.name, "parents": [sel_id]}
                                            media = MediaIoBaseUpload(
                                                _io.BytesIO(uf.read()),
                                                mimetype=uf.type or "application/octet-stream",
                                                resumable=True
                                            )
                                            drive_service.files().create(
                                                body=meta, media_body=media, fields="id"
                                            ).execute()
                                            ok_count += 1
                                        except Exception as _ue:
                                            st.error(f"❌ {uf.name}: {_ue}")
                                if ok_count:
                                    st.success(f"✅ {ok_count} fichier(s) uploadé(s) dans le dossier de **{sel_name}** !")
                                    st.rerun()

    except ImportError:
        st.error("🚨 Bibliothèque 'google-api-python-client' manquante.")
        st.info("Ajoute `google-api-python-client>=2.0.0` dans requirements.txt")
    except Exception as _e_ec:
        st.error(f"Erreur Google Drive : {_e_ec}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DEVIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Devis":
    st.markdown('<h1 style="font-size:2rem;">Devis</h1>', unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE,
                         COL_RELANCE1, COL_RELANCE2, COL_RELANCE3, COL_STATUT] if c]
    search = st.text_input("🔍 Rechercher", placeholder="Client, chantier, numéro...")
    df_d   = df.copy()
    if search:
        mask = pd.Series([False]*len(df_d), index=df_d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col:
                mask |= df_d[col].astype(str).str.contains(search, case=False, na=False)
        df_d = df_d[mask]
    t1, t2 = st.tabs(["⏳ En attente de signature", "✅ Signés"])
    with t1:
        d = df_d[~df_d["_signe"]]
        st.caption(f"{len(d)} devis — CA potentiel : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_attente")
    with t2:
        d = df_d[df_d["_signe"]]
        st.caption(f"{len(d)} devis — CA confirmé : {fmt(d['_montant'].sum())}")
        show_table(d[cols].reset_index(drop=True) if cols else d, "devis_signes")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES & PAIEMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💶 Factures & Paiements":
    st.markdown('<h1 style="font-size:2rem;">Factures & Paiements</h1>', unsafe_allow_html=True)
    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Factures finales émises", nb_fact_ok)
    c2.metric("⚠️ Sans facture finale", len(df_imp))
    c3.metric("💸 CA à facturer", fmt(df_imp["_montant"].sum()))
    st.divider()
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ACOMPTE1,
                         COL_ACOMPTE2, COL_FACT_FIN, COL_PV, COL_RESERVE,
                         COL_MODALITE, COL_TVA, COL_STATUT] if c]
    search_f = st.text_input("🔍 Rechercher", placeholder="Client, chantier...", key="search_f")
    df_f = df.copy()
    if search_f:
        mask = pd.Series([False]*len(df_f), index=df_f.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col:
                mask |= df_f[col].astype(str).str.contains(search_f, case=False, na=False)
        df_f = df_f[mask]
    t1, t2 = st.tabs(["⚠️ À facturer", "✅ Facturés"])
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
    st.markdown('<h1 style="font-size:2rem;">Chantiers</h1>', unsafe_allow_html=True)
    df["_statut_ch"] = df["_pv"].apply(lambda x: "✅ Terminé" if x else "🟡 En cours")
    c1, c2, c3, c4  = st.columns(4)
    c1.metric("🏗️ En cours", int((~df["_pv"]).sum()))
    c2.metric("💰 CA en cours", fmt(df[~df["_pv"]]["_montant"].sum()))
    c3.metric("✅ Terminés (PV signé)", int(df["_pv"].sum()))
    c4.metric("💰 CA réalisé", fmt(df[df["_pv"]]["_montant"].sum()))
    st.divider()
    search_ch = st.text_input("🔍 Rechercher", placeholder="Client, lieu...", key="search_ch")
    df_ch = df.copy()
    if search_ch:
        mask = pd.Series([False]*len(df_ch), index=df_ch.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col:
                mask |= df_ch[col].astype(str).str.contains(search_ch, case=False, na=False)
        df_ch = df_ch[mask]
    cols_ch = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_DATE, COL_RESERVE, "_statut_ch"] if c]
    t1, t2  = st.tabs(["🟡 En cours de travaux", "✅ Terminés"])
    with t1:
        d = df_ch[~df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) — {fmt(d['_montant'].sum())}")
        show_table(d[cols_ch].reset_index(drop=True) if cols_ch else d, "ch_cours")
    with t2:
        d = df_ch[df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) — {fmt(d['_montant'].sum())}")
        show_table(d[cols_ch].reset_index(drop=True) if cols_ch else d, "ch_termines")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : STATISTIQUES AVANCÉES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Statistiques Avancées":
    st.markdown('<h1 style="font-size:2rem;margin-bottom:4px;">📈 Statistiques Avancées</h1>', unsafe_allow_html=True)
    st.caption(f"Analyse basée sur {len(df)} dossiers")

    # ── Chargement feuille prestations pour stats marges ──────────────────────
    @st.cache_resource(ttl=60)
    def load_presta_stats(u):
        ws, err = get_worksheet(u, "Feuille 1")
        if err:
            return pd.DataFrame()
        try:
            all_vals = ws.get_all_values()
            if not all_vals:
                return pd.DataFrame()
            headers = _dedup_headers(all_vals[0])
            rows = all_vals[1:]
            n = len(headers)
            padded = [r + [""]*(n-len(r)) if len(r)<n else r[:n] for r in rows]
            dfp = pd.DataFrame(padded, columns=headers)
            dfp = dfp.replace("", pd.NA).dropna(how="all").fillna("")
            useful = [c for c in dfp.columns if not c.startswith("_col")]
            return dfp[useful]
        except:
            return pd.DataFrame()

    df_presta = load_presta_stats(user)

    # ── KPIs financiers ───────────────────────────────────────────────────────
    st.markdown("### 💰 KPIs Financiers")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("CA Total TTC", fmt(total_ca))
    k2.metric("CA Sécurisé", fmt(ca_signe), f"{taux_conv}% conv.")

    if not df_presta.empty:
        col_mo   = fcol(df_presta, "mo ht")
        col_fourn = fcol(df_presta, "fourn")
        col_total_p = fcol(df_presta, "total ht")
        col_marge_p = fcol(df_presta, "marge")
        col_type_p  = fcol(df_presta, "type de poste", "type")
        col_cat_p   = fcol(df_presta, "categ", "colonne")

        if col_mo and col_fourn and col_total_p:
            df_presta["_mo"]    = df_presta[col_mo].apply(clean_amount)
            df_presta["_fourn"] = df_presta[col_fourn].apply(clean_amount)
            df_presta["_total"] = df_presta[col_total_p].apply(clean_amount)
            df_presta["_marge_val"] = df_presta[col_marge_p].apply(clean_amount) if col_marge_p else 0

            total_mo    = df_presta["_mo"].sum()
            total_fourn = df_presta["_fourn"].sum()
            total_ht    = df_presta["_total"].sum()
            marge_nette = total_ht - total_mo - total_fourn
            taux_marge  = (marge_nette / total_ht * 100) if total_ht > 0 else 0

            k3.metric("Marge Nette", fmt(marge_nette), f"{taux_marge:.1f}%")
            k4.metric("Total Fournitures", fmt(total_fourn))

            st.markdown("<br>", unsafe_allow_html=True)
            col_g1, col_g2 = st.columns(2)

            # ── CA par type de poste ───────────────────────────────────────────
            if col_type_p:
                with col_g1:
                    with st.container(border=True):
                        ca_type = df_presta.groupby(col_type_p)["_total"].sum().reset_index()
                        ca_type.columns = ["Type de poste", "CA HT (€)"]
                        ca_type = ca_type[ca_type["CA HT (€)"] > 0].sort_values("CA HT (€)", ascending=False)
                        fig_type = px.bar(
                            ca_type, x="CA HT (€)", y="Type de poste",
                            orientation="h",
                            title="📊 CA HT par type de poste",
                            color="CA HT (€)",
                            color_continuous_scale=["#1e3a5f","#4f8ef7","#00d68f"],
                        )
                        fig_type.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#F8FAFC", height=380,
                            coloraxis_showscale=False,
                            margin=dict(t=40, b=20, l=10, r=10),
                            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                        )
                        st.plotly_chart(fig_type, use_container_width=True)

            # ── CA par catégorie ───────────────────────────────────────────────
            if col_cat_p:
                with col_g2:
                    with st.container(border=True):
                        ca_cat = df_presta.groupby(col_cat_p)["_total"].sum().reset_index()
                        ca_cat.columns = ["Catégorie", "CA HT (€)"]
                        ca_cat = ca_cat[ca_cat["CA HT (€)"] > 0].sort_values("CA HT (€)", ascending=False)
                        fig_cat = px.pie(
                            ca_cat, values="CA HT (€)", names="Catégorie",
                            title="🏠 Répartition par catégorie",
                            hole=0.45,
                            color_discrete_sequence=px.colors.sequential.Blues_r,
                        )
                        fig_cat.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="#F8FAFC", height=380,
                            margin=dict(t=40, b=20, l=10, r=10),
                        )
                        st.plotly_chart(fig_cat, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Tableau détail marges par type ────────────────────────────────
            if col_type_p:
                with st.container(border=True):
                    st.markdown("#### 📋 Détail marges par type de poste")
                    grp = df_presta.groupby(col_type_p).agg(
                        CA_HT=("_total", "sum"),
                        MO_HT=("_mo", "sum"),
                        Fourn_HT=("_fourn", "sum"),
                        Nb_lignes=(col_type_p, "count"),
                    ).reset_index()
                    grp["Marge_€"]  = grp["CA_HT"] - grp["MO_HT"] - grp["Fourn_HT"]
                    grp["Marge_%"]  = (grp["Marge_€"] / grp["CA_HT"] * 100).round(1)
                    grp = grp.sort_values("CA_HT", ascending=False)
                    grp.columns = ["Type de poste", "CA HT (€)", "MO HT (€)", "Fourn. HT (€)", "Nb lignes", "Marge (€)", "Marge (%)"]
                    for col_m in ["CA HT (€)", "MO HT (€)", "Fourn. HT (€)", "Marge (€)"]:
                        grp[col_m] = grp[col_m].apply(lambda v: f"{v:,.0f} €".replace(",", " "))
                    grp["Marge (%)"] = grp["Marge (%)"].apply(lambda v: f"{v:.1f}%")
                    st.dataframe(grp, use_container_width=True, hide_index=True)
        else:
            k3.metric("Données prestations", "N/A")
            k4.metric("", "")
    else:
        k3.metric("Données prestations", "N/A")
        k4.metric("", "")
        st.info("ℹ️ La feuille 'Feuille 1' (Prestations) est vide ou introuvable.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Statistiques Devis")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total devis émis", nb_devis)
    s2.metric("Devis signés", nb_signes)
    s3.metric("En attente", nb_attente)
    s4.metric("Taux conversion", f"{taux_conv}%")

    # ── Devis par statut ───────────────────────────────────────────────────────
    if COL_STATUT:
        with st.container(border=True):
            st.markdown("#### 📊 Répartition par statut global")
            stat_counts = df[COL_STATUT].value_counts().reset_index()
            stat_counts.columns = ["Statut", "Nombre"]
            fig_stat = px.bar(
                stat_counts, x="Statut", y="Nombre",
                color="Nombre",
                color_continuous_scale=["#1e3a5f","#4f8ef7"],
            )
            fig_stat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC", coloraxis_showscale=False,
                margin=dict(t=20, b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig_stat, use_container_width=True)

    # ── Top clients par CA ────────────────────────────────────────────────────
    if COL_CLIENT:
        with st.container(border=True):
            st.markdown("#### 🏆 Top 10 clients par CA")
            top_clients = df.groupby(COL_CLIENT)["_montant"].sum().reset_index()
            top_clients.columns = ["Client", "CA (€)"]
            top_clients = top_clients.sort_values("CA (€)", ascending=False).head(10)
            fig_top = px.bar(
                top_clients, x="Client", y="CA (€)",
                color="CA (€)",
                color_continuous_scale=["#1e3a5f","#00d68f"],
            )
            fig_top.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC", coloraxis_showscale=False,
                margin=dict(t=20, b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickangle=-30),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig_top, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : TOUS LES DOSSIERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Tous les dossiers":
    st.markdown('<h1 style="font-size:2rem;">Tous les dossiers</h1>', unsafe_allow_html=True)
    search = st.text_input("🔍 Rechercher", placeholder="Client, chantier, numéro...", key="search_all")
    d = df.copy()
    if search:
        mask = pd.Series([False]*len(d), index=d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col:
                mask |= d[col].astype(str).str.contains(search, case=False, na=False)
        d = d[mask]
    st.caption(f"{len(d)} dossier(s)")
    drop_cols = ["_montant", "_signe", "_fact_fin", "_pv", "_statut_ch"]
    show_table(d.drop(columns=drop_cols, errors="ignore").reset_index(drop=True), "all")

# ── Auto-refresh ───────────────────────────────────────────────────────────────
time.sleep(30)
st.rerun()
