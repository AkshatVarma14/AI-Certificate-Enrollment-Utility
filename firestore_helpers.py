"""
firestore_helpers.py – CertEn Firestore data layer
====================================================
Zero composite indexes required.
Every multi-field filter or sort is done in Python after
fetching with a single-field Firestore query.
"""

from werkzeug.security import check_password_hash
from firebase_admin import firestore
from firebase_config import db
from datetime import datetime, timezone


# ── Tiny helpers ───────────────────────────────────────────────────

def _doc(snapshot):
    """DocumentSnapshot → plain dict with 'id' key."""
    if snapshot is None:
        return None
    d = snapshot.to_dict()
    d["id"] = snapshot.id
    return d

def _first_where(collection, field, value):
    """Single-field equality query, returns first match as dict or None."""
    for snap in db.collection(collection).where(field, "==", value).limit(1).stream():
        return _doc(snap)
    return None

def _all_where(collection, field, value):
    """Single-field equality query, returns all matches as list of dicts."""
    return [_doc(s) for s in db.collection(collection).where(field, "==", value).stream()]

def _all_docs(collection):
    """Fetch every document in a collection as list of dicts."""
    return [_doc(s) for s in db.collection(collection).stream()]


# ══════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════

def get_user_by_email(email: str):
    return _first_where("users", "email", email)

def get_user_by_id(user_id: str):
    snap = db.collection("users").document(user_id).get()
    return _doc(snap) if snap.exists else None

def get_all_users(admin=False):
    """Return all non-admin users sorted by first name — no index needed."""
    all_users = _all_docs("users")
    if not admin:
        all_users = [u for u in all_users if not u.get("is_admin", False)]
    return sorted(all_users, key=lambda u: u.get("first_name", "").lower())

def create_user(first_name, last_name, email, dob="", is_admin=False, password_hash=""):
    existing = get_user_by_email(email)
    if existing:
        return existing
    ts, ref = db.collection("users").add({
        "first_name": first_name,
        "last_name":  last_name,
        "email":      email.lower(),
        "dob":        dob,
        "is_admin":       is_admin,
        "password_hash":  password_hash,
        "created_at":     firestore.SERVER_TIMESTAMP,
    })
    return get_user_by_id(ref.id)

def user_full_name(u: dict) -> str:
    return f"{u['first_name']} {u['last_name']}"

def user_initials(u: dict) -> str:
    return f"{u['first_name'][0]}{u['last_name'][0]}".upper()

def verify_user_password(email: str, password: str):
    """Return the user dict if email+password match, else None.
    Accounts with no password_hash set (legacy/seeded) are rejected outright —
    they must go through the password reset flow before they can sign in."""
    user = get_user_by_email(email)
    if not user:
        return None
    stored_hash = user.get("password_hash", "")
    if not stored_hash:            # legacy / seeded account – no password set, reject
        return None
    if check_password_hash(stored_hash, password):
        return user
    return None


# ══════════════════════════════════════════════════════════════════
# PROGRAMS
# ══════════════════════════════════════════════════════════════════

def get_all_programs():
    """All programs sorted by name — no index needed."""
    programs = _all_docs("programs")
    return sorted(programs, key=lambda p: p.get("name", "").lower())

def get_program_by_id(program_id: str):
    if not program_id:
        return None
    snap = db.collection("programs").document(program_id).get()
    return _doc(snap) if snap.exists else None

# ── SEED-ONLY ──────────────────────────────────────────────────────
# create_program is not called by any live route.
# It is used exclusively by seed_firebase.py to populate Firestore.
# Do not wire this into an app route without adding auth/validation.
def create_program(name, description="", mode=""):
    ts, ref = db.collection("programs").add({
        "name":        name,
        "description": description,
        "mode":        mode,
        "created_at":  firestore.SERVER_TIMESTAMP,
    })
    return get_program_by_id(ref.id)


# ══════════════════════════════════════════════════════════════════
# ENROLLMENTS
# ══════════════════════════════════════════════════════════════════

def get_enrollment(user_id: str, program_id: str):
    """
    Fetch by user_id only (single field), then filter by program_id in Python.
    No composite index needed.
    """
    for enr in _all_where("enrollments", "user_id", user_id):
        if enr.get("program_id") == program_id:
            return enr
    return None

def get_user_enrollments(user_id: str):
    return _all_where("enrollments", "user_id", user_id)

def get_program_enrollments(program_id: str):
    return _all_where("enrollments", "program_id", program_id)

def create_enrollment(user_id, program_id, start_date="", time_from="", time_to=""):
    if get_enrollment(user_id, program_id):
        return None  # duplicate
    ts, ref = db.collection("enrollments").add({
        "user_id":     user_id,
        "program_id":  program_id,
        "start_date":  start_date,
        "time_from":   time_from,
        "time_to":     time_to,
        "enrolled_at": firestore.SERVER_TIMESTAMP,
    })
    return ref.id


