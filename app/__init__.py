import os

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

from .database import get_service_db
from .models import User
from .mail import mail

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "danger"

csrf = CSRFProtect()


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    # --- Mail configuration (used for "forgot password" emails) ---
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "localhost")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = _env_bool("MAIL_USE_TLS", True)
    app.config["MAIL_USE_SSL"] = _env_bool("MAIL_USE_SSL", False)
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME"))

    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # --- Blueprints ---
    from .auth import auth_bp
    from .main import main_bp
    from .users import users_bp
    from .documents import documents_bp
    from .chat import chat_bp
    from .profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(profile_bp)

    # --- Flask-Login user loader ---
    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            db = get_service_db()
            res = db.table("users").select("*").eq("id", user_id).limit(1).execute()
            rows = res.data or []
            return User(rows[0]) if rows else None
        except Exception:
            return None

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403,
                                message="Vous n'avez pas les privilèges nécessaires pour accéder à cette page ou effectuer cette action."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404,
                                message="Page introuvable."), 404

    return app
