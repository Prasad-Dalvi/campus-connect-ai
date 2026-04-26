# app.py — CampusConnect main application entry point

from flask import Flask
import os

from extensions import db, login_manager   # ← from extensions, NOT defined here


def create_app():
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'campusconnect-secret-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campusconnect.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to continue.'
    login_manager.login_message_category = 'warning'

    # ── Blueprints ────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.ambassador import ambassador_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ambassador_bp, url_prefix='/ambassador')

    # ── User loader ───────────────────────────────────────────────────────
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── DB init + seed ────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        from seed import seed_data
        seed_data()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)