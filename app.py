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

# ── THEME (WHITE / DARK MODE) ──────────────────────────────────────────────────
if "themes" not in st.session_state:
    st.session_state.themes = "dark"

def toggle_theme():
    st.session_state.themes = "light" if st.session_state.themes == "dark" else "dark"

if st.session_state.themes == "light":
    theme_css_vars = """
    --bg-app: #F8FAFC;
    --bg-surface: #F1F5F9;
    --bg-card: #FFFFFF;
    --bg-sidebar: #E2E8F0;
    --text-main: #0F172A;
    --text-muted: #475569;
    --text-dim: #94A3B8;
    --border: rgba(0,0,0,0.1);
    --border-hover: rgba(79,142,247,0.5);
    """
    chart_bg = "#FFFFFF"
    chart_font = "#0F172A"
    chart_grid = "#E2E8F0"
else:
    theme_css_vars = """
    --bg-app: #080f1a;
    --bg-surface: #0f1e30;
    --bg-card: #132238;
    --bg-sidebar: #060d18;
    --text-main: #e8f0fe;
    --text-muted: #6b84a3;
    --text-dim: #3d5473;
    --border: rgba(255,255,255,0.06);
    --border-hover: rgba(79,142,247,0.35);
    """
    chart_bg = "rgba(0,0,0,0)"
    chart_font = "#e8f0fe"
    chart_grid = "rgba(255,255,255,0.06)"

# ── CSS PREMIUM ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {{
    {theme_css_vars}
    --primary: #4f8ef7;
    --primary-glow: rgba(79,142,247,0.15);
    --success: #00d68f;
    --success-glow: rgba(0,214,143,0.12);
    --warning: #ffb84d;
    --warning-glow: rgba(255,184,77,0.12);
    --danger: #ff5c7a;
    --radius: 14px;
    --radius-sm: 8px;
}}

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--bg-app) !important;
    font-family: 'Inter', sans-serif;
    color: var(--text-main);
    -webkit-font-smoothing: antialiased;
}}

[data-testid="stDataFrame"] div[role="grid"] div[role="row"]:hover {{
    background-color: rgba(79, 142, 247, 0.15) !important;
    transition: background 0.2s ease;
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-surface) 100%) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] > div {{ padding: 0 !important; }}

::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--text-dim); border-radius: 99px; }}

[data-testid="stMetric"] {{
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 22px !important;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease;
}}
[data-testid="stMetric"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary), transparent);
    opacity: 0.6;
}}
[data-testid="stMetric"]:hover {{ transform: translateY(-2px); border-color: var(--border-hover); }}
[data-testid="stMetric"] label {{
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}
[data-testid="stMetricValue"] {{
    color: var(--text-main) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: var(--bg-surface);
    border-radius: var(--radius-sm);
    padding: 4px;
    border: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 6px !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 8px 18px !important;
    transition: all 0.15s ease;
}}
.stTabs [aria-selected="true"] {{
    background: var(--primary) !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 12px rgba(79,142,247,0.3) !important;
}}

.stButton > button {{
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    color: var(--text-main) !important;
    padding: 8px 16px !important;
}}
.stButton > button:hover {{
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: var(--primary-glow) !important;
    transform: translateY(-1px);
}}

.stTextInput input, .stNumberInput input, .stSelectbox select,
[data-testid="stTextArea"] textarea {{
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-main) !important;
    font-family: 'Inter', sans-serif !important;
}}

[data-testid="stDataFrame"] {{
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
}}

hr {{ border-color: var(--border) !important; margin: 16px 0 !important; }}

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
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {{ background: var(--bg-card); border-color: var(--border); }}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
    background: linear-gradient(135deg, var(--primary-glow), rgba(79,142,247,0.08)) !important;
    border-color: rgba(79,142,247,0.4) !important;
}}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p {{ color: var(--primary) !important; font-weight: 700 !important; }}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p {{ margin: 0; font-size: 0.92rem; color: var(--text-muted); }}

