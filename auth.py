import streamlit as st
import hashlib
import json
import os
import secrets
import string

# ══════════════════════════════════════════════════════════════════════════════
# STOCKAGE DES USERS
# ══════════════════════════════════════════════════════════════════════════════
# Streamlit Cloud est READ-ONLY → on ne peut pas écrire sur disque.
# Les users sont stockés dans st.secrets sous la clé USERS_DB (JSON string).
#
# Dans Streamlit Cloud → Settings → Secrets, ajoute :
#
#   SHEET_NAME = "Prestation1"
#   GOOGLE_SERVICE_ACCOUNT = '''{ ... }'''
#   USERS_DB = '''{}'''
#
# Quand tu crées un user via le panel admin, le nouveau users.json est affiché
# à l'écran pour que tu le copie-colles dans les Secrets Streamlit.
#
# Structure USERS_DB :
# {
#   "dupont_elec": {
#     "password": "<sha256>",
#     "role": "viewer",
#     "sheet_name": "SheetDupont",
#     "google_sa": "{...json...}"
#   }
# }
# Note : florian (admin) n'est PAS dans USERS_DB — il est toujours dans st.secrets.
# ══════════════════════════════════════════════════════════════════════════════

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _load_users() -> dict:
    """
    Charge les users depuis st.secrets["USERS_DB"] (JSON string).
    Florian (admin) est géré séparément via st.secrets["ADMIN_PASSWORD"].
    """
    users = {}
    try:
        raw = st.secrets.get("USERS_DB", "{}")
        users = json.loads(raw) if raw else {}
    except Exception:
        users = {}

    # Injecter florian depuis st.secrets (toujours présent, jamais dans USERS_DB)
    admin_pwd_hash = st.secrets.get("ADMIN_PASSWORD", _hash("florian2024"))
    users["florian"] = {
        "password":   admin_pwd_hash,
        "role":       "admin",
        "sheet_name": None,   # → lire depuis st.secrets["SHEET_NAME"]
        "google_sa":  None,   # → lire depuis st.secrets["GOOGLE_SERVICE_ACCOUNT"]
    }
    return users

def get_user_credentials(username: str):
    """
    Retourne (sheet_name, google_sa_json_str) pour le user connecté.
    - florian → st.secrets["SHEET_NAME"] + st.secrets["GOOGLE_SERVICE_ACCOUNT"]
    - autres  → valeurs stockées dans st.secrets["USERS_DB"]
    """
    users = _load_users()
    u = users.get(username, {})
    sheet = u.get("sheet_name")
    gsa   = u.get("google_sa")

    if not sheet:
        sheet = st.secrets.get("SHEET_NAME", "")
    if not gsa:
        gsa = st.secrets.get("GOOGLE_SERVICE_ACCOUNT", "")

    return sheet, gsa

def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))

