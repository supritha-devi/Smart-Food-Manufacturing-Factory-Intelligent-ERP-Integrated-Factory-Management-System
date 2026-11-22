from flask import current_app, request, session


def add_audit(action, module, record_id=None, previous_value=None, new_value=None):
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute(
        f"INSERT INTO audit_logs (user_id, user_email, effective_context, action, module, record_id, previous_value, new_value, ip_address) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            session.get("user_id"),
            session.get("email"),
            ", ".join(session.get("roles", [])),
            action,
            module,
            str(record_id) if record_id is not None else None,
            previous_value,
            new_value,
            request.remote_addr if request else None,
        ),
    )
    con.commit(); con.close()
