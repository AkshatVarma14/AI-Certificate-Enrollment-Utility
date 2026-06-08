"""
models.py – CertEn database schema
====================================
Tables:
  users            – registered users (admin + regular)
  programs         – training programs
  enrollments      – which users are enrolled in which programs (M2M)
  tasks            – tasks belonging to a program
  task_completions – per-user completion status for each task
  certificates     – certificates granted/requested per user per program
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80),  nullable=False)
    last_name  = db.Column(db.String(80),  nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    dob        = db.Column(db.String(20))          # stored as "DD/MM/YYYY"
    is_admin   = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # relationships
    enrollments      = db.relationship("Enrollment",      back_populates="user", cascade="all, delete-orphan")
    task_completions = db.relationship("TaskCompletion",  back_populates="user", cascade="all, delete-orphan")
    certificates     = db.relationship("Certificate",     back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def __repr__(self):
        return f"<User {self.email}>"


# ─────────────────────────────────────────────────────────────────
# Program
# ─────────────────────────────────────────────────────────────────
class Program(db.Model):
    __tablename__ = "programs"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    mode        = db.Column(db.String(20))   # Online / Offline / Hybrid
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # relationships
    enrollments  = db.relationship("Enrollment",  back_populates="program", cascade="all, delete-orphan")
    tasks        = db.relationship("Task",         back_populates="program", cascade="all, delete-orphan",
                                   order_by="Task.serial")
    certificates = db.relationship("Certificate", back_populates="program", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Program {self.name}>"


# ─────────────────────────────────────────────────────────────────
# Enrollment  (User ↔ Program  M2M with extra data)
# ─────────────────────────────────────────────────────────────────
class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"),    nullable=False)
    program_id  = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    start_date  = db.Column(db.String(20))
    time_from   = db.Column(db.String(10))
    time_to     = db.Column(db.String(10))

    user    = db.relationship("User",    back_populates="enrollments")
    program = db.relationship("Program", back_populates="enrollments")

    __table_args__ = (db.UniqueConstraint("user_id", "program_id", name="uq_user_program"),)

    @property
    def progress(self):
        """Percentage of tasks completed by this user in this program."""
        total = len(self.program.tasks)
        if total == 0:
            return 0
        completed = TaskCompletion.query.filter_by(
            user_id=self.user_id, status="C"
        ).join(Task).filter(Task.program_id == self.program_id).count()
        return round((completed / total) * 100)

    def __repr__(self):
        return f"<Enrollment user={self.user_id} program={self.program_id}>"


# ─────────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────────
class Task(db.Model):
    __tablename__ = "tasks"

    id         = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    serial     = db.Column(db.Integer, nullable=False)
    name       = db.Column(db.String(120), nullable=False)
    due_date   = db.Column(db.String(20))   # "DD/MM/YYYY"

    program     = db.relationship("Program",        back_populates="tasks")
    completions = db.relationship("TaskCompletion", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task {self.serial}: {self.name}>"


# ─────────────────────────────────────────────────────────────────
# TaskCompletion  – per-user status for each task
# ─────────────────────────────────────────────────────────────────
class TaskCompletion(db.Model):
    __tablename__ = "task_completions"

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"),  nullable=False)
    task_id  = db.Column(db.Integer, db.ForeignKey("tasks.id"),  nullable=False)
    status   = db.Column(db.String(2), default="NC")   # "C" | "NC"
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="task_completions")
    task = db.relationship("Task", back_populates="completions")

    __table_args__ = (db.UniqueConstraint("user_id", "task_id", name="uq_user_task"),)

    def __repr__(self):
        return f"<TaskCompletion user={self.user_id} task={self.task_id} status={self.status}>"


# ─────────────────────────────────────────────────────────────────
# Certificate
# ─────────────────────────────────────────────────────────────────
class Certificate(db.Model):
    __tablename__ = "certificates"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"),    nullable=False)
    program_id  = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    # Status lifecycle: "requested" → "granted" | "denied"
    status      = db.Column(db.String(20), default="requested")
    requested_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    granted_at   = db.Column(db.DateTime, nullable=True)

    user    = db.relationship("User",    back_populates="certificates")
    program = db.relationship("Program", back_populates="certificates")

    __table_args__ = (db.UniqueConstraint("user_id", "program_id", name="uq_user_program_cert"),)

    def __repr__(self):
        return f"<Certificate user={self.user_id} program={self.program_id} status={self.status}>"
