import os
from datetime import timedelta
from flask import Flask, redirect, session, url_for
from dotenv import load_dotenv

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.settings.BaseConfig")

    if test_config:
        app.config.update(test_config)

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
    app.config["FACTORY_TIMEZONE"] = "Tamilnadu"

    from app.database import Database
    app.extensions["database"] = Database(app.config.get("DATABASE_URL") or os.getenv("DATABASE_URL"))

    from app.auth.routes import auth_bp
    from app.users.routes import users_bp
    from app.dashboards.routes import dashboards_bp
    from app.modules import modules_bp
    from app.voice import voice_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(dashboards_bp)
    app.register_blueprint(modules_bp)
    app.register_blueprint(voice_bp)

    @app.context_processor
    def inject_csrf():
        import secrets
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"]}

    @app.context_processor
    def inject_factory_time():
        from app.time_utils import now, format_date
        current = now()
        return {
            "factory_now": current,
            "factory_date": format_date(current),
            "factory_time": current.strftime("%I:%M:%S %p"),
            "factory_timezone": "Tamilnadu",
        }

    @app.template_filter("rupees")
    def format_rupees(value):
        try:
            val = float(value or 0) / 100.0
            return f"₹{val:,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    @app.before_request
    def enforce_csrf():
        import secrets
        from flask import request, abort
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.headers.get("X-CSRF-Token") != session.get("csrf_token") and request.form.get("csrf_token") != session.get("csrf_token"):
                abort(400, "Invalid or missing CSRF token")

    @app.errorhandler(403)
    def access_denied(error):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(401)
    def unauthorized(error):
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    @app.errorhandler(400)
    def bad_request(error):
        from flask import render_template
        return render_template("errors/400.html", message=error.description), 400

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboards.dashboard"))
        return redirect(url_for("auth.login"))

    @app.cli.command("purge-voice-recordings")
    def purge_voice_recordings():
        """Purge archived or expired voice audio and database records."""
        from app.voice.routes import purge_expired_voice_files
        deleted = purge_expired_voice_files(app.extensions["database"])
        print(f"Purged {deleted} voice recording(s).")

    return app
