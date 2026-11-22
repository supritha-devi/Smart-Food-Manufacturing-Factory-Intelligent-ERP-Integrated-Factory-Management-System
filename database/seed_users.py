import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from werkzeug.security import generate_password_hash
from app.database import Database, init_schema


ROLE_PERMISSIONS = {
    "OWNER": ["*"],
    "FACTORY ADMIN": [
        "customers:VIEW", "customers:CREATE", "customers:EDIT", "orders:VIEW", "orders:CREATE", "orders:APPROVE",
        "invoices:VIEW", "invoices:CREATE", "dispatch:VIEW", "dispatch:MANAGE", "payments:VIEW", "payments:CREATE",
        "suppliers:VIEW", "suppliers:CREATE", "suppliers:EDIT", "purchases:VIEW", "purchases:CREATE",
        "inventory:VIEW", "reports:VIEW", "employees:VIEW"
    ],
    "PRODUCTION SUPERVISOR": [
        "production:VIEW", "production:CREATE", "production:EDIT", "production:REPORT", "inventory:VIEW", "reports:VIEW"
    ],
    "SALESMAN": [
        "customers:VIEW_ASSIGNED", "orders:VIEW_OWN", "orders:CREATE", "products:VIEW", "inventory:VIEW_AVAILABILITY"
    ],
    "ACCOUNTANT / AUDITOR": [
        "sales:VIEW", "purchases:VIEW", "gst:VIEW", "invoices:VIEW", "payments:VIEW", "costing:VIEW",
        "inventory:VIEW", "reports:VIEW", "reports:EXPORT", "audit:VIEW", "outstanding:VIEW"
    ],
}

DEMO_USERS = [
    ("EMP-OWNER-001", "Owner", "owner@smartfactory.com", "owner", "Owner@123", "OWNER"),
    ("EMP-ADMIN-001", "Factory Admin", "admin@smartfactory.com", "admin", "Admin@123", "FACTORY ADMIN"),
    ("EMP-SUP-001", "Production Supervisor", "supervisor@smartfactory.com", "supervisor", "Supervisor@123", "PRODUCTION SUPERVISOR"),
    ("EMP-SALES-001", "Salesman A", "sales1@smartfactory.com", "sales1", "Sales@123", "SALESMAN"),
    ("EMP-SALES-002", "Salesman B", "sales2@smartfactory.com", "sales2", "Sales@456", "SALESMAN"),
    ("EMP-AUD-001", "Accountant Auditor", "auditor@smartfactory.com", "auditor", "Auditor@123", "ACCOUNTANT / AUDITOR"),
]


def seed():
    db = Database()
    init_schema(db)
    con = db.connect()
    p = db.placeholder()
    try:
        cur = con.cursor()

        for role_name, permission_codes in ROLE_PERMISSIONS.items():
            cur.execute(f"INSERT INTO roles (name, description) VALUES ({p}, {p}) ON CONFLICT (name) DO NOTHING", (role_name, role_name.title())) if db.is_postgres else cur.execute(f"INSERT OR IGNORE INTO roles (name, description) VALUES ({p}, {p})", (role_name, role_name.title()))

            cur.execute(f"SELECT id FROM roles WHERE name={p}", (role_name,))
            role = cur.fetchone()
            role_id = role["id"] if db.is_postgres else role[0]

            if "*" in permission_codes:
                continue
            for code in permission_codes:
                module, action = code.split(":", 1)
                values = (code, module, action, code)
                cur.execute(
                    f"INSERT INTO permissions (code, module, action, description) VALUES ({p}, {p}, {p}, {p}) ON CONFLICT (code) DO NOTHING"
                    if db.is_postgres else
                    f"INSERT OR IGNORE INTO permissions (code, module, action, description) VALUES ({p}, {p}, {p}, {p})",
                    values,
                )
                cur.execute(f"SELECT id FROM permissions WHERE code={p}", (code,))
                permission = cur.fetchone()
                permission_id = permission["id"] if db.is_postgres else permission[0]
                cur.execute(
                    f"INSERT INTO role_permissions (role_id, permission_id) VALUES ({p}, {p}) ON CONFLICT (role_id, permission_id) DO NOTHING"
                    if db.is_postgres else
                    f"INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES ({p}, {p})",
                    (role_id, permission_id),
                )

        for employee_id, name, email, username, password, role_name in DEMO_USERS:
            password_hash = generate_password_hash(password)
            cur.execute(
                f"INSERT INTO users (employee_id, name, email, username, password_hash) VALUES ({p},{p},{p},{p},{p}) ON CONFLICT (email) DO NOTHING"
                if db.is_postgres else
                f"INSERT OR IGNORE INTO users (employee_id, name, email, username, password_hash) VALUES ({p},{p},{p},{p},{p})",
                (employee_id, name, email, username, password_hash),
            )
            cur.execute(f"SELECT id FROM users WHERE email={p}", (email,))
            user = cur.fetchone()
            user_id = user["id"] if db.is_postgres else user[0]

            cur.execute(f"SELECT id FROM roles WHERE name={p}", (role_name,))
            role = cur.fetchone()
            role_id = role["id"] if db.is_postgres else role[0]
            cur.execute(
                f"INSERT INTO user_roles (user_id, role_id, is_primary) VALUES ({p},{p},{p}) ON CONFLICT (user_id, role_id) DO NOTHING"
                if db.is_postgres else
                f"INSERT OR IGNORE INTO user_roles (user_id, role_id, is_primary) VALUES ({p},{p},{p})",
                (user_id, role_id, True),
            )
            cur.execute(
                f"INSERT INTO employee_details (user_id, job_title, department) VALUES ({p},{p},{p}) ON CONFLICT (user_id) DO NOTHING"
                if db.is_postgres else
                f"INSERT OR IGNORE INTO employee_details (user_id, job_title, department) VALUES ({p},{p},{p})",
                (user_id, name, role_name),
            )

        con.commit()
        print("Database initialized and demo accounts are ready.")

        con.close()
        from database.seed_factory import seed as seed_factory
        seed_factory()
    finally:
        con.close()


if __name__ == "__main__":
    seed()
