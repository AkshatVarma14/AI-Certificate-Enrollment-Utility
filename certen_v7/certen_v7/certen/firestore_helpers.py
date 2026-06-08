"""
firestore_helpers.py – CertEn Firestore data layer
====================================================
Every function here replaces a SQLAlchemy model query from v6.
app.py imports from this file instead of models.py.

Collections:
  users            email, first_name, last_name, dob, is_admin, created_at
  programs         name, description, mode, created_at
  enrollments      user_id, program_id, start_date, time_from, time_to, enrolled_at
  tasks            program_id, serial, name, due_date
  task_completions user_id, task_id, status ("C" | "NC")
  certificates     user_id, program_id, status, requested_at, granted_at
"""

from firebase_admin import firestore
from firebase_config import db
from datetime import datetime, timezone


# ── Tiny helper ────────────────────────────────────────────────────
def _doc(snapshot):
    """Convert a Firestore DocumentSnapshot → plain dict with 'id' key."""
    if snapshot is None:
        return None
    d = snapshot.to_dict()
    d["id"] = snapshot.id
    return d


def _first(query):
    """Return the first result of a query as a dict, or None."""
    for snap in query.limit(1).stream():
        return _doc(snap)
    return None


def _all(query):
    """Return all results of a query as a list of dicts."""
    return [_doc(s) for s in query.stream()]


# ══════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════

def get_user_by_email(email: str):
    return _first(db.collection("users").where("email", "==", email))


def get_user_by_id(user_id: str):
    snap = db.collection("users").document(user_id).get()
    return _doc(snap) if snap.exists else None


def get_all_users(admin=False):
    """Return all non-admin users (admin=False) or all users (admin=True)."""
    if admin:
        return _all(db.collection("users").order_by("first_name"))
    return _all(
        db.collection("users")
        .where("is_admin", "==", False)
        .order_by("first_name")
    )


def create_user(first_name, last_name, email, dob="", is_admin=False):
    existing = get_user_by_email(email)
    if existing:
        return existing
    ts, ref = db.collection("users").add({
        "first_name": first_name,
        "last_name":  last_name,
        "email":      email.lower(),
        "dob":        dob,
        "is_admin":   is_admin,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return get_user_by_id(ref.id)


def user_full_name(u: dict) -> str:
    return f"{u['first_name']} {u['last_name']}"


def user_initials(u: dict) -> str:
    return f"{u['first_name'][0]}{u['last_name'][0]}".upper()


# ══════════════════════════════════════════════════════════════════
# PROGRAMS
# ══════════════════════════════════════════════════════════════════

def get_all_programs():
    return _all(db.collection("programs").order_by("name"))


def get_program_by_id(program_id: str):
    snap = db.collection("programs").document(program_id).get()
    return _doc(snap) if snap.exists else None


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
    return _first(
        db.collection("enrollments")
        .where("user_id",    "==", user_id)
        .where("program_id", "==", program_id)
    )


def get_user_enrollments(user_id: str):
    return _all(db.collection("enrollments").where("user_id", "==", user_id))


def get_program_enrollments(program_id: str):
    return _all(db.collection("enrollments").where("program_id", "==", program_id))


def create_enrollment(user_id, program_id, start_date="", time_from="", time_to=""):
    if get_enrollment(user_id, program_id):
        return None   # duplicate
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
    return _all(
        db.collection("tasks")
        .where("program_id", "==", program_id)
        .order_by("serial")
    )


def get_task_by_id(task_id: str):
    snap = db.collection("tasks").document(task_id).get()
    return _doc(snap) if snap.exists else None


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
    doc = _first(
        db.collection("task_completions")
        .where("user_id", "==", user_id)
        .where("task_id", "==", task_id)
    )
    return doc["status"] if doc else "NC"


def create_task_completion(user_id: str, task_id: str, status="NC"):
    existing = _first(
        db.collection("task_completions")
        .where("user_id", "==", user_id)
        .where("task_id", "==", task_id)
    )
    if existing:
        return
    db.collection("task_completions").add({
        "user_id": user_id,
        "task_id": task_id,
        "status":  status,
    })


def get_task_rows(user_id: str, program_id: str):
    """Return list of task dicts with per-user completion status."""
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
    """Used for admin stat card only."""
    return _all(db.collection("task_completions"))


# ══════════════════════════════════════════════════════════════════
# CERTIFICATES
# ══════════════════════════════════════════════════════════════════

def get_certificate(user_id: str, program_id: str):
    return _first(
        db.collection("certificates")
        .where("user_id",    "==", user_id)
        .where("program_id", "==", program_id)
    )


def get_granted_certificate(user_id: str, program_id: str):
    return _first(
        db.collection("certificates")
        .where("user_id",    "==", user_id)
        .where("program_id", "==", program_id)
        .where("status",     "==", "granted")
    )


def get_certificate_by_id(cert_id: str):
    snap = db.collection("certificates").document(cert_id).get()
    return _doc(snap) if snap.exists else None


def count_granted_certificates() -> int:
    return len(_all(db.collection("certificates").where("status", "==", "granted")))


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
# ENROLLMENT PROGRESS (replaces SQLAlchemy Enrollment.progress)
# ══════════════════════════════════════════════════════════════════

def enrollment_progress(user_id: str, program_id: str) -> int:
    tasks = get_program_tasks(program_id)
    if not tasks:
        return 0
    completed = sum(1 for t in tasks if get_task_status(user_id, t["id"]) == "C")
    return round((completed / len(tasks)) * 100)
