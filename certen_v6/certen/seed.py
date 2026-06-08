"""
seed.py – Populate the CertEn database with sample data.
Run once:  python seed.py
"""
from app import app
from models import db, User, Program, Enrollment, Task, TaskCompletion, Certificate
from datetime import datetime, timezone


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ── Users ────────────────────────────────────────────────
        admin = User(first_name="Admin", last_name="User",
                     email="admin@certen.com", is_admin=True, dob="01/01/1990")
        u1 = User(first_name="Alice",   last_name="Smith",  email="alice@gmail.com",   dob="05/03/1998")
        u2 = User(first_name="Bob",     last_name="Jones",  email="bob@gmail.com",     dob="12/07/1995")
        u3 = User(first_name="Carol",   last_name="White",  email="carol@gmail.com",   dob="22/11/2000")
        u4 = User(first_name="David",   last_name="Brown",  email="david@gmail.com",   dob="30/04/1997")
        db.session.add_all([admin, u1, u2, u3, u4])
        db.session.flush()

        # ── Programs ─────────────────────────────────────────────
        p1 = Program(name="Python Fundamentals",   mode="Online",  description="Core Python programming skills.")
        p2 = Program(name="Data Analysis",         mode="Hybrid",  description="NumPy, Pandas, and visualisation.")
        p3 = Program(name="Machine Learning",      mode="Online",  description="Supervised & unsupervised learning.")
        p4 = Program(name="Web Development",       mode="Offline", description="HTML, CSS, JS, and Flask.")
        db.session.add_all([p1, p2, p3, p4])
        db.session.flush()

        # ── Tasks per program ────────────────────────────────────
        tasks_p1 = [
            Task(program=p1, serial=1, name="Variables & Types",   due_date="10/06/2025"),
            Task(program=p1, serial=2, name="Control Flow",        due_date="17/06/2025"),
            Task(program=p1, serial=3, name="Functions & Modules", due_date="24/06/2025"),
        ]
        tasks_p2 = [
            Task(program=p2, serial=1, name="NumPy Arrays",        due_date="12/06/2025"),
            Task(program=p2, serial=2, name="Pandas DataFrames",   due_date="19/06/2025"),
            Task(program=p2, serial=3, name="Matplotlib Plots",    due_date="26/06/2025"),
        ]
        tasks_p3 = [
            Task(program=p3, serial=1, name="Linear Regression",   due_date="15/06/2025"),
            Task(program=p3, serial=2, name="Decision Trees",      due_date="22/06/2025"),
            Task(program=p3, serial=3, name="Model Evaluation",    due_date="29/06/2025"),
        ]
        tasks_p4 = [
            Task(program=p4, serial=1, name="HTML & CSS Basics",   due_date="11/06/2025"),
            Task(program=p4, serial=2, name="JavaScript Essentials",due_date="18/06/2025"),
            Task(program=p4, serial=3, name="Flask Backend",       due_date="25/06/2025"),
        ]
        all_tasks = tasks_p1 + tasks_p2 + tasks_p3 + tasks_p4
        db.session.add_all(all_tasks)
        db.session.flush()

        # ── Enrollments ──────────────────────────────────────────
        enrollments = [
            Enrollment(user=u1, program=p1, start_date="01/06/2025", time_from="09:00 AM", time_to="11:00 AM"),
            Enrollment(user=u1, program=p2, start_date="01/06/2025", time_from="12:00 PM", time_to="02:00 PM"),
            Enrollment(user=u1, program=p3, start_date="02/06/2025", time_from="03:00 PM", time_to="05:00 PM"),
            Enrollment(user=u2, program=p1, start_date="01/06/2025", time_from="09:00 AM", time_to="11:00 AM"),
            Enrollment(user=u2, program=p4, start_date="02/06/2025", time_from="10:00 AM", time_to="12:00 PM"),
            Enrollment(user=u3, program=p2, start_date="03/06/2025", time_from="01:00 PM", time_to="03:00 PM"),
            Enrollment(user=u3, program=p3, start_date="03/06/2025", time_from="04:00 PM", time_to="06:00 PM"),
            Enrollment(user=u4, program=p1, start_date="04/06/2025", time_from="09:00 AM", time_to="11:00 AM"),
            Enrollment(user=u4, program=p2, start_date="04/06/2025", time_from="12:00 PM", time_to="02:00 PM"),
            Enrollment(user=u4, program=p4, start_date="05/06/2025", time_from="03:00 PM", time_to="05:00 PM"),
        ]
        db.session.add_all(enrollments)
        db.session.flush()

        # ── Task Completions ─────────────────────────────────────
        completions = [
            # Alice – P1: all done, P2: partial, P3: none
            TaskCompletion(user=u1, task=tasks_p1[0], status="C"),
            TaskCompletion(user=u1, task=tasks_p1[1], status="C"),
            TaskCompletion(user=u1, task=tasks_p1[2], status="C"),   # P1 fully done ✓
            TaskCompletion(user=u1, task=tasks_p2[0], status="C"),
            TaskCompletion(user=u1, task=tasks_p2[1], status="NC"),
            TaskCompletion(user=u1, task=tasks_p2[2], status="NC"),
            TaskCompletion(user=u1, task=tasks_p3[0], status="NC"),
            TaskCompletion(user=u1, task=tasks_p3[1], status="NC"),
            TaskCompletion(user=u1, task=tasks_p3[2], status="NC"),
            # Bob – P1 partial, P4 partial
            TaskCompletion(user=u2, task=tasks_p1[0], status="C"),
            TaskCompletion(user=u2, task=tasks_p1[1], status="NC"),
            TaskCompletion(user=u2, task=tasks_p1[2], status="NC"),
            TaskCompletion(user=u2, task=tasks_p4[0], status="C"),
            TaskCompletion(user=u2, task=tasks_p4[1], status="C"),
            TaskCompletion(user=u2, task=tasks_p4[2], status="NC"),
            # Carol – P2 all done, P3 partial
            TaskCompletion(user=u3, task=tasks_p2[0], status="C"),
            TaskCompletion(user=u3, task=tasks_p2[1], status="C"),
            TaskCompletion(user=u3, task=tasks_p2[2], status="C"),   # P2 fully done ✓
            TaskCompletion(user=u3, task=tasks_p3[0], status="C"),
            TaskCompletion(user=u3, task=tasks_p3[1], status="NC"),
            TaskCompletion(user=u3, task=tasks_p3[2], status="NC"),
            # David – all partial
            TaskCompletion(user=u4, task=tasks_p1[0], status="C"),
            TaskCompletion(user=u4, task=tasks_p1[1], status="NC"),
            TaskCompletion(user=u4, task=tasks_p1[2], status="NC"),
            TaskCompletion(user=u4, task=tasks_p2[0], status="C"),
            TaskCompletion(user=u4, task=tasks_p2[1], status="C"),
            TaskCompletion(user=u4, task=tasks_p2[2], status="NC"),
            TaskCompletion(user=u4, task=tasks_p4[0], status="NC"),
            TaskCompletion(user=u4, task=tasks_p4[1], status="NC"),
            TaskCompletion(user=u4, task=tasks_p4[2], status="NC"),
        ]
        db.session.add_all(completions)
        db.session.flush()

        # ── Certificates ─────────────────────────────────────────
        # Alice completed P1 → grant automatically
        cert1 = Certificate(user=u1, program=p1, status="granted",
                            granted_at=datetime.now(timezone.utc))
        # Carol completed P2 → grant automatically
        cert2 = Certificate(user=u3, program=p2, status="granted",
                            granted_at=datetime.now(timezone.utc))
        db.session.add_all([cert1, cert2])

        db.session.commit()
        print("✅ Database seeded successfully.")
        print(f"   Users: {User.query.count()}")
        print(f"   Programs: {Program.query.count()}")
        print(f"   Tasks: {Task.query.count()}")
        print(f"   Enrollments: {Enrollment.query.count()}")
        print(f"   Completions: {TaskCompletion.query.count()}")
        print(f"   Certificates: {Certificate.query.count()}")


if __name__ == "__main__":
    seed()