.pulse-dot {{
    display: inline-block; width: 7px; height: 7px;
    border-radius: 50%; background: var(--success);
    animation: pulse-anim 2s ease-in-out infinite;
    margin-right: 6px; vertical-align: middle;
}}
@keyframes pulse-anim {{ 0%, 100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: 0.4; transform: scale(0.85); }} }}

.page-header {{ padding: 8px 0 24px; border-bottom: 1px solid var(--border); margin-bottom: 28px; }}
.page-header h1 {{ font-family: 'Inter', sans-serif !important; font-size: 1.9rem !important; font-weight: 800 !important; letter-spacing: -0.03em; margin: 0 !important; color: var(--text-main) !important; }}
.page-header .subtitle {{ color: var(--text-muted); font-size: 0.88rem; margin-top: 4px; }}

.client-alert-card {{
    display:flex; align-items:center; gap:12px; padding:10px 14px;
    background:rgba(255,184,77,0.06); border:1px solid rgba(255,184,77,0.15);
    border-radius:8px; margin-bottom:8px; cursor:pointer;
    transition: border-color 0.2s, background 0.2s;
    text-decoration: none;
}}
.client-alert-card:hover {{
    background: rgba(79,142,247,0.1);
    border-color: rgba(79,142,247,0.4);
}}
</style>
""", unsafe_allow_html=True)

# ── AUTH ───────────────────────────────────────────────────────────────────────
if not check_login():
    st.stop()

# ── CONFIG GOOGLE SHEETS & DRIVE ───────────────────────────────────────────────
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

# ── HELPERS & FONCTIONS D'AFFICHAGE ────────────────────────────────────────────
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

def style_relances(row):
    r3_col = next((c for c in row.index if "relance 3" in str(c).lower()), None)
    st_col = next((c for c in row.index if "statut" in str(c).lower()), None)
    
    if r3_col and st_col:
        r3_val = str(row.get(r3_col, "")).strip()
        st_val = str(row.get(st_col, "")).lower()
        if r3_val != "" and "envoyé" not in st_val:
            return ['background-color: rgba(255, 92, 122, 0.25); color: #ff5c7a; font-weight: bold;'] * len(row)
    return [''] * len(row)

LIMIT = 100

def show_table(dataframe, key_suffix=""):
    total = len(dataframe)
    if total == 0:
        st.info("Aucun dossier trouvé.")
        return
        
    show_all = st.session_state.get(f"show_all_{key_suffix}", False)
    displayed = dataframe if show_all else dataframe.head(LIMIT)
    
    if isinstance(displayed, pd.DataFrame):
        styled_df = displayed.style.apply(style_relances, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
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
                <div style='font-family:Inter,sans-serif;font-weight:800;font-size:0.95rem;color:var(--text-main);'>Florian AI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.button("🌓 Basculer Thème", on_click=toggle_theme, use_container_width=True)
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    user = st.session_state.get("username", "")
    role = st.session_state.get("role", "viewer")

    st.markdown("<div style='padding: 0 12px;'>", unsafe_allow_html=True)
    
    pages = [
        "📊 Vue Générale",
        "📋 Devis",
        "💶 Factures & Paiements",
        "🏗️ Chantiers",
        "📅 Planning",
        "🗂️ Espace Clients", 
        "📁 Tous les dossiers",
        "📝 Éditeur Google Sheet",
        "📞 Coordonnées & RGPD"
    ]
    if role == "admin":
        pages.append("👥 Utilisateurs")

    # Handle navigation override from session state (e.g. click on client card)
    if "nav_override" in st.session_state:
        default_idx = pages.index(st.session_state["nav_override"]) if st.session_state["nav_override"] in pages else 0
        del st.session_state["nav_override"]
    else:
        default_idx = 0

    page = st.radio("Navigation", pages, label_visibility="collapsed", index=st.session_state.get("_page_index", default_idx))
    # Store current page index
    if page in pages:
        st.session_state["_page_index"] = pages.index(page)
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='position:absolute;bottom:0;left:0;right:0;padding:16px;border-top:1px solid rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;'>
        <div style='width:32px;height:32px;background:linear-gradient(135deg,#132238,#1e3a5f);
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:0.85rem;border:1px solid rgba(79,142,247,0.3); color:#fff;'>
            {user[0].upper() if user else '?'}
        </div>
        <div>
            <div style='font-weight:600;font-size:0.85rem;color:var(--text-main);'>{user}</div>
            <div style='font-size:0.72rem;color:var(--text-muted);'>{role}</div>
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

# ── NAVIGATE TO ESPACE CLIENTS (triggered by clicking a client card) ───────────
if st.session_state.get("_goto_espace_clients"):
    st.session_state["_goto_espace_clients"] = False
    st.session_state["_page_index"] = pages.index("🗂️ Espace Clients")
    st.rerun()

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

elif page == "📞 Coordonnées & RGPD":
    page_header("📞 Coordonnées & RGPD", "Informations légales et contact")
    st.markdown(f"""
    <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius); padding:24px; margin-bottom:20px;">
        <h3 style="color:var(--primary); margin-top:0;">👤 Contact Développeur</h3>
        <p style="font-size:1.1rem; color:var(--text-main);"><strong>Email :</strong> <a href="mailto:flogagnebien611@gmail.com" style="color:var(--primary);">flogagnebien611@gmail.com</a></p>
        <p style="font-size:1.1rem; color:var(--text-main);"><strong>Téléphone :</strong> 06 33 79 05 42</p>
    </div>
    
    <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius); padding:24px;">
        <h3 style="color:var(--primary); margin-top:0;">🛡️ Conformité RGPD</h3>
        <p style="color:var(--text-main);">Cette application respecte le <strong>Règlement Général sur la Protection des Données (RGPD)</strong>.</p>
        <ul style="color:var(--text-muted); line-height:1.6;">
            <li><strong>Finalité :</strong> Les données collectées via Google Drive et Sheets sont utilisées exclusivement pour la gestion opérationnelle de votre activité.</li>
            <li><strong>Sécurité :</strong> L'accès est sécurisé par authentification et via les protocoles de sécurité officiels de l'API Google.</li>
            <li><strong>Droit d'accès :</strong> Vous disposez d'un droit permanent de modification et de suppression de vos données via l'éditeur intégré ou directement sur votre Google Sheet source.</li>
            <li><strong>Conservation :</strong> Aucune donnée personnelle n'est stockée sur nos serveurs en dehors des identifiants de connexion nécessaires à la session.</li>
        </ul>
        <p style="font-style:italic; font-size:0.85rem; color:var(--text-dim);">Pour toute question relative à vos données, contactez l'administrateur via les coordonnées ci-dessus.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# NOUVELLE PAGE : ESPACE CLIENTS (GOOGLE DRIVE)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗂️ Espace Clients":
    page_header("🗂️ Espace Clients", "Documents et dossiers synchronisés avec Google Drive")

    # Pre-fill search if navigated from a client card click
    prefill_client = st.session_state.pop("_prefill_client_search", "")

    def get_google_doc_content(file_id, mime_type, drive_service):
        try:
            if 'application/vnd.google-apps.document' in mime_type:
                request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
                return request.execute().decode('utf-8')
            elif 'text/plain' in mime_type:
                request = drive_service.files().get_media(fileId=file_id)
                return request.execute().decode('utf-8')
            return None
        except Exception:
            return None

    try:
        from googleapiclient.discovery import build
        
        sheet_name, gsa_json = get_user_credentials(user)
        if not gsa_json:
            st.error("Identifiants Google introuvables pour ce compte.")
            st.stop()
            
        creds = Credentials.from_service_account_info(json.loads(gsa_json), scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)

        query_main = "name = 'espace clients' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_main = drive_service.files().list(q=query_main, fields="files(id, name)").execute()
        main_folders = res_main.get('files', [])

        if not main_folders:
            st.warning("⚠️ Dossier principal 'espace clients' introuvable sur le Google Drive.")
        else:
            main_folder_id = main_folders[0]['id']

            query_clients = f"'{main_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res_clients = drive_service.files().list(q=query_clients, fields="files(id, name)", pageSize=1000).execute()
            client_folders = res_clients.get('files', [])

            if not client_folders:
                st.info("Aucun dossier client trouvé dans 'espace clients'.")
            else:
                client_folders = sorted(client_folders, key=lambda x: x['name'].lower())
                client_names = [f["name"] for f in client_folders]
                
                search_client = st.text_input("🔍 Rechercher un client :", placeholder="Tapez le nom d'un client...", value=prefill_client)
                
                filtered_client_names = [name for name in client_names if search_client.lower() in name.lower()]
                
                if not filtered_client_names:
                    st.warning("Aucun client ne correspond à votre recherche.")
                else:
                    selected_client_name = st.selectbox("👤 Sélectionnez un client :", filtered_client_names)
                    selected_client_id = next(f['id'] for f in client_folders if f['name'] == selected_client_name)

                    st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
                    st.subheader(f"📂 Fichiers de : {selected_client_name}")

                    query_files = f"'{selected_client_id}' in parents and trashed = false"
                    res_files = drive_service.files().list(q=query_files, fields="files(id, name, mimeType, webViewLink)", orderBy="folder, name", pageSize=1000).execute()
                    files = res_files.get('files', [])

                    def display_file(f_dict):
                        mime = f_dict.get('mimeType', '').lower()
                        icon = "📄"
                        if "folder" in mime: icon = "📁"
                        elif "pdf" in mime: icon = "📕"
                        elif "image" in mime: icon = "🖼️"
                        elif "spreadsheet" in mime or "sheet" in mime or "excel" in mime: icon = "📊"
                        elif "document" in mime or "word" in mime: icon = "📝"

                        st.markdown(f"""
                        <a href="{f_dict.get('webViewLink', '#')}" target="_blank" style="text-decoration:none;">
                            <div style="display:flex; align-items:center; gap:12px; padding:10px 16px; background:var(--bg-surface); border:1px solid var(--border); border-radius:8px; margin-bottom:8px; transition:0.2s;">
                                <div style="font-size:1.2rem;">{icon}</div>
                                <div style="color:var(--text-main); font-weight:600; font-size:0.9rem;">{f_dict.get('name')}</div>
                                <div style="margin-left:auto; color:var(--primary); font-size:0.75rem; font-weight:600;">Ouvrir ↗</div>
                            </div>
                        </a>
                        """, unsafe_allow_html=True)

                    if not files:
                        st.info("Ce dossier client est vide.")
                    else:
                        for file in files:
                            mime_type = file.get('mimeType', '')
                            
                            if mime_type == 'application/vnd.google-apps.folder':
                                with st.expander(f"📁 **{file.get('name')}**"):
                                    sub_query = f"'{file.get('id')}' in parents and trashed = false"
                                    sub_res = drive_service.files().list(q=sub_query, fields="files(id, name, mimeType, webViewLink)", orderBy="folder, name", pageSize=1000).execute()
                                    sub_files = sub_res.get('files', [])
                                    
                                    if not sub_files:
                                        st.caption("Ce dossier est vide.")
                                    else:
                                        is_infos_clients = (file.get('name').strip().lower() in ["infos clients", "info client", "infos client"])
                                        
                                        for sub_file in sub_files:
                                            sub_mime = sub_file.get('mimeType', '').lower()
                                            
                                            if is_infos_clients and ('document' in sub_mime or 'text' in sub_mime):
                                                content = get_google_doc_content(sub_file['id'], sub_mime, drive_service)
                                                if content:
                                                    st.markdown(f"""
                                                    <div style="background:var(--bg-surface); border:1px solid var(--border); border-radius:8px; padding:16px; margin-bottom:12px;">
                                                        <div style="font-weight:700; color:var(--primary); margin-bottom:8px;">📝 {sub_file.get('name')}</div>
                                                        <div style="white-space: pre-wrap; font-size:0.9rem; color:var(--text-main);">{content}</div>
                                                    </div>
                                                    """, unsafe_allow_html=True)
                                                else:
                                                    display_file(sub_file) 
                                            else:
                                                display_file(sub_file)
                            else:
                                display_file(file)

    except ImportError:
        st.error("🚨 La bibliothèque 'google-api-python-client' n'est pas installée.")
        st.info("Ajoute `google-api-python-client>=2.0.0` dans ton fichier **requirements.txt**.")
    except Exception as e:
        st.error(f"Erreur de communication avec Google Drive : {e}")

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
                    st.markdown("<div style='font-weight:700;font-size:1rem;color:var(--text-main);margin-bottom:12px;'>📅 Période du graphique</div>", unsafe_allow_html=True)
                    col_dt1, col_dt2 = st.columns(2)
                    min_dt = d2["_date"].min().date()
                    max_dt = d2["_date"].max().date()
                    with col_dt1:
                        start_dt = st.date_input("Du", value=min_dt, key="start_dt")
                    with col_dt2:
                        end_dt = st.date_input("Au", value=max_dt, key="end_dt")
                    
                    d2 = d2[(d2["_date"].dt.date >= start_dt) & (d2["_date"].dt.date <= end_dt)]
                    
                    if d2.empty:
                        st.info("Aucune donnée sur cette période.")
                    else:
                        # ── COURBE MULTI-LIGNES (style graphique boursier) ──────────────────
                        d2["_mois"] = d2["_date"].dt.to_period("M").dt.to_timestamp()

                        # CA Signé cumulé par mois
                        ca_signe_m = (
                            d2[d2["_signe"]]
                            .groupby("_mois")["_montant"].sum()
                            .reset_index()
                            .rename(columns={"_montant": "CA Signé ✅"})
                        )
                        # CA En attente cumulé par mois
                        ca_attente_m = (
                            d2[~d2["_signe"]]
                            .groupby("_mois")["_montant"].sum()
                            .reset_index()
                            .rename(columns={"_montant": "CA En attente ⏳"})
                        )
                        # CA Total par mois
                        ca_total_m = (
                            d2.groupby("_mois")["_montant"].sum()
                            .reset_index()
                            .rename(columns={"_montant": "CA Total 📊"})
                        )

                        # Merge on mois
                        all_months = pd.DataFrame({"_mois": sorted(d2["_mois"].unique())})
                        merged = all_months.copy()
                        merged = merged.merge(ca_total_m, on="_mois", how="left")
                        merged = merged.merge(ca_signe_m, on="_mois", how="left")
                        merged = merged.merge(ca_attente_m, on="_mois", how="left")
                        merged = merged.fillna(0)

                        fig = go.Figure()

                        # CA Total — courbe principale (bleu clair)
                        fig.add_trace(go.Scatter(
                            x=merged["_mois"],
                            y=merged["CA Total 📊"],
                            name="CA Total",
                            mode="lines+markers",
                            line=dict(color="#4f8ef7", width=2.5, shape="spline"),
                            marker=dict(size=6, color="#4f8ef7"),
                            fill="tozeroy",
                            fillcolor="rgba(79,142,247,0.07)",
                        ))

                        # CA Signé — courbe verte
                        fig.add_trace(go.Scatter(
                            x=merged["_mois"],
                            y=merged["CA Signé ✅"],
                            name="CA Signé",
                            mode="lines+markers",
                            line=dict(color="#00d68f", width=2.5, shape="spline"),
                            marker=dict(size=6, color="#00d68f"),
                            fill="tozeroy",
                            fillcolor="rgba(0,214,143,0.07)",
                        ))

                        # CA En attente — courbe orange
                        fig.add_trace(go.Scatter(
                            x=merged["_mois"],
                            y=merged["CA En attente ⏳"],
                            name="CA En attente",
                            mode="lines+markers",
                            line=dict(color="#ffb84d", width=2, shape="spline", dash="dot"),
                            marker=dict(size=5, color="#ffb84d"),
                        ))

                        fig.update_layout(
                            title=dict(
                                text="📈 Évolution du CA par mois",
                                font=dict(size=14, color=chart_font, family="Inter"),
                            ),
                            paper_bgcolor=chart_bg,
                            plot_bgcolor=chart_bg,
                            font=dict(color=chart_font, family="Inter"),
                            xaxis=dict(
                                showgrid=True,
                                gridcolor=chart_grid,
                                title="",
                                tickfont=dict(color=chart_font, size=11),
                                tickformat="%b %Y",
                                showline=False,
                                zeroline=False,
                            ),
                            yaxis=dict(
                                gridcolor=chart_grid,
                                title="CA (€)",
                                tickfont=dict(color=chart_font, size=11),
                                showline=False,
                                zeroline=False,
                            ),
                            legend=dict(
                                bgcolor="rgba(255,255,255,0.05)",
                                bordercolor=chart_grid,
                                borderwidth=1,
                                font=dict(color=chart_font, size=11),
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="left",
                                x=0,
                            ),
                            hovermode="x unified",
                            margin=dict(t=60, b=20, l=20, r=20),
                        )

                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Colonne 'Date creation devis' non détectée pour le graphique.")

    with cr:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:1rem;color:#ffb84d;margin-bottom:12px;'>🚨 Actions Requises</div>", unsafe_allow_html=True)

            df_alertes_all = df[~df["_signe"]]
            ALERT_PREVIEW = 6

            # ── Session state pour "voir plus" dans Actions Requises ───────────
            if "alertes_show_all" not in st.session_state:
                st.session_state["alertes_show_all"] = False

            df_alertes_display = df_alertes_all if st.session_state["alertes_show_all"] else df_alertes_all.head(ALERT_PREVIEW)

            if len(df_alertes_all) > 0:
                for idx, (_, row) in enumerate(df_alertes_display.iterrows()):
                    client = str(row[COL_CLIENT]) if COL_CLIENT else "Inconnu"
                    montant = fmt(row["_montant"])
                    chantier = row[COL_CHANTIER] if COL_CHANTIER else ""
                    num_devis = row[COL_NUM] if COL_NUM else ""
                    date_creation = row[COL_DATE] if COL_DATE else ""

                    tooltip_parts = [client]
                    if chantier and str(chantier).strip():
                        tooltip_parts.append(str(chantier))
                    if num_devis and str(num_devis).strip():
                        tooltip_parts.append(f"Devis: {num_devis}")
                    if date_creation and str(date_creation).strip():
                        tooltip_parts.append(str(date_creation))
                    tooltip = " • ".join(tooltip_parts)

                    # Button-driven navigation to Espace Clients
                    btn_col, card_col = st.columns([0.08, 0.92])
                    with card_col:
                        st.markdown(f"""
                        <div title="{tooltip}" style="display:flex; align-items:center; gap:12px; padding:10px 14px; background:rgba(255,184,77,0.06); border:1px solid rgba(255,184,77,0.15); border-radius:8px; margin-bottom:4px;">
                            <div style="font-size:1.1rem; flex-shrink:0;">📄</div>
                            <div style="flex:1; min-width:0;">
                                <div style="font-weight:600; font-size:0.88rem; color:var(--text-main); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{client}</div>
                                <div style="font-size:0.78rem; color:var(--text-muted);">{montant}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with btn_col:
                        if st.button("↗", key=f"goto_client_{idx}_{client}", help=f"Ouvrir dossier {client}"):
                            st.session_state["_prefill_client_search"] = client
                            st.session_state["_page_index"] = pages.index("🗂️ Espace Clients")
                            st.rerun()

                # ── Bouton Voir Plus / Réduire ─────────────────────────────────
                if nb_attente > ALERT_PREVIEW:
                    if not st.session_state["alertes_show_all"]:
                        remaining = nb_attente - ALERT_PREVIEW
                        if st.button(f"📂 Voir les {remaining} autres devis en attente", use_container_width=True, key="btn_alertes_more"):
                            st.session_state["alertes_show_all"] = True
                            st.rerun()
                    else:
                        if st.button("🔼 Réduire", use_container_width=True, key="btn_alertes_less"):
                            st.session_state["alertes_show_all"] = False
                            st.rerun()
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
                                     font_size=28, font_color=chart_font,
                                     font_family="Inter", showarrow=False)
            fig_donut.update_layout(
                title="Taux de transformation", title_font_color=chart_font,
                paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", font_color=chart_font),
                margin=dict(t=40, b=20, l=20, r=20), height=250,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
    with col_d2:
        with st.container(border=True):
            st.markdown("<div style='font-weight:700;font-size:0.95rem;color:var(--text-main);margin-bottom:16px;'>📊 Résumé financier</div>", unsafe_allow_html=True)
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
                    padding:8px 0;border-bottom:1px solid var(--border);'>
                    <span style='color:var(--text-muted);font-size:0.85rem;'>{label}</span>
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
    
    valid_rename_map = {
        COL_CLIENT: "Client",
        COL_CHANTIER: "Projet / Chantier",
        COL_MONTANT: "Budget (€)",
        COL_ADRESSE: "Lieu des travaux",
        COL_DATE_DEBUT: "Début",
        COL_DATE_FIN: "Fin prévue",
        COL_RESERVE: "Réserves",
        "_statut_ch": "État d'avancement"
    }

    t1, t2 = st.tabs(["🟡 En cours", "✅ Livrés (PV signé)"])
    with t1:
        d = df_ch[~df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) actif(s) — {fmt(d['_montant'].sum())}")
        d_renamed = d[cols_ch].rename(columns=valid_rename_map) if cols_ch else d
        show_table(d_renamed.reset_index(drop=True), "ch_cours")
    with t2:
        d = df_ch[df_ch["_pv"]]
        st.caption(f"{len(d)} chantier(s) livré(s) — {fmt(d['_montant'].sum())}")
        d_renamed = d[cols_ch].rename(columns=valid_rename_map) if cols_ch else d
        show_table(d_renamed.reset_index(drop=True), "ch_termines")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PLANNING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Planning":
    page_header("Planning des Chantiers", "Vue calendrier des interventions")

    if not COL_DATE_DEBUT or not COL_DATE_FIN:
        st.warning("⚠️ Colonnes de dates non détectées.")
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
        if row["_pv"]: return "termine"
        if row["_end"].date() < today.date(): return "retard"
        return "en-cours"

    df_plan["_statut_code"] = df_plan.apply(get_statut_code, axis=1)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🟡 En cours", int((df_plan["_statut_code"] == "en-cours").sum()))
    k2.metric("🔴 En retard", int((df_plan["_statut_code"] == "retard").sum()))
    k3.metric("✅ Terminés", int((df_plan["_statut_code"] == "termine").sum()))
    k4.metric("📅 Démarrent (7j)", int(((df_plan["_start"].dt.date >= today.date()) & (df_plan["_start"].dt.date <= (today + timedelta(days=7)).date())).sum()))

    st.markdown("<br>", unsafe_allow_html=True)
    view_mode = st.radio("Vue", ["📅 Calendrier mensuel", "📊 Gantt", "📋 Liste"], horizontal=True, key="plan_view")
    st.markdown("<br>", unsafe_allow_html=True)

    if view_mode == "📅 Calendrier mensuel":
        if "plan_year" not in st.session_state: st.session_state["plan_year"] = today.year
        if "plan_month" not in st.session_state: st.session_state["plan_month"] = today.month

        mois_fr = ["","Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("◀ Mois Précédent", use_container_width=True):
                if st.session_state["plan_month"] == 1:
                    st.session_state["plan_month"] = 12
                    st.session_state["plan_year"] -= 1
                else: st.session_state["plan_month"] -= 1
                st.rerun()
        with nav2:
            st.markdown(f"<h2 style='text-align:center;margin:0;color:var(--text-main);'>{mois_fr[st.session_state['plan_month']]} {st.session_state['plan_year']}</h2>", unsafe_allow_html=True)
        with nav3:
            if st.button("Mois Suivant ▶", use_container_width=True):
                if st.session_state["plan_month"] == 12:
                    st.session_state["plan_month"] = 1
                    st.session_state["plan_year"] += 1
                else: st.session_state["plan_month"] += 1
                st.rerun()

        sel_y, sel_m = st.session_state["plan_year"], st.session_state["plan_month"]
        
        days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        cal_grid = calendar.monthcalendar(sel_y, sel_m)
        
        with st.container(border=True):
            cols_h = st.columns(7)
            for i, d in enumerate(days_fr):
                cols_h[i].markdown(f"<div style='text-align:center; font-weight:bold; color:var(--primary);'>{d}</div>", unsafe_allow_html=True)
            
            for week in cal_grid:
                cols_w = st.columns(7)
                for i, day in enumerate(week):
                    if day != 0:
                        current_date = datetime(sel_y, sel_m, day).date()
                        evs = df_plan[(df_plan["_start"].dt.date <= current_date) & (df_plan["_end"].dt.date >= current_date)]
                        
                        label = str(day)
                        if not evs.empty:
                            if "retard" in evs["_statut_code"].values: label += " 🔴"
                            elif "en-cours" in evs["_statut_code"].values: label += " 🔵"
                            else: label += " 🟢"
                        
                        if cols_w[i].button(label, key=f"d_{sel_y}_{sel_m}_{day}", use_container_width=True):
                            st.session_state["selected_date"] = datetime(sel_y, sel_m, day)

        if "selected_date" in st.session_state:
            sd = st.session_state["selected_date"]
            st.markdown(f"### 📋 Chantiers du {sd.strftime('%d/%m/%Y')}")
            day_events = df_plan[(df_plan["_start"].dt.date <= sd.date()) & (df_plan["_end"].dt.date >= sd.date())]
            if not day_events.empty:
                for _, row in day_events.iterrows():
                    color = "#ff5c7a" if row['_statut_code']=="retard" else "#00d68f" if row['_statut_code']=="termine" else "#4f8ef7"
                    st.markdown(f"""
                    <div style="border-left: 4px solid {color}; padding: 12px; background: var(--bg-surface); border-radius: 6px; margin-bottom: 10px; border-top: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border);">
                        <div style="font-weight:bold; color:var(--text-main); font-size:1rem;">{row[COL_CHANTIER]}</div>
                        <div style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">👤 Client : {row[COL_CLIENT]}</div>
                        <div style="font-size:0.85rem; color:var(--text-muted);">📍 Lieu : {row.get(COL_ADRESSE, 'Non renseigné')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("Aucun chantier prévu ce jour.")

    elif view_mode == "📊 Gantt":
        df_gantt = df_plan.sort_values("_start")
        fig_gantt = px.timeline(df_gantt, x_start="_start", x_end="_end", y=COL_CHANTIER or COL_CLIENT, color="_statut_code", 
                               color_discrete_map={"en-cours": "#4f8ef7", "retard": "#ff5c7a", "termine": "#00d68f"})
        fig_gantt.update_layout(
            paper_bgcolor=chart_bg, 
            plot_bgcolor=chart_bg, 
            font_color=chart_font, 
            margin=dict(t=20, b=20, l=10, r=10), 
            height=400,
            xaxis=dict(gridcolor=chart_grid),
            yaxis=dict(gridcolor=chart_grid)
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

    elif view_mode == "📋 Liste":
        cols_l = [c for c in [COL_CLIENT, COL_CHANTIER, "_start", "_end", "_statut_code"] if c]
        df_list = df_plan[cols_l].sort_values("_start")
        show_table(df_list, "plan_list")

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
                  "_statut_ch","_start","_end","_statut_code","_mois_str","_mois_ord"]
    show_table(d.drop(columns=drop_cols, errors="ignore").reset_index(drop=True), "all")
