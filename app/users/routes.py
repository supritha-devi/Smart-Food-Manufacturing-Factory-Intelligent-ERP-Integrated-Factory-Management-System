from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from app.auth.permissions import require_login, require_permission
from app.audit.service import add_audit

users_bp = Blueprint("users", __name__, url_prefix="/users")


def fetch_roles(db):
    con = db.connect(); cur = con.cursor()
    cur.execute("SELECT id, name FROM roles ORDER BY name")
    rows = cur.fetchall(); con.close()
    return [dict(row) if db.is_postgres else dict(row) for row in rows]


@users_bp.get("/")
@require_login
@require_permission("employees:VIEW")
def user_list():
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role", "")
    params = []
    conditions = []
    if search:
        conditions.append(f"(LOWER(u.name) LIKE {p} OR LOWER(u.email) LIKE {p} OR LOWER(u.employee_id) LIKE {p})")
        term = f"%{search.lower()}%"; params.extend([term, term, term])
    if role_filter:
        conditions.append(f"r.name={p}"); params.append(role_filter)
    where = " AND ".join(conditions)
    if where:
        where = "WHERE " + where
    cur.execute(
        f"SELECT u.id,u.employee_id,u.name,u.email,u.username,u.phone,u.is_active,u.last_login_at,u.created_at,r.name AS role_name "
        f"FROM users u LEFT JOIN user_roles ur ON ur.user_id=u.id LEFT JOIN roles r ON r.id=ur.role_id {where} ORDER BY u.created_at DESC",
        params,
    )
    rows = cur.fetchall(); con.close()
    users = [dict(row) if db.is_postgres else dict(row) for row in rows]
    return render_template("users/list.html", users=users, roles=fetch_roles(db), selected_role=role_filter)


@users_bp.get("/new")
@require_login
def new_user():
    if "OWNER" not in session.get("roles", []): abort(403)
    db = current_app.extensions["database"]
    return render_template("users/form.html", user=None, roles=fetch_roles(db), title="Create Employee")


@users_bp.post("/new")
@require_login
def create_user():
    if "OWNER" not in session.get("roles", []): abort(403)
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    employee_id = request.form.get("employee_id", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    username = request.form.get("username", "").strip()
    phone = request.form.get("phone", "").strip()
    role_id = request.form.get("role_id")
    password = request.form.get("temporary_password", "")
    if not all([employee_id, name, email, username, role_id, password]) or len(password) < 8:
        con.close(); flash("Complete all required fields. Temporary password must have at least 8 characters.", "danger")
        return redirect(url_for("users.new_user"))
    try:
        cur.execute(f"INSERT INTO users (employee_id,name,email,username,phone,password_hash,must_change_password) VALUES ({p},{p},{p},{p},{p},{p},1)", (employee_id,name,email,username,phone,generate_password_hash(password)))
        if db.is_postgres:
            cur.execute("SELECT id FROM users WHERE email=%s", (email,)); user = cur.fetchone(); user_id=user["id"]
        else:
            user_id=cur.lastrowid
        cur.execute(f"INSERT INTO user_roles (user_id,role_id,is_primary) VALUES ({p},{p},1)", (user_id, role_id))
        cur.execute(f"INSERT INTO employee_details (user_id,job_title,status) VALUES ({p},{p},'ACTIVE')", (user_id, name))
        con.commit()
        add_audit("CREATE", "Users", str(user_id), new_value=f"Created {name} ({email})")
        flash("Employee account created successfully.", "success")
    except Exception:
        con.rollback(); flash("Employee ID, email or username already exists.", "danger")
    finally:
        con.close()
    return redirect(url_for("users.user_list"))


@users_bp.post("/<int:user_id>/toggle")
@require_login
def toggle_user(user_id):
    if "OWNER" not in session.get("roles", []): abort(403)
    db=current_app.extensions["database"]; con=db.connect(); p=db.placeholder(); cur=con.cursor()
    cur.execute(f"SELECT is_active,name,email FROM users WHERE id={p}",(user_id,)); row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    user=dict(row) if db.is_postgres else dict(row)
    new_status=0 if user["is_active"] else 1
    cur.execute(f"UPDATE users SET is_active={p},updated_at=CURRENT_TIMESTAMP WHERE id={p}",(new_status,user_id))
    con.commit(); con.close()
    add_audit("ACTIVATE" if new_status else "DEACTIVATE","Users",str(user_id),previous_value=str(bool(user["is_active"])),new_value=str(bool(new_status)))
    flash("Account status updated.", "success")
    return redirect(url_for("users.user_list"))


@users_bp.get("/<int:user_id>/edit")
@require_login
def edit_user(user_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(
        f"SELECT u.*, r.id AS role_id FROM users u LEFT JOIN user_roles ur ON ur.user_id=u.id AND ur.is_primary=1 LEFT JOIN roles r ON r.id=ur.role_id WHERE u.id={p}",
        (user_id,),
    )
    row = cur.fetchone()
    con.close()
    if not row:
        abort(404)
    user = dict(row) if db.is_postgres else dict(row)
    return render_template("users/form.html", user=user, roles=fetch_roles(db), title="Edit Employee")


@users_bp.post("/<int:user_id>/edit")
@require_login
def update_user(user_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    employee_id = request.form.get("employee_id", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    username = request.form.get("username", "").strip()
    phone = request.form.get("phone", "").strip()
    role_id = request.form.get("role_id")
    if not all([employee_id, name, email, username, role_id]):
        con.close()
        flash("Complete all required fields.", "danger")
        return redirect(url_for("users.edit_user", user_id=user_id))
    try:
        cur.execute(
            f"UPDATE users SET employee_id={p}, name={p}, email={p}, username={p}, phone={p}, updated_at=CURRENT_TIMESTAMP WHERE id={p}",
            (employee_id, name, email, username, phone, user_id),
        )
        cur.execute(f"DELETE FROM user_roles WHERE user_id={p}", (user_id,))
        cur.execute(f"INSERT INTO user_roles (user_id,role_id,is_primary) VALUES ({p},{p},1)", (user_id, role_id))
        cur.execute(f"UPDATE employee_details SET job_title={p} WHERE user_id={p}", (name, user_id))
        con.commit()
        add_audit("UPDATE", "Users", str(user_id), new_value=f"Updated {name} ({email})")
        flash("Employee account updated successfully.", "success")
    except Exception:
        con.rollback()
        flash("Employee ID, email or username already exists.", "danger")
    finally:
        con.close()
    return redirect(url_for("users.user_list"))


@users_bp.post("/<int:user_id>/reset-password")
@require_login
def reset_password(user_id):
    if "OWNER" not in session.get("roles", []): abort(403)
    password=request.form.get("password","")
    if len(password)<8:
        flash("Temporary password must contain at least 8 characters.","danger"); return redirect(url_for("users.user_list"))
    db=current_app.extensions["database"]; con=db.connect(); p=db.placeholder(); cur=con.cursor()
    cur.execute(f"UPDATE users SET password_hash={p},must_change_password=1,failed_attempts=0,locked_until=NULL,updated_at=CURRENT_TIMESTAMP WHERE id={p}",(generate_password_hash(password),user_id))
    con.commit(); con.close()
    add_audit("RESET_PASSWORD","Users",str(user_id),new_value="Temporary password assigned")
    flash("Password reset successfully. The user must change it on next login.","success")
    return redirect(url_for("users.user_list"))
