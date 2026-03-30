import streamlit as st
import hashlib
import json
import os
import secrets
import string

# ── Fichier de stockage des users ─────────────────────────────────────────────
USERS_FILE = "users.json"

# Structure users.json :
# {
#   "florian": {
#     "password": "<sha256>",
#     "role": "admin",
#     "sheet_name": null,    <- null = lire depuis st.secrets
#     "google_sa": null      <- null = lire depuis st.secrets
#   },
#   "dupont_elec": {
#     "password": "<sha256>",
#     "role": "viewer",
#     "sheet_name": "SheetDupont",
#     "google_sa": "{...json complet...}"
#   }
# }

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _load_users() -> dict:
    users = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
        except Exception:
            users = {}

    # Garantir que florian (admin) existe toujours
    if "florian" not in users:
        users["florian"] = {
            "password":   _hash("florian2024"),
            "role":       "admin",
            "sheet_name": None,
            "google_sa":  None,
        }
        _save_users(users)
    return users

def _save_users(users: dict):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erreur sauvegarde users : {e}")

def get_user_credentials(username: str):
    """
    Retourne (sheet_name, google_sa_json_str) pour le user connecté.
    - Si sheet_name/google_sa sont null dans users.json → on lit st.secrets (admin Florian)
    - Sinon → on utilise les valeurs stockées dans users.json
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
        # Logo depuis fichier — mets logo.png à la racine du repo GitHub
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
            u = users.get(username)
            if u and u["password"] == _hash(password):
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
    users = _load_users()

    # ── Liste ──────────────────────────────────────────────────────────────────
    st.markdown("### Utilisateurs existants")
    for uname, udata in list(users.items()):
        c1, c2, c3 = st.columns([3, 3, 1])
        c1.markdown(f"**{uname}**")
        role  = udata.get("role", "viewer")
        sheet = udata.get("sheet_name") or "*(depuis secrets)*"
        c2.markdown(f"`{role}` — Sheet : `{sheet}`")
        if uname != "florian":
            if c3.button("🗑️", key=f"del_{uname}"):
                del users[uname]
                _save_users(users)
                st.success(f"User **{uname}** supprimé.")
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
        elif new_username in users:
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
            users[new_username] = {
                "password":   _hash(pwd),
                "role":       new_role,
                "sheet_name": new_sheet.strip(),
                "google_sa":  new_gsa.strip(),
            }
            _save_users(users)
            st.success(f"✅ User **{new_username}** créé avec le rôle `{new_role}`.")
            if not new_password.strip():
                st.info(f"🔑 Mot de passe généré : `{pwd}`  — notez-le maintenant, il ne sera plus affiché.")

    st.divider()

    # ── Changer son propre mot de passe ───────────────────────────────────────
    st.markdown("### 🔑 Changer mon mot de passe")
    with st.form("change_pwd_form"):
        old_pwd  = st.text_input("Ancien mot de passe", type="password")
        new_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2 = st.text_input("Confirmer le nouveau", type="password")
        chg = st.form_submit_button("Mettre à jour", use_container_width=True)

    if chg:
        me = st.session_state.get("username", "")
        if users.get(me, {}).get("password") != _hash(old_pwd):
            st.error("Ancien mot de passe incorrect.")
        elif new_pwd1 != new_pwd2:
            st.error("Les deux mots de passe ne correspondent pas.")
        elif len(new_pwd1) < 8:
            st.error("Minimum 8 caractères.")
        else:
            users[me]["password"] = _hash(new_pwd1)
            _save_users(users)
            st.success("✅ Mot de passe mis à jour.")
