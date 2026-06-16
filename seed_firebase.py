"""
seed_firebase.py – Populate Firestore with sample data.
=========================================================
Run ONCE after setting up Firebase:
    python seed_firebase.py

This creates the same 5 users, 4 programs, 12 tasks,
10 enrollments, 30 task completions and 2 certificates
as the original SQLite seed.py — but in Firestore.
"""

from firebase_config import db
from firebase_admin import firestore
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from firestore_helpers import (
    create_user, create_program, create_task,
    create_enrollment, create_task_completion, grant_certificate_db,
    get_all_users, get_all_programs,
)


def clear_collection(name):
    """Delete every document in a collection."""
    batch = db.batch()
    count = 0
    for doc in db.collection(name).stream():
        batch.delete(doc.reference)
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
    if count % 400 != 0:
        batch.commit()
    print(f"  Cleared {count} docs from '{name}'")


def seed():
    print("Clearing existing data...")
    for col in ["users", "programs", "tasks", "enrollments", "task_completions", "certificates"]:
        clear_collection(col)

    print("\nSeeding users...")
    # Generic seeded passwords (bcrypt-hashed) — change these after first login.
    ADMIN_PASSWORD = "Admin@123"
    USER_PASSWORD  = "User@123"

    admin  = create_user("Admin", "User",  "admin@certen.com",  dob="01/01/1990", is_admin=True,
                          password_hash=generate_password_hash(ADMIN_PASSWORD))
    alice  = create_user("Alice", "Smith", "alice@gmail.com",   dob="05/03/1998",
                          password_hash=generate_password_hash(USER_PASSWORD))
    bob    = create_user("Bob",   "Jones", "bob@gmail.com",     dob="12/07/1995",
                          password_hash=generate_password_hash(USER_PASSWORD))
    carol  = create_user("Carol", "White", "carol@gmail.com",   dob="22/11/2000",
                          password_hash=generate_password_hash(USER_PASSWORD))
    david  = create_user("David", "Brown", "david@gmail.com",   dob="30/04/1997",
                          password_hash=generate_password_hash(USER_PASSWORD))
    for u in [admin, alice, bob, carol, david]:
        print(f"  ✓ {u['email']}  →  {u['id']}")

    print("\nSeeding programs...")
    p1 = create_program("Python Fundamentals", "Core Python programming skills.",    "Online")
    p2 = create_program("Data Analysis",       "NumPy, Pandas, and visualisation.", "Hybrid")
    p3 = create_program("Machine Learning",    "Supervised & unsupervised learning.", "Online")
    p4 = create_program("Web Development",     "HTML, CSS, JS, and Flask.",          "Offline")
    for p in [p1, p2, p3, p4]:
        print(f"  ✓ {p['name']}  →  {p['id']}")

    print("\nSeeding tasks...")
    t_p1 = [
        create_task(p1["id"], 1, "Variables & Types",    "10/06/2025"),
        create_task(p1["id"], 2, "Control Flow",         "17/06/2025"),
        create_task(p1["id"], 3, "Functions & Modules",  "24/06/2025"),
    ]
    t_p2 = [
        create_task(p2["id"], 1, "NumPy Arrays",         "12/06/2025"),
        create_task(p2["id"], 2, "Pandas DataFrames",    "19/06/2025"),
        create_task(p2["id"], 3, "Matplotlib Plots",     "26/06/2025"),
    ]
    t_p3 = [
        create_task(p3["id"], 1, "Linear Regression",   "15/06/2025"),
        create_task(p3["id"], 2, "Decision Trees",      "22/06/2025"),
        create_task(p3["id"], 3, "Model Evaluation",    "29/06/2025"),
    ]
    t_p4 = [
        create_task(p4["id"], 1, "HTML & CSS Basics",    "11/06/2025"),
        create_task(p4["id"], 2, "JavaScript Essentials","18/06/2025"),
        create_task(p4["id"], 3, "Flask Backend",        "25/06/2025"),
    ]
    print(f"  ✓ 12 tasks created")

    print("\nSeeding enrollments...")
    enrollments = [
        (alice["id"], p1["id"], "01/06/2025", "09:00 AM", "11:00 AM"),
        (alice["id"], p2["id"], "01/06/2025", "12:00 PM", "02:00 PM"),
        (alice["id"], p3["id"], "02/06/2025", "03:00 PM", "05:00 PM"),
        (bob["id"],   p1["id"], "01/06/2025", "09:00 AM", "11:00 AM"),
        (bob["id"],   p4["id"], "02/06/2025", "10:00 AM", "12:00 PM"),
        (carol["id"], p2["id"], "03/06/2025", "01:00 PM", "03:00 PM"),
        (carol["id"], p3["id"], "03/06/2025", "04:00 PM", "06:00 PM"),
        (david["id"], p1["id"], "04/06/2025", "09:00 AM", "11:00 AM"),
        (david["id"], p2["id"], "04/06/2025", "12:00 PM", "02:00 PM"),
        (david["id"], p4["id"], "05/06/2025", "03:00 PM", "05:00 PM"),
    ]
    for uid, pid, sd, tf, tt in enrollments:
        create_enrollment(uid, pid, sd, tf, tt)
    print(f"  ✓ {len(enrollments)} enrollments created")

    print("\nSeeding task completions...")
    completions = [
        # Alice – P1 all done
        (alice["id"], t_p1[0], "C"),  (alice["id"], t_p1[1], "C"),  (alice["id"], t_p1[2], "C"),
        # Alice – P2 partial
        (alice["id"], t_p2[0], "C"),  (alice["id"], t_p2[1], "NC"), (alice["id"], t_p2[2], "NC"),
        # Alice – P3 none
        (alice["id"], t_p3[0], "NC"), (alice["id"], t_p3[1], "NC"), (alice["id"], t_p3[2], "NC"),
        # Bob – P1 partial
        (bob["id"],   t_p1[0], "C"),  (bob["id"],   t_p1[1], "NC"), (bob["id"],   t_p1[2], "NC"),
        # Bob – P4 partial
        (bob["id"],   t_p4[0], "C"),  (bob["id"],   t_p4[1], "C"),  (bob["id"],   t_p4[2], "NC"),
        # Carol – P2 all done
        (carol["id"], t_p2[0], "C"),  (carol["id"], t_p2[1], "C"),  (carol["id"], t_p2[2], "C"),
        # Carol – P3 partial
        (carol["id"], t_p3[0], "C"),  (carol["id"], t_p3[1], "NC"), (carol["id"], t_p3[2], "NC"),
        # David – all partial
        (david["id"], t_p1[0], "C"),  (david["id"], t_p1[1], "NC"), (david["id"], t_p1[2], "NC"),
        (david["id"], t_p2[0], "C"),  (david["id"], t_p2[1], "C"),  (david["id"], t_p2[2], "NC"),
        (david["id"], t_p4[0], "NC"), (david["id"], t_p4[1], "NC"), (david["id"], t_p4[2], "NC"),
    ]
    for uid, task_id, status in completions:
        create_task_completion(uid, task_id, status)
    print(f"  ✓ {len(completions)} task completions created")

    print("\nSeeding certificates...")
    grant_certificate_db(alice["id"], p1["id"])   # Alice completed P1
    grant_certificate_db(carol["id"], p2["id"])   # Carol completed P2
    print("  ✓ 2 certificates granted")

    print("\n✅ Firebase seed complete!")
    print("   Log in with:")
    print(f"     admin@certen.com  /  {ADMIN_PASSWORD}   (Admin)")
    print(f"     alice@gmail.com   /  {USER_PASSWORD}")
    print(f"     bob@gmail.com     /  {USER_PASSWORD}")
    print(f"     carol@gmail.com   /  {USER_PASSWORD}")
    print(f"     david@gmail.com   /  {USER_PASSWORD}")
    print("   Change these passwords via 'Forgot Password' after first login.")


if __name__ == "__main__":
    seed()