# ── CSS page login ─────────────────────────────────────────────────────────────
_LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0F2942 0%, #0D1F33 100%) !important;
    font-family: 'DM Sans', sans-serif;
    color: #F8FAFC;
}
[data-testid="stForm"] {
    background: rgba(19,34,54,0.95);
    border-radius: 16px;
    padding: 28px 24px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.4);
    border: 1px solid #1E3A5F;
}
.stButton > button {
    background: linear-gradient(135deg, #22C55E, #16A34A) !important;
    color: #0F2942 !important; border: none !important;
    border-radius: 9px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 900 !important; font-size: 1rem !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
[data-testid="stTextInput"] label { color: #94A3B8 !important; font-weight: 600; }
</style>
"""

# ── Login ──────────────────────────────────────────────────────────────────────
def check_login() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=180)
        else:
            st.markdown(
                "<div style='text-align:center;font-size:3.5rem;padding:24px 0'>⚡</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div style='text-align:center;padding-bottom:20px;'>"
            "<div style='color:#94A3B8;font-size:0.8rem;letter-spacing:2px;"
            "text-transform:uppercase;'>ERP – Accès sécurisé</div></div>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username  = st.text_input("👤 Identifiant", placeholder="florian")
            password  = st.text_input("🔒 Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            users = _load_users()
            u = users.get(username)  # None si user inexistant
            if u is not None and u.get("password") == _hash(password):
                st.session_state["authenticated"] = True
                st.session_state["username"]      = username
                st.session_state["role"]          = u.get("role", "viewer")
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect.")

    return False

def logout():
    for k in ["authenticated", "username", "role"]:
        st.session_state.pop(k, None)

# ── Panel admin ────────────────────────────────────────────────────────────────
def admin_panel():
    st.markdown('<h1 style="font-size:2rem;">👥 Gestion des utilisateurs</h1>', unsafe_allow_html=True)

    # Charger USERS_DB (sans florian)
    try:
        raw = st.secrets.get("USERS_DB", "{}")
        users_db = json.loads(raw) if raw else {}
    except Exception:
        users_db = {}

    # ── Liste ──────────────────────────────────────────────────────────────────
    st.markdown("### Utilisateurs existants")

    # Florian (admin, depuis secrets)
    c1, c2, _ = st.columns([3, 4, 1])
    c1.markdown("**florian** *(admin)*")
    sheet_f = st.secrets.get("SHEET_NAME", "—")
    c2.caption(f"Sheet : `{sheet_f}` — credentials depuis Streamlit Secrets")

    for uname, udata in list(users_db.items()):
        c1, c2, c3 = st.columns([3, 4, 1])
        c1.markdown(f"**{uname}**")
        role  = udata.get("role", "viewer")
        sheet = udata.get("sheet_name", "—")
        c2.caption(f"`{role}` — Sheet : `{sheet}`")
        if c3.button("🗑️", key=f"del_{uname}"):
            del users_db[uname]
            _show_updated_secrets(users_db)
            st.rerun()

    st.divider()

    # ── Créer un user ──────────────────────────────────────────────────────────
    st.markdown("### ➕ Créer un utilisateur")
    with st.form("create_user_form"):
        new_username = st.text_input("Identifiant (login)", placeholder="dupont_elec")
        new_role     = st.selectbox("Rôle", ["viewer", "comptable", "admin"])
        new_password = st.text_input(
            "Mot de passe (laisser vide = généré automatiquement)",
            type="password",
        )
        new_sheet = st.text_input(
            "SHEET_NAME — nom exact du Google Sheet",
            placeholder="SonGoogleSheet"
        )
        new_gsa = st.text_area(
            "GOOGLE_SERVICE_ACCOUNT — JSON complet du compte de service",
            placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  ...\n}',
            height=220,
        )
        submitted_create = st.form_submit_button("✅ Créer l'utilisateur", use_container_width=True)

    if submitted_create:
        err = None
        if not new_username.strip():
            err = "L'identifiant ne peut pas être vide."
        elif new_username == "florian":
            err = "Le nom 'florian' est réservé à l'admin."
        elif new_username in users_db:
            err = f"L'identifiant **{new_username}** existe déjà."
        elif not new_sheet.strip():
            err = "Le SHEET_NAME est obligatoire."
        elif not new_gsa.strip():
            err = "Le JSON Google Service Account est obligatoire."
        else:
            try:
                json.loads(new_gsa.strip())
            except json.JSONDecodeError as e:
                err = f"JSON invalide : {e}"

        if err:
            st.error(err)
        else:
            pwd = new_password.strip() if new_password.strip() else _generate_password()
            users_db[new_username] = {
                "password":   _hash(pwd),
                "role":       new_role,
                "sheet_name": new_sheet.strip(),
                "google_sa":  new_gsa.strip(),
            }
            st.success(f"✅ User **{new_username}** créé avec le rôle `{new_role}`.")
            if not new_password.strip():
                st.info(f"🔑 Mot de passe généré : `{pwd}`  — notez-le, il ne sera plus affiché.")
            _show_updated_secrets(users_db)

    st.divider()

    # ── Changer le mot de passe admin ─────────────────────────────────────────
    st.markdown("### 🔑 Changer le mot de passe admin (florian)")
    with st.form("change_pwd_form"):
        old_pwd  = st.text_input("Ancien mot de passe", type="password")
        new_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2 = st.text_input("Confirmer le nouveau", type="password")
        chg = st.form_submit_button("Mettre à jour", use_container_width=True)

    if chg:
        current_hash = st.secrets.get("ADMIN_PASSWORD", _hash("florian2024"))
        if _hash(old_pwd) != current_hash:
            st.error("Ancien mot de passe incorrect.")
        elif new_pwd1 != new_pwd2:
            st.error("Les deux mots de passe ne correspondent pas.")
        elif len(new_pwd1) < 8:
            st.error("Minimum 8 caractères.")
        else:
            new_hash = _hash(new_pwd1)
            st.success("✅ Nouveau hash généré. Mets à jour ADMIN_PASSWORD dans les Secrets :")
            st.code(f'ADMIN_PASSWORD = "{new_hash}"', language="toml")

def _show_updated_secrets(users_db: dict):
    """Affiche le USERS_DB mis à jour à copier-coller dans Streamlit Secrets."""
    updated_json = json.dumps(users_db, ensure_ascii=False, indent=2)
    st.warning(
        "⚠️ **Action requise** — Streamlit Cloud ne permet pas l'écriture sur disque.\n\n"
        "Copie ce contenu et colle-le dans **Streamlit Cloud → Settings → Secrets** "
        "à la place de la valeur actuelle de `USERS_DB` :"
    )
    st.code(f"USERS_DB = '''\n{updated_json}\n'''", language="toml")
