"""
app.py – CertEn v7  (Firebase Firestore backend)
=================================================
SQLAlchemy / SQLite have been fully removed.
All data operations go through firestore_helpers.py.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

from firestore_helpers import (
    get_user_by_email, get_user_by_id, get_all_users, create_user,
    get_all_programs, get_program_by_id,
    get_enrollment, get_user_enrollments, get_program_enrollments, create_enrollment,
    get_program_tasks, create_task, create_task_completion,
    get_task_rows, all_tasks_complete, get_all_task_completions,
    get_certificate, get_granted_certificate, get_certificate_by_id,
    count_granted_certificates, request_certificate, grant_certificate_db,
    enrollment_progress, user_full_name, user_initials,
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "certen_secret_key_change_in_production")


# ══════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════

def get_current_user():
    email = session.get("email")
    if not email:
        return None
    return get_user_by_email(email)


# ══════════════════════════════════════════════════════════════════
# Auth routes
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signin", methods=["POST"])
def signin():
    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Please enter your email address.", "error")
        return redirect(url_for("index"))

    user = get_user_by_email(email)
    if not user:
        flash("No account found with that email. Please register first.", "error")
        return redirect(url_for("index"))

    session["email"] = user["email"]
    session["role"]  = "admin" if user.get("is_admin") else "user"
    session["uid"]   = user["id"]

    if user.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("user_dashboard"))


@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("index"))


# ══════════════════════════════════════════════════════════════════
# Registration / Enrollment
# ══════════════════════════════════════════════════════════════════

@app.route("/register", methods=["GET"])
def register():
    programs = get_all_programs()
    return render_template("register.html", programs=programs, modes=["Online", "Offline", "Hybrid"])


@app.route("/register", methods=["POST"])
def register_submit():
    first_name     = request.form.get("first_name",     "").strip()
    last_name      = request.form.get("last_name",      "").strip()
    email          = request.form.get("email",          "").strip().lower()
    dob_day        = request.form.get("dob_day",        "")
    dob_month      = request.form.get("dob_month",      "")
    dob_year       = request.form.get("dob_year",       "")
    program_id     = request.form.get("program",        "")
    mode           = request.form.get("mode",           "")
    date_day       = request.form.get("date_day",       "")
    date_month     = request.form.get("date_month",     "")
    date_year      = request.form.get("date_year",      "")
    time_from_h    = request.form.get("time_from_h",    "00")
    time_from_m    = request.form.get("time_from_m",    "00")
    time_from_ampm = request.form.get("time_from_ampm", "AM")
    time_to_h      = request.form.get("time_to_h",      "00")
    time_to_m      = request.form.get("time_to_m",      "00")
    time_to_ampm   = request.form.get("time_to_ampm",   "AM")

    if not all([first_name, last_name, email, program_id]):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("register"))

    program = get_program_by_id(program_id)
    if not program:
        flash("Selected program not found.", "error")
        return redirect(url_for("register"))

    # Create or fetch user
    user = get_user_by_email(email)
    if not user:
        user = create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            dob=f"{dob_day}/{dob_month}/{dob_year}",
        )

    # Check duplicate enrollment
    if get_enrollment(user["id"], program_id):
        flash(f"{user_full_name(user)} is already enrolled in that program.", "error")
        return redirect(url_for("register"))

    start_date = f"{date_day}/{date_month}/{date_year}"
    time_from  = f"{time_from_h}:{time_from_m} {time_from_ampm}"
    time_to    = f"{time_to_h}:{time_to_m} {time_to_ampm}"

    create_enrollment(user["id"], program_id, start_date, time_from, time_to)

    # Create NC task-completion rows for every task in the program
    for task in get_program_tasks(program_id):
        create_task_completion(user["id"], task["id"], status="NC")

    flash(f"Enrollment successful for {user_full_name(user)} in {program['name']}!", "success")
    return redirect(url_for("index"))


# ══════════════════════════════════════════════════════════════════
# Admin Dashboard
# ══════════════════════════════════════════════════════════════════

@app.route("/admin")
def admin_dashboard():
    selected_user_id    = request.args.get("user_id",    "")
    selected_program_id = request.args.get("program_id", "")
    view_mode           = request.args.get("view", "user")

    users    = get_all_users(admin=False)
    programs = get_all_programs()

    selected_user    = get_user_by_id(selected_user_id)       if selected_user_id    else None
    selected_program = get_program_by_id(selected_program_id) if selected_program_id else None

    # ── Stat cards ────────────────────────────────────────────────
    stats = {
        "total_users":          len(get_all_users(admin=False)),
        "total_programs":       len(programs),
        "certificates_granted": count_granted_certificates(),
        "tasks_assigned":       len(get_all_task_completions()),
    }

    # ── User-centric panel ────────────────────────────────────────
    user_enrolled_programs = []
    user_task_rows         = []
    user_program_cert      = None

    if selected_user:
        for enr in get_user_enrollments(selected_user["id"]):
            prog = get_program_by_id(enr["program_id"])
            if prog:
                user_enrolled_programs.append({
                    "id":       prog["id"],
                    "name":     prog["name"],
                    "progress": enrollment_progress(selected_user["id"], prog["id"]),
                })
        if selected_program:
            user_task_rows    = get_task_rows(selected_user["id"], selected_program["id"])
            user_program_cert = get_certificate(selected_user["id"], selected_program["id"])

    # ── Program-centric panel ─────────────────────────────────────
    program_enrolled_users = []
    program_task_rows      = []
    program_detail_user    = None
    program_detail_cert    = None
    prog_detail_user_id    = request.args.get("prog_user_id", "")

    if selected_program and view_mode == "program":
        for enr in get_program_enrollments(selected_program["id"]):
            u = get_user_by_id(enr["user_id"])
            if u:
                program_enrolled_users.append({
                    "id":       u["id"],
                    "name":     user_full_name(u),
                    "initials": user_initials(u),
                    "email":    u["email"],
                    "progress": enrollment_progress(u["id"], selected_program["id"]),
                })
        if prog_detail_user_id:
            program_detail_user = get_user_by_id(prog_detail_user_id)
            if program_detail_user:
                program_task_rows   = get_task_rows(prog_detail_user_id, selected_program["id"])
                program_detail_cert = get_certificate(prog_detail_user_id, selected_program["id"])

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        users=users,
        programs=programs,
        selected_user=selected_user,
        selected_program=selected_program,
        view_mode=view_mode,
        user_enrolled_programs=user_enrolled_programs,
        user_task_rows=user_task_rows,
        user_program_cert=user_program_cert,
        program_enrolled_users=program_enrolled_users,
        program_task_rows=program_task_rows,
        program_detail_user=program_detail_user,
        program_detail_cert=program_detail_cert,
        prog_detail_user_id=prog_detail_user_id,
        user_full_name=user_full_name,
        user_initials=user_initials,
    )


@app.route("/admin/grant_certificate", methods=["POST"])
def grant_certificate():
    user_id    = request.form.get("user_id",    "")
    program_id = request.form.get("program_id", "")
    view_mode  = request.form.get("view", "user")

    user    = get_user_by_id(user_id)
    program = get_program_by_id(program_id)

    if not user or not program:
        flash("Invalid user or program.", "error")
        return redirect(url_for("admin_dashboard"))

    grant_certificate_db(user_id, program_id)
    flash(f"Certificate granted to {user_full_name(user)} for {program['name']}.", "success")

    if view_mode == "program":
        return redirect(url_for("admin_dashboard",
                                program_id=program_id, view="program",
                                prog_user_id=user_id))
    return redirect(url_for("admin_dashboard", user_id=user_id, program_id=program_id, view="user"))


@app.route("/certificate/view/<user_id>/<program_id>")
def view_certificate(user_id, program_id):
    cert    = get_granted_certificate(user_id, program_id)
    user    = get_user_by_id(user_id)
    program = get_program_by_id(program_id)

    if not cert or not user or not program:
        flash("Certificate not found.", "error")
        return redirect(url_for("index"))

    # Convert Firestore Timestamp → Python datetime if needed
    granted_at = cert.get("granted_at")
    if hasattr(granted_at, "timestamp"):
        granted_at = datetime.fromtimestamp(granted_at.timestamp(), tz=timezone.utc)
    cert["granted_at"] = granted_at

    return render_template("certificate.html", cert=cert, user=user, program=program,
                           user_full_name=user_full_name)


# ══════════════════════════════════════════════════════════════════
# User Dashboard
# ══════════════════════════════════════════════════════════════════

@app.route("/dashboard")
def user_dashboard():
    user = get_current_user()
    if not user:
        flash("Please sign in first.", "error")
        return redirect(url_for("index"))

    selected_program_id = request.args.get("program_id", "")

    enrollments = get_user_enrollments(user["id"])
    enrolled_programs = []
    for e in enrollments:
        prog = get_program_by_id(e["program_id"])
        if prog:
            enrolled_programs.append({
                "id":       prog["id"],
                "name":     prog["name"],
                "progress": enrollment_progress(user["id"], prog["id"]),
            })

    if not selected_program_id and enrolled_programs:
        selected_program_id = enrolled_programs[0]["id"]

    selected_program = get_program_by_id(selected_program_id) if selected_program_id else None

    task_rows = get_task_rows(user["id"], selected_program_id) if selected_program else []

    completed_count = sum(
        1 for e in enrollments
        if all_tasks_complete(user["id"], e["program_id"])
    )

    stats = {
        "programs_enrolled":  len(enrollments),
        "programs_completed": completed_count,
        "programs_remaining": len(enrollments) - completed_count,
    }

    cert      = None
    can_apply = False
    if selected_program:
        cert      = get_certificate(user["id"], selected_program["id"])
        tasks_done = all_tasks_complete(user["id"], selected_program["id"])
        can_apply  = tasks_done or cert is not None

    return render_template(
        "user_dashboard.html",
        user=user,
        stats=stats,
        enrolled_programs=enrolled_programs,
        selected_program=selected_program,
        task_rows=task_rows,
        cert=cert,
        can_apply=can_apply,
        user_full_name=user_full_name,
    )


@app.route("/dashboard/apply_certificate", methods=["POST"])
def apply_certificate():
    user = get_current_user()
    if not user:
        flash("Please sign in first.", "error")
        return redirect(url_for("index"))

    program_id = request.form.get("program_id", "")
    program    = get_program_by_id(program_id)

    if not program:
        flash("Invalid program.", "error")
        return redirect(url_for("user_dashboard"))

    cert       = get_certificate(user["id"], program_id)
    tasks_done = all_tasks_complete(user["id"], program_id)

    if cert and cert.get("status") == "granted":
        flash(f"You have already been granted a certificate for {program['name']}.", "success")
        return redirect(url_for("user_dashboard", program_id=program_id))

    if not tasks_done:
        request_certificate(user["id"], program_id)
        flash(
            f"Your certificate request for {program['name']} has been submitted. "
            "It will be granted once all tasks are completed or approved by an admin.",
            "error"
        )
        return redirect(url_for("user_dashboard", program_id=program_id))

    grant_certificate_db(user["id"], program_id)
    flash(f"🎉 Certificate granted for {program['name']}! Congratulations!", "success")
    return redirect(url_for("user_dashboard", program_id=program_id))


if __name__ == "__main__":
    app.run(debug=True)
