import streamlit as st
import hashlib
import secrets
import string
from datetime import datetime

# ── LOGO ─────────────────────────────────────────────────────────────────────
LOGO_B64 = "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"

ROLES = {
    "admin":   "Administrateur",
    "manager": "Manager",
    "viewer":  "Lecteur",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _generate_password(length=12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def _load_users() -> dict:
    """
    Charge les users depuis st.secrets["USERS"].
    Format attendu dans secrets.toml :
        [USERS.florian]
        hash = "sha256..."
        role = "admin"

        [USERS.comptable]
        hash = "sha256..."
        role = "viewer"
    """
    try:
        raw = st.secrets.get("USERS", {})
        if raw:
            result = {}
            for username, data in raw.items():
                result[username] = dict(data)
            return result
    except Exception:
        pass
    # Fallback si aucun secret configuré
    return {
        "florian": {
            "hash": _hash("florian2024"),
            "role": "admin",
        }
    }

# ── Page de login ─────────────────────────────────────────────────────────────

def check_login() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Sans:wght@300;400;500&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0F2942 0%, #1E3A5F 100%) !important;
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stForm"] {
        background: rgba(255,255,255,0.06);
        border-radius: 20px;
        padding: 32px 28px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.10);
        backdrop-filter: blur(12px);
    }
    .stButton > button {
        background: linear-gradient(135deg, #22C55E, #16A34A) !important;
        color: #0F2942 !important; border: none !important;
        border-radius: 10px !important; font-family: 'Nunito', sans-serif !important;
        font-weight: 900 !important; font-size: 1rem !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }
    [data-testid="stTextInput"] label { color: #94A3B8 !important; font-size: 0.85rem; }
    [data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.07) !important; color: #F8FAFC !important;
        border: 1px solid #1E3A5F !important; border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            f"""<div style="text-align:center; padding: 32px 0 20px;">
                <img src="data:image/jpeg;base64,{LOGO_B64}"
                     style="width:180px; border-radius:16px; box-shadow:0 4px 24px rgba(0,0,0,0.4);" />
            </div>
            <div style="text-align:center; padding-bottom:28px;">
                <div style="color:#94A3B8; font-size:0.75rem; letter-spacing:3px; text-transform:uppercase;">
                    ERP – Accès sécurisé
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("👤 Identifiant", placeholder="florian")
            password = st.text_input("🔒 Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            users = _load_users()
            u = users.get(username)
            if u and u.get("hash") == _hash(password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["role"] = u.get("role", "viewer")
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect.")

        st.markdown(
            '<div style="text-align:center;color:#475569;font-size:0.72rem;margin-top:20px;">Accès réservé – Florian AI Bâtiment</div>',
            unsafe_allow_html=True,
        )
    return False

def logout():
    for k in ["authenticated", "username", "role"]:
        st.session_state.pop(k, None)

# ── Panel admin ───────────────────────────────────────────────────────────────

def admin_panel():
    """
    Panel de gestion des utilisateurs (admin uniquement).
    Les users sont stockés dans st.secrets — la modification se fait
    manuellement dans Streamlit Cloud > Settings > Secrets.
    Ce panel génère les lignes TOML prêtes à copier-coller.
    """
    if st.session_state.get("role") != "admin":
        st.warning("⛔ Accès réservé aux administrateurs.")
        return

    st.markdown('<h2 style="font-size:1.6rem;">👥 Gestion des utilisateurs</h2>', unsafe_allow_html=True)

    users = _load_users()

    # ── Liste des users actuels ───────────────────────────────────────────────
    st.markdown("### Utilisateurs actifs")
    for uname, udata in users.items():
        c1, c2, c3 = st.columns([2, 2, 2])
        c1.markdown(f"**{uname}**")
        c2.markdown(f"🏷️ {ROLES.get(udata.get('role', 'viewer'), 'Lecteur')}")
        c3.markdown(f"{'👑 Admin' if udata.get('role') == 'admin' else ''}")

    st.divider()

    # ── Générer un nouvel utilisateur ─────────────────────────────────────────
    st.markdown("### ➕ Créer un utilisateur")
    st.info("💡 Sur Streamlit Cloud, les users sont stockés dans les **Secrets**. Ce formulaire génère les lignes TOML à copier dans **Settings → Secrets**.")

    with st.form("create_user_form"):
        c1, c2, c3 = st.columns(3)
        new_username = c1.text_input("Identifiant", placeholder="jean.dupont")
        new_role     = c2.selectbox("Rôle", list(ROLES.keys()), format_func=lambda x: ROLES[x])
        new_password = c3.text_input("Mot de passe (vide = auto-généré)", type="password")
        submitted    = st.form_submit_button("Générer les lignes TOML", use_container_width=True)

    if submitted:
        if not new_username:
            st.error("L'identifiant est obligatoire.")
        else:
            pwd = new_password if new_password else _generate_password()
            h   = _hash(pwd)
            toml_lines = f"""
[USERS.{new_username}]
hash = "{h}"
role = "{new_role}"
"""
            st.success(f"✅ Lignes TOML générées pour **{new_username}**")
            if not new_password:
                st.warning(f"🔑 Mot de passe auto-généré : `{pwd}`  ← Notez-le maintenant !")
            st.code(toml_lines, language="toml")
            st.markdown("👆 **Copiez ces lignes** et ajoutez-les dans **Streamlit Cloud → Settings → Secrets**, puis cliquez Save. L'utilisateur sera actif au prochain redémarrage.")

    st.divider()

    # ── Générer un hash pour changer un mot de passe ──────────────────────────
    st.markdown("### 🔐 Changer un mot de passe")
    st.info("Génère le hash à coller dans les Secrets pour mettre à jour un mot de passe.")

    with st.form("change_pwd_form"):
        target_user = st.selectbox("Utilisateur", list(users.keys()))
        new_pwd1    = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2    = st.text_input("Confirmer", type="password")
        submitted2  = st.form_submit_button("Générer le nouveau hash", use_container_width=True)

    if submitted2:
        if new_pwd1 != new_pwd2:
            st.error("❌ Les mots de passe ne correspondent pas.")
        elif len(new_pwd1) < 8:
            st.error("❌ Minimum 8 caractères.")
        else:
            h = _hash(new_pwd1)
            toml_update = f"""
[USERS.{target_user}]
hash = "{h}"
role = "{users[target_user].get('role', 'viewer')}"
"""
            st.success(f"✅ Nouveau hash généré pour **{target_user}**")
            st.code(toml_update, language="toml")
            st.markdown("👆 **Remplacez** la section correspondante dans **Streamlit Cloud → Settings → Secrets**.")
