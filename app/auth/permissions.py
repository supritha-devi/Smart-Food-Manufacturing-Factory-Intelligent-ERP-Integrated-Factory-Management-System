from functools import wraps
from flask import abort, current_app, session


def get_user_roles(user_id):
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(f"SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id=r.id WHERE ur.user_id={p}", (user_id,))
    rows = cur.fetchall(); con.close()
    return [dict(row)["name"] if db.is_postgres else row["name"] for row in rows]


def get_user_permissions(user_id):
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(f"SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id=r.id WHERE ur.user_id={p}", (user_id,))
    role_rows = cur.fetchall()
    roles = [dict(row)["name"] if db.is_postgres else row["name"] for row in role_rows]
    if "OWNER" in roles:
        con.close()
        return ["*"]
    cur.execute(
        f"SELECT DISTINCT permission_id FROM (SELECT permission_id FROM role_permissions WHERE role_id IN (SELECT role_id FROM user_roles WHERE user_id={p}) UNION SELECT permission_id FROM user_permissions WHERE user_id={p}) effective",
        (user_id, user_id),
    )
    permission_ids = cur.fetchall()
    if not permission_ids:
        con.close(); return []
    ids = [dict(row)["permission_id"] if db.is_postgres else row["permission_id"] for row in permission_ids]
    placeholders = ",".join([p] * len(ids))
    cur.execute(f"SELECT code FROM permissions WHERE id IN ({placeholders})", ids)
    rows = cur.fetchall(); con.close()
    return [dict(row)["code"] if db.is_postgres else row["code"] for row in rows]


def has_permission(code):
    permissions = session.get("permissions", [])
    return "*" in permissions or code in permissions


def require_permission(code):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                abort(401)
            if not has_permission(code):
                abort(403)
            return func(*args, **kwargs)
        return wrapped
    return decorator


def require_login(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            abort(401)
        return func(*args, **kwargs)
    return wrapped
