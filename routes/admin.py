# routes/admin.py — All admin-facing routes + API endpoints

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
import random

from app import db
from models import User, Ambassador, Task, TaskAssignment, Submission

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return login_required(decorated)


# ── Dashboard ──────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    ambassadors = Ambassador.query.order_by(Ambassador.risk_score.desc()).all()
    total       = len(ambassadors)
    at_risk     = [a for a in ambassadors if a.risk_score >= 60]
    engaged     = [a for a in ambassadors if a.risk_score < 40]
    engagement_pct = round(len(engaged) / total * 100) if total else 0

    # Recalculate risk for all (keep scores fresh)
    for a in ambassadors:
        a.calculate_risk()
    db.session.commit()

    # Top 10 leaderboard
    leaderboard = Ambassador.query.order_by(Ambassador.points.desc()).limit(10).all()

    tasks = Task.query.order_by(Task.created_at.desc()).all()

    return render_template(
        'admin/dashboard.html',
        ambassadors=ambassadors,
        at_risk=at_risk,
        total=total,
        engagement_pct=engagement_pct,
        leaderboard=leaderboard,
        tasks=tasks,
    )


# ── Ambassador Detail ──────────────────────────────────────────────────────
@admin_bp.route('/ambassador/<int:amb_id>')
@admin_required
def ambassador_detail(amb_id):
    amb = Ambassador.query.get_or_404(amb_id)
    risk_score, reasons = amb.calculate_risk()
    db.session.commit()

    # Weekly activity — last 7 days (mock based on inactive_days)
    weekly = []
    for i in range(6, -1, -1):
        active = i >= amb.inactive_days
        weekly.append({'day': i, 'active': active})

    # Trend data — simulate declining activity
    trend_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    base = int(amb.completion_rate * 100)
    trend_data = [
        min(100, base + random.randint(10, 30)),
        min(100, base + random.randint(5, 20)),
        min(100, base + random.randint(0, 10)),
        base,
    ]

    assignments = TaskAssignment.query.filter_by(ambassador_id=amb.id).all()
    submissions = Submission.query.filter_by(ambassador_id=amb.id).order_by(Submission.submitted_at.desc()).all()

    return render_template(
        'admin/ambassador_detail.html',
        amb=amb,
        risk_score=risk_score,
        reasons=reasons,
        weekly=weekly,
        trend_labels=trend_labels,
        trend_data=trend_data,
        assignments=assignments,
        submissions=submissions,
    )


# ── Execute All Interventions (AI Engine) ─────────────────────────────────
@admin_bp.route('/api/intervene/<int:amb_id>', methods=['POST'])
@admin_required
def intervene(amb_id):
    amb = Ambassador.query.get_or_404(amb_id)

    # 1. Auto-create quick task
    quick_task = Task(
        title='Quick Re-engagement: Share a Campus Moment',
        description='Take a photo/screenshot of something interesting on your campus today and share it. Easy 50 points!',
        points=50,
        deadline=datetime.utcnow().replace(hour=23, minute=59),
        created_by=current_user.id,
    )
    db.session.add(quick_task)
    db.session.flush()

    # Check if assignment already exists
    existing = TaskAssignment.query.filter_by(
        task_id=quick_task.id, ambassador_id=amb.id
    ).first()
    if not existing:
        assignment = TaskAssignment(
            task_id=quick_task.id,
            ambassador_id=amb.id,
            status='pending',
            auto_assigned=True,
        )
        db.session.add(assignment)

    # 2. Motivation message (mock — logged)
    amb.intervention_note = (
        f"🚀 Hey {amb.name.split()[0]}! We noticed you've been quiet lately — "
        f"we miss you! Complete today's quick task and earn 50 bonus points. "
        f"You're just {500 - amb.points} points away from the next tier! 💪"
    )

    # 3. Bonus points activation
    amb.points += 25  # Bonus points for re-engagement

    # 4. Update status
    amb.status = 'intervention'

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Intervention executed for {amb.name}',
        'actions': [
            {'icon': '📋', 'text': 'Quick task assigned: Share a Campus Moment'},
            {'icon': '💬', 'text': f'Motivation message queued for {amb.name}'},
            {'icon': '🎁', 'text': '25 bonus points activated'},
        ],
        'new_status': 'Intervention Active',
        'task_title': quick_task.title,
    })


