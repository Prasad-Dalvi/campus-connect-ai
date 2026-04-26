# routes/ambassador.py — Ambassador-facing routes

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
import random

from app import db
from models import Ambassador, Task, TaskAssignment, Submission

ambassador_bp = Blueprint('ambassador', __name__)


def ambassador_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'ambassador':
            flash('Ambassador access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return login_required(decorated)


# ── Ambassador Dashboard ───────────────────────────────────────────────────
@ambassador_bp.route('/dashboard')
@ambassador_required
def dashboard():
    amb = Ambassador.query.filter_by(user_id=current_user.id).first()
    if not amb:
        flash('Ambassador profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    amb.calculate_risk()
    db.session.commit()

    # My tasks
    assignments = (
        TaskAssignment.query
        .filter_by(ambassador_id=amb.id)
        .order_by(TaskAssignment.assigned_at.desc())
        .all()
    )

    # Leaderboard (top 10 + my position)
    leaderboard = Ambassador.query.order_by(Ambassador.points.desc()).limit(10).all()

    # Skills list
    skills = [s.strip() for s in (amb.skills or '').split(',') if s.strip()]

    # Growth tips
    tips = _growth_tips(amb)

    return render_template(
        'ambassador/dashboard.html',
        amb=amb,
        assignments=assignments,
        leaderboard=leaderboard,
        skills=skills,
        tips=tips,
    )


# ── Task Detail / Submit Proof ─────────────────────────────────────────────
@ambassador_bp.route('/task/<int:assignment_id>', methods=['GET', 'POST'])
@ambassador_required
def task_detail(assignment_id):
    assignment = TaskAssignment.query.get_or_404(assignment_id)
    amb = Ambassador.query.filter_by(user_id=current_user.id).first()

    # Ownership check
    if assignment.ambassador_id != amb.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('ambassador.dashboard'))

    if request.method == 'POST':
        proof_url  = request.form.get('proof_url', '').strip()
        proof_text = request.form.get('proof_text', '').strip()

        if not proof_url and not proof_text:
            flash('Please provide a proof URL or description.', 'warning')
            return redirect(url_for('ambassador.task_detail', assignment_id=assignment_id))

        # Create submission
        sub = Submission(
            assignment_id=assignment.id,
            ambassador_id=amb.id,
            proof_url=proof_url,
            proof_text=proof_text,
            submitted_at=datetime.utcnow(),
            status='pending',
            # Mock AI verification
            ai_confidence=round(random.uniform(0.80, 0.97), 2),
            ai_verdict='verified',
        )
        db.session.add(sub)

        # Update assignment status
        assignment.status = 'submitted'

        # Ambassador activity update
        amb.inactive_days = 0
        amb.last_active   = datetime.utcnow()
        amb.calculate_risk()

        db.session.commit()
        flash('✅ Proof submitted! Admin will review shortly.', 'success')
        return redirect(url_for('ambassador.dashboard'))

    return render_template('ambassador/task_detail.html', assignment=assignment, amb=amb)


# ── Growth Tips helper ────────────────────────────────────────────────────
def _growth_tips(amb):
    tips = []
    skills = [s.strip() for s in (amb.skills or '').split(',')]
    if len(skills) < 4:
        tips.append(f'Add {4 - len(skills)} more skills to boost your portfolio score.')
    if amb.portfolio_score < 90:
        diff = 90 - amb.portfolio_score
        tips.append(f'Complete {max(1, diff // 10)} more tasks to reach a portfolio score of 90.')
    if amb.completion_rate < 0.8:
        tips.append('Increase task completion rate above 80% for a recruiter highlight.')
    if not tips:
        tips.append('Great work! Keep completing tasks to maintain your top ranking.')
    return tips
