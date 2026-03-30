import streamlit as st
import hashlib
import json
import os
import secrets
import string
from datetime import datetime

# ── Fichier local de stockage des users (dans le repo) ───────────────────────
USERS_FILE = "users.json"

# ── Users par défaut (admin uniquement au premier lancement) ─────────────────
DEFAULT_USERS = {
    "florian": {
        "hash": hashlib.sha256("florian2024".encode()).hexdigest(),
        "role": "admin",
        "created": "2026-01-01",
    },
    "comptable": {
        "hash": hashlib.sha256("compta2024".encode()).hexdigest(),
        "role": "viewer",
        "created": "2026-01-01",
    },
}

ROLES = {
    "admin":   "Administrateur",
    "manager": "Manager",
    "viewer":  "Lecteur",
}

# Logo base64 extrait du auth.py fourni
LOGO_B64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAGFAYUDASIAAhEBAxEB/8QAHQABAAEFAQEBAAAAAAAAAAAAAAgBBQYHCQQDAv/EAEwQAAIBAwIDBQQFCAYFDQAAAAABAgMEBQYRBxIhCDFBUWETFHGBIpGhsbIVMjU3QnR1syQ2UmKSwSMzcoKiF0NFZGVzg5OWKiQ2crq8ov/EABkBAQEBAQEBAAAAAAAAAAAAAAADAgEEBf/EACMRAQEAAgEDBAMBAAAAAAAAAAABAgMREiExBBNBYRQyUSL/2gAMAwEAAhEDEQA/AJfAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAowGAKgAD4315aWFpO7vrqha29Nbzq1pqEILu6tvZFpt9ZaQuHtQ1Vgqz/ALmQpP7pGAdq3CZDL8LpV7CTdPHXMLu5pL9ukoyi3/u8ylt5JvwRDktr1TOeUstlxvh0QjnsHJfRzOOkvS5g/wDM/azOHf8A0tY/+oh/8nOwG/x5/Wfd+nRGWcwsV9LL46PxuYL/ADPhU1Rpmn/rNRYiH+1e01/mc9QPx5/T3fp0IstV6Wvb2FlZ6lw1zdTe0KNK+pTnJ+Cipbv5F3r1KdGlKtWnGnThFuU5tJRW3Vtvolsc4aU50qkatKThODUoyi9nF+DTXcTb4iW2Q1zwGrvET/pWQxtC7hGPT2iXJUcFt4tJrbzexjPVMa3js5jKKGs9H158lDVeBqS7uWGQpN/UpHt/LuE5eb8sY7l8/eYbfec7gU/Hn9Y92uhdDU2m699TsaGoMTVu6j2hQhe05VJvyUU938i7HO/S1apb6nxVxRk41KV5RlCS6NNTTTXzR0QI7NfQphl1AAJtgAAAAAAAAAAAAC06v1BjNK6fuc5l7j2FnbJOTit5Se6SjFeLb2W33d6j3ne09fu5ksFpi1p0U9oTvKzlKS8G4w2S+G7+Jt/jpo+91vw+ucPjakY30KkLi3jN7RqSjv8AQb8N0317t9t9iG+b0Xq3CV5UcppvKWso9OaVtJwe3lJLla9Vui+rHGzulsyynjw2nS7TOs1U3q4TASh4KNKqn9bqbGf8OO0NiM/lrXEZ/FyxFzcTVKncQq+0oOb6JPdJwTfTx9Wl3RZp4zJVJqFPH3c5dyjGjJv6kjPeGvCPWWps5aOth7zG42NSMq93dUnSSgmm+RSW8nt0W3TfvaRXLDDhPHLLlNoAHjekAAAAAAAAAAAAAAAAAAAAAUYDAFQABYeI8Iz4eakpyW6lirqLXp7KRz8OgvEL+oGof4Xc/wAqRz6PV6fxUNvkAPpbUZ3FzSt6S3nVmoQXq3sj0IvmCSNr2Xd7aDutZ8tZxXPGnjt4xfik3UTa9enwR+a/Zcmo70NbKT8FPGbL61VJe9g37eSOBNHsvZxZnhHYUZT5q2MqTs5/BPmh8uWUV8jSuoezhrfH0pVcXc43LRX7FOq6VR/BTSj/AMRtHst6J1Vo/HZuWpLT3GF7UpO3tpTjKScFNSk+VtJPeK83y9y6b42ZY5Yt4Syon5SCp5O6pxW0Y1pxS9E2jznqzH6Xvf3if4meUvEXu09+n8d+9Uvxo6JnOzT36fx371S/GiePE3UC0toDNZ6L2qWtq3R8vay2jT+XM4/Igdp79P4796pfjRL3tXXEqHBy8pRT2r3VCnLby5+b74ohtnNiuu8SobSlKUnKbcpN7tvvbKAF0noxljdZPI22OsaLrXVzVhRo047bznJpJLfp3tG4NWdnrUWB0hXzlPLWd9XtKLrXNpTpOLjBLeXLJv6TS3e2y228XsjHezTbUrnjVgY1VGUYOvVSfnGhNrb13SfyJs1qVOtRnSqRUoTi4yi+5prZrb4ENuy45SRXDCWOcAP1Vh7OrOCakoycU147dD8l0mRcMtQVNL69w2bhVdOnb3MPb7eNJvlqL/AAuRMHtC7PgxqPbqvd4fzYEHCafF+tK47OmQuJpqVXF284p8y38bmQez/UV13tULAAXSAZDw204tW65xOnZVnQp3lbapOO28YJOUtt+m/Knt4b7EtHwH4Ye604H5Aq80Et6vvtbml57/S2+pL02MZ7Jh2bxwuTHMvXjc9j6FSK6LD0KfzhUhF/aiJpNnjdjrHEcBs3jMdbxtrO1s6dOjSh3QiqkEl16v4+PiQmMabzK1snFkDLODf61tL/AMUofjRiZlnBr9bGl/4pQ/GiuXipzzE9SI/ELg1xHzHErNXdti6d1bXt7VuKV27inGn7OUm4ppy5k0mlts2tvFbMlx3GjuJ3aFxGCu62L0taU8zd0nyzuZy2toPxS26z8umy8mzx6rlL/l6M+LO7EcD2YsvVhGWc1PZ2j23cLShKt8t5OCX2mSQ7MWnPZ7S1JlnPbvVKml9WxqTNcdeJeSqScM5TsKT/AObtLaEVH4SacvtMfrcSeIFV7z1nnV/sXs4/cy/TsvynzhF3478M63DfK2NJZKOQs7+E5UJul7OcXBpSjJbtftR6rv8AJbGvT3ZnM5fNXEbjMZS9yVaMdozuq8qrivJOT3S9DwlcZZO6d45CXXY8rSq8K7qEu6llasI/D2dKX3tkRSXPY62/5Lbz1y9X+VSJ7v1b1eVh7a36I0y/+sV/wwIyEm+2t+iNNfvFf8MCMh3T+kc2fsGT6D0DqnW9S5jp3He8xtkvbVJ1Y04Qb32W8n1fTuW/T0MYJQ9iypJ6b1DT6csbulJfFwaf3I7syuM5cxkt4Rw1PgMtpnNVsNm7OVpe0NuenJprZrdNNPZrbxXQtpu3tk0oQ4lY2pGKTqYmnzbeLVWqk/q2XyNJGsbzJTKcXgJodlm4nW4MYuEnv7CtXpx9F7WUtvtNP8G+At3qWyo53VNatjsZVSnb21NJV68fCTbW0I/W2u7ZbNyZ0pp7C6SwdPEYW290saLc+WU3Lq+rbcnv6+S9CG7OWcRTXjZ3q8A/FCtRr0Y1rerTrUpreE6bTTXo10aP2eZdRgMAVAAFi4hf1A1F/Crn+VI59nQLiRONLh5qSpJ7Rjibpv8A8qRz9PV6fxUNvkAB6EQE/OGGNxuP0BgaeOtKFGlLH0Jtwglzt003JtLq23vv4l7vcdj7+jKje2NrdU5LaUK1GM015NNbHmu/i8cLTV28oKcG5uHFfS8tu/KUF09Zpf5k9TC8Vwt0FitS09RY/TlvbZClLmpyhKap05bbbxp78ifwS28NmZoT2ZzOxTDG4zu50Zj9L3v7xP8AEzynoyc41MldVIPeM600mnGRbcfPeS8V1+LQm++Oixy+M74zT7FEJqVXquj55LoxpOjp/K0MriPOXpK4q+0p89Z/9LWKi5pVKNTlW6alnCSSb6c29lt0bfkTf4P8SNN644W5Or6VjFUrCMW92moU4xSfnu3v+JHQtplxVy+bF5O4tMjbXcaVGNnRu6ko00lJLaLe3e1u9+5bHkxmcv1SuGU1S3bQAB5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABRgMAVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWLU2ksLqGpRr31CcLqitqVzbzdOrBeSkvD0e6Lhg8dHFYujYRuru6jS32q3VX2lSW7b6y269+3okke0Heq2cfDMwkvPyAA40AAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACjAYAqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACk/AAAf/9k="

