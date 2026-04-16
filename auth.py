import streamlit as st
import json
import os
import secrets
import string
import requests
import bcrypt
import time

RIGHTS_FILE = "user_rights.json"

AVAILABLE_PAGES = [
    "Vue Générale",
    "Créer un devis",
    "Devis",
    "Factures & Paiements",
    "Chantiers",
    "Planning",
    "Salariés",
    "Notifications",
    "Espace Clients",
    "Tous les dossiers",
    "Éditeur Google Sheet",
    "Dépenses",
    "Retards & Avenants",
    "Coordonnées & RGPD",
]


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

def _sb_admin_headers() -> dict:
    """
    Headers "service role" pour les opérations d'écriture (update/insert/delete).
    Si la clé n'existe pas, on retombe sur SUPABASE_KEY (comportement historique).
    """
    k = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "") or _sb_key()
    return {
        "apikey":        k,
        "Authorization": f"Bearer {k}",
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
        headers=_sb_admin_headers(),
        json=user,
        timeout=10,
    )
    return r.ok

def _sb_delete(username: str) -> bool:
    """Supprime un user."""
    r = requests.delete(
        f"{_sb_url()}/rest/v1/users?username=eq.{username}",
        headers=_sb_admin_headers(),
        timeout=10,
    )
    return r.ok

def _sb_update_password(username: str, new_hash: str) -> bool:
    """Met à jour le mot de passe."""
    r = requests.patch(
        f"{_sb_url()}/rest/v1/users?username=eq.{username}",
        headers=_sb_admin_headers(),
        json={"password_hash": new_hash},
        timeout=10,
    )
    return r.ok

def _sb_update_user(username: str, payload: dict) -> tuple:
    r = requests.patch(
        f"{_sb_url()}/rest/v1/users?username=eq.{username}",
        headers=_sb_admin_headers(),
        json=payload,
        timeout=10,
    )
    # On renvoie aussi le détail pour pouvoir diagnostiquer "Impossible de mettre à jour les droits."
    return r.ok, r.status_code, (r.text or "").strip()

