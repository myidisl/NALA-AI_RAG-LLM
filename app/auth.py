# Login/sesi sederhana sebagai fondasi identitas untuk RBAC: user_id dan role
# SELALU dibaca dari sesi terautentikasi (cookie bertanda tangan SessionMiddleware),
# tidak pernah dari body request.
from fastapi import Request

# User demo, KHUSUS development: password plaintext & hardcoded. Jangan dipakai di production.
USERS = {
    "budi.umum": {"password": "nala123", "role": "staff_umum", "nama": "Budi"},
    "sari.finance": {"password": "nala123", "role": "staff_finance", "nama": "Sari"},
    "andi.super": {"password": "nala123", "role": "supervisor", "nama": "Andi"},
    "thoriq.netsec": {"password": "nala123", "role": "staff_netsec", "nama": "Thoriq"},
    "zein.netsec": {"password": "nala123", "role": "spv_netsec", "nama": "Zein"},
}

# Label role yang ditampilkan di UI (banner "Masuk sebagai ...").
ROLE_LABELS = {
    "staff_umum": "Staff Umum",
    "staff_finance": "Staff Finance",
    "supervisor": "Supervisor",
    "staff_netsec": "Staff NetSec",
    "spv_netsec": "Supervisor NetSec",
}


def verify_user(username: str, password: str) -> dict | None:
    """Return {user_id, role, nama} if the username/password pair matches a demo user, else None."""
    user = USERS.get(username)
    if user is None or user["password"] != password:
        return None
    return {"user_id": username, "role": user["role"], "nama": user["nama"]}


def get_current_user(request: Request) -> dict | None:
    """Return the logged-in user {user_id, role, nama, role_label} from the session, or None if not logged in."""
    user_id = request.session.get("user_id")
    role = request.session.get("role")
    if not user_id or not role:
        return None
    return {
        "user_id": user_id,
        "role": role,
        "nama": request.session.get("nama", user_id),
        "role_label": ROLE_LABELS.get(role, role),
    }
