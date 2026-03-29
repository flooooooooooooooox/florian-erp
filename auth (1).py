import streamlit as st
import hashlib

DEFAULT_USERS = {
    "florian":   hashlib.sha256("florian2024".encode()).hexdigest(),
    "comptable": hashlib.sha256("compta2024".encode()).hexdigest(),
    "admin":     hashlib.sha256("admin2024".encode()).hexdigest(),
}

ROLES = {
    "florian":   "Artisan",
    "comptable": "Comptable",
    "admin":     "Admin",
}

def _get_users():
    try:
        raw = st.secrets.get("USERS", None)
        if raw:
            return dict(raw)
    except Exception:
        pass
    return DEFAULT_USERS

def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login():
    if st.session_state.get("authenticated"):
        return True

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 32px;">
            <div style="font-size:3.5rem;">⚡</div>
            <div style="font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;color:#F8FAFC;margin-top:8px;">
                Florian AI Bâtiment
            </div>
            <div style="color:#94A3B8;font-size:0.85rem;letter-spacing:2px;text-transform:uppercase;margin-top:4px;">
                ERP – Accès sécurisé
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Identifiant", placeholder="florian")
            password = st.text_input("🔒 Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            users = _get_users()
            if username in users and users[username] == _hash(password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["role"] = ROLES.get(username, "Utilisateur")
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect.")

    return False

def logout():
    for key in ["authenticated", "username", "role"]:
        st.session_state.pop(key, None)
