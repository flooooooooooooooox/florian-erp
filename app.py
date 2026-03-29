import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import time
import json
from auth import check_login, logout

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Florian AI Bâtiment – ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Variables couleurs */
:root {
    --blanc:   #F8FAFC;
    --vert:    #22C55E;
    --vert-dk: #16A34A;
    --bleu:    #0F2942;
    --bleu-md: #1E3A5F;
    --bleu-lt: #1D4ED8;
    --gris:    #94A3B8;
    --surface: #0D1F33;
    --card:    #132236;
    --border:  #1E3A5F;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bleu) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--blanc);
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

/* Titres */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetric"] label { color: var(--gris) !important; font-size: 0.8rem; }
[data-testid="stMetricValue"] { color: var(--blanc) !important; font-family: 'Syne', sans-serif; font-size: 1.8rem !important; }
[data-testid="stMetricDelta"] { font-size: 0.8rem; }

/* Boutons */
.stButton > button {
    background: var(--vert) !important;
    color: var(--bleu) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    padding: 0.4rem 1.2rem !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: var(--vert-dk) !important;
    transform: translateY(-1px);
}

/* Tableaux */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
thead th { background: var(--bleu-md) !important; color: var(--blanc) !important; }

/* Badge statut */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-vert  { background: #14532D; color: #86EFAC; }
.badge-rouge { background: #7F1D1D; color: #FCA5A5; }
.badge-jaune { background: #713F12; color: #FDE68A; }
.badge-gris  { background: #1E293B; color: #94A3B8; }

/* Cards section */
.section-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
}

/* Sidebar nav */
[data-testid="stSidebarNav"] { display: none; }

div[data-testid="stSelectbox"] label { color: var(--gris) !important; }

/* Ligne séparatrice */
hr { border-color: var(--border); }

/* Auto-refresh indicator */
.refresh-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--vert);
    animation: pulse 2s infinite;
    margin-right: 6px;
}
@keyframes pulse {
    0%,100% { opacity:1; } 50% { opacity:.3; }
}
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()

# ── Connexion Google Sheets ───────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource(ttl=30)
def get_sheet_data():
    """Charge les données depuis Google Sheets (cache 30 sec)."""
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open(st.secrets["SHEET_NAME"])
        ws = sh.sheet1
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ── Helpers ───────────────────────────────────────────────────────────────────
def clean_amount(val):
    """Convertit une cellule montant en float."""
    if pd.isna(val) or val == "":
        return 0.0
    s = str(val).replace(" ", "").replace("\u202f", "").replace(",", ".").replace("€", "").strip()
    try:
        return float(s)
    except:
        return 0.0

def is_checked(val):
    """Retourne True si la cellule est cochée (✓, TRUE, OUI, oui, 1, x)."""
    if pd.isna(val):
        return False
    v = str(val).strip().lower()
    return v in ["✓", "✔", "true", "oui", "1", "x", "yes", "✅", "oui ✅"]

def status_badge(statut):
    statut = str(statut).lower()
    if "terminé" in statut or "payé" in statut:
        return f'<span class="badge badge-vert">✅ {statut.title()}</span>'
    elif "relance" in statut or "retard" in statut:
        return f'<span class="badge badge-rouge">🔴 {statut.title()}</span>'
    elif "en cours" in statut:
        return f'<span class="badge badge-jaune">🟡 {statut.title()}</span>'
    else:
        return f'<span class="badge badge-gris">⬜ {statut.title()}</span>'

# ── Chargement données ────────────────────────────────────────────────────────
df_raw, error = get_sheet_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 24px;">
        <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#F8FAFC;">
            ⚡ Florian AI
        </div>
        <div style="font-size:0.75rem; color:#94A3B8; letter-spacing:2px; text-transform:uppercase;">
            Bâtiment ERP
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.selectbox(
        "Navigation",
        ["📊 Vue Générale", "📋 Devis", "💶 Factures & Paiements", "🏗️ Chantiers", "📁 Tous les dossiers"],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown(f'<span class="refresh-dot"></span><span style="font-size:0.75rem;color:#94A3B8;">Sync toutes les 30s</span>', unsafe_allow_html=True)

    if st.button("🔄 Actualiser maintenant"):
        st.cache_resource.clear()
        st.rerun()

    st.divider()
    user = st.session_state.get("username", "")
    st.markdown(f'<div style="font-size:0.8rem;color:#94A3B8;">Connecté : <b style="color:#F8FAFC">{user}</b></div>', unsafe_allow_html=True)
    if st.button("🚪 Déconnexion"):
        logout()
        st.rerun()

# ── Gestion erreur ────────────────────────────────────────────────────────────
if error:
    st.error(f"❌ Impossible de charger le Google Sheet : {error}")
    st.info("Vérifiez les secrets `GOOGLE_SERVICE_ACCOUNT` et `SHEET_NAME` dans Replit.")
    st.stop()

if df_raw.empty:
    st.warning("📭 Le Google Sheet est vide ou inaccessible.")
    st.stop()

# ── Préparation des données ───────────────────────────────────────────────────
df = df_raw.copy()

# Colonnes attendues (mapping flexible)
COL_CLIENT     = next((c for c in df.columns if "client" in c.lower()), df.columns[0])
COL_CHANTIER   = next((c for c in df.columns if "objet" in c.lower() or "chantier" in c.lower()), None)
COL_NUM_DEVIS  = next((c for c in df.columns if "devis" in c.lower() and "n°" in c.lower() or "num" in c.lower() and "devis" in c.lower()), None)
COL_MONTANT    = next((c for c in df.columns if "montant" in c.lower()), None)
COL_DEVIS_CREE = next((c for c in df.columns if "créé" in c.lower() or "cree" in c.lower()), None)
COL_DEVIS_SIGN = next((c for c in df.columns if "signé" in c.lower() and "devis" in c.lower()), None)
COL_FACT_FINALE= next((c for c in df.columns if "finale" in c.lower() or "final" in c.lower()), None)
COL_PV         = next((c for c in df.columns if "pv" in c.lower()), None)
COL_STATUT     = next((c for c in df.columns if "statut" in c.lower()), None)
COL_DATE       = next((c for c in df.columns if "date" in c.lower()), None)
COL_MODALITE   = next((c for c in df.columns if "modalit" in c.lower()), None)
COL_TVA        = next((c for c in df.columns if "tva" in c.lower()), None)
COL_RELANCE1   = next((c for c in df.columns if "relance 1" in c.lower()), None)
COL_RELANCE2   = next((c for c in df.columns if "relance 2" in c.lower()), None)
COL_ACOMPTE1   = next((c for c in df.columns if "acompte 1" in c.lower()), None)
COL_ACOMPTE2   = next((c for c in df.columns if "acompte 2" in c.lower()), None)

if COL_MONTANT:
    df["_montant"] = df[COL_MONTANT].apply(clean_amount)
else:
    df["_montant"] = 0.0

if COL_DEVIS_SIGN:
    df["_signe"] = df[COL_DEVIS_SIGN].apply(is_checked)
else:
    df["_signe"] = False

if COL_FACT_FINALE:
    df["_facture_finale"] = df[COL_FACT_FINALE].apply(is_checked)
else:
    df["_facture_finale"] = False

if COL_PV:
    df["_pv"] = df[COL_PV].apply(is_checked)
else:
    df["_pv"] = False

# ── KPIs globaux ─────────────────────────────────────────────────────────────
total_ca        = df["_montant"].sum()
nb_devis        = len(df)
nb_signes       = df["_signe"].sum()
nb_en_attente   = nb_devis - nb_signes
nb_factures_ok  = df["_facture_finale"].sum()
ca_signe        = df[df["_signe"]]["_montant"].sum()
ca_non_signe    = df[~df["_signe"]]["_montant"].sum()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : VUE GÉNÉRALE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Vue Générale":

    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;margin-bottom:4px;">Vue Générale</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#94A3B8;font-size:0.85rem;">Mise à jour : {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>', unsafe_allow_html=True)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 CA Total (TTC)", f"{total_ca:,.0f} €".replace(",", " "))
    c2.metric("📋 Devis créés", nb_devis, f"{nb_signes} signés")
    c3.metric("⏳ En attente de signature", nb_en_attente)
    c4.metric("🏁 Factures finales émises", int(nb_factures_ok))

    st.divider()

    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Graphique CA par mois
        if COL_DATE and COL_MONTANT:
            df_date = df.copy()
            df_date["_date"] = pd.to_datetime(df_date[COL_DATE], dayfirst=True, errors="coerce")
            df_date = df_date.dropna(subset=["_date"])
            df_date["_mois"] = df_date["_date"].dt.to_period("M").astype(str)
            ca_mois = df_date.groupby("_mois")["_montant"].sum().reset_index()
            ca_mois.columns = ["Mois", "CA (€)"]

            fig = px.bar(
                ca_mois, x="Mois", y="CA (€)",
                title="📈 Chiffre d'affaires par mois",
                color_discrete_sequence=["#22C55E"],
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC",
                title_font_family="Syne",
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#1E3A5F"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # Donut devis
        fig2 = go.Figure(data=[go.Pie(
            labels=["Signés", "En attente"],
            values=[nb_signes, max(nb_en_attente, 0)],
            hole=0.65,
            marker_colors=["#22C55E", "#1E3A5F"],
            textinfo="none",
        )])
        fig2.update_layout(
            title="📋 Statut des devis",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F8FAFC",
            title_font_family="Syne",
            showlegend=True,
            legend=dict(font=dict(color="#94A3B8")),
            annotations=[dict(
                text=f"<b>{int(nb_signes/nb_devis*100) if nb_devis else 0}%</b>",
                x=0.5, y=0.5, font_size=22, showarrow=False, font_color="#F8FAFC"
            )]
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Derniers dossiers
    st.markdown("### 🕐 Derniers dossiers")
    cols_show = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_STATUT] if c]
    if cols_show:
        st.dataframe(
            df[cols_show].tail(10).iloc[::-1],
            use_container_width=True,
            hide_index=True,
        )

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : DEVIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Devis":

    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Devis</h1>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["⏳ En attente de signature", "✅ Signés"])

    cols_devis = [c for c in [COL_CLIENT, COL_CHANTIER, COL_NUM_DEVIS, COL_MONTANT, COL_DATE,
                               COL_RELANCE1, COL_RELANCE2, COL_STATUT] if c]

    with tab1:
        df_attente = df[~df["_signe"]][cols_devis] if cols_devis else df[~df["_signe"]]
        st.markdown(f'<p style="color:#94A3B8;">{len(df_attente)} devis en attente — CA potentiel : <b style="color:#22C55E">{ca_non_signe:,.0f} €</b></p>'.replace(",", " "), unsafe_allow_html=True)
        st.dataframe(df_attente, use_container_width=True, hide_index=True)

    with tab2:
        df_signes = df[df["_signe"]][cols_devis] if cols_devis else df[df["_signe"]]
        st.markdown(f'<p style="color:#94A3B8;">{len(df_signes)} devis signés — CA confirmé : <b style="color:#22C55E">{ca_signe:,.0f} €</b></p>'.replace(",", " "), unsafe_allow_html=True)
        st.dataframe(df_signes, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : FACTURES & PAIEMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💶 Factures & Paiements":

    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Factures & Paiements</h1>', unsafe_allow_html=True)

    cols_fact = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT,
                              COL_ACOMPTE1, COL_ACOMPTE2, COL_FACT_FINALE,
                              COL_MODALITE, COL_TVA, COL_STATUT] if c]

    # Impayés = signé mais pas de facture finale
    df_impayes = df[df["_signe"] & ~df["_facture_finale"]]
    ca_impayes = df_impayes["_montant"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("💶 Factures finales émises", int(nb_factures_ok))
    c2.metric("⚠️ Dossiers sans facture finale", len(df_impayes))
    c3.metric("💸 CA à facturer", f"{ca_impayes:,.0f} €".replace(",", " "))

    st.divider()

    tab1, tab2 = st.tabs(["⚠️ À facturer (sans facture finale)", "✅ Facturés"])

    with tab1:
        st.dataframe(df_impayes[cols_fact] if cols_fact else df_impayes, use_container_width=True, hide_index=True)

    with tab2:
        df_fact_ok = df[df["_facture_finale"]]
        st.dataframe(df_fact_ok[cols_fact] if cols_fact else df_fact_ok, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : CHANTIERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏗️ Chantiers":

    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Chantiers</h1>', unsafe_allow_html=True)

    # Statut chantier = PV signé → terminé
    df["_statut_chantier"] = df["_pv"].apply(lambda x: "Terminé ✅" if x else "En cours 🟡")

    c1, c2 = st.columns(2)
    c1.metric("🏗️ En cours", int((~df["_pv"]).sum()))
    c2.metric("✅ Terminés (PV signé)", int(df["_pv"].sum()))

    st.divider()

    cols_chant = [c for c in [COL_CLIENT, COL_CHANTIER, COL_MONTANT, COL_DATE, "_statut_chantier"] if c]
    st.dataframe(df[cols_chant].sort_values("_statut_chantier") if cols_chant else df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE : TOUS LES DOSSIERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Tous les dossiers":

    st.markdown('<h1 style="font-family:Syne,sans-serif;font-size:2rem;">Tous les dossiers</h1>', unsafe_allow_html=True)

    # Recherche
    search = st.text_input("🔍 Rechercher (client, chantier...)", placeholder="Ex: Dupont, cuisine...")
    if search and COL_CLIENT:
        mask = df[COL_CLIENT].astype(str).str.contains(search, case=False, na=False)
        if COL_CHANTIER:
            mask |= df[COL_CHANTIER].astype(str).str.contains(search, case=False, na=False)
        df_filtered = df[mask]
    else:
        df_filtered = df

    st.caption(f"{len(df_filtered)} dossier(s)")
    st.dataframe(df_filtered.drop(columns=["_montant","_signe","_facture_finale","_pv"], errors="ignore"),
                 use_container_width=True, hide_index=True)

# ── Auto-refresh (30 secondes) ────────────────────────────────────────────────
time.sleep(30)
st.rerun()
