import secrets
from datetime import datetime, timedelta
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for, abort
from werkzeug.security import check_password_hash, generate_password_hash
from app.time_utils import now as factory_now

from app.auth.permissions import get_user_roles, get_user_permissions, require_permission
from app.audit.service import add_audit


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboards.dashboard"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    db = current_app.extensions["database"]
    con = db.connect()
    p = db.placeholder()
    identifier = request.form.get("identifier", "").strip().lower()
    password = request.form.get("password", "")

    cur = con.cursor()
    cur.execute(
        f"SELECT * FROM users WHERE LOWER(email)={p} OR LOWER(username)={p}",
        (identifier, identifier),
    )
    row = cur.fetchone()
    user = dict(row) if db.is_postgres else (dict(row) if row else None)

    cur.execute(
        f"INSERT INTO login_attempts (email_or_username, ip_address, succeeded) VALUES ({p},{p},{p})",
        (identifier, request.remote_addr or "", bool(user and check_password_hash(user["password_hash"], password))),
    )

    if not user:
        con.commit(); con.close()
        flash("Invalid email/username or password.", "danger")
        return redirect(url_for("auth.login"))

    current_time = factory_now()
    current_time_naive = current_time.replace(tzinfo=None)
    locked_until = user.get("locked_until")
    if locked_until:
        try:
            lock = datetime.fromisoformat(str(locked_until).replace("Z", "+00:00")).replace(tzinfo=None)
            if lock > current_time_naive:
                con.commit(); con.close()
                flash("Account temporarily locked. Try again later.", "danger")
                return redirect(url_for("auth.login"))
        except ValueError:
            pass

    valid_password = check_password_hash(user["password_hash"], password)
    if not user["is_active"]:
        con.commit(); con.close()
        flash("Invalid email/username or password.", "danger")
        return redirect(url_for("auth.login"))

    if not valid_password:
        attempts = int(user["failed_attempts"] or 0) + 1
        lock_value = None
        if attempts >= 5:
            lock_value = (current_time + timedelta(minutes=15)).isoformat()
            cur.execute(f"UPDATE users SET failed_attempts={p}, locked_until={p}, updated_at=CURRENT_TIMESTAMP WHERE id={p}", (attempts, lock_value, user["id"]))
        else:
            cur.execute(f"UPDATE users SET failed_attempts={p}, updated_at=CURRENT_TIMESTAMP WHERE id={p}", (attempts, user["id"]))
        con.commit(); con.close()
        flash("Invalid email/username or password.", "danger")
        return redirect(url_for("auth.login"))

    cur.execute(f"UPDATE users SET failed_attempts=0, locked_until=NULL, last_login_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id={p}", (user["id"],))
    con.commit(); con.close()

    session.clear()
    session.permanent = bool(request.form.get("remember"))
    session["user_id"] = user["id"]
    session["email"] = user["email"]
    session["name"] = user["name"]
    session["roles"] = get_user_roles(user["id"])
    session["permissions"] = get_user_permissions(user["id"])
    session["session_id"] = secrets.token_urlsafe(32)
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(
        f"INSERT INTO user_sessions (session_id,user_id,ip_address,user_agent) VALUES ({p},{p},{p},{p})",
        (session["session_id"], user["id"], request.remote_addr or "", request.user_agent.string),
    )
    con.commit(); con.close()
    add_audit("LOGIN", "Authentication", str(user["id"]), new_value="Successful login")
    if user["must_change_password"]:
        return redirect(url_for("auth.change_password"))
    return redirect(url_for("dashboards.dashboard"))


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    add_audit("LOGOUT", "Authentication")
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(
        f"UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE session_id={p}",
        (session.get("session_id"),),
    )
    con.commit(); con.close()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.get("/change-password")
def change_password():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    return render_template("auth/change_password.html")


@auth_bp.post("/change-password")
def change_password_post():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    if len(password) < 8 or password != confirm:
        flash("Password must be at least 8 characters and both entries must match.", "danger")
        return redirect(url_for("auth.change_password"))
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(f"UPDATE users SET password_hash={p}, must_change_password=0, failed_attempts=0, locked_until=NULL, updated_at=CURRENT_TIMESTAMP WHERE id={p}", (generate_password_hash(password), session["user_id"]))
    cur.execute(
        f"UPDATE user_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE user_id={p} AND revoked_at IS NULL",
        (session["user_id"],),
    )
    con.commit(); con.close()
    add_audit("CHANGE_PASSWORD", "Authentication", str(session["user_id"]), new_value="Password changed")
    flash("Password changed successfully.", "success")
    return redirect(url_for("dashboards.dashboard"))


@auth_bp.get("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")


@auth_bp.post("/forgot-password")
def forgot_password_post():
    db = current_app.extensions["database"]
    identifier = request.form.get("identifier", "").strip()
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(f"SELECT id, email FROM users WHERE LOWER(email)={p} OR LOWER(username)={p}", (identifier.lower(), identifier.lower()))
    row = cur.fetchone()
    if row:
        user = dict(row) if db.is_postgres else dict(row)
        token = secrets.token_urlsafe(32)
        expires = (factory_now() + timedelta(minutes=30)).isoformat()
        import hashlib
        cur.execute(f"DELETE FROM password_reset_tokens WHERE user_id={p} AND (used_at IS NOT NULL OR expires_at < {p})", (user["id"], factory_now().replace(tzinfo=None).isoformat()))
        cur.execute(f"INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES ({p},{p},{p})", (user["id"], hashlib.sha256(token.encode()).hexdigest(), expires))
        con.commit()
    con.close()
    flash("If the account exists, password reset instructions have been prepared.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.get("/reset-password/<token>")
def reset_password(token):
    return render_template("auth/reset_password.html", token=token)


@auth_bp.post("/reset-password/<token>")
def reset_password_post(token):
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    if len(password) < 8 or password != confirm_password:
        flash("Password must be at least 8 characters and both entries must match.", "danger")
        return redirect(url_for("auth.reset_password", token=token))

    import hashlib
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    cur.execute(
        f"SELECT user_id, expires_at FROM password_reset_tokens WHERE token_hash={p} AND used_at IS NULL",
        (token_hash,),
    )
    row = cur.fetchone()
    if not row:
        con.close()
        flash("This password reset link is invalid or has already been used.", "danger")
        return redirect(url_for("auth.login"))

    reset = dict(row) if db.is_postgres else dict(row)
    try:
        expires = datetime.fromisoformat(str(reset["expires_at"]).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        expires = datetime.min
    if expires <= factory_now().replace(tzinfo=None):
        con.close()
        flash("This password reset link has expired.", "danger")
        return redirect(url_for("auth.login"))

    cur.execute(
        f"UPDATE users SET password_hash={p}, must_change_password=0, failed_attempts=0, locked_until=NULL, updated_at=CURRENT_TIMESTAMP WHERE id={p}",
        (generate_password_hash(password), reset["user_id"]),
    )
    cur.execute(
        f"UPDATE password_reset_tokens SET used_at=CURRENT_TIMESTAMP WHERE token_hash={p}",
        (token_hash,),
    )
    con.commit()
    con.close()
    add_audit("RESET_PASSWORD", "Authentication", str(reset["user_id"]), new_value="Password reset by secure link")
    flash("Password reset successfully. You can now sign in.", "success")
    return redirect(url_for("auth.login"))
