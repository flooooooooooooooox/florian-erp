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

def _sb_available() -> bool:
    """Vérifie rapidement si Supabase est joignable (timeout 3s)."""
    url = _sb_url()
    if not url or not _sb_key():
        return False
    try:
        r = requests.get(
            f"{url}/rest/v1/users?select=username&limit=1",
            headers=_sb_headers(),
            timeout=3,
        )
        return r.status_code < 500
    except Exception:
        return False

def _sb_get(username: str):
    """Récupère un user depuis Supabase."""
    r = requests.get(
        f"{_sb_url()}/rest/v1/users?username=eq.{username}&select=*",
        headers=_sb_headers(),
        timeout=8,
    )
    data = r.json()
    return data[0] if data else None

def _sb_all_users() -> list:
    """Récupère tous les users. Retourne [] si Supabase est inaccessible."""
    url = _sb_url()
    if not url or not _sb_key():
        return []
    try:
        r = requests.get(
            f"{url}/rest/v1/users?select=*&order=created_at.asc",
            headers=_sb_headers(),
            timeout=8,
        )
        return r.json() if r.ok else []
    except requests.exceptions.ConnectionError:
        return []
    except requests.exceptions.Timeout:
        return []
    except Exception:
        return []

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

def _sb_get_user_rights(username: str) -> tuple:
    r = requests.get(
        f"{_sb_url()}/rest/v1/user_rights?username=eq.{username}&select=allowed_pages",
        headers=_sb_admin_headers(),
        timeout=10,
    )
    detail = (r.text or "").strip()
    if not r.ok:
        return None, r.status_code, detail
    try:
        data = r.json()
    except Exception:
        return None, r.status_code, detail
    if not data:
        return [], r.status_code, ""
    allowed_pages = data[0].get("allowed_pages", [])
    if isinstance(allowed_pages, list):
        return allowed_pages, r.status_code, ""
    return [], r.status_code, ""

def _sb_set_user_rights(username: str, selected_pages: list) -> tuple:
    payload = {
        "username": username,
        "allowed_pages": [p for p in selected_pages if p in AVAILABLE_PAGES],
    }
    headers = _sb_admin_headers().copy()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    r = requests.post(
        f"{_sb_url()}/rest/v1/user_rights",
        headers=headers,
        json=payload,
        timeout=10,
    )
    return r.ok, r.status_code, (r.text or "").strip()

def _sb_delete_user_rights(username: str) -> tuple:
    r = requests.delete(
        f"{_sb_url()}/rest/v1/user_rights?username=eq.{username}",
        headers=_sb_admin_headers(),
        timeout=10,
    )
    return r.ok, r.status_code, (r.text or "").strip()

def _uses_missing_rights_table(status_code: int, detail: str) -> bool:
    detail_low = (detail or "").lower()
    return status_code in (400, 404) and (
        "user_rights" in detail_low or
        "schema cache" in detail_low or
        "could not find" in detail_low
    )

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

def _delete_local_rights(username: str) -> bool:
    rights_map = _load_local_rights()
    if username in rights_map:
        rights_map.pop(username, None)
        return _save_local_rights(rights_map)
    return True

def get_allowed_pages(username: str, user_record: dict | None = None) -> list:
    if username == "florian":
        return AVAILABLE_PAGES.copy() + ["Utilisateurs"]

    sb_rights, _, _ = _sb_get_user_rights(username)
    if isinstance(sb_rights, list) and sb_rights:
        return [p for p in sb_rights if p in AVAILABLE_PAGES]

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
    ok, status_code, detail = _sb_set_user_rights(username, selected_pages)
    if ok:
        _delete_local_rights(username)
        return True, status_code, detail
    if not _uses_missing_rights_table(status_code, detail):
        return False, status_code, detail

    rights_map = _load_local_rights()
    rights_map[username] = [p for p in selected_pages if p in AVAILABLE_PAGES]
    ok = _save_local_rights(rights_map)
    if ok:
        return True, 200, "fallback_local"
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

# ── Lockout (5 tentatives → blocage 30 minutes) — STOCKAGE SERVEUR ────────────
_MAX_ATTEMPTS  = 5
_LOCKOUT_SECS  = 30 * 60  # 30 minutes
_LOCKOUT_FILE  = "lockout_state.json"   # fichier persistant côté serveur

