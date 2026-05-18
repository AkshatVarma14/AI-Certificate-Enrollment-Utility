from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = "certen_secret_key"

# ── Mock Data ──────────────────────────────────────────────────────────────────
USERS = [
    {"id": 1, "name": "User 1", "email": "user1@gmail.com", "initials": "U1"},
    {"id": 2, "name": "User 2", "email": "user2@gmail.com", "initials": "U2"},
    {"id": 3, "name": "User 3", "email": "user3@gmail.com", "initials": "U3"},
    {"id": 4, "name": "User 4", "email": "user4@gmail.com", "initials": "U4"},
]

PROGRAMS = [
    {"id": 1, "name": "Program 1"},
    {"id": 2, "name": "Program 2"},
    {"id": 3, "name": "Program 3"},
    {"id": 4, "name": "Program 4"},
]

TASKS = [
    {"serial": 1, "name": "Task 1", "due_date": "15/06/2025", "status": "C"},
    {"serial": 2, "name": "Task 2", "due_date": "20/06/2025", "status": "C"},
    {"serial": 3, "name": "Task 3", "due_date": "25/06/2025", "status": "NC"},
]

ADMIN_STATS = {
    "total_users": 10,
    "total_programs": 6,
    "certificates_granted": 3,
    "tasks_assigned": 18,
}

USER_STATS = {
    "programs_enrolled": 3,
    "programs_completed": 1,
    "programs_remaining": 2,
}

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Homepage / Sign-in page."""
    return render_template("index.html")


@app.route("/signin", methods=["POST"])
def signin():
    email = request.form.get("email", "").strip()
    if not email:
        flash("Please enter your email address.", "error")
        return redirect(url_for("index"))
    # Simple mock auth: admin vs. regular user
    if "admin" in email.lower():
        session["role"] = "admin"
        session["email"] = email
        return redirect(url_for("admin_dashboard"))
    else:
        session["role"] = "user"
        session["email"] = email
        return redirect(url_for("user_dashboard"))


@app.route("/register")
def register():
    """User registration / enrollment form."""
    return render_template(
        "register.html",
        programs=PROGRAMS,
        modes=["Online", "Offline", "Hybrid"],
    )


@app.route("/register", methods=["POST"])
def register_submit():
    first_name  = request.form.get("first_name", "")
    last_name   = request.form.get("last_name", "")
    dob_day     = request.form.get("dob_day", "")
    dob_month   = request.form.get("dob_month", "")
    dob_year    = request.form.get("dob_year", "")
    email       = request.form.get("email", "")
    program     = request.form.get("program", "")
    mode        = request.form.get("mode", "")
    date_day    = request.form.get("date_day", "")
    date_month  = request.form.get("date_month", "")
    date_year   = request.form.get("date_year", "")
    time_from   = request.form.get("time_from", "")
    time_to     = request.form.get("time_to", "")

    # In production: validate + save to DB
    flash(f"Enrollment successful for {first_name} {last_name}!", "success")
    return redirect(url_for("index"))


@app.route("/admin")
def admin_dashboard():
    """Admin dashboard."""
    selected_user_id = request.args.get("user_id", type=int)
    selected_program_id = request.args.get("program_id", type=int)

    selected_user    = next((u for u in USERS    if u["id"] == selected_user_id),    None)
    selected_program = next((p for p in PROGRAMS if p["id"] == selected_program_id), None)

    return render_template(
        "admin_dashboard.html",
        stats=ADMIN_STATS,
        users=USERS,
        programs=PROGRAMS,
        selected_user=selected_user,
        selected_program=selected_program,
        tasks=TASKS,
    )


@app.route("/admin/grant_certificate", methods=["POST"])
def grant_certificate():
    user_id    = request.form.get("user_id")
    program_id = request.form.get("program_id")
    flash(f"Certificate granted for User {user_id} in Program {program_id}.", "success")
    return redirect(url_for("admin_dashboard", user_id=user_id, program_id=program_id))


@app.route("/dashboard")
def user_dashboard():
    """User dashboard."""
    selected_program_id = request.args.get("program_id", type=int, default=1)
    selected_program = next((p for p in PROGRAMS if p["id"] == selected_program_id), PROGRAMS[0])

    enrolled_programs = [
        {"id": p["id"], "name": p["name"], "progress": 50}
        for p in PROGRAMS[:3]
    ]

    return render_template(
        "user_dashboard.html",
        stats=USER_STATS,
        enrolled_programs=enrolled_programs,
        selected_program=selected_program,
        tasks=TASKS,
    )


@app.route("/dashboard/apply_certificate", methods=["POST"])
def apply_certificate():
    program_id = request.form.get("program_id")
    flash(f"Certificate application submitted for Program {program_id}.", "success")
    return redirect(url_for("user_dashboard", program_id=program_id))


@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
