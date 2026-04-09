import streamlit as st
import hashlib
import json
import os
import secrets
import string
import requests
import time  # <--- Ajouté pour le délai de redirection

# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES DE SÉCURITÉ
# ══════════════════════════════════════════════════════════════════════════════

def _hash(password: str) -> str:
    """Génère un hash SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def _verify_hash(password: str, password_hash: str) -> bool:
    """Vérifie si le mot de passe correspond au hash."""
    return _hash(password) == password_hash

# ══════════════════════════════════════════════════════════════════════════════
# SUPABASE — config
# ══════════════════════════════════════════════════════════════════════════════

def _sb_url() -> str:
    return st.secrets.get("SUPABASE_URL", "").rstrip("/")

def _sb_key() -> str:
    return st.secrets.get("SUPABASE_KEY", "")

def _sb_headers() -> dict:
    return {
        "apikey":        _sb_key(),
        "Authorization": f"Bearer {_sb_key()}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }

def _sb_get(username: str):
    """Récupère un user depuis Supabase."""
    try:
        r = requests.get(
            f"{_sb_url()}/rest/v1/users?username=eq.{username}&select=*",
            headers=_sb_headers(),
            timeout=10,
        )
        data = r.json()
        return data[0] if data else None
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════════════════
# LOGIQUE DE CONNEXION
# ══════════════════════════════════════════════════════════════════════════════

def check_login():
    """Gère l'affichage du formulaire de login et la validation."""
    if st.session_state.get("authenticated", False):
        return True

    st.title("⚡ Florian AI Bâtiment")
    st.subheader("Connexion à l'ERP")

    with st.form("login_form"):
        username = st.text_input("Identifiant").strip().lower()
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter", use_container_width=True)

    if submit:
        # --- MODE DÉPANNAGE TEMPORAIRE ---
        if username == "florian" and password == "test":
            st.session_state.authenticated = True
            st.session_state.username = "florian"
            st.session_state.user_role = "admin"
            st.session_state.sheet_name = st.secrets.get("SHEET_NAME", "")
            st.success("Mode dépannage activé ! Bienvenue Florian.")
            time.sleep(1)
            st.rerun()
        # --------------------------------

        # Vérification classique via Supabase pour les autres
        user_data = _sb_get(username)
        if user_data and _verify_hash(password, user_data.get("password_hash", "")):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_role = user_data.get("role", "user")
            st.session_state.sheet_name = user_data.get("sheet_name", "")
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect.")
    
    return False

def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

# Note: Garde tes autres fonctions (admin_panel, etc.) en dessous de ce code.
