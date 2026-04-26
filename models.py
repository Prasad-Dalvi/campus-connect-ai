# models.py — CampusConnect database models

from extensions import db          # ← from extensions, NOT from app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    """Auth user — can be admin or ambassador."""
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False, default='ambassador')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    ambassador = db.relationship('Ambassador', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class Ambassador(db.Model):
    """Ambassador profile — linked to a User."""
    __tablename__ = 'ambassadors'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name              = db.Column(db.String(100), nullable=False)
    college           = db.Column(db.String(150), nullable=False)
    city              = db.Column(db.String(80))
    lat               = db.Column(db.Float)
    lng               = db.Column(db.Float)
    points            = db.Column(db.Integer, default=100)
    rank              = db.Column(db.Integer, default=0)
    risk_score        = db.Column(db.Integer, default=0)
    status            = db.Column(db.String(30), default='active')
    inactive_days     = db.Column(db.Integer, default=0)
    completion_rate   = db.Column(db.Float, default=1.0)
    response_time_hrs = db.Column(db.Float, default=4.0)
    portfolio_score   = db.Column(db.Integer, default=70)
    skills            = db.Column(db.String(200), default='Communication,Marketing')
    intervention_note = db.Column(db.Text)
    joined_at         = db.Column(db.DateTime, default=datetime.utcnow)
    last_active       = db.Column(db.DateTime, default=datetime.utcnow)

    tasks       = db.relationship('TaskAssignment', backref='ambassador', lazy='dynamic')
    submissions = db.relationship('Submission', backref='ambassador', lazy='dynamic')

    def calculate_risk(self):
        risk = 0
        reasons = []

        if self.inactive_days > 3:
            risk += 30
            reasons.append({'factor': f'Inactive {self.inactive_days} days', 'score': 30, 'icon': '😴'})

        if self.completion_rate < 0.5:
            risk += 30
            reasons.append({'factor': f'Task completion {int(self.completion_rate * 100)}%', 'score': 30, 'icon': '📋'})
        elif self.completion_rate < 0.75:
            risk += 15
            reasons.append({'factor': f'Task completion {int(self.completion_rate * 100)}%', 'score': 15, 'icon': '📋'})

        if self.response_time_hrs > 24:
            risk += 20
            reasons.append({'factor': f'Response delay >{int(self.response_time_hrs)}h', 'score': 20, 'icon': '⏱️'})
        elif self.response_time_hrs > 12:
            risk += 10
            reasons.append({'factor': f'Response delay >{int(self.response_time_hrs)}h', 'score': 10, 'icon': '⏱️'})

        self.risk_score = min(risk, 100)
        self.status = 'at_risk' if self.risk_score >= 70 else 'active'
        return self.risk_score, reasons

    def risk_label(self):
        if self.risk_score >= 70: return 'danger'
        if self.risk_score >= 40: return 'warning'
        return 'success'

    def risk_badge(self):
        if self.risk_score >= 70: return '🔴'
        if self.risk_score >= 40: return '🟡'
        return '🟢'

    def __repr__(self):
        return f'<Ambassador {self.name}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    points      = db.Column(db.Integer, default=50)
    deadline    = db.Column(db.DateTime)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'))

    assignments = db.relationship('TaskAssignment', backref='task', lazy='dynamic')


class TaskAssignment(db.Model):
    __tablename__ = 'task_assignments'

    id             = db.Column(db.Integer, primary_key=True)
    task_id        = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    ambassador_id  = db.Column(db.Integer, db.ForeignKey('ambassadors.id'), nullable=False)
    status         = db.Column(db.String(30), default='pending')
    assigned_at    = db.Column(db.DateTime, default=datetime.utcnow)
    auto_assigned  = db.Column(db.Boolean, default=False)

    submission = db.relationship('Submission', backref='assignment', uselist=False)


class Submission(db.Model):
    __tablename__ = 'submissions'

    id             = db.Column(db.Integer, primary_key=True)
    assignment_id  = db.Column(db.Integer, db.ForeignKey('task_assignments.id'), nullable=False)
    ambassador_id  = db.Column(db.Integer, db.ForeignKey('ambassadors.id'), nullable=False)
    proof_url      = db.Column(db.String(500))
    proof_text     = db.Column(db.Text)
    submitted_at   = db.Column(db.DateTime, default=datetime.utcnow)
    status         = db.Column(db.String(30), default='pending')
    ai_confidence  = db.Column(db.Float)
    ai_verdict     = db.Column(db.String(50))
    points_awarded = db.Column(db.Integer, default=0)