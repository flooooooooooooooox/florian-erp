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
            "Colonne 1", "Type de poste", "Sous-prestation", "Description",
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
                with st.form("form_add_presta"):
                    headers_p = list(df_p.columns) if len(df_p) > 0 else PRESTA_COLS
                    inputs_p  = {}
                    cols1     = st.columns(3)
                    for i, h in enumerate(headers_p):
                        with cols1[i % 3]:
                            inputs_p[h] = st.text_input(h, key=f"add_p_{h}")
                    submit_add_p = st.form_submit_button("✅ Ajouter", use_container_width=True)

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

                    with st.form("form_mod_presta"):
                        mod_inputs = {}
                        cols2      = st.columns(3)
                        for i, h in enumerate(headers_p2):
                            with cols2[i % 3]:
                                mod_inputs[h] = st.text_input(
                                    h, value=str(df_p.iloc[sel_idx][h]), key=f"mod_p_{h}"
                                )
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