# ══════════════════════════════════════════════════════════════════
# TASKS
# ══════════════════════════════════════════════════════════════════

def get_program_tasks(program_id: str):
    """
    Fetch by program_id only, then sort by serial in Python.
    No composite index needed.
    """
    tasks = _all_where("tasks", "program_id", program_id)
    return sorted(tasks, key=lambda t: t.get("serial", 0))

def get_task_by_id(task_id: str):
    snap = db.collection("tasks").document(task_id).get()
    return _doc(snap) if snap.exists else None

# ── SEED-ONLY ──────────────────────────────────────────────────────
# create_task is not called by any live route.
# It is used exclusively by seed_firebase.py to populate Firestore.
# Do not wire this into an app route without adding auth/validation.
def create_task(program_id, serial, name, due_date=""):
    ts, ref = db.collection("tasks").add({
        "program_id": program_id,
        "serial":     serial,
        "name":       name,
        "due_date":   due_date,
    })
    return ref.id


# ══════════════════════════════════════════════════════════════════
# TASK COMPLETIONS
# ══════════════════════════════════════════════════════════════════

def get_task_status(user_id: str, task_id: str) -> str:
    """
    Fetch by user_id only, filter by task_id in Python.
    No composite index needed.
    """
    for doc in _all_where("task_completions", "user_id", user_id):
        if doc.get("task_id") == task_id:
            return doc.get("status", "NC")
    return "NC"

def create_task_completion(user_id: str, task_id: str, status="NC"):
    # Check duplicate using single-field query + Python filter
    for doc in _all_where("task_completions", "user_id", user_id):
        if doc.get("task_id") == task_id:
            return  # already exists
    db.collection("task_completions").add({
        "user_id": user_id,
        "task_id": task_id,
        "status":  status,
    })

def get_task_rows(user_id: str, program_id: str):
    """Return task list with per-user status for a given program."""
    tasks = get_program_tasks(program_id)
    rows = []
    for task in tasks:
        rows.append({
            "serial":   task["serial"],
            "name":     task["name"],
            "due_date": task.get("due_date", ""),
            "status":   get_task_status(user_id, task["id"]),
        })
    return rows

def all_tasks_complete(user_id: str, program_id: str) -> bool:
    tasks = get_program_tasks(program_id)
    if not tasks:
        return False
    return all(get_task_status(user_id, t["id"]) == "C" for t in tasks)

def get_all_task_completions():
    """Used only for the admin stat card count."""
    return _all_docs("task_completions")


# ══════════════════════════════════════════════════════════════════
# CERTIFICATES
# ══════════════════════════════════════════════════════════════════

def get_certificate(user_id: str, program_id: str):
    """
    Fetch by user_id only, filter by program_id in Python.
    No composite index needed.
    """
    for doc in _all_where("certificates", "user_id", user_id):
        if doc.get("program_id") == program_id:
            return doc
    return None

def get_granted_certificate(user_id: str, program_id: str):
    """Returns the certificate only if status == 'granted'."""
    cert = get_certificate(user_id, program_id)
    if cert and cert.get("status") == "granted":
        return cert
    return None

def get_certificate_by_id(cert_id: str):
    snap = db.collection("certificates").document(cert_id).get()
    return _doc(snap) if snap.exists else None

def count_granted_certificates() -> int:
    """Count granted certs using single-field query — no composite index."""
    return len(_all_where("certificates", "status", "granted"))

def request_certificate(user_id: str, program_id: str):
    if not get_certificate(user_id, program_id):
        db.collection("certificates").add({
            "user_id":      user_id,
            "program_id":   program_id,
            "status":       "requested",
            "requested_at": datetime.now(timezone.utc),
            "granted_at":   None,
        })

def grant_certificate_db(user_id: str, program_id: str):
    now = datetime.now(timezone.utc)
    existing = get_certificate(user_id, program_id)
    if existing:
        db.collection("certificates").document(existing["id"]).update({
            "status":     "granted",
            "granted_at": now,
        })
    else:
        db.collection("certificates").add({
            "user_id":      user_id,
            "program_id":   program_id,
            "status":       "granted",
            "requested_at": now,
            "granted_at":   now,
        })


# ══════════════════════════════════════════════════════════════════
# ENROLLMENT PROGRESS
# ══════════════════════════════════════════════════════════════════

def enrollment_progress(user_id: str, program_id: str) -> int:
    tasks = get_program_tasks(program_id)
    if not tasks:
        return 0
    completed = sum(1 for t in tasks if get_task_status(user_id, t["id"]) == "C")
    return round((completed / len(tasks)) * 100)
