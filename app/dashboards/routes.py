from flask import Blueprint, render_template, session, redirect, url_for, current_app

from app.auth.permissions import require_login

dashboards_bp = Blueprint("dashboards", __name__, url_prefix="/dashboard")


@dashboards_bp.get("/")
@require_login
def dashboard():
    roles = session.get("roles", [])
    role = roles[0] if roles else ""
    if role == "OWNER":
        return redirect(url_for("dashboards.owner_dashboard"))
    return render_template("dashboards/dashboard.html", role=role)


def dashboard_counts():
    from app.modules.routes import count_table
    return {
        "products": count_table("products"), "departments": count_table("departments"),
        "batches": count_table("production_batches"), "stock": count_table("stock_items"),
        "orders": count_table("sales_orders"), "machines": count_table("machines"),
        "employees": count_table("employees"), "invoices": count_table("invoices"),
    }


def dashboard_operational_counts(db):
    con = db.connect(); cur = con.cursor(); p = db.placeholder()
    counts = {}
    queries = {
        "active_batches": "SELECT COUNT(*) AS c FROM production_batches WHERE batch_status='IN_PROGRESS'",
        "held_batches": "SELECT COUNT(*) AS c FROM production_batches WHERE batch_status='ON_HOLD'",
        "submitted_orders": "SELECT COUNT(*) AS c FROM sales_orders WHERE status='SUBMITTED'",
        "approved_orders": "SELECT COUNT(*) AS c FROM sales_orders WHERE status='APPROVED'",
        "pending_inspections": "SELECT COUNT(*) AS c FROM quality_inspections WHERE status='PENDING'",
        "open_complaints": "SELECT COUNT(*) AS c FROM quality_complaints WHERE status='OPEN'",
        "open_work_orders": "SELECT COUNT(*) AS c FROM maintenance_work_orders WHERE status='OPEN'",
        "pending_adjustments": "SELECT COUNT(*) AS c FROM stock_adjustments WHERE status='PENDING'",
        "pending_receipts": "SELECT COUNT(*) AS c FROM goods_receipts WHERE status='PENDING_QC'",
        "awaiting_dispatch": "SELECT COUNT(*) AS c FROM warehouse_dispatches WHERE status='AWAITING_PICKING'",
        "outstanding_invoices": "SELECT COUNT(*) AS c FROM invoices WHERE outstanding_paise>0",
    }
    for key, query in queries.items():
        cur.execute(query)
        row = cur.fetchone()
        counts[key] = dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COALESCE(SUM(outstanding_paise),0) AS total FROM invoices")
    row = cur.fetchone()
    counts["receivable"] = dict(row)["total"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM audit_logs")
    row = cur.fetchone()
    counts["audit_entries"] = dict(row)["c"] if db.is_postgres else row[0]
    con.close()
    return counts


@dashboards_bp.get("/owner")
@require_login
def owner_dashboard():
    if "OWNER" not in session.get("roles", []):
        return redirect(url_for("dashboards.dashboard"))
    db = current_app.extensions["database"]
    con = db.connect(); cur = con.cursor()
    cur.execute("SELECT status FROM factory_initialization ORDER BY id DESC LIMIT 1")
    row = cur.fetchone(); con.close()
    status = (dict(row)["status"] if db.is_postgres else row["status"]) if row else "NOT_STARTED"
    if status != "COMPLETED":
        return redirect(url_for("modules.initialization_wizard"))
    counts = dashboard_counts()
    operational = dashboard_operational_counts(db)
    return render_template("dashboards/owner.html", counts=counts, operational=operational)
