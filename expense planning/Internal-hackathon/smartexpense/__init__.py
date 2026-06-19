from flask import Flask, redirect, url_for
from .extensions import db, migrate, login_manager
from .config import Config

from .blueprints.auth.routes import auth_bp
from .blueprints.dashboard.routes import dashboard_bp
from .blueprints.expenses.routes import expenses_bp
from .blueprints.reports.routes import reports_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Ensure tables exist for a smooth first run
    with app.app_context():
        db.create_all()
        # Seed global categories (shared across all accounts) if not present
        try:
            from .models import Category
            defaults = [
                ("Groceries", "expense"),
                ("Clothing", "expense"),
                ("Transport", "expense"),
                ("Bills", "expense"),
                ("Entertainment", "expense"),
            ]
            existing = {c.name.lower(): c for c in Category.query.filter_by(user_id=None).all()}
            created = 0
            for name, ctype in defaults:
                if name.lower() not in existing:
                    db.session.add(Category(user_id=None, name=name, type=ctype))
                    created += 1
            if created:
                db.session.commit()
        except Exception:
            # Do not block app startup if seeding fails
            db.session.rollback()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(reports_bp)

    @app.route("/")
    def root():
        return redirect(url_for("dashboard.index"))

    return app