# ── Gestion des users (stockage JSON local) ───────────────────────────────────

def _load_users() -> dict:
    """Charge les users depuis users.json ou retourne les defaults."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_USERS.copy()

def _save_users(users: dict):
    """Sauvegarde les users dans users.json."""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erreur sauvegarde users : {e}")

def _hash(password: str) -> str:
    """Hash SHA-256 du mot de passe."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _generate_password(length=12) -> str:
    """Génère un mot de passe aléatoire sécurisé."""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))

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
        color: #0F2942 !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Nunito', sans-serif !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        letter-spacing: 0.5px;
        transition: all 0.2s;
    }
    .stButton > button:hover { opacity: 0.85 !important; transform: translateY(-1px); }
    [data-testid="stTextInput"] label { color: #94A3B8 !important; font-size: 0.85rem; }
    [data-testid="stTextInput"] input { background: rgba(255,255,255,0.07) !important; color: #F8FAFC !important; border: 1px solid #1E3A5F !important; border-radius: 8px !important; }
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

# ── Panel admin : gestion des utilisateurs ────────────────────────────────────

def admin_panel():
    """Affiche le panel de gestion des utilisateurs (admin uniquement)."""
    role = st.session_state.get("role", "viewer")
    if role != "admin":
        st.warning("⛔ Accès réservé aux administrateurs.")
        return

    st.markdown('<h2 style="font-family:Syne,sans-serif;font-size:1.6rem;">👥 Gestion des utilisateurs</h2>', unsafe_allow_html=True)

    users = _load_users()

    # ── Liste des users ───────────────────────────────────────────────────────
    st.markdown("### Utilisateurs existants")
    for uname, udata in users.items():
        col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
        col1.markdown(f"**{uname}**")
        col2.markdown(f"🏷️ {ROLES.get(udata.get('role','viewer'), 'Lecteur')}")
        col3.markdown(f"📅 {udata.get('created', '—')}")
        if uname != st.session_state.get("username"):
            if col4.button("🗑️", key=f"del_{uname}", help=f"Supprimer {uname}"):
                del users[uname]
                _save_users(users)
                st.success(f"Utilisateur **{uname}** supprimé.")
                st.rerun()

    st.divider()

    # ── Créer un nouvel utilisateur ───────────────────────────────────────────
    st.markdown("### ➕ Créer un utilisateur")
    with st.form("create_user_form"):
        c1, c2, c3 = st.columns(3)
        new_username = c1.text_input("Identifiant", placeholder="jean.dupont")
        new_role = c2.selectbox("Rôle", list(ROLES.keys()), format_func=lambda x: ROLES[x])
        new_password = c3.text_input("Mot de passe (laisser vide = auto)", type="password")
        submitted = st.form_submit_button("Créer l'utilisateur", use_container_width=True)

    if submitted:
        if not new_username:
            st.error("L'identifiant est obligatoire.")
        elif new_username in users:
            st.error(f"L'identifiant **{new_username}** existe déjà.")
        else:
            pwd = new_password if new_password else _generate_password()
            users[new_username] = {
                "hash": _hash(pwd),
                "role": new_role,
                "created": datetime.now().strftime("%Y-%m-%d"),
            }
            _save_users(users)
            st.success(f"✅ Utilisateur **{new_username}** créé avec le rôle **{ROLES[new_role]}**.")
            if not new_password:
                st.info(f"🔑 Mot de passe généré : `{pwd}`  ← Notez-le, il ne sera plus affiché.")

    st.divider()

    # ── Changer son propre mot de passe ──────────────────────────────────────
    st.markdown("### 🔐 Changer mon mot de passe")
    with st.form("change_pwd_form"):
        old_pwd  = st.text_input("Ancien mot de passe", type="password")
        new_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
        submitted2 = st.form_submit_button("Mettre à jour", use_container_width=True)

    if submitted2:
        me = st.session_state.get("username")
        if users.get(me, {}).get("hash") != _hash(old_pwd):
            st.error("❌ Ancien mot de passe incorrect.")
        elif new_pwd1 != new_pwd2:
            st.error("❌ Les nouveaux mots de passe ne correspondent pas.")
        elif len(new_pwd1) < 8:
            st.error("❌ Le mot de passe doit faire au moins 8 caractères.")
        else:
            users[me]["hash"] = _hash(new_pwd1)
            _save_users(users)
            st.success("✅ Mot de passe mis à jour.")
