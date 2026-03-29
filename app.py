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
[data-testid="stMetricDelta"] { font-size: 0.8rem; }
.stButton > button { background: var(--vert) !important; color: var(--bleu) !important; border: none !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; padding: 0.4rem 1.2rem !important; }
.stButton > button:hover { background: var(--vert-dk) !important; }
.refresh-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--vert); animation: pulse 2s infinite; margin-right: 6px; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
hr { border-color: var(--border); }
</style>
""", unsafe_allow_html=True)

if not check_login():
    st.stop()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource(ttl=30)
def get_sheet_data():
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(st.secrets["SHEET_NAME"])
        # Lire l'onglet "suivie" spécifiquement
        try:
            ws = sh.worksheet("suivie")
        except:
            ws = sh.sheet1
        data = ws.get_all_records(expected_headers=[])
        df = pd.DataFrame(data)
        # Supprimer les lignes complètement vides
        df = df.dropna(how="all")
        df = df[df.apply(lambda r: any(str(v).strip() not in ["", "0"] for v in r), axis=1)]
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def clean_amount(val):
    """Convertit une cellule montant en float — gère virgule française."""
    if not val and val != 0:
        return 0.0
    s = str(val).replace("\xa0", "").replace("\u202f", "").replace(" ", "")
    s = s.replace(",", ".").replace("€", "").strip()
    try:
        return float(s)
    except:
        return 0.0

def is_checked(val):
    """
    Détecte si une case est cochée.
    Dans le Sheet de Florian, coché = "✅", non coché = "" ou "📧" (relance)
    """
    if val is None:
        return False
    s = str(val).strip()
    if s == "":
        return False
    # Valeurs explicitement cochées
    CHECKED = {"✅", "✓", "✔", "TRUE", "true", "oui", "Oui", "OUI", "1", "x", "X", "yes", "Yes"}
    # Valeurs explicitement NON cochées (relances, vide, etc.)
    NOT_CHECKED = {"", "📧", "0", "FALSE", "false", "non", "Non", "NON"}
    if s in CHECKED:
        return True
    if s in NOT_CHECKED:
        return False
    # Par défaut : si contient ✅ c'est coché
    return "✅" in s

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 24px;">
        <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#F8FAFC;">⚡ Florian AI</div>
        <div style="font-size:0.75rem; color:#94A3B8; letter-spacing:2px; text-transform:uppercase;">Bâtiment ERP</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.selectbox("Nav", [
        "📊 Vue Générale", "📋 Devis",
        "💶 Factures & Paiements", "🏗️ Chantiers", "📁 Tous les dossiers"
    ], label_visibility="collapsed")

    st.divider()
    st.markdown('<span class="refresh-dot"></span><span style="font-size:0.75rem;color:#94A3B8;">Sync toutes les 30s</span>', unsafe_allow_html=True)
    if st.button("🔄 Actualiser maintenant"):
        st.cache_resource.clear()
        st.rerun()
    st.divider()
    user = st.session_state.get("username", "")
    st.markdown(f'<div style="font-size:0.8rem;color:#94A3B8;">Connecté : <b style="color:#F8FAFC">{user}</b></div>', unsafe_allow_html=True)
    if st.button("🚪 Déconnexion"):
        logout()
        st.rerun()

df_raw, error = get_sheet_data()

if error:
    st.error(f"❌ Impossible de charger le Google Sheet : {error}")
    st.stop()

if df_raw.empty:
    st.warning("📭 Le Google Sheet est vide ou inaccessible.")
    st.stop()

df = df_raw.copy()

# ── Détection flexible des colonnes ──────────────────────────────────────────
def fcol(df, *keywords):
    for kw in keywords:
        for c in df.columns:
            if kw.lower() in str(c).lower():
                return c
    return None

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
COL_ACOMPTE1 = fcol(df, "acompte 1")
COL_ACOMPTE2 = fcol(df, "acompte 2")

# ── Calcul des colonnes internes ──────────────────────────────────────────────
df["_montant"] = df[COL_MONTANT].apply(clean_amount) if COL_MONTANT else 0.0
df["_signe"]   = df[COL_SIGN].apply(is_checked)      if COL_SIGN    else False
df["_fact_fin"]= df[COL_FACT_FIN].apply(is_checked)  if COL_FACT_FIN else False
df["_pv"]      = df[COL_PV].apply(is_checked)         if COL_PV      else False

# ── KPIs ─────────────────────────────────────────────────────────────────────
total_ca    = df["_montant"].sum()
nb_devis    = len(df)
nb_signes   = int(df["_signe"].sum())
nb_attente  = nb_devis - nb_signes
nb_fact_ok  = int(df["_fact_fin"].sum())
ca_signe    = df[df["_signe"]]["_montant"].sum()
ca_non_sign = df[~df["_signe"]]["_montant"].sum()
fmt = lambda v: f"{v:,.0f} €".replace(",", " ")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : VUE GÉNÉRALE
# ═══════════════════════════════════════════════════════════════════════════════
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
                fig = px.bar(cm, x="Mois", y="CA (€)", title="📈 CA par mois", color_discrete_sequence=["#22C55E"])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1E3A5F"))
                st.plotly_chart(fig, use_container_width=True)

    with cr:
        fig2 = go.Figure(go.Pie(
            labels=["Signés", "En attente"],
            values=[max(nb_signes, 0), max(nb_attente, 0)],
            hole=0.65, marker_colors=["#22C55E", "#1E3A5F"], textinfo="none"
        ))
        pct = int(nb_signes / nb_devis * 100) if nb_devis else 0
        fig2.update_layout(
            title="📋 Statut des devis",
            paper_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC",
            showlegend=True, legend=dict(font=dict(color="#94A3B8")),
            annotations=[dict(text=f"<b>{pct}%</b>", x=0.5, y=0.5, font_size=22, showarrow=False, font_color="#F8FAFC")]
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🕐 Derniers dossiers")
    cols_show = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_STATUT] if c]
    st.dataframe(df[cols_show].tail(10).iloc[::-1] if cols_show else df.tail(10), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : DEVIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Devis":
    st.markdown('<h1 style="font-size:2rem;">Devis</h1>', unsafe_allow_html=True)
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM, COL_MONTANT, COL_DATE, COL_RELANCE1, COL_RELANCE2, COL_STATUT] if c]
    t1, t2 = st.tabs(["⏳ En attente de signature", "✅ Signés"])
    with t1:
        d = df[~df["_signe"]]
        st.caption(f"{len(d)} devis — CA potentiel : {fmt(ca_non_sign)}")
        st.dataframe(d[cols] if cols else d, use_container_width=True, hide_index=True)
    with t2:
        d = df[df["_signe"]]
        st.caption(f"{len(d)} devis — CA confirmé : {fmt(ca_signe)}")
        st.dataframe(d[cols] if cols else d, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES & PAIEMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💶 Factures & Paiements":
    st.markdown('<h1 style="font-size:2rem;">Factures & Paiements</h1>', unsafe_allow_html=True)
    df_imp = df[df["_signe"] & ~df["_fact_fin"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Factures finales émises", nb_fact_ok)
    c2.metric("⚠️ Sans facture finale", len(df_imp))
    c3.metric("💸 CA à facturer", fmt(df_imp["_montant"].sum()))
    st.divider()
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_ACOMPTE1, COL_ACOMPTE2, COL_FACT_FIN, COL_MODALITE, COL_STATUT] if c]
    t1, t2 = st.tabs(["⚠️ À facturer", "✅ Facturés"])
    with t1:
        st.dataframe(df_imp[cols] if cols else df_imp, use_container_width=True, hide_index=True)
    with t2:
        d = df[df["_fact_fin"]]
        st.dataframe(d[cols] if cols else d, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : CHANTIERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Chantiers":
    st.markdown('<h1 style="font-size:2rem;">Chantiers</h1>', unsafe_allow_html=True)
    df["_statut_ch"] = df["_pv"].apply(lambda x: "✅ Terminé" if x else "🟡 En cours")
    c1, c2 = st.columns(2)
    c1.metric("🏗️ En cours", int((~df["_pv"]).sum()))
    c2.metric("✅ Terminés (PV signé)", int(df["_pv"].sum()))
    st.divider()
    cols = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_DATE, "_statut_ch"] if c]
    st.dataframe(df[cols].sort_values("_statut_ch") if cols else df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : TOUS LES DOSSIERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Tous les dossiers":
    st.markdown('<h1 style="font-size:2rem;">Tous les dossiers</h1>', unsafe_allow_html=True)
    search = st.text_input("🔍 Rechercher", placeholder="Client, chantier...")
    d = df.copy()
    if search and COL_CLIENT:
        mask = d[COL_CLIENT].astype(str).str.contains(search, case=False, na=False)
        if COL_CHANTIER:
            mask |= d[COL_CHANTIER].astype(str).str.contains(search, case=False, na=False)
        d = d[mask]
    st.caption(f"{len(d)} dossier(s)")
    st.dataframe(
        d.drop(columns=["_montant", "_signe", "_fact_fin", "_pv", "_statut_ch"], errors="ignore"),
        use_container_width=True, hide_index=True
    )

time.sleep(30)
st.rerun()