# ── Approve Submission ─────────────────────────────────────────────────────
@admin_bp.route('/api/approve/<int:sub_id>', methods=['POST'])
@admin_required
def approve_submission(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    sub.status = 'verified'
    sub.points_awarded = sub.assignment.task.points

    amb = sub.ambassador
    old_points = amb.points
    old_risk   = amb.risk_score
    old_rank   = amb.rank

    amb.points          += sub.points_awarded
    amb.inactive_days    = max(0, amb.inactive_days - 2)
    amb.completion_rate  = min(1.0, amb.completion_rate + 0.15)
    amb.last_active      = datetime.utcnow()

    sub.assignment.status = 'verified'
    amb.calculate_risk()

    # Recalculate all ranks
    all_ambs = Ambassador.query.order_by(Ambassador.points.desc()).all()
    for idx, a in enumerate(all_ambs, 1):
        a.rank = idx

    db.session.commit()

    return jsonify({
        'success': True,
        'old_points': old_points,
        'new_points': amb.points,
        'old_risk': old_risk,
        'new_risk': amb.risk_score,
        'old_rank': old_rank,
        'new_rank': amb.rank,
        'status': amb.risk_badge(),
        'risk_label': amb.risk_label(),
    })


# ── Reject Submission ─────────────────────────────────────────────────────
@admin_bp.route('/api/reject/<int:sub_id>', methods=['POST'])
@admin_required
def reject_submission(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    sub.status = 'rejected'
    sub.assignment.status = 'rejected'
    db.session.commit()
    return jsonify({'success': True})


# ── Create Task ────────────────────────────────────────────────────────────
@admin_bp.route('/api/tasks', methods=['POST'])
@admin_required
def create_task():
    data  = request.json
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Title required'}), 400

    task = Task(
        title=title,
        description=data.get('description', ''),
        points=int(data.get('points', 50)),
        created_by=current_user.id,
    )
    db.session.add(task)
    db.session.flush()

    # Assign to specific ambassador if provided
    amb_id = data.get('ambassador_id')
    if amb_id:
        ta = TaskAssignment(task_id=task.id, ambassador_id=int(amb_id), status='pending')
        db.session.add(ta)

    db.session.commit()
    return jsonify({'success': True, 'task_id': task.id, 'title': task.title})


# ── Leaderboard API ────────────────────────────────────────────────────────
@admin_bp.route('/api/leaderboard')
@admin_required
def leaderboard_api():
    top = Ambassador.query.order_by(Ambassador.points.desc()).limit(15).all()
    return jsonify([{
        'rank':   a.rank,
        'name':   a.name,
        'college': a.college,
        'points': a.points,
        'badge':  a.risk_badge(),
        'status': a.status,
    } for a in top])


# ── Analytics API ──────────────────────────────────────────────────────────
@admin_bp.route('/api/analytics')
@admin_required
def analytics_api():
    ambassadors = Ambassador.query.all()
    total = len(ambassadors)

    risk_dist = {
        'safe':    sum(1 for a in ambassadors if a.risk_score < 40),
        'warning': sum(1 for a in ambassadors if 40 <= a.risk_score < 70),
        'danger':  sum(1 for a in ambassadors if a.risk_score >= 70),
    }

    # Completion trend (mock weekly data)
    completion_trend = [65, 68, 72, 70, 74, 71, 78]
    engagement_trend = [70, 72, 75, 73, 77, 75, 78]

    # Map data
    map_data = [{
        'name':    a.name,
        'college': a.college,
        'lat':     a.lat,
        'lng':     a.lng,
        'points':  a.points,
        'risk':    a.risk_score,
        'badge':   a.risk_badge(),
    } for a in ambassadors if a.lat and a.lng]

    return jsonify({
        'total':            total,
        'risk_dist':        risk_dist,
        'completion_trend': completion_trend,
        'engagement_trend': engagement_trend,
        'map_data':         map_data,
    })


# ── Submissions list (for admin review) ────────────────────────────────────
@admin_bp.route('/submissions')
@admin_required
def submissions():
    pending = Submission.query.filter_by(status='pending').order_by(Submission.submitted_at.desc()).all()
    return render_template('admin/submissions.html', submissions=pending)
