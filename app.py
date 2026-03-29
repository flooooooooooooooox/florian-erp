import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import json
from auth import check_login, logout

st.set_page_config(
    page_title="Florian AI Bâtiment – ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root {
    --blanc: #F8FAFC; --vert: #22C55E; --vert-dk: #16A34A;
    --bleu: #0F2942; --bleu-md: #1E3A5F; --gris: #94A3B8;
    --surface: #0D1F33; --card: #132236; --border: #1E3A5F;
}
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bleu) !important;
    font-family: 'DM Sans', sans-serif; color: var(--blanc);
}
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }
[data-testid="stMetric"] { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; }
[data-testid="stMetric"] label { color: var(--gris) !important; font-size: 0.8rem; }
[data-testid="stMetricValue"] { color: var(--blanc) !important; font-family: 'Syne', sans-serif; font-size: 1.8rem !important; }
.stButton > button { background: var(--vert) !important; color: var(--bleu) !important; border: none !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }
.stButton > button:hover { background: var(--vert-dk) !important; }
.refresh-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--vert); animation: pulse 2s infinite; margin-right: 6px; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
</style>
""", unsafe_allow_html=True)

if not check_login():
    st.stop()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

@st.cache_resource(ttl=30)
def get_sheet_data():
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(st.secrets["SHEET_NAME"])
        ws = sh.sheet1

        # ── FIX : colonnes vides / doublons dans la ligne d'en-tête ──
        all_values = ws.get_all_values()
        if not all_values:
            return pd.DataFrame(), None

        raw_headers = all_values[0]
        # Renommer les colonnes vides en _col_0, _col_1 …
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
        # Aligner les lignes sur le nombre de colonnes
        n = len(clean_headers)
        padded = [r + [""] * (n - len(r)) if len(r) < n else r[:n] for r in rows]

        df = pd.DataFrame(padded, columns=clean_headers)
        # Supprimer les colonnes fantômes (_col_X)
        df = df.loc[:, ~df.columns.str.startswith("_col_")]
        # Supprimer les lignes entièrement vides
        df = df.replace("", pd.NA).dropna(how="all").fillna("")

        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def clean_amount(val):
    if pd.isna(val) or val == "":
        return 0.0
    s = (str(val)
         .replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
         .replace(",", ".").replace("€", "").strip())
    try:
        return float(s)
    except:
        return 0.0

def is_checked(val):
    if pd.isna(val):
        return False
    return str(val).strip().lower() in ["✓", "✔", "true", "oui", "1", "x", "yes", "✅"]

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:8px 0 24px;">
        <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#F8FAFC;">⚡ Florian AI</div>
        <div style="font-size:0.75rem;color:#94A3B8;letter-spacing:2px;text-transform:uppercase;">Bâtiment ERP</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.selectbox("Navigation", [
        "📊 Vue Générale", "📋 Devis",
        "💶 Factures & Paiements", "🏗️ Chantiers", "📁 Tous les dossiers"
    ], label_visibility="collapsed")

    st.divider()
    st.markdown('<span class="refresh-dot"></span><span style="font-size:0.75rem;color:#94A3B8;">Sync toutes les 30s</span>', unsafe_allow_html=True)
    if st.button("🔄 Actualiser"):
        st.cache_resource.clear()
        st.rerun()
    st.divider()
    user = st.session_state.get("username", "")
    st.markdown(f'<div style="font-size:0.8rem;color:#94A3B8;">Connecté : <b style="color:#F8FAFC">{user}</b></div>', unsafe_allow_html=True)
    if st.button("🚪 Déconnexion"):
        logout()
        st.rerun()

# ── Chargement données ────────────────────────────────────────────────────────
df_raw, error = get_sheet_data()

if error:
    st.error(f"❌ Impossible de charger le Google Sheet : {error}")
    st.stop()

if df_raw.empty:
    st.warning("📭 Le Google Sheet est vide ou inaccessible.")
    st.stop()

df = df_raw.copy()

# ── Détection colonnes (robuste, strip espaces) ───────────────────────────────
def find_col(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in c.strip().lower():
                return c
    return None

COL_CLIENT    = find_col(df, "client")
COL_CHANTIER  = find_col(df, "objet", "chantier")
COL_NUM_DEVIS = find_col(df, "n° devis", "num")
COL_MONTANT   = find_col(df, "montant")
COL_DEVIS_CR  = find_col(df, "devis créé", "devis cree")
COL_DEVIS_SIGN= find_col(df, "signé", "signe")
COL_RELANCE1  = find_col(df, "relance 1")
COL_RELANCE2  = find_col(df, "relance 2")
COL_RELANCE3  = find_col(df, "relance 3")
COL_ACOMPTE1  = find_col(df, "acompte 1")
COL_ACOMPTE2  = find_col(df, "acompte 2")
COL_FACT_FIN  = find_col(df, "finale", "final")
COL_PV        = find_col(df, "pv")
COL_RESERVE   = find_col(df, "réserve", "reserve")
COL_MODALITE  = find_col(df, "modalit")
COL_TVA       = find_col(df, "tva")
COL_STATUT    = find_col(df, "statut")
COL_DATE      = find_col(df, "date")

# ── Colonnes calculées ────────────────────────────────────────────────────────
df["_montant"]  = df[COL_MONTANT].apply(clean_amount)   if COL_MONTANT   else 0.0
df["_signe"]    = df[COL_DEVIS_SIGN].apply(is_checked)  if COL_DEVIS_SIGN else False
df["_fact_fin"] = df[COL_FACT_FIN].apply(is_checked)    if COL_FACT_FIN  else False
df["_pv"]       = df[COL_PV].apply(is_checked)          if COL_PV        else False

total_ca     = df["_montant"].sum()
nb_devis     = len(df)
nb_signes    = int(df["_signe"].sum())
nb_attente   = nb_devis - nb_signes
nb_fact_ok   = int(df["_fact_fin"].sum())
ca_signe     = df[df["_signe"]]["_montant"].sum()
ca_non_signe = df[~df["_signe"]]["_montant"].sum()

def fmt(val):
    return f"{val:,.0f} €".replace(",", " ")

# ── Pages ─────────────────────────────────────────────────────────────────────
if page == "📊 Vue Générale":
    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;margin-bottom:4px;">Vue Générale</h1>', unsafe_allow_html=True)
    st.caption(f"Mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 CA Total TTC", fmt(total_ca))
    c2.metric("📋 Devis créés", nb_devis, f"{nb_signes} signés")
    c3.metric("⏳ En attente signature", nb_attente)
    c4.metric("🏁 Factures finales", nb_fact_ok)

    st.divider()
    col_l, col_r = st.columns([3, 2])

    with col_l:
        if COL_DATE:
            df2 = df.copy()
            df2["_date"] = pd.to_datetime(df2[COL_DATE], dayfirst=True, errors="coerce")
            df2 = df2.dropna(subset=["_date"])
            df2["_mois"] = df2["_date"].dt.to_period("M").astype(str)
            ca_mois = df2.groupby("_mois")["_montant"].sum().reset_index()
            ca_mois.columns = ["Mois", "CA (€)"]
            fig = px.bar(ca_mois, x="Mois", y="CA (€)", title="📈 CA par mois",
                         color_discrete_sequence=["#22C55E"])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC", title_font_family="Syne",
                xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1E3A5F")
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = go.Figure(data=[go.Pie(
            labels=["Signés", "En attente"],
            values=[nb_signes, max(nb_attente, 0)],
            hole=0.65, marker_colors=["#22C55E", "#1E3A5F"], textinfo="none"
        )])
        fig2.update_layout(
            title="📋 Statut devis", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F8FAFC", title_font_family="Syne", showlegend=True,
            legend=dict(font=dict(color="#94A3B8")),
            annotations=[dict(
                text=f"<b>{int(nb_signes/nb_devis*100) if nb_devis else 0}%</b>",
                x=0.5, y=0.5, font_size=22, showarrow=False, font_color="#F8FAFC"
            )]
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🕐 Derniers dossiers")
    cols_show = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_STATUT] if c]
    st.dataframe(
        df[cols_show].tail(10).iloc[::-1] if cols_show else df.tail(10),
        use_container_width=True, hide_index=True
    )

elif page == "📋 Devis":
    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Devis</h1>', unsafe_allow_html=True)

    cols = [c for c in [
        COL_CLIENT, COL_CHANTIER, COL_NUM_DEVIS, COL_MONTANT, COL_DATE,
        COL_DEVIS_CR, COL_DEVIS_SIGN,
        COL_RELANCE1, COL_RELANCE2, COL_RELANCE3,
        COL_STATUT
    ] if c]

    tab1, tab2 = st.tabs(["⏳ En attente de signature", "✅ Signés"])
    with tab1:
        d = df[~df["_signe"]]
        st.caption(f"{len(d)} devis — CA potentiel : {fmt(ca_non_signe)}")
        st.dataframe(d[cols] if cols else d, use_container_width=True, hide_index=True)
    with tab2:
        d = df[df["_signe"]]
        st.caption(f"{len(d)} devis — CA confirmé : {fmt(ca_signe)}")
        st.dataframe(d[cols] if cols else d, use_container_width=True, hide_index=True)

elif page == "💶 Factures & Paiements":
    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Factures & Paiements</h1>', unsafe_allow_html=True)

    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Factures finales émises", nb_fact_ok)
    c2.metric("⚠️ Sans facture finale", len(df_imp))
    c3.metric("💸 CA à facturer", fmt(df_imp["_montant"].sum()))

    st.divider()
    cols = [c for c in [
        COL_CLIENT, COL_CHANTIER, COL_MONTANT,
        COL_ACOMPTE1, COL_ACOMPTE2, COL_FACT_FIN,
        COL_PV, COL_RESERVE,
        COL_MODALITE, COL_TVA, COL_STATUT
    ] if c]

    tab1, tab2 = st.tabs(["⚠️ À facturer", "✅ Facturés"])
    with tab1:
        st.dataframe(df_imp[cols] if cols else df_imp, use_container_width=True, hide_index=True)
    with tab2:
        d = df[df["_fact_fin"]]
        st.dataframe(d[cols] if cols else d, use_container_width=True, hide_index=True)

elif page == "🏗️ Chantiers":
    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Chantiers</h1>', unsafe_allow_html=True)

    df["_statut_ch"] = df["_pv"].apply(lambda x: "✅ Terminé" if x else "🟡 En cours")
    c1, c2 = st.columns(2)
    c1.metric("🏗️ En cours", int((~df["_pv"]).sum()))
    c2.metric("✅ Terminés (PV signé)", int(df["_pv"].sum()))

    st.divider()
    cols = [c for c in [
        COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_DATE,
        COL_RESERVE, COL_MODALITE, "_statut_ch"
    ] if c]
    st.dataframe(
        df[cols].sort_values("_statut_ch") if cols else df,
        use_container_width=True, hide_index=True
    )

elif page == "📁 Tous les dossiers":
    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Tous les dossiers</h1>', unsafe_allow_html=True)

    search = st.text_input("🔍 Rechercher", placeholder="Client, chantier...")
    df_f = df.copy()
    if search and COL_CLIENT:
        mask = df_f[COL_CLIENT].astype(str).str.contains(search, case=False, na=False)
        if COL_CHANTIER:
            mask |= df_f[COL_CHANTIER].astype(str).str.contains(search, case=False, na=False)
        df_f = df_f[mask]

    st.caption(f"{len(df_f)} dossier(s)")
    drop_cols = ["_montant", "_signe", "_fact_fin", "_pv"]
    if "_statut_ch" in df_f.columns:
        drop_cols.append("_statut_ch")
    st.dataframe(
        df_f.drop(columns=drop_cols, errors="ignore"),
        use_container_width=True, hide_index=True
    )

time.sleep(30)
st.rerun()
