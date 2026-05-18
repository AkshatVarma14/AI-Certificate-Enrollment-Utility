"""
app.py – CertEn Flask application
====================================
All data now served from SQLite via SQLAlchemy (models.py).
Run `python seed.py` once to populate the database.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timezone
from models import db, User, Program, Enrollment, Task, TaskCompletion, Certificate

app = Flask(__name__)
app.secret_key = "certen_secret_key_change_in_production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///certen.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ══════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════

def get_current_user():
    """Return the logged-in User object or None."""
    email = session.get("email")
    if not email:
        return None
    return User.query.filter_by(email=email).first()


def all_tasks_complete(user_id: int, program_id: int) -> bool:
    """True iff every task in the program has status='C' for this user."""
    tasks = Task.query.filter_by(program_id=program_id).all()
    if not tasks:
        return False
    for task in tasks:
        tc = TaskCompletion.query.filter_by(user_id=user_id, task_id=task.id).first()
        if not tc or tc.status != "C":
            return False
    return True


def get_task_rows(user_id: int, program_id: int):
    """Return list of dicts with task info + per-user status."""
    tasks = Task.query.filter_by(program_id=program_id).order_by(Task.serial).all()
    rows = []
    for task in tasks:
        tc = TaskCompletion.query.filter_by(user_id=user_id, task_id=task.id).first()
        rows.append({
            "serial":   task.serial,
            "name":     task.name,
            "due_date": task.due_date,
            "status":   tc.status if tc else "NC",
        })
    return rows


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

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No account found with that email. Please register first.", "error")
        return redirect(url_for("index"))

    session["email"] = user.email
    session["role"]  = "admin" if user.is_admin else "user"

    if user.is_admin:
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
    programs = Program.query.order_by(Program.name).all()
    return render_template("register.html", programs=programs, modes=["Online", "Offline", "Hybrid"])


@app.route("/register", methods=["POST"])
def register_submit():
    first_name  = request.form.get("first_name",  "").strip()
    last_name   = request.form.get("last_name",   "").strip()
    email       = request.form.get("email",       "").strip().lower()
    dob_day     = request.form.get("dob_day",     "")
    dob_month   = request.form.get("dob_month",   "")
    dob_year    = request.form.get("dob_year",    "")
    program_id  = request.form.get("program",     type=int)
    mode        = request.form.get("mode",        "")
    date_day    = request.form.get("date_day",    "")
    date_month  = request.form.get("date_month",  "")
    date_year   = request.form.get("date_year",   "")
    time_from_h    = request.form.get("time_from_h",    "00")
    time_from_m    = request.form.get("time_from_m",    "00")
    time_from_ampm = request.form.get("time_from_ampm", "AM")
    time_to_h      = request.form.get("time_to_h",      "00")
    time_to_m      = request.form.get("time_to_m",      "00")
    time_to_ampm   = request.form.get("time_to_ampm",   "AM")

    if not all([first_name, last_name, email, program_id]):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("register"))

    # Create or fetch user
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            dob=f"{dob_day}/{dob_month}/{dob_year}",
        )
        db.session.add(user)
        db.session.flush()

    # Check duplicate enrollment
    existing = Enrollment.query.filter_by(user_id=user.id, program_id=program_id).first()
    if existing:
        flash(f"{user.full_name} is already enrolled in that program.", "error")
        return redirect(url_for("register"))

    program = Program.query.get(program_id)
    if not program:
        flash("Selected program not found.", "error")
        return redirect(url_for("register"))

    start_date = f"{date_day}/{date_month}/{date_year}"
    time_from  = f"{time_from_h}:{time_from_m} {time_from_ampm}"
    time_to    = f"{time_to_h}:{time_to_m} {time_to_ampm}"

    enrollment = Enrollment(user=user, program=program,
                            start_date=start_date, time_from=time_from, time_to=time_to)
    db.session.add(enrollment)

    # Create NC task completion rows for every task in the program
    for task in program.tasks:
        tc_exists = TaskCompletion.query.filter_by(user_id=user.id, task_id=task.id).first()
        if not tc_exists:
            db.session.add(TaskCompletion(user=user, task=task, status="NC"))

    db.session.commit()
    flash(f"Enrollment successful for {user.full_name} in {program.name}!", "success")
    return redirect(url_for("index"))


# ══════════════════════════════════════════════════════════════════
# Admin Dashboard
# ══════════════════════════════════════════════════════════════════

@app.route("/admin")
def admin_dashboard():
    # ── query params ──────────────────────────────────────────────
    selected_user_id    = request.args.get("user_id",    type=int)
    selected_program_id = request.args.get("program_id", type=int)
    view_mode           = request.args.get("view", "user")   # "user" | "program"

    users    = User.query.filter_by(is_admin=False).order_by(User.first_name).all()
    programs = Program.query.order_by(Program.name).all()

    selected_user    = User.query.get(selected_user_id)    if selected_user_id    else None
    selected_program = Program.query.get(selected_program_id) if selected_program_id else None

    # ── stat cards ────────────────────────────────────────────────
    stats = {
        "total_users":           User.query.filter_by(is_admin=False).count(),
        "total_programs":        Program.query.count(),
        "certificates_granted":  Certificate.query.filter_by(status="granted").count(),
        "tasks_assigned":        TaskCompletion.query.count(),
    }

    # ── detail data (user-centric view) ───────────────────────────
    user_enrolled_programs = []
    user_task_rows         = []
    if selected_user:
        for enr in selected_user.enrollments:
            user_enrolled_programs.append({
                "id":       enr.program.id,
                "name":     enr.program.name,
                "progress": enr.progress,
            })
        if selected_program:
            user_task_rows = get_task_rows(selected_user.id, selected_program.id)

    # ── detail data (program-centric view) ────────────────────────
    program_enrolled_users = []
    program_task_rows      = []
    program_detail_user    = None
    prog_detail_user_id    = request.args.get("prog_user_id", type=int)

    if selected_program and view_mode == "program":
        for enr in selected_program.enrollments:
            program_enrolled_users.append({
                "id":       enr.user.id,
                "name":     enr.user.full_name,
                "initials": enr.user.initials,
                "email":    enr.user.email,
                "progress": enr.progress,
            })
        if prog_detail_user_id:
            program_detail_user = User.query.get(prog_detail_user_id)
            if program_detail_user:
                program_task_rows = get_task_rows(prog_detail_user_id, selected_program.id)

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
        program_enrolled_users=program_enrolled_users,
        program_task_rows=program_task_rows,
        program_detail_user=program_detail_user,
        prog_detail_user_id=prog_detail_user_id,
    )


@app.route("/admin/grant_certificate", methods=["POST"])
def grant_certificate():
    user_id    = request.form.get("user_id",    type=int)
    program_id = request.form.get("program_id", type=int)

    user    = User.query.get(user_id)
    program = Program.query.get(program_id)
    if not user or not program:
        flash("Invalid user or program.", "error")
        return redirect(url_for("admin_dashboard"))

    cert = Certificate.query.filter_by(user_id=user_id, program_id=program_id).first()
    if cert:
        cert.status     = "granted"
        cert.granted_at = datetime.now(timezone.utc)
    else:
        cert = Certificate(user_id=user_id, program_id=program_id,
                           status="granted", granted_at=datetime.now(timezone.utc))
        db.session.add(cert)
    db.session.commit()

    flash(f"Certificate granted to {user.full_name} for {program.name}.", "success")
    return redirect(url_for("admin_dashboard", user_id=user_id, program_id=program_id))


# ══════════════════════════════════════════════════════════════════
# User Dashboard
# ══════════════════════════════════════════════════════════════════

@app.route("/dashboard")
def user_dashboard():
    user = get_current_user()
    if not user:
        flash("Please sign in first.", "error")
        return redirect(url_for("index"))

    selected_program_id = request.args.get("program_id", type=int)

    # enrolled programs for this user
    enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    enrolled_programs = [
        {"id": e.program.id, "name": e.program.name, "progress": e.progress}
        for e in enrollments
    ]

    # default to first enrolled program
    if not selected_program_id and enrolled_programs:
        selected_program_id = enrolled_programs[0]["id"]

    selected_program = Program.query.get(selected_program_id) if selected_program_id else None

    # task rows for selected program
    task_rows = []
    if selected_program:
        task_rows = get_task_rows(user.id, selected_program.id)

    # stats
    completed_program_ids = set()
    for e in enrollments:
        if all_tasks_complete(user.id, e.program_id):
            completed_program_ids.add(e.program_id)

    stats = {
        "programs_enrolled":  len(enrollments),
        "programs_completed": len(completed_program_ids),
        "programs_remaining": len(enrollments) - len(completed_program_ids),
    }

    # certificate status for selected program
    cert = None
    can_apply = False
    if selected_program:
        cert = Certificate.query.filter_by(user_id=user.id,
                                           program_id=selected_program.id).first()
        tasks_done = all_tasks_complete(user.id, selected_program.id)
        already_requested = cert is not None
        can_apply = tasks_done or already_requested   # see logic below

    return render_template(
        "user_dashboard.html",
        user=user,
        stats=stats,
        enrolled_programs=enrolled_programs,
        selected_program=selected_program,
        task_rows=task_rows,
        cert=cert,
        can_apply=can_apply,
    )


@app.route("/dashboard/apply_certificate", methods=["POST"])
def apply_certificate():
    user = get_current_user()
    if not user:
        flash("Please sign in first.", "error")
        return redirect(url_for("index"))

    program_id = request.form.get("program_id", type=int)
    program    = Program.query.get(program_id)

    if not program:
        flash("Invalid program.", "error")
        return redirect(url_for("user_dashboard"))

    # ── Certificate grant logic ───────────────────────────────────
    # Condition A: all tasks completed
    tasks_done = all_tasks_complete(user.id, program_id)

    # Condition B: user explicitly requests (button clicked = intent)
    # We always allow creating a "requested" record, but only grant
    # immediately if tasks are done.
    cert = Certificate.query.filter_by(user_id=user.id, program_id=program_id).first()

    if cert and cert.status == "granted":
        flash(f"You have already been granted a certificate for {program.name}.", "success")
        return redirect(url_for("user_dashboard", program_id=program_id))

    if not tasks_done:
        # Not all tasks done — record the request but don't grant yet
        if not cert:
            cert = Certificate(user_id=user.id, program_id=program_id, status="requested")
            db.session.add(cert)
            db.session.commit()
        flash(
            f"Your certificate request for {program.name} has been submitted. "
            "It will be granted once all tasks are completed or approved by an admin.",
            "error"
        )
        return redirect(url_for("user_dashboard", program_id=program_id))

    # All tasks done → grant immediately
    if not cert:
        cert = Certificate(user_id=user.id, program_id=program_id,
                           status="granted", granted_at=datetime.now(timezone.utc))
        db.session.add(cert)
    else:
        cert.status     = "granted"
        cert.granted_at = datetime.now(timezone.utc)

    db.session.commit()
    flash(f"🎉 Certificate granted for {program.name}! Congratulations!", "success")
    return redirect(url_for("user_dashboard", program_id=program_id))


# ══════════════════════════════════════════════════════════════════
# Initialise DB tables on first run
# ══════════════════════════════════════════════════════════════════

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
