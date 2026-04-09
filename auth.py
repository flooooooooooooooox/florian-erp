import streamlit as st
import hashlib
import json
import os
import secrets
import string
import requests

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
    r = requests.get(
        f"{_sb_url()}/rest/v1/users?username=eq.{username}&select=*",
        headers=_sb_headers(),
        timeout=10,
    )
    data = r.json()
    return data[0] if data else None

def _sb_all_users() -> list:
    """Récupère tous les users."""
    r = requests.get(
        f"{_sb_url()}/rest/v1/users?select=*&order=created_at.asc",
        headers=_sb_headers(),
        timeout=10,
    )
    return r.json() if r.ok else []

def _sb_insert(user: dict) -> bool:
    """Insère un nouveau user."""
    r = requests.post(
        f"{_sb_url()}/rest/v1/users",
        headers=_sb_headers(),
        json=user,
        timeout=10,
    )
    return r.ok

def _sb_delete(username: str) -> bool:
    """Supprime un user."""
    r = requests.delete(
        f"{_sb_url()}/rest/v1/users?username=eq.{username}",
        headers=_sb_headers(),
        timeout=10,
    )
    return r.ok

def _sb_update_password(username: str, new_hash: str) -> bool:
    """Met à jour le mot de passe."""
    r = requests.patch(
        f"{_sb_url()}/rest/v1/users?username=eq.{username}",
        headers=_sb_headers(),
        json={"password_hash": new_hash},
        timeout=10,
    )
    return r.ok

# ── Helpers ────────────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def get_user_credentials(username: str):
    """
    Retourne (sheet_name, google_sa_json_str) pour le user connecté.
    Tous les users passent par Supabase, y compris florian.
    Fallback sur Streamlit Secrets pour florian si absent de Supabase.
    """
    u = _sb_get(username)
    if u:
        sheet = u.get("sheet_name", "")
        gsa   = u.get("google_sa", "")
        # Si les credentials Google ne sont pas dans Supabase pour florian,
        # on les prend dans les Secrets Streamlit
        if username == "florian" and (not sheet or not gsa):
            sheet = sheet or st.secrets.get("SHEET_NAME", "")
            gsa   = gsa   or st.secrets.get("GOOGLE_SERVICE_ACCOUNT", "")
        return sheet, gsa
    # Dernier recours pour florian
    if username == "florian":
        return (
            st.secrets.get("SHEET_NAME", ""),
            st.secrets.get("GOOGLE_SERVICE_ACCOUNT", ""),
        )
    return "", ""

# ── CSS login ──────────────────────────────────────────────────────────────────
_LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0F2942 0%, #0D1F33 100%) !important;
    font-family: 'DM Sans', sans-serif; color: #F8FAFC;
}
[data-testid="stForm"] {
    background: rgba(19,34,54,0.95);
    border-radius: 16px; padding: 28px 24px;
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
            # Tous les users passent par Supabase, y compris florian
            try:
                u = _sb_get(username)
                if u and u.get("password_hash") == _hash(password):
                    st.session_state["authenticated"] = True
                    st.session_state["username"]      = username
                    st.session_state["role"]          = u.get("role", "viewer")
                    st.rerun()
                else:
                    st.error("❌ Identifiant ou mot de passe incorrect.")
            except Exception as e:
                st.error(f"❌ Erreur de connexion : {e}")

    return False

def logout():
    for k in ["authenticated", "username", "role"]:
        st.session_state.pop(k, None)

# ── Panel admin ────────────────────────────────────────────────────────────────
def admin_panel():
    st.markdown('<h1 style="font-size:2rem;">👥 Gestion des utilisateurs</h1>', unsafe_allow_html=True)

    st.markdown("### Utilisateurs existants")

    try:
        users = _sb_all_users()
        for u in users:
            uname = u.get("username", "")
            c1, c2, c3 = st.columns([3, 4, 1])
            c1.markdown(f"**{uname}**" + (" *(admin)*" if uname == "florian" else ""))
            c2.caption(f"`{u.get('role','viewer')}` — Sheet : `{u.get('sheet_name','—')}`")
            if uname != "florian":
                if c3.button("🗑️", key=f"del_{uname}"):
                    if _sb_delete(uname):
                        st.success(f"✅ User **{uname}** supprimé.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la suppression.")
    except Exception as e:
        st.error(f"Erreur chargement users : {e}")

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
        gsa_clean = new_gsa.strip() if new_gsa else ""

        if not new_username.strip():
            err = "L'identifiant ne peut pas être vide."
        elif new_username == "florian":
            err = "Le nom 'florian' est réservé à l'admin."
        elif not new_sheet.strip():
            err = "Le SHEET_NAME est obligatoire."
        elif not gsa_clean:
            err = "Le JSON Google Service Account est obligatoire."
        else:
            if gsa_clean.startswith("```"):
                gsa_clean = gsa_clean.split("```")[1]
                if gsa_clean.startswith("json"):
                    gsa_clean = gsa_clean[4:]
                gsa_clean = gsa_clean.strip()
            try:
                parsed = json.loads(gsa_clean)
                if parsed.get("type") != "service_account":
                    err = "Ce JSON ne semble pas être un Google Service Account."
                else:
                    gsa_clean = json.dumps(parsed)
            except json.JSONDecodeError as e:
                err = f"JSON invalide : {e}"
                st.code(gsa_clean[:300], language="text")

        if err:
            st.error(err)
        else:
            pwd = new_password.strip() if new_password.strip() else _generate_password()
            ok = _sb_insert({
                "username":      new_username.strip(),
                "password_hash": _hash(pwd),
                "role":          new_role,
                "sheet_name":    new_sheet.strip(),
                "google_sa":     gsa_clean,
            })
            if ok:
                st.success(f"✅ User **{new_username}** créé avec le rôle `{new_role}`.")
                if not new_password.strip():
                    st.info(f"🔑 Mot de passe : `{pwd}` — notez-le, il ne sera plus affiché.")
            else:
                st.error("❌ Erreur lors de la création. L'identifiant existe peut-être déjà.")

    st.divider()

    # ── Changer mot de passe (via Supabase) ────────────────────────────────────
    st.markdown("### 🔑 Changer le mot de passe admin (florian)")
    with st.form("change_pwd_form"):
        old_pwd  = st.text_input("Ancien mot de passe", type="password")
        new_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2 = st.text_input("Confirmer le nouveau", type="password")
        chg = st.form_submit_button("Mettre à jour", use_container_width=True)

    if chg:
        u = _sb_get("florian")
        if not u or u.get("password_hash") != _hash(old_pwd):
            st.error("Ancien mot de passe incorrect.")
        elif new_pwd1 != new_pwd2:
            st.error("Les deux mots de passe ne correspondent pas.")
        elif len(new_pwd1) < 8:
            st.error("Minimum 8 caractères.")
        else:
            if _sb_update_password("florian", _hash(new_pwd1)):
                st.success("✅ Mot de passe mis à jour avec succès !")
            else:
                st.error("❌ Erreur lors de la mise à jour.")