# ── Helpers lecture/écriture du fichier lockout ────────────────────────────────
def _load_lockout_data() -> dict:
    """Charge le fichier JSON de lockout serveur. Retourne {} si absent."""
    if not os.path.exists(_LOCKOUT_FILE):
        return {}
    try:
        with open(_LOCKOUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_lockout_data(data: dict) -> None:
    """Sauvegarde le fichier JSON de lockout serveur."""
    try:
        with open(_LOCKOUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass  # silencieux — on ne bloque pas l'app si le fichier est inaccessible

def _lockout_key(username: str) -> str:
    """Clé de lockout unique par username (en minuscules)."""
    return username.strip().lower()

# ── API publique lockout ───────────────────────────────────────────────────────
def _is_locked_out(username: str = "") -> bool:
    """Vérifie si le username est actuellement bloqué (fichier serveur)."""
    data = _load_lockout_data()
    key  = _lockout_key(username) if username else "__global__"
    entry = data.get(key, {})
    locked_until = entry.get("locked_until", 0)
    if time.time() < locked_until:
        return True
    # Nettoyage si expiration passée
    if locked_until and time.time() >= locked_until:
        data.pop(key, None)
        _save_lockout_data(data)
    return False

def _lockout_remaining(username: str = "") -> int:
    """Retourne le nombre de secondes restantes avant déblocage."""
    data = _load_lockout_data()
    key  = _lockout_key(username) if username else "__global__"
    locked_until = data.get(key, {}).get("locked_until", 0)
    return max(0, int(locked_until - time.time()))

def _get_attempts(username: str) -> int:
    """Retourne le nombre de tentatives échouées pour ce username."""
    data = _load_lockout_data()
    return data.get(_lockout_key(username), {}).get("attempts", 0)

def _record_failed_attempt(username: str = "") -> None:
    """Incrémente le compteur côté serveur. Bloque si _MAX_ATTEMPTS atteint."""
    data  = _load_lockout_data()
    key   = _lockout_key(username) if username else "__global__"
    entry = data.get(key, {"attempts": 0, "locked_until": 0})
    entry["attempts"] += 1
    if entry["attempts"] >= _MAX_ATTEMPTS:
        entry["locked_until"] = time.time() + _LOCKOUT_SECS
        entry["attempts"]     = 0
    data[key] = entry
    _save_lockout_data(data)

def _reset_attempts(username: str = "") -> None:
    """Réinitialise le compteur après une connexion réussie."""
    data = _load_lockout_data()
    key  = _lockout_key(username) if username else "__global__"
    data.pop(key, None)
    _save_lockout_data(data)

# Compat. session_state (inchangé pour le reste du code qui l'appelle)
def _init_lockout():
    pass  # plus nécessaire — état géré côté serveur

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

# ── Timeout de session ────────────────────────────────────────────────────────
_SESSION_TIMEOUT_SECS = 8 * 60 * 60  # 8 heures

def _check_session_timeout() -> bool:
    """
    Vérifie que la session n'a pas expiré.
    Retourne True si valide, False si expirée (efface l'état automatiquement).
    """
    last_activity = st.session_state.get("last_activity", 0)
    if last_activity and (time.time() - last_activity) > _SESSION_TIMEOUT_SECS:
        for k in ["authenticated", "username", "role", "allowed_pages", "last_activity"]:
            st.session_state.pop(k, None)
        return False
    st.session_state["last_activity"] = time.time()
    return True

# ── Login ──────────────────────────────────────────────────────────────────────
def check_login() -> bool:
    if st.session_state.get("authenticated"):
        if not _check_session_timeout():
            st.warning("⏱️ Votre session a expiré après 8h d'inactivité. Reconnectez-vous.")
        else:
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

        # ── Vérification blocage (après saisie du username) ────────────────────
        # On précharge le username depuis le form si possible via query_params
        # mais le check principal se fait au moment du submit (voir ci-dessous).
        # On vérifie aussi le blocage global en amont pour bloquer dès l'affichage.
        if _is_locked_out("__global__"):
            mins = _lockout_remaining("__global__") // 60
            secs = _lockout_remaining("__global__") % 60
            st.error(f"🔒 Trop de tentatives. Réessayez dans **{mins}m {secs}s**.")
            st.stop()

        if submitted:
            # Vérification blocage par username
            if _is_locked_out(username):
                mins = _lockout_remaining(username) // 60
                secs = _lockout_remaining(username) % 60
                st.error(f"🔒 Compte bloqué. Réessayez dans **{mins}m {secs}s**.")
                st.stop()

            attempts_done = _get_attempts(username)
            attempts_left = _MAX_ATTEMPTS - attempts_done
            if 0 < attempts_left <= 2:
                st.warning(f"⚠️ {attempts_left} tentative(s) restante(s) avant blocage de 30 minutes.")

            # Florian → vérification via ADMIN_PASSWORD dans secrets
            if username == "florian":
                admin_hash = st.secrets.get("ADMIN_PASSWORD", "")
                if admin_hash and _verify(password, admin_hash):
                    _reset_attempts(username)
                    st.session_state["authenticated"] = True
                    st.session_state["username"]      = "florian"
                    st.session_state["role"]          = "admin"
                    st.session_state["allowed_pages"] = AVAILABLE_PAGES.copy() + ["Utilisateurs"]
                    st.session_state["last_activity"] = time.time()
                    st.rerun()
                else:
                    _record_failed_attempt(username)
                    st.error("❌ Identifiant ou mot de passe incorrect.")
            else:
                # Autres users → vérification via Supabase
                try:
                    u = _sb_get(username)
                    if u and _verify(password, u.get("password_hash", "")):
                        _reset_attempts(username)
                        st.session_state["authenticated"] = True
                        st.session_state["username"]      = username
                        st.session_state["role"]          = u.get("role", "viewer")
                        st.session_state["allowed_pages"] = get_allowed_pages(username, u)
                        st.session_state["last_activity"] = time.time()
                        st.rerun()
                    else:
                        _record_failed_attempt(username)
                        st.error("❌ Identifiant ou mot de passe incorrect.")
                except Exception as e:
                    _record_failed_attempt(username)
                    st.error(f"❌ Erreur de connexion : {e}")

    return False

def logout():
    username = st.session_state.get("username", "")
    if username:
        _reset_attempts(username)
    for k in ["authenticated", "username", "role", "allowed_pages", "last_activity"]:
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

    sb_ok = _sb_available()
    if not sb_ok:
        st.warning(
            "⚠️ Supabase est inaccessible depuis ce serveur. "
            "Les utilisateurs existants ne peuvent pas être chargés. "
            "Vérifie la connexion réseau du serveur ou la config `SUPABASE_URL` dans les secrets Streamlit."
        )
        with st.expander("🔍 Diagnostic", expanded=True):
            url = _sb_url()
            key = _sb_key()
            st.markdown(f"- **SUPABASE_URL** : `{url or '❌ vide'}`")
            st.markdown(f"- **SUPABASE_KEY** : `{'✅ configurée' if key else '❌ vide'}`")
            st.caption("Si l'URL et la clé sont correctes, le problème est réseau (DNS, firewall, proxy). Redémarre l'app ou vérifie que le serveur accède bien à internet.")
    else:
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
                        ok_rights_cleanup, status_cleanup, detail_cleanup = _sb_delete_user_rights(uname)
                        if not ok_rights_cleanup and not _uses_missing_rights_table(status_cleanup, detail_cleanup):
                            st.warning(f"Droits Supabase non nettoyés pour {uname}.")
                        _delete_local_rights(uname)
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
                                if detail == "fallback_local":
                                    st.success(f"Droits mis à jour pour {uname} (stockage local temporaire).")
                                else:
                                    st.success(f"Droits mis à jour pour {uname}.")
                                st.rerun()
                            else:
                                st.error(f"Impossible de mettre à jour les droits. (HTTP {status_code}) {detail[:300]}")
        except Exception as e:
            st.error(f"Erreur inattendue lors du chargement des utilisateurs : {e}")

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
                st.error("❌ Erreur lors de la création. ssL'identifiant existe peut-être déjà.")

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
