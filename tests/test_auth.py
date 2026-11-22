import os
import tempfile
import pytest

from app import create_app
from app.database import Database, init_schema
from database.seed_users import seed


@pytest.fixture()
def client(tmp_path, monkeypatch):
    os.environ["INSTANCE_DIR"] = str(tmp_path)
    app = create_app({"TESTING": True, "DATABASE_URL": None, "SECRET_KEY": "test-secret"})
    db = app.extensions["database"]
    init_schema(db)
    from database.seed_users import seed
    os.environ["INSTANCE_DIR"] = str(tmp_path)
    seed()
    with app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize("email,password,role", [
    ("owner@smartfactory.com", "Owner@123", "OWNER"),
    ("admin@smartfactory.com", "Admin@123", "FACTORY ADMIN"),
    ("supervisor@smartfactory.com", "Supervisor@123", "PRODUCTION SUPERVISOR"),
    ("sales1@smartfactory.com", "Sales@123", "SALESMAN"),
    ("sales2@smartfactory.com", "Sales@456", "SALESMAN"),
    ("auditor@smartfactory.com", "Auditor@123", "ACCOUNTANT / AUDITOR"),
])
def test_demo_accounts_login(client, email, password, role):
    response = client.post("/login", data={"identifier": email, "password": password, "csrf_token": client.get("/").request.csrf_token if False else ""}, follow_redirects=False)
    # Obtain CSRF token from the login page session rather than submitting it manually.
    client.get("/login")
    client.get("/users/")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post("/login", data={"identifier": email, "password": password, "csrf_token": csrf}, follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/dashboard/")


def test_inactive_user_cannot_login(client):
    db = Database(); con = db.connect(); cur = con.cursor(); p=db.placeholder()
    cur.execute(f"UPDATE users SET is_active=0 WHERE email={p}", ("owner@smartfactory.com",)); con.commit(); con.close()
    client.get("/login")
    with client.session_transaction() as sess: csrf=sess["csrf_token"]
    response=client.post("/login",data={"identifier":"owner@smartfactory.com","password":"Owner@123","csrf_token":csrf},follow_redirects=True)
    assert b"Invalid email/username or password" in response.data


def test_owner_user_management_access(client):
    client.get("/login")
    with client.session_transaction() as sess: csrf=sess["csrf_token"]
    client.post("/login",data={"identifier":"owner@smartfactory.com","password":"Owner@123","csrf_token":csrf})
    assert client.get("/users/").status_code == 200


def test_module_dashboards_require_login(client):
    assert client.get("/production-config").status_code in (302, 401)


def test_owner_factory_layout(client):
    client.get("/login")
    with client.session_transaction() as sess: csrf=sess["csrf_token"]
    client.post("/login",data={"identifier":"owner@smartfactory.com","password":"Owner@123","csrf_token":csrf})
    assert client.get("/factory/layout").status_code == 200


def test_owner_can_create_department(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/factory/departments/new")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/factory/departments/new",
        data={
            "code": "QC-TEST",
            "name": "Test Quality Department",
            "department_type": "QUALITY_CONTROL",
            "status": "ACTIVE",
            "daily_target_batches": "0",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_initialization_wizard(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/initialization/wizard")
    assert response.status_code == 200
    assert b"Factory Initialization" in response.data


def test_owner_can_save_initialization_progress(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/initialization/wizard")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/initialization/save",
        data={
            "factory_name": "Smart Food Manufacturing Factory",
            "business_type": "South Indian Snacks Manufacturing",
            "progress": "9",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_production_configuration(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/production-config/workspace")
    assert response.status_code == 200
    assert b"Production Configuration" in response.data


def test_owner_can_create_configured_product(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/production-config/products/new")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/production-config/products/new",
        data={
            "code": "TEST-SNACK",
            "name": "Test Snack",
            "category": "Snack",
            "packet_weight": "200",
            "unit": "gram",
            "selling_unit": "packet",
            "standard_batch_output": "200",
            "daily_target_batches": "2",
            "selling_price_paise": "5000",
            "gst_percent": "5",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_machine_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/machines/workspace")
    assert response.status_code == 200
    assert b"Machine Management" in response.data


def test_owner_can_register_machine(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/machines/new")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/machines/new",
        data={
            "code": "TEST-MACHINE-001",
            "name": "Test Production Machine",
            "machine_type": "Testing",
            "capacity_per_hour": "100",
            "hourly_cost_paise": "500",
            "status": "OPERATIONAL",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_production_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/production/workspace")
    assert response.status_code == 200
    assert b"Production Planning &amp; Batches" in response.data or b"Production Planning & Batches" in response.data


def test_owner_can_create_production_plan(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/production/workspace")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    db = Database()
    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM products WHERE code='PRD001'")
    product_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM departments WHERE code='PROD001'")
    department_id = cur.fetchone()[0]
    con.close()
    response = client.post(
        "/production/plans",
        data={
            "plan_date": "2026-11-22",
            "product_id": str(product_id),
            "department_id": str(department_id),
            "planned_quantity": "200",
            "planned_batches": "1",
            "priority": "1",
            "notes": "Test plan",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_salesman_cannot_access_users(client):
    client.get("/login")
    with client.session_transaction() as sess: csrf=sess["csrf_token"]
    client.post("/login",data={"identifier":"sales1@smartfactory.com","password":"Sales@123","csrf_token":csrf})
    assert client.get("/users/").status_code == 403


def test_owner_can_edit_employee_account(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})

    db = Database()
    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", ("sales1@smartfactory.com",))
    user_id = cur.fetchone()["id"]
    cur.execute("SELECT id FROM roles WHERE name=?", ("SALESMAN",))
    role_id = cur.fetchone()["id"]
    con.close()

    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        f"/users/{user_id}/edit",
        data={
            "employee_id": "EMP-SALES-001",
            "name": "Salesman A Updated",
            "email": "sales1@smartfactory.com",
            "username": "sales1",
            "phone": "9876543210",
            "role_id": str(role_id),
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Employee account updated successfully" in response.data


def test_owner_reset_password_requires_change_on_login(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/users/")

    db = Database()
    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", ("sales1@smartfactory.com",))
    user_id = cur.fetchone()["id"]
    con.close()

    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        f"/users/{user_id}/reset-password",
        data={"password": "Temporary123!", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/logout", data={"csrf_token": csrf}, follow_redirects=False)
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/login",
        data={"identifier": "sales1@smartfactory.com", "password": "Temporary123!", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.location.endswith("/change-password")


def test_owner_can_access_labour_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/labour/workforce")
    assert response.status_code == 200
    assert b"Labour &amp; Workforce" in response.data or b"Labour & Workforce" in response.data


def test_owner_can_create_employee_record(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/labour/employees/new")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/labour/employees/new",
        data={
            "employee_code": "WRK-TEST-001",
            "name": "Test Production Worker",
            "phone": "9876543210",
            "email": "worker.test@example.com",
            "employment_type": "PERMANENT",
            "designation": "Frying Operator",
            "status": "ACTIVE",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_purchasing_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/purchasing/workspace")
    assert response.status_code == 200
    assert b"Purchasing &amp; Procurement" in response.data or b"Purchasing & Procurement" in response.data


def test_owner_can_create_supplier(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/purchasing/suppliers/new")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/purchasing/suppliers/new",
        data={
            "code": "SUP-TEST-001",
            "name": "Test Supplier",
            "contact_person": "Supplier Contact",
            "phone": "9876543210",
            "email": "supplier@test.com",
            "gstin": "TESTGSTIN",
            "address": "Test address",
            "credit_days": "30",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_quality_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/quality/workspace")
    assert response.status_code == 200
    assert b"Quality Control" in response.data


def test_owner_can_record_quality_inspection(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/quality/workspace")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/quality/inspections",
        data={
            "inspection_type": "Finished Goods",
            "reference_type": "DEPARTMENT",
            "reference_id": "1",
            "result": "PASS",
            "notes": "Test quality inspection",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_maintenance_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/maintenance/workspace")
    assert response.status_code == 200
    assert b"Maintenance &amp; Work Orders" in response.data or b"Maintenance & Work Orders" in response.data


def test_owner_can_create_maintenance_work_order(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/maintenance/workspace")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/maintenance/work-orders",
        data={
            "work_order_type": "CORRECTIVE",
            "title": "Test machine inspection",
            "description": "Test maintenance description",
            "priority": "HIGH",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_inventory_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/inventory/workspace")
    assert response.status_code == 200
    assert b"Inventory &amp; Warehouse" in response.data or b"Inventory & Warehouse" in response.data


def test_owner_can_submit_stock_adjustment(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    db = Database()
    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM raw_materials LIMIT 1")
    material_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM warehouses LIMIT 1")
    warehouse_id = cur.fetchone()[0]
    con.close()
    client.get("/inventory/workspace")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/inventory/stock",
        data={
            "item_type": "RAW_MATERIAL",
            "item_id": str(material_id),
            "warehouse_id": str(warehouse_id),
            "quantity": "25",
            "reason": "Opening test adjustment",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_sales_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/sales/workspace")
    assert response.status_code == 200
    assert b"Sales &amp; GST Billing" in response.data or b"Sales & GST Billing" in response.data


def test_owner_can_create_customer(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/sales/customers/new")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/sales/customers/new",
        data={
            "code": "CUS-TEST-001",
            "name": "Test Retailer",
            "contact_person": "Test Contact",
            "phone": "9876543210",
            "email": "retailer@test.com",
            "gstin": "TEST-CUS-GSTIN",
            "address": "Test address",
            "credit_limit_paise": "100000",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_owner_can_access_finance_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/finance/workspace")
    assert response.status_code == 200
    assert b"Financial Management" in response.data


def test_accountant_can_view_finance_but_not_mutate(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "auditor@smartfactory.com", "password": "Auditor@123", "csrf_token": csrf})
    assert client.get("/finance/workspace").status_code == 200
    client.get("/finance/workspace")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/finance/accounts",
        data={"code": "TEST-ASSET", "name": "Test Asset", "account_type": "ASSET", "opening_balance_paise": "100", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_owner_can_access_dispatch_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/warehouse/workspace")
    assert response.status_code == 200
    assert b"Warehouse Dispatch" in response.data


def test_salesman_cannot_create_dispatch(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "sales1@smartfactory.com", "password": "Sales@123", "csrf_token": csrf})
    client.get("/warehouse/workspace")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/warehouse/dispatches",
        data={"invoice_id": "1", "warehouse_id": "1", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code in (403, 404)


def test_owner_can_access_reports_workspace(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/reports/workspace")
    assert response.status_code == 200
    assert b"Reports &amp; Audit Trail" in response.data or b"Reports & Audit Trail" in response.data


def test_accountant_can_export_audit_csv(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "auditor@smartfactory.com", "password": "Auditor@123", "csrf_token": csrf})
    response = client.get("/reports/export/audit.csv")
    assert response.status_code == 200
    assert response.content_type.startswith("text/csv")
    assert "attachment" in response.headers["Content-Disposition"]


def test_owner_can_access_voice_library(client):
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    response = client.get("/voice/library")
    assert response.status_code == 200
    assert b"Voice Records Library" in response.data


def test_owner_can_upload_voice_recording(client):
    import io
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/voice/record")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        "/voice/record",
        data={
            "title": "Test factory update",
            "language": "TAMIL_ENGLISH_MIXED",
            "module_name": "Production",
            "transcript": "Murukku production 200 packets",
            "duration_seconds": "12",
            "audio": (io.BytesIO(b"RIFFtestaudio"), "test.wav"),
            "csrf_token": csrf,
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_confirmed_breakdown_marks_exact_machine_down(client):
    import io
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/voice/record")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post(
        "/voice/record",
        data={
            "title": "Machine breakdown",
            "language": "ENGLISH",
            "module_name": "Machines",
            "transcript": "Murukku Extruder machine breakdown",
            "duration_seconds": "8",
            "audio": (io.BytesIO(b"RIFFmachine"), "machine.wav"),
            "csrf_token": csrf,
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    db = Database()
    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM voice_recordings ORDER BY id DESC LIMIT 1")
    recording_id = cur.fetchone()[0]
    con.close()
    client.get(f"/voice/{recording_id}")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        f"/voice/{recording_id}/confirm",
        data={"csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 302
    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT status FROM machines WHERE name='Murukku Extruder'")
    status = cur.fetchone()[0]
    con.close()
    assert status == "UNDER_MAINTENANCE"


def test_voice_record_link_rejects_missing_record(client):
    import io
    client.get("/login")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post("/login", data={"identifier": "owner@smartfactory.com", "password": "Owner@123", "csrf_token": csrf})
    client.get("/voice/record")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    client.post(
        "/voice/record",
        data={
            "title": "Linked voice note",
            "language": "ENGLISH",
            "module_name": "Machines",
            "transcript": "Machine inspection",
            "duration_seconds": "5",
            "audio": (io.BytesIO(b"RIFFlink"), "link.wav"),
            "csrf_token": csrf,
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    db = Database()
    con = db.connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM voice_recordings ORDER BY id DESC LIMIT 1")
    recording_id = cur.fetchone()[0]
    con.close()
    client.get(f"/voice/{recording_id}")
    with client.session_transaction() as sess:
        csrf = sess["csrf_token"]
    response = client.post(
        f"/voice/{recording_id}/link",
        data={
            "target_module": "Machines",
            "target_record_type": "Machine",
            "target_record_id": "999999",
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert b"The related ERP record does not exist" in response.data
