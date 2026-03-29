import streamlit as st
import hashlib

LOGO_B64 = "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"

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

    # CSS page login aux couleurs du logo
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Sans:wght@300;400;500&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #EEF1F5 !important;
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stForm"] {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 28px 24px;
        box-shadow: 0 4px 24px rgba(45,62,80,0.10);
        border: 1px solid #D5DCE6;
    }
    .stButton > button {
        background: #2D3E50 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Nunito', sans-serif !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
    }
    .stButton > button:hover { background: #5B9BAE !important; }
    [data-testid="stTextInput"] label { color: #2D3E50 !important; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # Logo centré
        st.markdown(
            f"""
            <div style="text-align:center; padding: 40px 0 20px;">
                <img src="data:image/jpeg;base64,{LOGO_B64}"
                     style="width:200px; border-radius:14px; background:#fff;
                            padding:12px; box-shadow: 0 4px 16px rgba(45,62,80,0.10);" />
            </div>
            <div style="text-align:center; padding-bottom:24px;">
                <div style="color:#6B7A8D; font-size:0.8rem; letter-spacing:2px;
                            text-transform:uppercase; font-family:'DM Sans',sans-serif;">
                    ERP – Accès sécurisé
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
