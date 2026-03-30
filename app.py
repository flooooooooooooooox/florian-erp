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

# ── CSS global ────────────────────────────────────────────────────────────────
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
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
.stTextInput input {
    background: rgba(255,255,255,0.06) !important;
    color: var(--blanc) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
.stTextInput label { color: var(--gris) !important; font-size: 0.85rem; }
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

# ── Connexion Google Sheet (par user) ─────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource(ttl=30)
def get_sheet_data(username: str):
    """Charge le Sheet du user connecté avec SES propres credentials."""
    try:
        sheet_name, gsa_json = get_user_credentials(username)

        if not sheet_name:
            return pd.DataFrame(), "SHEET_NAME non configuré pour cet utilisateur."
        if not gsa_json:
            return pd.DataFrame(), "GOOGLE_SERVICE_ACCOUNT non configuré pour cet utilisateur."

        creds_dict = json.loads(gsa_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(sheet_name)

        # Essayer l'onglet "suivie", sinon sheet1
        try:
            ws = sh.worksheet("suivie")
        except Exception:
            ws = sh.sheet1

        # Lecture robuste (gère colonnes vides / doublons)
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

        rows = all_values[1:]
        n = len(clean_headers)
        padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]
        df = pd.DataFrame(padded, columns=clean_headers)

        # Supprimer colonnes fantômes et lignes vides
        df = df.loc[:, ~df.columns.str.startswith("_col_")]
        df = df.replace("", pd.NA).dropna(how="all").fillna("")

        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ── Helpers ────────────────────────────────────────────────────────────────────
def clean_amount(val):
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    s = (str(val)
         .replace("\xa0", "").replace("\u202f", "").replace(" ", "")
         .replace(",", ".").replace("€", "").strip())
    try:
        return float(s)
    except:
        return 0.0

def is_checked(val):
    if pd.isna(val):
        return False
    s = str(val).strip()
    CHECKED = {"✅", "✓", "✔", "TRUE", "true", "oui", "Oui", "OUI", "1", "x", "X", "yes", "Yes"}
    if s in CHECKED:
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
    show_all = st.session_state.get(f"show_all_{key_suffix}", False)
    displayed = dataframe if show_all else dataframe.head(LIMIT)
    st.dataframe(displayed, use_container_width=True, hide_index=True)
    if total > LIMIT:
        if not show_all:
            st.caption(f"Affichage des {LIMIT} premiers sur {total} dossiers.")
            if st.button(f"📂 Voir les {total - LIMIT} suivants", key=f"btn_more_{key_suffix}"):
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
        st.markdown(
            "<div style='text-align:center;font-size:2rem;padding:8px 0'>⚡</div>",
            unsafe_allow_html=True,
        )

    user = st.session_state.get("username", "")
    role = st.session_state.get("role", "viewer")

    pages = [
        "📊 Vue Générale", "📋 Devis",
        "💶 Factures & Paiements", "🏗️ Chantiers", "📁 Tous les dossiers"
    ]
    if role == "admin":
        pages.append("👥 Utilisateurs")

    page = st.selectbox("Navigation", pages, label_visibility="collapsed")

    st.divider()
    st.markdown(
        '<span class="refresh-dot"></span>'
        '<span style="font-size:0.75rem;color:#94A3B8;">Sync toutes les 30s</span>',
        unsafe_allow_html=True,
    )
    if st.button("🔄 Actualiser"):
        st.cache_resource.clear()
        st.rerun()

    st.divider()
    st.markdown(
        f'<div style="font-size:0.8rem;color:#94A3B8;">'
        f'👤 <b style="color:#F8FAFC">{user}</b> &nbsp;·&nbsp; {role}</div>',
        unsafe_allow_html=True,
    )
    if st.button("🚪 Déconnexion"):
        logout()
        st.rerun()

# ── Page admin ─────────────────────────────────────────────────────────────────
if page == "👥 Utilisateurs":
    admin_panel()
    st.stop()

# ── Chargement données ─────────────────────────────────────────────────────────
df_raw, error = get_sheet_data(user)

if error:
    st.error(f"❌ Impossible de charger le Google Sheet : {error}")
    st.stop()

if df_raw.empty:
    st.warning("📭 Le Google Sheet est vide ou inaccessible.")
    st.stop()

df = df_raw.copy()

# ── Détection colonnes ─────────────────────────────────────────────────────────
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
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#F8FAFC", title_font_family="Nunito",
                    xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1E3A5F"),
                )
                st.plotly_chart(fig, use_container_width=True)

    with cr:
        pct = int(nb_signes / nb_devis * 100) if nb_devis else 0
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

    cols = [c for c in [
        COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE,
        COL_RELANCE1, COL_RELANCE2, COL_RELANCE3, COL_STATUT,
    ] if c]

    search = st.text_input("🔍 Rechercher", placeholder="Client, chantier, numéro...")
    df_d = df.copy()
    if search:
        mask = pd.Series([False] * len(df_d), index=df_d.index)
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

    cols = [c for c in [
        COL_CLIENT, COL_CHANTIER, COL_MONTANT,
        COL_ACOMPTE1, COL_ACOMPTE2, COL_FACT_FIN,
        COL_PV, COL_RESERVE, COL_MODALITE, COL_TVA, COL_STATUT,
    ] if c]

    search_f = st.text_input("🔍 Rechercher", placeholder="Client, chantier...", key="search_f")
    df_f = df.copy()
    if search_f:
        mask = pd.Series([False] * len(df_f), index=df_f.index)
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
    nb_cours    = int((~df["_pv"]).sum())
    nb_termines = int(df["_pv"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏗️ En cours", nb_cours)
    c2.metric("💰 CA en cours", fmt(df[~df["_pv"]]["_montant"].sum()))
    c3.metric("✅ Terminés (PV signé)", nb_termines)
    c4.metric("💰 CA réalisé", fmt(df[df["_pv"]]["_montant"].sum()))

    st.divider()

    search_ch = st.text_input("🔍 Rechercher un chantier", placeholder="Client, lieu...", key="search_ch")
    df_ch = df.copy()
    if search_ch:
        mask = pd.Series([False] * len(df_ch), index=df_ch.index)
        for col in [COL_CLIENT, COL_CHANTIER]:
            if col:
                mask |= df_ch[col].astype(str).str.contains(search_ch, case=False, na=False)
        df_ch = df_ch[mask]

    cols_ch = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_DATE, COL_RESERVE, "_statut_ch"] if c]

    t1, t2 = st.tabs(["🟡 En cours de travaux", "✅ Terminés"])
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

    search = st.text_input("🔍 Rechercher", placeholder="Client, chantier, numéro de devis...", key="search_all")
    d = df.copy()
    if search:
        mask = pd.Series([False] * len(d), index=d.index)
        for col in [COL_CLIENT, COL_CHANTIER, COL_NUM]:
            if col:
                mask |= d[col].astype(str).str.contains(search, case=False, na=False)
        d = d[mask]

    st.caption(f"{len(d)} dossier(s)")
    drop_cols = ["_montant", "_signe", "_fact_fin", "_pv", "_statut_ch"]
    show_table(
        d.drop(columns=drop_cols, errors="ignore").reset_index(drop=True),
        "all",
    )

# ── Auto-refresh ───────────────────────────────────────────────────────────────
time.sleep(30)
st.rerun()