def _load_local_rights() -> dict:
    if not os.path.exists(RIGHTS_FILE):
        return {}
    try:
        with open(RIGHTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_local_rights(data: dict) -> bool:
    try:
        with open(RIGHTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def get_allowed_pages(username: str, user_record: dict | None = None) -> list:
    if username == "florian":
        return AVAILABLE_PAGES.copy() + ["Utilisateurs"]

    rights_map = _load_local_rights()
    local_rights = rights_map.get(username)
    if isinstance(local_rights, list) and local_rights:
        return [p for p in local_rights if p in AVAILABLE_PAGES]

    u = user_record if user_record is not None else _sb_get(username)
    if isinstance(u, dict):
        allowed_pages = u.get("allowed_pages")
        if isinstance(allowed_pages, list) and allowed_pages:
            return [p for p in allowed_pages if p in AVAILABLE_PAGES]

    return AVAILABLE_PAGES.copy()

def set_allowed_pages(username: str, selected_pages: list) -> tuple:
    rights_map = _load_local_rights()
    rights_map[username] = [p for p in selected_pages if p in AVAILABLE_PAGES]
    ok = _save_local_rights(rights_map)
    if ok:
        return True, 200, ""
    return False, 500, "Impossible d'écrire le fichier local des droits."

# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    return bcrypt.hashpw(password.strip().encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _verify(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt. Strip les espaces."""
    try:
        return bcrypt.checkpw(password.strip().encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# ── Lockout (30 tentatives → blocage 30 minutes) ──────────────────────────────
_MAX_ATTEMPTS  = 30
_LOCKOUT_SECS  = 30 * 60  # 30 minutes

def _init_lockout():
    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = 0
    if "lockout_until" not in st.session_state:
        st.session_state["lockout_until"] = 0

def _is_locked_out() -> bool:
    _init_lockout()
    return time.time() < st.session_state["lockout_until"]

def _lockout_remaining() -> int:
    """Retourne le nombre de secondes restantes avant déblocage."""
    return max(0, int(st.session_state["lockout_until"] - time.time()))

def _record_failed_attempt():
    _init_lockout()
    st.session_state["login_attempts"] += 1
    if st.session_state["login_attempts"] >= _MAX_ATTEMPTS:
        st.session_state["lockout_until"] = time.time() + _LOCKOUT_SECS
        st.session_state["login_attempts"] = 0

def _reset_attempts():
    st.session_state["login_attempts"] = 0
    st.session_state["lockout_until"]  = 0

def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def get_user_credentials(username: str):
    """
    Retourne (sheet_name, google_sa_json_str) pour le user connecté.
    - florian → st.secrets (SHEET_NAME + GOOGLE_SERVICE_ACCOUNT)
    - autres  → valeurs dans Supabase
    """
    if username == "florian":
        return (
            st.secrets.get("SHEET_NAME", ""),
            st.secrets.get("GOOGLE_SERVICE_ACCOUNT", ""),
        )
    u = _sb_get(username)
    if not u:
        return "", ""
    return u.get("sheet_name", ""), u.get("google_sa", "")

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

        # ── Vérification blocage ───────────────────────────────────────────────
        if _is_locked_out():
            mins = _lockout_remaining() // 60
            secs = _lockout_remaining() % 60
            st.error(f"🔒 Trop de tentatives. Réessayez dans **{mins}m {secs}s**.")
            st.stop()

        attempts_left = _MAX_ATTEMPTS - st.session_state.get("login_attempts", 0)
        if attempts_left <= 5:
            st.warning(f"⚠️ {attempts_left} tentative(s) restante(s) avant blocage de 30 minutes.")

        with st.form("login_form"):
            username  = st.text_input("👤 Identifiant", placeholder="florian")
            password  = st.text_input("🔒 Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            # Florian → vérification via ADMIN_PASSWORD dans secrets
            if username == "florian":
                admin_hash = st.secrets.get("ADMIN_PASSWORD", "")
                if admin_hash and _verify(password, admin_hash):
                    _reset_attempts()
                    st.session_state["authenticated"] = True
                    st.session_state["username"]      = "florian"
                    st.session_state["role"]          = "admin"
                    st.session_state["allowed_pages"] = AVAILABLE_PAGES.copy() + ["Utilisateurs"]
                    st.rerun()
                else:
                    _record_failed_attempt()
                    st.error("❌ Identifiant ou mot de passe incorrect.")
            else:
                # Autres users → vérification via Supabase
                try:
                    u = _sb_get(username)
                    if u and _verify(password, u.get("password_hash", "")):
                        _reset_attempts()
                        st.session_state["authenticated"] = True
                        st.session_state["username"]      = username
                        st.session_state["role"]          = u.get("role", "viewer")
                        st.session_state["allowed_pages"] = get_allowed_pages(username, u)
                        st.rerun()
                    else:
                        _record_failed_attempt()
                        st.error("❌ Identifiant ou mot de passe incorrect.")
                except Exception as e:
                    _record_failed_attempt()
                    st.error(f"❌ Erreur de connexion : {e}")

    return False

def logout():
    for k in ["authenticated", "username", "role", "allowed_pages"]:
        st.session_state.pop(k, None)

# ── Panel admin ────────────────────────────────────────────────────────────────
def admin_panel():
    st.markdown('<h1 style="font-size:2rem;">👥 Gestion des utilisateurs</h1>', unsafe_allow_html=True)

    # ── Liste ──────────────────────────────────────────────────────────────────
    st.markdown("### Utilisateurs existants")

    # Florian (admin, toujours dans secrets)
    c1, c2, _ = st.columns([3, 4, 1])
    c1.markdown("**florian** *(admin)*")
    c2.caption(f"Sheet : `{st.secrets.get('SHEET_NAME','—')}` — credentials dans Streamlit Secrets")

    try:
        users = _sb_all_users()
        for u in users:
            uname = u.get("username", "")
            if uname == "florian":
                continue
            c1, c2, c3 = st.columns([3, 4, 1])
            c1.markdown(f"**{uname}**")
            current_rights = get_allowed_pages(uname, u)
            rights_count = len(current_rights or AVAILABLE_PAGES)
            c2.caption(f"`{u.get('role','viewer')}` — Sheet : `{u.get('sheet_name','—')}` — Accès : {rights_count} onglets")
            if c3.button("🗑️", key=f"del_{uname}"):
                if _sb_delete(uname):
                    st.success(f"✅ User **{uname}** supprimé.")
                    st.rerun()
                else:
                    st.error("Erreur lors de la suppression.")

            with st.expander(f"Droits d'accès : {uname}", expanded=False):
                selected_pages = st.multiselect(
                    "Onglets autorisés",
                    AVAILABLE_PAGES,
                    default=[p for p in current_rights if p in AVAILABLE_PAGES],
                    key=f"rights_{uname}",
                )
                if st.button("Enregistrer les droits", key=f"save_rights_{uname}", use_container_width=True):
                    if len(selected_pages) == 0:
                        st.error("Sélectionne au moins un onglet.")
                    else:
                        ok_rights, status_code, detail = set_allowed_pages(uname, selected_pages)
                        if ok_rights:
                            st.success(f"Droits mis à jour pour {uname}.")
                            st.rerun()
                        else:
                            # Détail tronqué pour éviter l'affichage d'infos trop longues.
                            st.error(f"Impossible de mettre à jour les droits. (HTTP {status_code}) {detail[:300]}")
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
        new_allowed_pages = st.multiselect(
            "Onglets autorisés",
            AVAILABLE_PAGES,
            default=AVAILABLE_PAGES,
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
        elif len(new_allowed_pages) == 0:
            err = "Sélectionne au moins un onglet autorisé."
        else:
            # Nettoyage JSON
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
                set_allowed_pages(new_username.strip(), new_allowed_pages)
                st.success(f"✅ User **{new_username}** créé avec le rôle `{new_role}`.")
                if not new_password.strip():
                    st.info(f"🔑 Mot de passe : `{pwd}` — notez-le, il ne sera plus affiché.")
            else:
                st.error("❌ Erreur lors de la création. L'identifiant existe peut-être déjà.")

    st.divider()

    # ── Changer mot de passe admin ─────────────────────────────────────────────
    st.markdown("### 🔑 Changer le mot de passe admin (florian)")
    with st.form("change_pwd_form"):
        old_pwd  = st.text_input("Ancien mot de passe", type="password")
        new_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2 = st.text_input("Confirmer le nouveau", type="password")
        chg = st.form_submit_button("Mettre à jour", use_container_width=True)

    if chg:
        current_hash = st.secrets.get("ADMIN_PASSWORD", "")
        if not current_hash or not _verify(old_pwd, current_hash):
            st.error("Ancien mot de passe incorrect.")
        elif new_pwd1 != new_pwd2:
            st.error("Les deux mots de passe ne correspondent pas.")
        elif len(new_pwd1) < 8:
            st.error("Minimum 8 caractères.")
        else:
            new_hash = _hash(new_pwd1)
            st.success("✅ Copie ce hash dans **Streamlit Secrets → ADMIN_PASSWORD** :")
            st.code(f'ADMIN_PASSWORD = "{new_hash}"', language="toml")
