from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from app.auth.permissions import require_login
from app.modules import modules_bp
from app.time_utils import now, now_iso, working_minutes, overtime_minutes, format_datetime

MODULES = {
    "layout": ("Factory Layout", "factory_layout", "Module 2"),
    "labour": ("Labour & Workforce", "labour", "Module 3"),
    "production-config": ("Production Configuration", "production_config", "Module 4"),
    "machines": ("Machine Management", "machines", "Module 5"),
    "production": ("Production Workflow", "production", "Module 6"),
    "initialization": ("Factory Initialization", "initialization", "Module 7"),
    "purchasing": ("Purchasing", "purchasing", "Module 8"),
    "quality": ("Quality Control", "quality", "Module 9"),
    "maintenance": ("Maintenance", "maintenance", "Module 10"),
    "inventory": ("Inventory & Warehouse", "inventory", "Module 11"),
    "sales": ("Sales & GST Billing", "sales", "Module 12"),
    "finance": ("Financial Management", "finance", "Module 13"),
    "warehouse": ("Dispatch & Logistics", "warehouse", "Module 14"),
    "reports": ("Reports & Audit", "reports", "Module 15"),
}

TABLES = {
    "departments": "departments",
    "products": "products",
    "machines": "machines",
    "employees": "employees",
    "shifts": "shifts",
    "suppliers": "suppliers",
    "customers": "customers",
    "raw-materials": "raw_materials",
    "batches": "production_batches",
    "plans": "production_plans",
}


def db_rows(table, limit=50):
    db = current_app.extensions["database"]
    con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(f"SELECT * FROM {table} LIMIT {p}", (limit,))
    rows = cur.fetchall(); con.close()
    return [dict(row) if db.is_postgres else dict(row) for row in rows]


def count_table(table):
    db = current_app.extensions["database"]
    con = db.connect(); cur = con.cursor()
    cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
    row = cur.fetchone(); con.close()
    return dict(row)["c"] if db.is_postgres else row[0]


@modules_bp.get("/factory/layout")
@require_login
def factory_layout():
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(
        "SELECT d.*, p.area_x,p.area_y,p.area_width,p.area_height,p.display_order "
        "FROM departments d LEFT JOIN factory_layout_positions p ON p.department_id=d.id "
        "ORDER BY p.display_order,d.name"
    )
    departments = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]

    if "OWNER" not in session.get("roles", []):
        if "PRODUCTION SUPERVISOR" in session.get("roles", []):
            cur.execute(
                f"SELECT department_id FROM department_assignments WHERE user_id={p}",
                (session["user_id"],),
            )
            assigned = {row["department_id"] if db.is_postgres else row[0] for row in cur.fetchall()}
            departments = [department for department in departments if department["id"] in assigned]
    con.close()
    summary = {
        "total": len(departments),
        "production": sum(1 for d in departments if d["department_type"] == "PRODUCTION"),
        "warehouses": sum(1 for d in departments if d["department_type"] == "WAREHOUSE"),
        "active": sum(1 for d in departments if d["status"] == "ACTIVE"),
        "inactive": sum(1 for d in departments if d["status"] == "INACTIVE"),
    }
    return render_template("modules/factory_layout.html", departments=departments, summary=summary)


@modules_bp.get("/factory/departments/<int:department_id>")
@require_login
def department_detail(department_id):
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(f"SELECT * FROM departments WHERE id={p}", (department_id,))
    row = cur.fetchone()
    if not row:
        con.close(); abort(404)
    department = dict(row) if db.is_postgres else dict(row)
    cur.execute(f"SELECT MAX(daily_target_batches) AS target FROM products WHERE department_id={p}", (department_id,))
    target_row = cur.fetchone()
    department["daily_target_batches"] = (dict(target_row)["target"] if db.is_postgres else target_row[0]) or 0

    if "OWNER" not in session.get("roles", []) and "PRODUCTION SUPERVISOR" in session.get("roles", []):
        cur.execute(f"SELECT 1 FROM department_assignments WHERE department_id={p} AND user_id={p}", (department_id, session["user_id"]))
        if not cur.fetchone():
            con.close(); abort(403)

    cur.execute(f"SELECT * FROM products WHERE department_id={p}", (department_id,))
    products = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(f"SELECT COUNT(*) AS c FROM machines WHERE department_id={p}", (department_id,))
    machine_row = cur.fetchone(); machine_count = dict(machine_row)["c"] if db.is_postgres else machine_row[0]
    cur.execute(f"SELECT COUNT(*) AS c FROM production_batches WHERE department_id={p}", (department_id,))
    batch_row = cur.fetchone(); batch_count = dict(batch_row)["c"] if db.is_postgres else batch_row[0]
    cur.execute(f"SELECT COUNT(*) AS c FROM production_section_assignments WHERE section_name={p}", (department["name"],))
    worker_row = cur.fetchone(); worker_count = dict(worker_row)["c"] if db.is_postgres else worker_row[0]
    cur.execute(f"SELECT COUNT(*) AS c FROM quality_inspections WHERE reference_type='DEPARTMENT' AND reference_id={p}", (str(department_id),))
    inspection_row = cur.fetchone(); inspection_count = dict(inspection_row)["c"] if db.is_postgres else inspection_row[0]
    cur.execute(f"SELECT COUNT(*) AS c FROM warehouse_dispatches", ())
    dispatch_row = cur.fetchone(); dispatch_count = dict(dispatch_row)["c"] if db.is_postgres else dispatch_row[0]

    target = products[0].get("daily_target_batches", 0) if products else 0
    con.close()
    data = {
        "department": department, "products": products, "target": target,
        "machine_count": machine_count, "batch_count": batch_count,
        "worker_count": worker_count, "inspection_count": inspection_count,
        "dispatch_count": dispatch_count,
    }
    return render_template("modules/department_detail.html", **data)


@modules_bp.route("/factory/departments/<int:department_id>/edit", methods=["GET", "POST"])
@require_login
def department_edit(department_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(f"SELECT * FROM departments WHERE id={p}", (department_id,))
    row = cur.fetchone()
    if not row:
        con.close(); abort(404)
    department = dict(row) if db.is_postgres else dict(row)
    cur.execute(f"SELECT MAX(daily_target_batches) AS target FROM products WHERE department_id={p}", (department_id,))
    target_row = cur.fetchone()
    department["daily_target_batches"] = (dict(target_row)["target"] if db.is_postgres else target_row[0]) or 0
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        status = request.form.get("status", "ACTIVE").strip()
        target = request.form.get("daily_target_batches", "0")
        if not name or status not in {"ACTIVE","INACTIVE","OPERATIONAL","UNDER_MAINTENANCE","TEMPORARILY_CLOSED"}:
            con.close(); flash("Enter a department name and valid status.","danger"); return redirect(url_for("modules.department_edit", department_id=department_id))
        try:
            target_value = int(target)
            if target_value < 0:
                raise ValueError
        except ValueError:
            con.close(); flash("Daily target must be zero or a positive number.","danger"); return redirect(url_for("modules.department_edit", department_id=department_id))
        cur.execute(f"UPDATE departments SET name={p},status={p} WHERE id={p}", (name,status,department_id))
        cur.execute(f"UPDATE products SET daily_target_batches={p} WHERE department_id={p}", (target_value,department_id))
        cur.execute(f"UPDATE production_sections SET daily_target_batches={p},current_status={p} WHERE department_id={p}", (target_value,status,department_id))
        cur.execute(f"INSERT INTO department_status_history(department_id,previous_status,new_status,changed_by) VALUES({p},{p},{p},{p})", (department_id,department.get("status"),status,session["user_id"]))
        cur.execute(f"INSERT INTO configuration_history(version,action,changed_by,record_summary) VALUES('1.0','UPDATE_DEPARTMENT',{p},{p})", (session["user_id"], f"{name} status={status} target={target_value}"))
        con.commit(); con.close()
        add_audit = __import__("app.audit.service", fromlist=["add_audit"]).add_audit
        add_audit("UPDATE","Factory Layout",str(department_id),previous_value=department.get("status"),new_value=status)
        flash("Department configuration updated.","success")
        return redirect(url_for("modules.department_detail", department_id=department_id))
    cur.execute("SELECT id,name FROM products ORDER BY name")
    products = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/department_edit.html", department=department, products=products)


@modules_bp.route("/factory/departments/new", methods=["GET", "POST"])
@require_login
def department_create():
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip()
        department_type = request.form.get("department_type", "PRODUCTION").strip()
        status = request.form.get("status", "ACTIVE").strip()
        target = request.form.get("daily_target_batches", "0")
        if not code or not name or department_type not in {"PRODUCTION","WAREHOUSE","QUALITY_CONTROL","DISPATCH","ADMINISTRATION"}:
            con.close(); flash("Complete the department code, name and type.","danger"); return redirect(url_for("modules.department_create"))
        try:
            target_value = int(target)
            if target_value < 0:
                raise ValueError
        except ValueError:
            con.close(); flash("Daily target must be zero or a positive number.","danger"); return redirect(url_for("modules.department_create"))
        try:
            cur.execute(f"INSERT INTO departments(code,name,department_type,status) VALUES({p},{p},{p},{p})", (code,name,department_type,status))
            if db.is_postgres:
                cur.execute("SELECT id FROM departments WHERE code=%s", (code,))
                department_id = cur.fetchone()["id"]
            else:
                department_id = cur.lastrowid
            grid_column = (department_id - 1) % 4
            grid_row = (department_id - 1) // 4
            area_x = 55 + (grid_column * 250)
            area_y = 55 + (grid_row * 160)
            cur.execute(f"INSERT INTO factory_layout_positions(department_id,area_x,area_y,area_width,area_height,display_order) VALUES({p},{p},{p},{p},{p},{p})", (department_id,area_x,area_y,200,150,department_id))
            cur.execute(f"INSERT INTO department_status_history(department_id,previous_status,new_status,changed_by) VALUES({p},NULL,{p},{p})", (department_id,status,session["user_id"]))
            cur.execute(f"INSERT INTO configuration_history(version,action,changed_by,record_summary) VALUES('1.0','CREATE_DEPARTMENT',{p},{p})", (session["user_id"], f"{name} ({code})"))
            con.commit()
            __import__("app.audit.service", fromlist=["add_audit"]).add_audit("CREATE","Factory Layout",str(department_id),new_value=name)
            con.close()
            flash("Department added successfully.","success")
            return redirect(url_for("modules.department_detail", department_id=department_id))
        except Exception:
            con.rollback(); con.close(); flash("Department code already exists or the department could not be created.","danger")
            return redirect(url_for("modules.department_create"))
    con.close()
    return render_template("modules/department_edit.html", department=None, products=[], creating=True)


def labour_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "PRODUCTION SUPERVISOR"})


def labour_scope(con, cur, db, p):
    if "OWNER" in session.get("roles", []) or "FACTORY ADMIN" in session.get("roles", []):
        return None
    cur.execute(
        f"SELECT department_id FROM department_assignments WHERE user_id={p}",
        (session["user_id"],),
    )
    rows = cur.fetchall()
    ids = [dict(row)["department_id"] if db.is_postgres else row[0] for row in rows]
    return ids


@modules_bp.get("/labour/workforce")
@require_login
def labour_dashboard():
    if not labour_allowed():
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    ids = labour_scope(con, cur, db, p)
    if ids is None:
        cur.execute("SELECT e.*,d.name AS department_name,s.name AS shift_name FROM employees e LEFT JOIN departments d ON d.id=e.department_id LEFT JOIN shifts s ON s.id=e.shift_id ORDER BY e.name")
    elif ids:
        placeholders = ",".join([p] * len(ids))
        cur.execute(f"SELECT e.*,d.name AS department_name,s.name AS shift_name FROM employees e LEFT JOIN departments d ON d.id=e.department_id LEFT JOIN shifts s ON s.id=e.shift_id WHERE e.department_id IN ({placeholders}) ORDER BY e.name", ids)
    else:
        employees = []
    if ids is None or ids:
        employees = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM employees")
    total_row = cur.fetchone(); total = dict(total_row)["c"] if db.is_postgres else total_row[0]
    cur.execute("SELECT COUNT(*) AS c FROM employees WHERE status='ACTIVE'")
    active_row = cur.fetchone(); active = dict(active_row)["c"] if db.is_postgres else active_row[0]
    cur.execute("SELECT COUNT(*) AS c FROM attendance WHERE attendance_date=CURRENT_DATE")
    attendance_row = cur.fetchone(); attendance_today = dict(attendance_row)["c"] if db.is_postgres else attendance_row[0]
    cur.execute("SELECT COUNT(*) AS c FROM employee_leave WHERE status='PENDING'")
    leave_row = cur.fetchone(); pending_leave = dict(leave_row)["c"] if db.is_postgres else leave_row[0]
    cur.execute("SELECT id,name FROM departments ORDER BY name")
    departments = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name,start_time,end_time FROM shifts WHERE is_active=1 ORDER BY start_time")
    shifts = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/labour_dashboard.html", employees=employees, departments=departments, shifts=shifts,
                           total=total, active=active, attendance_today=attendance_today, pending_leave=pending_leave)


@modules_bp.route("/labour/employees/new", methods=["GET", "POST"])
@require_login
def employee_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    if request.method == "POST":
        code = request.form.get("employee_code", "").strip().upper()
        name = request.form.get("name", "").strip()
        department_id = request.form.get("department_id") or None
        designation = request.form.get("designation", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        employment_type = request.form.get("employment_type", "PERMANENT")
        shift_id = request.form.get("shift_id") or None
        status = request.form.get("status", "ACTIVE")
        if not code or not name:
            con.close(); flash("Employee code and name are required.","danger"); return redirect(url_for("modules.employee_create"))
        try:
            cur.execute(
                f"INSERT INTO employees("
                f"employee_code,name,gender,date_of_birth,nationality,state,district,caste,religion,blood_group,"
                f"phone,email,address,permanent_address,aadhaar_number,pan_number,voter_id_number,ration_card_number,"
                f"id_card_type,id_card_number,emergency_contact_name,emergency_contact,"
                f"employment_type,department_id,designation,shift_id,status,date_joining"
                f") VALUES("
                + ",".join([p] * 27) + ",CURRENT_TIMESTAMP)",
                (
                    code,name,request.form.get("gender"),request.form.get("date_of_birth"),
                    request.form.get("nationality","Indian"),request.form.get("state"),request.form.get("district"),
                    request.form.get("caste"),request.form.get("religion"),request.form.get("blood_group"),
                    phone,email,request.form.get("address"),request.form.get("permanent_address"),
                    request.form.get("aadhaar_number"),request.form.get("pan_number"),
                    request.form.get("voter_id_number"),request.form.get("ration_card_number"),
                    request.form.get("id_card_type"),request.form.get("id_card_number"),
                    request.form.get("emergency_contact_name"),request.form.get("emergency_contact"),
                    employment_type,department_id,designation,shift_id,status,
                ),
            )
            if db.is_postgres:
                cur.execute("SELECT id FROM employees WHERE employee_code=%s",(code,))
                employee_id=cur.fetchone()["id"]
            else:
                employee_id=cur.lastrowid
            con.commit()
            __import__("app.audit.service", fromlist=["add_audit"]).add_audit("CREATE","Labour & Workforce",str(employee_id),new_value=name)
            con.close(); flash("Employee record created.","success")
            return redirect(url_for("modules.labour_dashboard"))
        except Exception:
            con.rollback(); con.close(); flash("Employee code or email already exists.","danger")
            return redirect(url_for("modules.employee_create"))
    cur.execute("SELECT id,name FROM departments ORDER BY name")
    departments = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name FROM shifts WHERE is_active=1 ORDER BY name")
    shifts = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/employee_form.html", employee=None, departments=departments, shifts=shifts)


@modules_bp.route("/labour/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@require_login
def employee_edit(employee_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(f"SELECT * FROM employees WHERE id={p}", (employee_id,))
    row = cur.fetchone()
    if not row:
        con.close(); abort(404)
    employee = dict(row) if db.is_postgres else dict(row)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        department_id = request.form.get("department_id") or None
        designation = request.form.get("designation", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        shift_id = request.form.get("shift_id") or None
        status = request.form.get("status", "ACTIVE")
        employment_type = request.form.get("employment_type", "PERMANENT")
        if not name:
            con.close(); flash("Employee name is required.","danger"); return redirect(url_for("modules.employee_edit", employee_id=employee_id))
        try:
            cur.execute(
                f"UPDATE employees SET name={p},gender={p},date_of_birth={p},nationality={p},state={p},district={p},"
                f"caste={p},religion={p},blood_group={p},phone={p},email={p},address={p},permanent_address={p},"
                f"aadhaar_number={p},pan_number={p},voter_id_number={p},ration_card_number={p},id_card_type={p},"
                f"id_card_number={p},emergency_contact_name={p},emergency_contact={p},employment_type={p},"
                f"department_id={p},designation={p},shift_id={p},status={p} WHERE id={p}",
                (
                    name,request.form.get("gender"),request.form.get("date_of_birth"),
                    request.form.get("nationality","Indian"),request.form.get("state"),request.form.get("district"),
                    request.form.get("caste"),request.form.get("religion"),request.form.get("blood_group"),
                    phone,email,request.form.get("address"),request.form.get("permanent_address"),
                    request.form.get("aadhaar_number"),request.form.get("pan_number"),
                    request.form.get("voter_id_number"),request.form.get("ration_card_number"),
                    request.form.get("id_card_type"),request.form.get("id_card_number"),
                    request.form.get("emergency_contact_name"),request.form.get("emergency_contact"),
                    employment_type,department_id,designation,shift_id,status,employee_id,
                ),
            )
            con.commit()
            __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Labour & Workforce",str(employee_id),previous_value=employee["name"],new_value=name)
            con.close(); flash("Employee record updated.","success")
            return redirect(url_for("modules.labour_dashboard"))
        except Exception:
            con.rollback(); con.close(); flash("Email already exists for another employee.","danger")
            return redirect(url_for("modules.employee_edit", employee_id=employee_id))
    cur.execute("SELECT id,name FROM departments ORDER BY name")
    departments = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name FROM shifts WHERE is_active=1 ORDER BY name")
    shifts = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/employee_form.html", employee=employee, departments=departments, shifts=shifts)


@modules_bp.get("/labour/employees/<int:employee_id>")
@require_login
def employee_profile(employee_id):
    if not labour_allowed():
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(
        "SELECT e.*,d.name AS department_name,s.name AS shift_name "
        "FROM employees e LEFT JOIN departments d ON d.id=e.department_id "
        "LEFT JOIN shifts s ON s.id=e.shift_id WHERE e.id=%s" if db.is_postgres
        else "SELECT e.*,d.name AS department_name,s.name AS shift_name "
        "FROM employees e LEFT JOIN departments d ON d.id=e.department_id "
        "LEFT JOIN shifts s ON s.id=e.shift_id WHERE e.id=?",
        (employee_id,),
    )
    row = cur.fetchone()
    if not row:
        con.close(); abort(404)
    employee = dict(row) if db.is_postgres else dict(row)
    con.close()
    return render_template("modules/employee_profile.html", employee=employee)


@modules_bp.post("/labour/attendance")
@require_login
def labour_attendance():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []) and "PRODUCTION SUPERVISOR" not in session.get("roles", []):
        abort(403)
    employee_id = request.form.get("employee_id")
    attendance_date = request.form.get("attendance_date", "")
    status = request.form.get("status", "")
    shift_id = request.form.get("shift_id") or None
    check_in = request.form.get("check_in") or None
    check_out = request.form.get("check_out") or None
    if not employee_id or not attendance_date or status not in {"PRESENT","ABSENT","LEAVE","HALF_DAY"}:
        flash("Select an employee, date and valid attendance status.","danger")
        return redirect(url_for("modules.labour_dashboard"))
    break_minutes = 30
    standard_minutes = 480
    total_minutes = 0
    overtime = 0
    if check_in and check_out:
        check_in_datetime = f"{attendance_date}T{check_in}:00"
        check_out_datetime = f"{attendance_date}T{check_out}:00"
        total_minutes = working_minutes(check_in_datetime, check_out_datetime, break_minutes)
        overtime = overtime_minutes(check_in_datetime, check_out_datetime, standard_minutes, break_minutes)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(f"DELETE FROM attendance WHERE employee_id={p} AND attendance_date={p}", (employee_id,attendance_date))
    cur.execute(
        f"INSERT INTO attendance(employee_id,attendance_date,status,shift_id,check_in,check_out,"
        f"total_working_minutes,overtime_minutes,break_minutes,standard_minutes) "
        f"VALUES({p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (employee_id,attendance_date,status,shift_id,check_in,check_out,total_minutes,overtime,break_minutes,standard_minutes),
    )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Labour & Workforce",str(employee_id),new_value=f"{attendance_date}: {status}")
    flash("Attendance recorded.","success")
    return redirect(url_for("modules.labour_dashboard"))


@modules_bp.post("/labour/leave")
@require_login
def labour_leave():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []) and "PRODUCTION SUPERVISOR" not in session.get("roles", []):
        abort(403)
    employee_id = request.form.get("employee_id")
    leave_type = request.form.get("leave_type", "").strip()
    from_date = request.form.get("from_date", "")
    to_date = request.form.get("to_date", "")
    reason = request.form.get("reason", "").strip()
    if not employee_id or not leave_type or not from_date or not to_date or to_date < from_date:
        flash("Enter valid leave dates and a leave type.","danger")
        return redirect(url_for("modules.labour_dashboard"))
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(
        f"INSERT INTO employee_leave(employee_id,leave_type,from_date,to_date,status,reason) VALUES({p},{p},{p},{p},'PENDING',{p})",
        (employee_id,leave_type,from_date,to_date,reason),
    )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("CREATE","Labour & Workforce",str(employee_id),new_value=f"{leave_type} leave {from_date} to {to_date}")
    flash("Leave request submitted.","success")
    return redirect(url_for("modules.labour_dashboard"))


def production_config_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "PRODUCTION SUPERVISOR"})


@modules_bp.get("/production-config/workspace")
@require_login
def production_config_dashboard():
    if not production_config_allowed():
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute("SELECT COUNT(*) AS c FROM departments WHERE department_type='PRODUCTION'")
    row = cur.fetchone(); sections = dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM products")
    row = cur.fetchone(); products_count = dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM recipes")
    row = cur.fetchone(); recipes_count = dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM machines")
    row = cur.fetchone(); machines_count = dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM employees")
    row = cur.fetchone(); workers_count = dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM shifts WHERE is_active=1")
    row = cur.fetchone(); shifts_count = dict(row)["c"] if db.is_postgres else row[0]
    cur.execute(
        "SELECT pr.id,pr.code,pr.name,pr.standard_batch_output,pr.daily_target_batches,"
        "d.name AS department_name,pr.is_active "
        "FROM products pr LEFT JOIN departments d ON d.id=pr.department_id ORDER BY pr.name"
    )
    products = [dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    warnings = []
    for product in products:
        cur.execute(f"SELECT COUNT(*) AS c FROM recipes WHERE product_id={p}", (product["id"],))
        row = cur.fetchone(); recipe_count = dict(row)["c"] if db.is_postgres else row[0]
        cur.execute(f"SELECT COUNT(*) AS c FROM production_stages WHERE product_id={p}", (product["id"],))
        row = cur.fetchone(); stage_count = dict(row)["c"] if db.is_postgres else row[0]
        if recipe_count == 0:
            warnings.append(f"{product['name']}: no BOM configured")
        if stage_count == 0:
            warnings.append(f"{product['name']}: no production stages configured")
    con.close()
    return render_template("modules/production_config_dashboard.html",
                           sections=sections, products_count=products_count, recipes_count=recipes_count,
                           machines_count=machines_count, workers_count=workers_count, shifts_count=shifts_count,
                           products=products, warnings=warnings)


@modules_bp.route("/production-config/products/new", methods=["GET","POST"])
@require_login
def production_product_create():
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    if request.method == "POST":
        code = request.form.get("code","").strip().upper()
        name = request.form.get("name","").strip()
        category = request.form.get("category","Snack").strip()
        department_id = request.form.get("department_id") or None
        packet_weight = request.form.get("packet_weight","0")
        unit = request.form.get("unit","packet").strip()
        selling_unit = request.form.get("selling_unit","packet").strip()
        batch_output = request.form.get("standard_batch_output","0")
        target = request.form.get("daily_target_batches","0")
        price = request.form.get("selling_price_paise","0")
        gst = request.form.get("gst_percent","5")
        if not code or not name:
            con.close(); flash("Product code and name are required.","danger"); return redirect(url_for("modules.production_product_create"))
        try:
            packet_weight=float(packet_weight); batch_output=int(batch_output); target=int(target); price=int(price); gst=float(gst)
            if packet_weight < 0 or batch_output <= 0 or target < 0 or price < 0 or gst < 0:
                raise ValueError
        except ValueError:
            con.close(); flash("Use valid non-negative values and a positive batch output.","danger"); return redirect(url_for("modules.production_product_create"))
        try:
            cur.execute(
                f"INSERT INTO products(code,name,category,packet_weight,unit,selling_unit,department_id,standard_batch_output,daily_target_batches,selling_price_paise,gst_percent,is_active) "
                f"VALUES({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},1)",
                (code,name,category,packet_weight,unit,selling_unit,department_id,batch_output,target,price,gst),
            )
            con.commit()
            if db.is_postgres:
                cur.execute("SELECT id FROM products WHERE code=%s",(code,))
                product_id=cur.fetchone()["id"]
            else:
                product_id=cur.lastrowid
            __import__("app.audit.service", fromlist=["add_audit"]).add_audit("CREATE","Production Configuration",str(product_id),new_value=name)
            con.close(); flash("Product configuration created.","success")
            return redirect(url_for("modules.production_config_dashboard"))
        except Exception:
            con.rollback(); con.close(); flash("Product code already exists or configuration is invalid.","danger")
            return redirect(url_for("modules.production_product_create"))
    cur.execute("SELECT id,code,name FROM departments WHERE department_type='PRODUCTION' ORDER BY name")
    departments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/product_form.html", product=None, departments=departments)


@modules_bp.route("/production-config/products/<int:product_id>/edit", methods=["GET","POST"])
@require_login
def production_product_edit(product_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db = current_app.extensions["database"]; con = db.connect(); cur = con.cursor(); p = db.placeholder()
    cur.execute(f"SELECT * FROM products WHERE id={p}",(product_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    product=dict(row) if db.is_postgres else dict(row)
    if request.method=="POST":
        fields={
            "name":request.form.get("name","").strip(),"category":request.form.get("category","Snack").strip(),
            "department_id":request.form.get("department_id") or None,"unit":request.form.get("unit","packet").strip(),
            "selling_unit":request.form.get("selling_unit","packet").strip(),
        }
        try:
            packet_weight=float(request.form.get("packet_weight","0"))
            batch_output=int(request.form.get("standard_batch_output","0"))
            target=int(request.form.get("daily_target_batches","0"))
            price=int(request.form.get("selling_price_paise","0"))
            gst=float(request.form.get("gst_percent","5"))
            if packet_weight<0 or batch_output<=0 or target<0 or price<0 or gst<0: raise ValueError
        except ValueError:
            con.close(); flash("Use valid non-negative values and a positive batch output.","danger"); return redirect(url_for("modules.production_product_edit",product_id=product_id))
        is_active=1 if request.form.get("is_active")=="1" else 0
        cur.execute(
            f"UPDATE products SET name={p},category={p},packet_weight={p},unit={p},selling_unit={p},department_id={p},standard_batch_output={p},daily_target_batches={p},selling_price_paise={p},gst_percent={p},is_active={p} WHERE id={p}",
            (fields["name"],fields["category"],packet_weight,fields["unit"],fields["selling_unit"],fields["department_id"],batch_output,target,price,gst,is_active,product_id),
        )
        con.commit(); con.close()
        __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Production Configuration",str(product_id),previous_value=product["name"],new_value=fields["name"])
        flash("Product configuration updated.","success")
        return redirect(url_for("modules.production_config_dashboard"))
    cur.execute("SELECT id,code,name FROM departments WHERE department_type='PRODUCTION' ORDER BY name")
    departments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/product_form.html", product=product, departments=departments)


@modules_bp.get("/production-config/products/<int:product_id>/recipe")
@require_login
def production_recipe(product_id):
    if not production_config_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT * FROM products WHERE id={p}",(product_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    product=dict(row) if db.is_postgres else dict(row)
    cur.execute(f"SELECT * FROM recipes WHERE product_id={p} ORDER BY id DESC",(product_id,))
    recipes=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    recipe=recipes[0] if recipes else None
    items=[]
    if recipe:
        cur.execute(f"SELECT * FROM recipe_items WHERE recipe_id={p} ORDER BY item_category,item_name",(recipe["id"],))
        items=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,code,name,unit,category,standard_cost_paise FROM raw_materials ORDER BY name")
    materials=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(f"SELECT * FROM production_stages WHERE product_id={p} ORDER BY stage_order",(product_id,))
    stages=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/production_recipe.html",product=product,recipe=recipe,items=items,materials=materials,stages=stages)


@modules_bp.post("/production-config/products/<int:product_id>/recipe")
@require_login
def production_recipe_save(product_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT id FROM products WHERE id={p}",(product_id,))
    if not cur.fetchone():
        con.close(); abort(404)
    version=request.form.get("version","V1").strip()
    yield_packets=request.form.get("yield_packets","0")
    wastage=request.form.get("wastage_percent","0")
    try:
        yield_packets=int(yield_packets); wastage=float(wastage)
        if yield_packets<=0 or wastage<0: raise ValueError
    except ValueError:
        con.close(); flash("Yield must be positive and wastage cannot be negative.","danger"); return redirect(url_for("modules.production_recipe",product_id=product_id))
    if db.is_postgres:
        cur.execute("INSERT INTO recipes(product_id,version,batch_quantity,is_active,yield_packets,notes) VALUES(%s,%s,1,1,%s,%s) ON CONFLICT(product_id,version) DO UPDATE SET is_active=1,yield_packets=EXCLUDED.yield_packets,notes=EXCLUDED.notes",(product_id,version,yield_packets,f"Standard wastage allowance: {wastage}%"))
        cur.execute("SELECT id FROM recipes WHERE product_id=%s AND version=%s",(product_id,version))
        recipe_id=cur.fetchone()["id"]
    else:
        cur.execute("INSERT OR REPLACE INTO recipes(product_id,version,batch_quantity,is_active,yield_packets,notes) VALUES(?,?,?,?,?,?)",(product_id,version,1,1,yield_packets,f"Standard wastage allowance: {wastage}%"))
        cur.execute("SELECT id FROM recipes WHERE product_id=? AND version=?",(product_id,version))
        recipe_id=cur.fetchone()[0]
    cur.execute(f"DELETE FROM recipe_items WHERE recipe_id={p}",(recipe_id,))
    names=request.form.getlist("item_name")
    categories=request.form.getlist("item_category")
    quantities=request.form.getlist("quantity")
    units=request.form.getlist("unit")
    for name,category,quantity,unit in zip(names,categories,quantities,units):
        if not name or not unit: continue
        try:
            quantity_value=float(quantity)
            if quantity_value<0: raise ValueError
        except ValueError:
            con.rollback(); con.close(); flash("BOM quantities cannot be negative.","danger"); return redirect(url_for("modules.production_recipe",product_id=product_id))
        cur.execute(
            f"INSERT INTO recipe_items(recipe_id,item_name,item_category,quantity,unit,wastage_percent) VALUES({p},{p},{p},{p},{p},{p})",
            (recipe_id,name,category,quantity_value,unit,wastage),
        )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Production Configuration",str(product_id),new_value=f"BOM {version} saved")
    flash("Recipe/BOM configuration saved.","success")
    return redirect(url_for("modules.production_recipe",product_id=product_id))


@modules_bp.post("/production-config/products/<int:product_id>/stages")
@require_login
def production_stages_save(product_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT department_id FROM products WHERE id={p}",(product_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    department_id=dict(row)["department_id"] if db.is_postgres else row[0]
    names=request.form.getlist("stage_name")
    cur.execute(f"DELETE FROM production_stages WHERE product_id={p}",(product_id,))
    for order,name in enumerate(names,1):
        name=name.strip()
        if name:
            cur.execute(
                f"INSERT INTO production_stages(product_id,stage_order,stage_name,department_id) VALUES({p},{p},{p},{p})",
                (product_id,order,name,department_id),
            )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Production Configuration",str(product_id),new_value="Production stages updated")
    flash("Production stages updated.","success")
    return redirect(url_for("modules.production_recipe",product_id=product_id))


@modules_bp.post("/production-config/products/<int:product_id>/target")
@require_login
def production_target_save(product_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    target=request.form.get("target_batches","0")
    target_date=request.form.get("target_date") or None
    shift_id=request.form.get("shift_id") or None
    reason=request.form.get("reason","").strip()
    try:
        target=int(target)
        if target<0: raise ValueError
    except ValueError:
        con.close(); flash("Production target must be zero or positive.","danger"); return redirect(url_for("modules.production_config_dashboard"))
    cur.execute(f"UPDATE products SET daily_target_batches={p} WHERE id={p}",(target,product_id))
    cur.execute(
        f"INSERT INTO production_targets(product_id,shift_id,target_date,target_batches,reason,approval_status) VALUES({p},{p},{p},{p},{p},'APPROVED')",
        (product_id,shift_id,target_date,target,reason),
    )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Production Configuration",str(product_id),new_value=f"Daily target {target} batches")
    flash("Production target saved.","success")
    return redirect(url_for("modules.production_config_dashboard"))


def machine_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "PRODUCTION SUPERVISOR"})


@modules_bp.get("/machines/workspace")
@require_login
def machines_dashboard():
    if not machine_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute("SELECT m.*,d.name AS department_name FROM machines m LEFT JOIN departments d ON d.id=m.department_id ORDER BY m.name")
    machines=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM machines")
    row=cur.fetchone(); total=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM machines WHERE status='OPERATIONAL'")
    row=cur.fetchone(); operational=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM machine_downtime WHERE status='OPEN'")
    row=cur.fetchone(); downtime=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM machines WHERE next_maintenance_at IS NOT NULL")
    row=cur.fetchone(); scheduled=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT id,name FROM departments WHERE department_type='PRODUCTION' OR department_type='WAREHOUSE' ORDER BY name")
    departments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    capacity=sum(float(machine.get("capacity_per_hour") or 0) for machine in machines if machine.get("status")=="OPERATIONAL")
    return render_template("modules/machines_dashboard.html",machines=machines,departments=departments,total=total,
                           operational=operational,downtime=downtime,scheduled=scheduled,capacity=capacity)


@modules_bp.route("/machines/new",methods=["GET","POST"])
@require_login
def machine_create():
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    if request.method=="POST":
        code=request.form.get("code","").strip().upper()
        name=request.form.get("name","").strip()
        machine_type=request.form.get("machine_type","").strip()
        department_id=request.form.get("department_id") or None
        capacity=request.form.get("capacity_per_hour","0")
        status=request.form.get("status","OPERATIONAL")
        hourly_cost=request.form.get("hourly_cost_paise","0")
        try:
            capacity=float(capacity); hourly_cost=int(hourly_cost)
            if capacity<0 or hourly_cost<0: raise ValueError
        except ValueError:
            con.close(); flash("Capacity and hourly cost must be non-negative.","danger"); return redirect(url_for("modules.machine_create"))
        if not code or not name:
            con.close(); flash("Machine code and name are required.","danger"); return redirect(url_for("modules.machine_create"))
        try:
            cur.execute(
                f"INSERT INTO machines(code,name,machine_type,department_id,status,capacity_per_hour,hourly_cost_paise) VALUES({p},{p},{p},{p},{p},{p},{p})",
                (code,name,machine_type,department_id,status,capacity,hourly_cost),
            )
            con.commit()
            if db.is_postgres:
                cur.execute("SELECT id FROM machines WHERE code=%s",(code,))
                machine_id=cur.fetchone()["id"]
            else:
                machine_id=cur.lastrowid
            __import__("app.audit.service", fromlist=["add_audit"]).add_audit("CREATE","Machine Management",str(machine_id),new_value=name)
            con.close(); flash("Machine registered.","success")
            return redirect(url_for("modules.machines_dashboard"))
        except Exception:
            con.rollback(); con.close(); flash("Machine code already exists or the configuration is invalid.","danger")
            return redirect(url_for("modules.machine_create"))
    cur.execute("SELECT id,name FROM departments ORDER BY name")
    departments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/machine_form.html",machine=None,departments=departments)


@modules_bp.route("/machines/<int:machine_id>/edit",methods=["GET","POST"])
@require_login
def machine_edit(machine_id):
    if "OWNER" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT * FROM machines WHERE id={p}",(machine_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    machine=dict(row) if db.is_postgres else dict(row)
    if request.method=="POST":
        name=request.form.get("name","").strip()
        machine_type=request.form.get("machine_type","").strip()
        department_id=request.form.get("department_id") or None
        status=request.form.get("status","OPERATIONAL")
        next_maintenance=request.form.get("next_maintenance_at") or None
        try:
            capacity=float(request.form.get("capacity_per_hour","0"))
            hourly_cost=int(request.form.get("hourly_cost_paise","0"))
            if capacity<0 or hourly_cost<0: raise ValueError
        except ValueError:
            con.close(); flash("Capacity and hourly cost must be non-negative.","danger"); return redirect(url_for("modules.machine_edit",machine_id=machine_id))
        if not name:
            con.close(); flash("Machine name is required.","danger"); return redirect(url_for("modules.machine_edit",machine_id=machine_id))
        cur.execute(
            f"UPDATE machines SET name={p},machine_type={p},department_id={p},status={p},capacity_per_hour={p},hourly_cost_paise={p},next_maintenance_at={p} WHERE id={p}",
            (name,machine_type,department_id,status,capacity,hourly_cost,next_maintenance,machine_id),
        )
        con.commit(); con.close()
        __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Machine Management",str(machine_id),previous_value=machine["name"],new_value=name)
        flash("Machine configuration updated.","success")
        return redirect(url_for("modules.machines_dashboard"))
    cur.execute("SELECT id,name FROM departments ORDER BY name")
    departments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/machine_form.html",machine=machine,departments=departments)


@modules_bp.post("/machines/<int:machine_id>/downtime")
@require_login
def machine_downtime(machine_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []) and "PRODUCTION SUPERVISOR" not in session.get("roles", []):
        abort(403)
    reason=request.form.get("reason","").strip()
    if not reason:
        flash("Downtime reason is required.","danger"); return redirect(url_for("modules.machines_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT id FROM machines WHERE id={p}",(machine_id,))
    if not cur.fetchone():
        con.close(); abort(404)
    cur.execute(
        f"INSERT INTO machine_downtime(machine_id,started_at,status,reason) VALUES({p},CURRENT_TIMESTAMP,'OPEN',{p})",
        (machine_id,reason),
    )
    cur.execute(f"UPDATE machines SET status='UNDER_MAINTENANCE' WHERE id={p}",(machine_id,))
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Machine Management",str(machine_id),new_value="Machine downtime opened")
    flash("Downtime recorded.","success")
    return redirect(url_for("modules.machines_dashboard"))


def production_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "PRODUCTION SUPERVISOR"})


@modules_bp.get("/production/workspace")
@require_login
def production_dashboard():
    if not production_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        "SELECT pp.*,pr.name AS product_name,d.name AS department_name,s.name AS shift_name "
        "FROM production_plans pp LEFT JOIN products pr ON pr.id=pp.product_id "
        "LEFT JOIN departments d ON d.id=pp.department_id LEFT JOIN shifts s ON s.id=pp.shift_id "
        "ORDER BY pp.plan_date DESC,pp.id DESC LIMIT 100"
    )
    plans=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT pb.*,pr.name AS product_name,d.name AS department_name "
        "FROM production_batches pb LEFT JOIN products pr ON pr.id=pb.product_id "
        "LEFT JOIN departments d ON d.id=pb.department_id ORDER BY pb.id DESC LIMIT 100"
    )
    batches=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM production_plans")
    row=cur.fetchone(); plan_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM production_batches")
    row=cur.fetchone(); batch_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM production_batches WHERE batch_status='IN_PROGRESS'")
    row=cur.fetchone(); active_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM production_batches WHERE batch_status='COMPLETED'")
    row=cur.fetchone(); completed_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT id,name,department_id,standard_batch_output,daily_target_batches FROM products WHERE is_active=1 ORDER BY name")
    products=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name FROM departments WHERE department_type='PRODUCTION' AND status!='INACTIVE' ORDER BY name")
    departments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name,start_time,end_time FROM shifts WHERE is_active=1 ORDER BY start_time")
    shifts=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/production_dashboard.html",plans=plans,batches=batches,products=products,
                           departments=departments,shifts=shifts,plan_count=plan_count,batch_count=batch_count,
                           active_count=active_count,completed_count=completed_count)


@modules_bp.post("/production/plans")
@require_login
def production_plan_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []) and "PRODUCTION SUPERVISOR" not in session.get("roles", []):
        abort(403)
    plan_date=request.form.get("plan_date","").strip()
    product_id=request.form.get("product_id")
    department_id=request.form.get("department_id") or None
    shift_id=request.form.get("shift_id") or None
    planned_quantity=request.form.get("planned_quantity","0")
    planned_batches=request.form.get("planned_batches","0")
    priority=request.form.get("priority","1")
    notes=request.form.get("notes","").strip()
    if not plan_date or not product_id:
        flash("Plan date and product are required.","danger"); return redirect(url_for("modules.production_dashboard"))
    try:
        planned_quantity=int(planned_quantity); planned_batches=int(planned_batches); priority=int(priority)
        if planned_quantity<0 or planned_batches<0 or priority<1: raise ValueError
    except ValueError:
        flash("Plan quantities and priority must be valid.","danger"); return redirect(url_for("modules.production_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        f"INSERT INTO production_plans(plan_date,department_id,product_id,planned_quantity,planned_batches,shift_id,priority,status,notes,created_by) "
        f"VALUES({p},{p},{p},{p},{p},{p},{p},'PLANNED',{p},{p})",
        (plan_date,department_id,product_id,planned_quantity,planned_batches,shift_id,priority,notes,session["user_id"]),
    )
    con.commit()
    if db.is_postgres:
        cur.execute("SELECT id FROM production_plans WHERE plan_date=%s AND product_id=%s ORDER BY id DESC LIMIT 1",(plan_date,product_id))
        plan_id=cur.fetchone()["id"]
    else:
        plan_id=cur.lastrowid
    con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("CREATE","Production",str(plan_id),new_value=f"Plan for {planned_batches} batches")
    flash("Production plan created.","success")
    return redirect(url_for("modules.production_dashboard"))


@modules_bp.post("/production/batches")
@require_login
def production_batch_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []) and "PRODUCTION SUPERVISOR" not in session.get("roles", []):
        abort(403)
    product_id=request.form.get("product_id")
    department_id=request.form.get("department_id") or None
    shift_id=request.form.get("shift_id") or None
    planned_quantity=request.form.get("planned_quantity","0")
    plan_id=request.form.get("plan_id") or None
    if not product_id:
        flash("Select a product.","danger"); return redirect(url_for("modules.production_dashboard"))
    try:
        planned_quantity=int(planned_quantity)
        if planned_quantity<0: raise ValueError
    except ValueError:
        flash("Planned quantity must be non-negative.","danger"); return redirect(url_for("modules.production_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT id FROM recipes WHERE product_id={p} AND is_active=1 ORDER BY id DESC LIMIT 1",(product_id,))
    recipe_row=cur.fetchone(); recipe_id=(dict(recipe_row)["id"] if db.is_postgres else recipe_row[0]) if recipe_row else None
    batch_number=f"BATCH-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO production_batches(batch_number,plan_id,product_id,department_id,shift_id,recipe_id,batch_status,planned_quantity,supervisor_id,created_by) "
        f"VALUES({p},{p},{p},{p},{p},{p},'PLANNED',{p},{p},{p})",
        (batch_number,plan_id,product_id,department_id,shift_id,recipe_id,planned_quantity,session["user_id"],session["user_id"]),
    )
    con.commit()
    if db.is_postgres:
        cur.execute("SELECT id FROM production_batches WHERE batch_number=%s",(batch_number,))
        batch_id=cur.fetchone()["id"]
    else:
        batch_id=cur.lastrowid
    con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("CREATE","Production",str(batch_id),new_value=batch_number)
    flash(f"Batch {batch_number} created.","success")
    return redirect(url_for("modules.production_dashboard"))


@modules_bp.post("/production/batches/<int:batch_id>/start")
@require_login
def production_batch_start(batch_id):
    if not production_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT batch_status FROM production_batches WHERE id={p}",(batch_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    status=dict(row)["batch_status"] if db.is_postgres else row[0]
    if status!="PLANNED":
        con.close(); flash("Only planned batches can be started.","danger"); return redirect(url_for("modules.production_dashboard"))
    cur.execute(f"UPDATE production_batches SET batch_status='IN_PROGRESS',started_at=CURRENT_TIMESTAMP WHERE id={p}",(batch_id,))
    cur.execute(f"SELECT pb.product_id,pb.department_id,pb.recipe_id FROM production_batches pb WHERE pb.id={p}",(batch_id,))
    batch_row=cur.fetchone()
    if db.is_postgres:
        product_id=batch_row["product_id"]; department_id=batch_row["department_id"]; recipe_id=batch_row["recipe_id"]
    else:
        product_id=batch_row["product_id"]; department_id=batch_row["department_id"]; recipe_id=batch_row["recipe_id"]
    cur.execute(f"SELECT id FROM production_stages WHERE product_id={p} ORDER BY stage_order",(product_id,))
    stages=cur.fetchall()
    for stage_row in stages:
        stage_id=dict(stage_row)["id"] if db.is_postgres else stage_row[0]
        cur.execute(
            f"INSERT INTO batch_stage_records(batch_id,stage_id,status) VALUES({p},{p},'PENDING')",
            (batch_id,stage_id),
        )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("START","Production",str(batch_id),new_value="Batch started")
    flash("Production batch started.","success")
    return redirect(url_for("modules.production_dashboard"))


@modules_bp.post("/production/batches/<int:batch_id>/complete")
@require_login
def production_batch_complete(batch_id):
    if not production_allowed():
        abort(403)
    actual_quantity=request.form.get("actual_quantity","0")
    damaged_quantity=request.form.get("damaged_quantity","0")
    wastage_quantity=request.form.get("wastage_quantity","0")
    reason=request.form.get("reason","").strip()
    try:
        actual=float(actual_quantity); damaged=float(damaged_quantity); wastage=float(wastage_quantity)
        if actual<0 or damaged<0 or wastage<0: raise ValueError
    except ValueError:
        flash("Actual, damaged and wastage quantities must be non-negative.","danger"); return redirect(url_for("modules.production_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT batch_status FROM production_batches WHERE id={p}",(batch_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    status=dict(row)["batch_status"] if db.is_postgres else row[0]
    if status!="IN_PROGRESS":
        con.close(); flash("Only in-progress batches can be completed.","danger"); return redirect(url_for("modules.production_dashboard"))
    cur.execute(
        f"UPDATE production_batches SET batch_status='COMPLETED',actual_quantity={p},damaged_quantity={p},wastage_quantity={p},reason={p},completed_at=CURRENT_TIMESTAMP WHERE id={p}",
        (actual,damaged,wastage,reason,batch_id),
    )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("COMPLETE","Production",str(batch_id),new_value=f"Actual={actual}, damaged={damaged}, wastage={wastage}")
    flash("Production batch completed.","success")
    return redirect(url_for("modules.production_dashboard"))


@modules_bp.post("/production/batches/<int:batch_id>/stages/<int:stage_id>/complete")
@require_login
def production_stage_complete(batch_id, stage_id):
    if not production_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        f"UPDATE batch_stage_records SET status='COMPLETED',completed_at=CURRENT_TIMESTAMP,notes={p} "
        f"WHERE batch_id={p} AND stage_id={p}",
        (request.form.get("notes","").strip(),batch_id,stage_id),
    )
    con.commit(); con.close()
    __import__("app.audit.service", fromlist=["add_audit"]).add_audit("UPDATE","Production",str(batch_id),new_value=f"Stage {stage_id} completed")
    flash("Production stage completed.","success")
    return redirect(url_for("modules.production_dashboard"))


def purchasing_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "ACCOUNTANT / AUDITOR"})


@modules_bp.get("/purchasing/workspace")
@require_login
def purchasing_dashboard():
    if not purchasing_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute("SELECT * FROM suppliers ORDER BY name")
    suppliers=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT po.*,s.name AS supplier_name "
        "FROM purchase_orders po LEFT JOIN suppliers s ON s.id=po.supplier_id "
        "ORDER BY po.order_date DESC,po.id DESC"
    )
    orders=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT gr.*,po.order_number,s.name AS supplier_name "
        "FROM goods_receipts gr LEFT JOIN purchase_orders po ON po.id=gr.purchase_order_id "
        "LEFT JOIN suppliers s ON s.id=po.supplier_id ORDER BY gr.received_date DESC,gr.id DESC"
    )
    receipts=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM suppliers")
    row=cur.fetchone(); supplier_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM purchase_orders")
    row=cur.fetchone(); order_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM goods_receipts")
    row=cur.fetchone(); receipt_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM purchase_orders WHERE status='APPROVED'")
    row=cur.fetchone(); approved_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT id,code,name,unit,standard_cost_paise FROM raw_materials ORDER BY name")
    materials=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,code,name,warehouse_type,status FROM warehouses WHERE status='ACTIVE' ORDER BY name")
    warehouses=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/purchasing_dashboard.html",suppliers=suppliers,orders=orders,receipts=receipts,
                           materials=materials,warehouses=warehouses,supplier_count=supplier_count,order_count=order_count,
                           receipt_count=receipt_count,approved_count=approved_count)


@modules_bp.route("/purchasing/suppliers/new",methods=["GET","POST"])
@require_login
def supplier_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    if request.method=="POST":
        code=request.form.get("code","").strip().upper()
        name=request.form.get("name","").strip()
        contact=request.form.get("contact_person","").strip()
        phone=request.form.get("phone","").strip()
        email=request.form.get("email","").strip().lower()
        gstin=request.form.get("gstin","").strip().upper()
        address=request.form.get("address","").strip()
        if not code or not name:
            con.close(); flash("Supplier code and name are required.","danger"); return redirect(url_for("modules.supplier_create"))
        try:
            credit_days=int(request.form.get("credit_days","0"))
            if credit_days<0: raise ValueError
        except ValueError:
            con.close(); flash("Credit days must be non-negative.","danger"); return redirect(url_for("modules.supplier_create"))
        try:
            cur.execute(
                f"INSERT INTO suppliers(code,name,contact_person,phone,email,gstin,address,credit_days,status) "
                f"VALUES({p},{p},{p},{p},{p},{p},{p},{p},'ACTIVE')",
                (code,name,contact,phone,email,gstin,address,credit_days),
            )
            con.commit()
            if db.is_postgres:
                cur.execute("SELECT id FROM suppliers WHERE code=%s",(code,))
                supplier_id=cur.fetchone()["id"]
            else:
                supplier_id=cur.lastrowid
            con.close()
            __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Purchasing",str(supplier_id),new_value=name)
            flash("Supplier created.","success")
            return redirect(url_for("modules.purchasing_dashboard"))
        except Exception:
            con.rollback(); con.close(); flash("Supplier code already exists.","danger")
            return redirect(url_for("modules.supplier_create"))
    con.close()
    return render_template("modules/supplier_form.html",supplier=None)


@modules_bp.post("/purchasing/orders")
@require_login
def purchase_order_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    supplier_id=request.form.get("supplier_id")
    order_date=request.form.get("order_date","").strip()
    material_id=request.form.get("material_id")
    quantity=request.form.get("quantity","0")
    unit=request.form.get("unit","").strip()
    unit_price=request.form.get("unit_price_paise","0")
    notes=request.form.get("notes","").strip()
    if not supplier_id or not order_date or not material_id or not unit:
        flash("Supplier, date, material and unit are required.","danger"); return redirect(url_for("modules.purchasing_dashboard"))
    try:
        quantity=float(quantity); unit_price=int(unit_price)
        if quantity<=0 or unit_price<0: raise ValueError
    except ValueError:
        flash("Quantity must be positive and unit price cannot be negative.","danger"); return redirect(url_for("modules.purchasing_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    order_number=f"PO-{now().strftime('%Y%m%d-%H%M%S')}"
    total_paise=int(quantity*unit_price)
    cur.execute(
        f"INSERT INTO purchase_orders(order_number,supplier_id,order_date,status,total_paise,notes,created_by) "
        f"VALUES({p},{p},{p},'DRAFT',{p},{p},{p})",
        (order_number,supplier_id,order_date,total_paise,notes,session["user_id"]),
    )
    if db.is_postgres:
        cur.execute("SELECT id FROM purchase_orders WHERE order_number=%s",(order_number,))
        order_id=cur.fetchone()["id"]
    else:
        order_id=cur.lastrowid
    cur.execute(
        f"INSERT INTO purchase_order_items(purchase_order_id,item_type,item_id,quantity,unit,unit_price_paise) "
        f"VALUES({p},'RAW_MATERIAL',{p},{p},{p},{p})",
        (order_id,material_id,quantity,unit,unit_price),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Purchasing",str(order_id),new_value=order_number)
    flash("Purchase order created.","success")
    return redirect(url_for("modules.purchasing_dashboard"))


@modules_bp.post("/purchasing/orders/<int:order_id>/approve")
@require_login
def purchase_order_approve(order_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT status FROM purchase_orders WHERE id={p}",(order_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    status=dict(row)["status"] if db.is_postgres else row[0]
    if status!="DRAFT":
        con.close(); flash("Only draft purchase orders can be approved.","danger"); return redirect(url_for("modules.purchasing_dashboard"))
    cur.execute(f"UPDATE purchase_orders SET status='APPROVED' WHERE id={p}",(order_id,))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("APPROVE","Purchasing",str(order_id),new_value="Approved")
    flash("Purchase order approved.","success")
    return redirect(url_for("modules.purchasing_dashboard"))


@modules_bp.post("/purchasing/receipts")
@require_login
def goods_receipt_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    order_id=request.form.get("order_id")
    warehouse_id=request.form.get("warehouse_id")
    received_date=request.form.get("received_date","").strip()
    if not order_id or not warehouse_id or not received_date:
        flash("Purchase order, warehouse and received date are required.","danger"); return redirect(url_for("modules.purchasing_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT status FROM purchase_orders WHERE id={p}",(order_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    status=dict(row)["status"] if db.is_postgres else row[0]
    if status!="APPROVED":
        con.close(); flash("Only approved purchase orders can be received.","danger"); return redirect(url_for("modules.purchasing_dashboard"))
    receipt_number=f"GR-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO goods_receipts(receipt_number,purchase_order_id,received_date,status,warehouse_id,created_by) "
        f"VALUES({p},{p},{p},'PENDING_QC',{p},{p})",
        (receipt_number,order_id,received_date,warehouse_id,session["user_id"]),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Purchasing",receipt_number,new_value="Goods receipt pending QC")
    flash("Goods receipt created; stock is not released until QC approval.","success")
    return redirect(url_for("modules.purchasing_dashboard"))


def quality_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "PRODUCTION SUPERVISOR", "ACCOUNTANT / AUDITOR"})


@modules_bp.get("/quality/workspace")
@require_login
def quality_dashboard():
    if not quality_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute("SELECT qi.*,p.name AS product_name,u.name AS inspector_name FROM quality_inspections qi LEFT JOIN products p ON p.id=qi.product_id LEFT JOIN users u ON u.id=qi.inspector_id ORDER BY qi.id DESC")
    inspections=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT qc.*,p.name AS product_name FROM quality_complaints qc LEFT JOIN products p ON p.id=qc.product_id ORDER BY qc.id DESC")
    complaints=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT * FROM capa_records ORDER BY id DESC")
    capas=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM quality_inspections")
    row=cur.fetchone(); total=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM quality_inspections WHERE status='PENDING'")
    row=cur.fetchone(); pending=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM quality_inspections WHERE result='PASS'")
    row=cur.fetchone(); passed=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM quality_inspections WHERE result='FAIL'")
    row=cur.fetchone(); failed=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM production_batches WHERE batch_status='ON_HOLD'")
    row=cur.fetchone(); held=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM quality_complaints WHERE status='OPEN'")
    row=cur.fetchone(); open_complaints=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT id,name FROM products WHERE is_active=1 ORDER BY name")
    products=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,batch_number FROM production_batches ORDER BY id DESC")
    batches=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,batch_number FROM production_batches WHERE batch_status='ON_HOLD' ORDER BY id DESC")
    held_batches=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,receipt_number FROM goods_receipts ORDER BY id DESC")
    receipts=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/quality_dashboard.html",inspections=inspections,complaints=complaints,capas=capas,
                           products=products,batches=batches,receipts=receipts,total=total,pending=pending,passed=passed,
                           failed=failed,held=held,open_complaints=open_complaints,held_batches=held_batches)


@modules_bp.post("/quality/inspections")
@require_login
def quality_inspection_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    inspection_type=request.form.get("inspection_type","").strip()
    reference_type=request.form.get("reference_type","").strip()
    reference_id=request.form.get("reference_id") or None
    product_id=request.form.get("product_id") or None
    result=request.form.get("result","PENDING").strip()
    notes=request.form.get("notes","").strip()
    if not inspection_type or result not in {"PENDING","PASS","FAIL","HOLD"}:
        flash("Inspection type and result are required.","danger"); return redirect(url_for("modules.quality_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    inspection_number=f"QI-{now().strftime('%Y%m%d-%H%M%S')}"
    status="COMPLETED" if result!="PENDING" else "PENDING"
    cur.execute(
        f"INSERT INTO quality_inspections(inspection_number,inspection_type,reference_type,reference_id,product_id,inspector_id,status,result,notes,inspected_at) "
        f"VALUES({p},{p},{p},{p},{p},{p},{p},{p},{p},CURRENT_TIMESTAMP)",
        (inspection_number,inspection_type,reference_type,reference_id,product_id,session["user_id"],status,result,notes),
    )
    if result=="FAIL" and reference_type=="BATCH" and reference_id:
        cur.execute(f"UPDATE production_batches SET batch_status='ON_HOLD',reason={p} WHERE id={p}",("Quality inspection failed",reference_id))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Quality",inspection_number,new_value=f"{inspection_type}: {result}")
    flash("Quality inspection recorded.","success")
    return redirect(url_for("modules.quality_dashboard"))


@modules_bp.post("/quality/batches/<int:batch_id>/release")
@require_login
def quality_batch_release(batch_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT batch_status FROM production_batches WHERE id={p}",(batch_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    status=dict(row)["batch_status"] if db.is_postgres else row[0]
    if status!="ON_HOLD":
        con.close(); flash("Only held batches can be released.","danger"); return redirect(url_for("modules.quality_dashboard"))
    cur.execute(f"UPDATE production_batches SET batch_status='COMPLETED' WHERE id={p}",(batch_id,))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("APPROVE","Quality",str(batch_id),new_value="Held batch released")
    flash("Held batch released by quality authorization.","success")
    return redirect(url_for("modules.quality_dashboard"))


@modules_bp.post("/quality/complaints")
@require_login
def quality_complaint_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    customer_name=request.form.get("customer_name","").strip()
    product_id=request.form.get("product_id") or None
    complaint_type=request.form.get("complaint_type","").strip()
    description=request.form.get("description","").strip()
    severity=request.form.get("severity","MEDIUM").strip()
    if not customer_name or not complaint_type or not description:
        flash("Customer, complaint type and description are required.","danger"); return redirect(url_for("modules.quality_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    complaint_number=f"QC-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO quality_complaints(complaint_number,customer_name,product_id,complaint_type,description,severity,status) "
        f"VALUES({p},{p},{p},{p},{p},{p},'OPEN')",
        (complaint_number,customer_name,product_id,complaint_type,description,severity),
    )
    con.commit()
    if db.is_postgres:
        cur.execute("SELECT id FROM quality_complaints WHERE complaint_number=%s",(complaint_number,))
        complaint_id=cur.fetchone()["id"]
    else:
        complaint_id=cur.lastrowid
    con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Quality",str(complaint_id),new_value=complaint_number)
    flash("Customer complaint recorded.","success")
    return redirect(url_for("modules.quality_dashboard"))


@modules_bp.post("/quality/complaints/<int:complaint_id>/capa")
@require_login
def quality_capa_create(complaint_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    corrective=request.form.get("corrective_action","").strip()
    preventive=request.form.get("preventive_action","").strip()
    owner=request.form.get("owner","").strip()
    due_date=request.form.get("due_date") or None
    if not corrective:
        flash("Corrective action is required.","danger"); return redirect(url_for("modules.quality_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT id FROM quality_complaints WHERE id={p}",(complaint_id,))
    if not cur.fetchone():
        con.close(); abort(404)
    cur.execute(
        f"INSERT INTO capa_records(complaint_id,corrective_action,preventive_action,owner,due_date,status) "
        f"VALUES({p},{p},{p},{p},{p},'OPEN')",
        (complaint_id,corrective,preventive,owner,due_date),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Quality",str(complaint_id),new_value="CAPA opened")
    flash("Corrective and preventive action opened.","success")
    return redirect(url_for("modules.quality_dashboard"))


def maintenance_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "PRODUCTION SUPERVISOR"})


@modules_bp.get("/maintenance/workspace")
@require_login
def maintenance_dashboard():
    if not maintenance_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        "SELECT wo.*,m.name AS machine_name,e.name AS employee_name "
        "FROM maintenance_work_orders wo LEFT JOIN machines m ON m.id=wo.machine_id "
        "LEFT JOIN employees e ON e.id=wo.assigned_employee_id ORDER BY wo.opened_at DESC,wo.id DESC"
    )
    work_orders=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT mp.*,m.name AS machine_name FROM maintenance_plans mp LEFT JOIN machines m ON m.id=mp.machine_id "
        "ORDER BY mp.next_due_at"
    )
    plans=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM maintenance_work_orders")
    row=cur.fetchone(); total_orders=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM maintenance_work_orders WHERE status='OPEN'")
    row=cur.fetchone(); open_orders=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM maintenance_plans WHERE status='ACTIVE'")
    row=cur.fetchone(); active_plans=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM machines WHERE status='UNDER_MAINTENANCE'")
    row=cur.fetchone(); unavailable=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT id,name,status FROM machines ORDER BY name")
    machines=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name,status FROM employees WHERE status='ACTIVE' ORDER BY name")
    employees=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    return render_template("modules/maintenance_dashboard.html",work_orders=work_orders,plans=plans,
                           machines=machines,employees=employees,total_orders=total_orders,open_orders=open_orders,
                           active_plans=active_plans,unavailable=unavailable)


@modules_bp.post("/maintenance/work-orders")
@require_login
def maintenance_work_order_create():
    if not maintenance_allowed():
        abort(403)
    machine_id=request.form.get("machine_id") or None
    assigned_employee_id=request.form.get("assigned_employee_id") or None
    work_order_type=request.form.get("work_order_type","CORRECTIVE").strip()
    title=request.form.get("title","").strip()
    description=request.form.get("description","").strip()
    priority=request.form.get("priority","MEDIUM").strip()
    if not title or work_order_type not in {"CORRECTIVE","PREVENTIVE"}:
        flash("Work-order title and type are required.","danger"); return redirect(url_for("modules.maintenance_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    work_order_number=f"WO-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO maintenance_work_orders(work_order_number,machine_id,work_order_type,title,description,assigned_employee_id,status,priority) "
        f"VALUES({p},{p},{p},{p},{p},{p},'OPEN',{p})",
        (work_order_number,machine_id,work_order_type,title,description,assigned_employee_id,priority),
    )
    if machine_id:
        cur.execute(f"UPDATE machines SET status='UNDER_MAINTENANCE' WHERE id={p}",(machine_id,))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Maintenance",work_order_number,new_value=f"{work_order_type}: {title}")
    flash("Maintenance work order created.","success")
    return redirect(url_for("modules.maintenance_dashboard"))


@modules_bp.post("/maintenance/work-orders/<int:work_order_id>/complete")
@require_login
def maintenance_work_order_complete(work_order_id):
    if not maintenance_allowed():
        abort(403)
    expense=request.form.get("expense_paise","0")
    try:
        expense=int(expense)
        if expense<0: raise ValueError
    except ValueError:
        flash("Maintenance expense must be non-negative.","danger"); return redirect(url_for("modules.maintenance_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT machine_id,status FROM maintenance_work_orders WHERE id={p}",(work_order_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    machine_id=dict(row)["machine_id"] if db.is_postgres else row[0]
    status=dict(row)["status"] if db.is_postgres else row[1]
    if status=="COMPLETED":
        con.close(); flash("This work order is already completed.","danger"); return redirect(url_for("modules.maintenance_dashboard"))
    cur.execute(f"UPDATE maintenance_work_orders SET status='COMPLETED',completed_at=CURRENT_TIMESTAMP,expense_paise={p} WHERE id={p}",(expense,work_order_id))
    if machine_id:
        cur.execute(f"UPDATE machines SET status='OPERATIONAL',last_maintenance_at=CURRENT_TIMESTAMP WHERE id={p}",(machine_id,))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("COMPLETE","Maintenance",str(work_order_id),new_value=f"Expense {expense} paise")
    flash("Maintenance work order completed.","success")
    return redirect(url_for("modules.maintenance_dashboard"))


@modules_bp.post("/maintenance/plans")
@require_login
def maintenance_plan_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    machine_id=request.form.get("machine_id")
    plan_type=request.form.get("plan_type","PREVENTIVE").strip()
    frequency=request.form.get("frequency_days","30")
    next_due=request.form.get("next_due_at") or None
    if not machine_id:
        flash("Select a machine.","danger"); return redirect(url_for("modules.maintenance_dashboard"))
    try:
        frequency=int(frequency)
        if frequency<=0: raise ValueError
    except ValueError:
        flash("Maintenance frequency must be positive.","danger"); return redirect(url_for("modules.maintenance_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        f"INSERT INTO maintenance_plans(machine_id,plan_type,frequency_days,next_due_at,status) "
        f"VALUES({p},{p},{p},{p},'ACTIVE')",
        (machine_id,plan_type,frequency,next_due),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Maintenance",str(machine_id),new_value=f"Preventive plan every {frequency} days")
    flash("Maintenance plan created.","success")
    return redirect(url_for("modules.maintenance_dashboard"))


def inventory_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "PRODUCTION SUPERVISOR", "ACCOUNTANT / AUDITOR"})


@modules_bp.get("/inventory/workspace")
@require_login
def inventory_dashboard():
    if not inventory_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        "SELECT si.*,w.name AS warehouse_name,"
        "CASE si.item_type WHEN 'RAW_MATERIAL' THEN rm.name WHEN 'PACKAGING' THEN rm.name ELSE pr.name END AS item_name,"
        "CASE si.item_type WHEN 'RAW_MATERIAL' THEN rm.unit WHEN 'PACKAGING' THEN rm.unit ELSE pr.unit END AS item_unit "
        "FROM stock_items si LEFT JOIN warehouses w ON w.id=si.warehouse_id "
        "LEFT JOIN raw_materials rm ON si.item_type IN ('RAW_MATERIAL','PACKAGING') AND rm.id=si.item_id "
        "LEFT JOIN products pr ON si.item_type='PRODUCT' AND pr.id=si.item_id "
        "ORDER BY w.name,item_name"
    )
    stock=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT sl.*,w.name AS warehouse_name FROM stock_ledger sl LEFT JOIN warehouses w ON w.id=sl.warehouse_id "
        "ORDER BY sl.id DESC LIMIT 100"
    )
    ledger=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT * FROM stock_adjustments ORDER BY id DESC")
    adjustments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,code,name,status FROM warehouses ORDER BY name")
    warehouses=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,code,name,unit,reorder_level FROM raw_materials ORDER BY name")
    materials=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,code,name,unit FROM products WHERE is_active=1 ORDER BY name")
    products=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM warehouses")
    row=cur.fetchone(); warehouse_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM stock_items")
    row=cur.fetchone(); stock_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM stock_adjustments WHERE status='PENDING'")
    row=cur.fetchone(); pending_adjustments=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM stock_items WHERE quantity <= reserved_quantity")
    row=cur.fetchone(); low_stock=dict(row)["c"] if db.is_postgres else row[0]
    con.close()
    return render_template("modules/inventory_dashboard.html",stock=stock,ledger=ledger,adjustments=adjustments,
                           warehouses=warehouses,materials=materials,products=products,warehouse_count=warehouse_count,
                           stock_count=stock_count,pending_adjustments=pending_adjustments,low_stock=low_stock)


@modules_bp.post("/inventory/stock")
@require_login
def inventory_stock_adjust():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    item_type=request.form.get("item_type","RAW_MATERIAL")
    item_id=request.form.get("item_id")
    warehouse_id=request.form.get("warehouse_id")
    quantity=request.form.get("quantity","0")
    batch_lot=request.form.get("batch_lot","").strip()
    expiry_date=request.form.get("expiry_date") or None
    reason=request.form.get("reason","").strip()
    if item_type not in {"RAW_MATERIAL","PACKAGING","PRODUCT"} or not item_id or not warehouse_id or not reason:
        flash("Item, warehouse and reason are required.","danger"); return redirect(url_for("modules.inventory_dashboard"))
    try:
        quantity=float(quantity)
        if quantity==0: raise ValueError
    except ValueError:
        flash("Adjustment quantity must be non-zero.","danger"); return redirect(url_for("modules.inventory_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        f"INSERT INTO stock_adjustments(item_type,item_id,warehouse_id,adjustment,reason,status,created_by) "
        f"VALUES({p},{p},{p},{p},{p},'PENDING',{p})",
        (item_type,item_id,warehouse_id,quantity,reason,session["user_id"]),
    )
    con.commit()
    if db.is_postgres:
        cur.execute("SELECT id FROM stock_adjustments WHERE item_type=%s AND item_id=%s AND warehouse_id=%s ORDER BY id DESC LIMIT 1",(item_type,item_id,warehouse_id))
        adjustment_id=cur.fetchone()["id"]
    else:
        adjustment_id=cur.lastrowid
    con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Inventory",str(adjustment_id),new_value=f"Adjustment {quantity}")
    flash("Stock adjustment submitted for approval.","success")
    return redirect(url_for("modules.inventory_dashboard"))


@modules_bp.post("/inventory/adjustments/<int:adjustment_id>/approve")
@require_login
def inventory_adjustment_approve(adjustment_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT * FROM stock_adjustments WHERE id={p}",(adjustment_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    adjustment=dict(row) if db.is_postgres else dict(row)
    if adjustment["status"]!="PENDING":
        con.close(); flash("Only pending adjustments can be approved.","danger"); return redirect(url_for("modules.inventory_dashboard"))
    cur.execute(
        f"UPDATE stock_adjustments SET status='APPROVED',approved_by={p} WHERE id={p}",
        (session["user_id"],adjustment_id),
    )
    cur.execute(
        f"SELECT quantity,reserved_quantity,batch_lot FROM stock_items "
        f"WHERE item_type={p} AND item_id={p} AND warehouse_id={p}",
        (adjustment["item_type"],adjustment["item_id"],adjustment["warehouse_id"]),
    )
    stock_row=cur.fetchone()
    old_quantity=(dict(stock_row)["quantity"] if db.is_postgres else stock_row["quantity"]) if stock_row else 0
    new_quantity=float(old_quantity)+float(adjustment["adjustment"])
    if new_quantity<0:
        con.rollback(); con.close(); flash("Adjustment cannot make stock negative.","danger"); return redirect(url_for("modules.inventory_dashboard"))
    if stock_row:
        cur.execute(
            f"UPDATE stock_items SET quantity={p} WHERE item_type={p} AND item_id={p} AND warehouse_id={p}",
            (new_quantity,adjustment["item_type"],adjustment["item_id"],adjustment["warehouse_id"]),
        )
    else:
        cur.execute(
            f"INSERT INTO stock_items(item_type,item_id,warehouse_id,quantity,reserved_quantity,batch_lot) "
            f"VALUES({p},{p},{p},{p},0,NULL)",
            (adjustment["item_type"],adjustment["item_id"],adjustment["warehouse_id"],new_quantity),
        )
    cur.execute(
        f"INSERT INTO stock_ledger(item_type,item_id,warehouse_id,movement_type,quantity,balance_quantity,reference_type,reference_id,remarks,created_by) "
        f"VALUES({p},{p},{p},'ADJUSTMENT',{p},{p},'STOCK_ADJUSTMENT',{p},{p},{p})",
        (adjustment["item_type"],adjustment["item_id"],adjustment["warehouse_id"],adjustment["adjustment"],
         new_quantity,str(adjustment_id),adjustment["reason"],session["user_id"]),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("APPROVE","Inventory",str(adjustment_id),new_value=f"Stock {new_quantity}")
    flash("Stock adjustment approved.","success")
    return redirect(url_for("modules.inventory_dashboard"))


def sales_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "SALESMAN", "ACCOUNTANT / AUDITOR"})


@modules_bp.get("/sales/workspace")
@require_login
def sales_dashboard():
    if not sales_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    roles=session.get("roles",[])
    if "SALESMAN" in roles and "OWNER" not in roles and "FACTORY ADMIN" not in roles:
        cur.execute(
            f"SELECT c.* FROM customers c LEFT JOIN users u ON u.id=c.assigned_salesman_id "
            f"WHERE c.assigned_salesman_id={p} ORDER BY c.name",
            (session["user_id"],),
        )
    else:
        cur.execute("SELECT * FROM customers ORDER BY name")
    customers=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    if "SALESMAN" in roles and "OWNER" not in roles and "FACTORY ADMIN" not in roles:
        cur.execute(
            f"SELECT so.*,c.name AS customer_name,u.name AS salesman_name "
            f"FROM sales_orders so LEFT JOIN customers c ON c.id=so.customer_id "
            f"LEFT JOIN users u ON u.id=so.salesman_id WHERE so.salesman_id={p} "
            f"ORDER BY so.order_date DESC,so.id DESC",
            (session["user_id"],),
        )
    else:
        cur.execute(
            "SELECT so.*,c.name AS customer_name,u.name AS salesman_name "
            "FROM sales_orders so LEFT JOIN customers c ON c.id=so.customer_id "
            "LEFT JOIN users u ON u.id=so.salesman_id ORDER BY so.order_date DESC,so.id DESC"
        )
    orders=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT i.*,c.name AS customer_name FROM invoices i "
        "LEFT JOIN customers c ON c.id=i.customer_id ORDER BY i.invoice_date DESC,i.id DESC"
    )
    invoices=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT cp.*,c.name AS customer_name,i.invoice_number "
        "FROM customer_payments cp LEFT JOIN customers c ON c.id=cp.customer_id "
        "LEFT JOIN invoices i ON i.id=cp.invoice_id ORDER BY cp.payment_date DESC,cp.id DESC"
    )
    payments=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name,selling_price_paise,gst_percent FROM products WHERE is_active=1 ORDER BY name")
    products=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM sales_orders")
    row=cur.fetchone(); order_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM sales_orders WHERE status='SUBMITTED'")
    row=cur.fetchone(); submitted_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM invoices")
    row=cur.fetchone(); invoice_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM customer_payments")
    row=cur.fetchone(); payment_count=dict(row)["c"] if db.is_postgres else row[0]
    con.close()
    return render_template("modules/sales_dashboard.html",customers=customers,orders=orders,invoices=invoices,
                           payments=payments,products=products,order_count=order_count,submitted_count=submitted_count,
                           invoice_count=invoice_count,payment_count=payment_count)


@modules_bp.route("/sales/customers/new",methods=["GET","POST"])
@require_login
def sales_customer_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    if request.method=="POST":
        code=request.form.get("code","").strip().upper()
        name=request.form.get("name","").strip()
        contact=request.form.get("contact_person","").strip()
        phone=request.form.get("phone","").strip()
        email=request.form.get("email","").strip().lower()
        gstin=request.form.get("gstin","").strip().upper()
        address=request.form.get("address","").strip()
        if not code or not name:
            con.close(); flash("Customer code and name are required.","danger"); return redirect(url_for("modules.sales_customer_create"))
        try:
            credit_limit=int(request.form.get("credit_limit_paise","0"))
            if credit_limit<0: raise ValueError
        except ValueError:
            con.close(); flash("Credit limit cannot be negative.","danger"); return redirect(url_for("modules.sales_customer_create"))
        try:
            cur.execute(
                f"INSERT INTO customers(code,name,contact_person,phone,email,gstin,address,credit_limit_paise,status) "
                f"VALUES({p},{p},{p},{p},{p},{p},{p},{p},'ACTIVE')",
                (code,name,contact,phone,email,gstin,address,credit_limit),
            )
            con.commit()
            if db.is_postgres:
                cur.execute("SELECT id FROM customers WHERE code=%s",(code,))
                customer_id=cur.fetchone()["id"]
            else:
                customer_id=cur.lastrowid
            con.close()
            __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Sales",str(customer_id),new_value=name)
            flash("Customer created.","success")
            return redirect(url_for("modules.sales_dashboard"))
        except Exception:
            con.rollback(); con.close(); flash("Customer code already exists.","danger")
            return redirect(url_for("modules.sales_customer_create"))
    con.close()
    return render_template("modules/customer_form.html",customer=None)


@modules_bp.post("/sales/orders")
@require_login
def sales_order_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []) and "SALESMAN" not in session.get("roles", []):
        abort(403)
    customer_id=request.form.get("customer_id")
    product_id=request.form.get("product_id")
    quantity=request.form.get("quantity","0")
    order_date=request.form.get("order_date","").strip()
    notes=request.form.get("notes","").strip()
    if not customer_id or not product_id or not order_date:
        flash("Customer, product and order date are required.","danger"); return redirect(url_for("modules.sales_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    if "SALESMAN" in session.get("roles",[]) and "OWNER" not in session.get("roles",[]) and "FACTORY ADMIN" not in session.get("roles",[]):
        cur.execute(f"SELECT 1 FROM customers WHERE id={p} AND assigned_salesman_id={p}",(customer_id,session["user_id"]))
        if not cur.fetchone():
            con.close(); abort(403)
    try:
        quantity=float(quantity)
        if quantity<=0: raise ValueError
    except ValueError:
        con.close(); flash("Order quantity must be positive.","danger"); return redirect(url_for("modules.sales_dashboard"))
    cur.execute(f"SELECT selling_price_paise,gst_percent FROM products WHERE id={p} AND is_active=1",(product_id,))
    product=cur.fetchone()
    if not product:
        con.close(); flash("Product is unavailable.","danger"); return redirect(url_for("modules.sales_dashboard"))
    unit_price=dict(product)["selling_price_paise"] if db.is_postgres else product["selling_price_paise"]
    gst_percent=dict(product)["gst_percent"] if db.is_postgres else product["gst_percent"]
    subtotal=int(round(quantity*unit_price)); gst=int(round(subtotal*float(gst_percent)/100)); total=subtotal+gst
    order_number=f"SO-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO sales_orders(order_number,customer_id,salesman_id,order_date,status,subtotal_paise,gst_paise,total_paise,notes) "
        f"VALUES({p},{p},{p},{p},'SUBMITTED',{p},{p},{p},{p})",
        (order_number,customer_id,session["user_id"],order_date,subtotal,gst,total,notes),
    )
    if db.is_postgres:
        cur.execute("SELECT id FROM sales_orders WHERE order_number=%s",(order_number,))
        order_id=cur.fetchone()["id"]
    else:
        order_id=cur.lastrowid
    cur.execute(
        f"INSERT INTO sales_order_items(sales_order_id,product_id,quantity,unit_price_paise,gst_percent) "
        f"VALUES({p},{p},{p},{p},{p})",
        (order_id,product_id,quantity,unit_price,gst_percent),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Sales",str(order_id),new_value=order_number)
    flash("Sales order submitted.","success")
    return redirect(url_for("modules.sales_dashboard"))


@modules_bp.post("/sales/orders/<int:order_id>/approve")
@require_login
def sales_order_approve(order_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT status FROM sales_orders WHERE id={p}",(order_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    status=dict(row)["status"] if db.is_postgres else row[0]
    if status!="SUBMITTED":
        con.close(); flash("Only submitted orders can be approved.","danger"); return redirect(url_for("modules.sales_dashboard"))
    cur.execute(f"UPDATE sales_orders SET status='APPROVED' WHERE id={p}",(order_id,))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("APPROVE","Sales",str(order_id),new_value="Approved")
    flash("Sales order approved.","success")
    return redirect(url_for("modules.sales_dashboard"))


@modules_bp.post("/sales/orders/<int:order_id>/invoice")
@require_login
def sales_invoice_create(order_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT * FROM sales_orders WHERE id={p}",(order_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    order=dict(row) if db.is_postgres else dict(row)
    if order["status"]!="APPROVED":
        con.close(); flash("Only approved sales orders can be invoiced.","danger"); return redirect(url_for("modules.sales_dashboard"))
    invoice_number=f"INV-{now().strftime('%Y%m%d-%H%M%S')}"
    subtotal=int(order["subtotal_paise"]); gst=int(order["gst_paise"])
    cur.execute(
        f"INSERT INTO invoices(invoice_number,sales_order_id,customer_id,invoice_date,status,subtotal_paise,cgst_paise,sgst_paise,igst_paise,total_paise,outstanding_paise) "
        f"VALUES({p},{p},{p},CURRENT_TIMESTAMP,'POSTED',{p},{p},{p},0,{p},{p})",
        (invoice_number,order_id,order["customer_id"],subtotal,gst//2,gst-gst//2,subtotal+gst,subtotal+gst),
    )
    if db.is_postgres:
        cur.execute("SELECT id FROM invoices WHERE invoice_number=%s",(invoice_number,))
        invoice_id=cur.fetchone()["id"]
    else:
        invoice_id=cur.lastrowid
    cur.execute(f"UPDATE sales_orders SET status='INVOICED' WHERE id={p}",(order_id,))
    cur.execute(f"UPDATE customers SET outstanding_paise=outstanding_paise+{p} WHERE id={p}",(subtotal+gst,order["customer_id"]))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Sales",str(invoice_id),new_value=invoice_number)
    flash("GST invoice generated.","success")
    return redirect(url_for("modules.sales_dashboard"))


@modules_bp.post("/sales/payments")
@require_login
def sales_payment_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    invoice_id=request.form.get("invoice_id")
    amount=request.form.get("amount_paise","0")
    payment_method=request.form.get("payment_method","").strip()
    payment_date=request.form.get("payment_date","").strip()
    reference=request.form.get("reference_number","").strip()
    try:
        amount=int(amount)
        if amount<=0: raise ValueError
    except ValueError:
        flash("Payment amount must be positive.","danger"); return redirect(url_for("modules.sales_dashboard"))
    if not invoice_id or not payment_method or not payment_date:
        flash("Invoice, method and payment date are required.","danger"); return redirect(url_for("modules.sales_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT customer_id,outstanding_paise FROM invoices WHERE id={p}",(invoice_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    customer_id=dict(row)["customer_id"] if db.is_postgres else row[0]
    outstanding=dict(row)["outstanding_paise"] if db.is_postgres else row[1]
    if amount>outstanding:
        con.close(); flash("Payment cannot exceed outstanding invoice balance.","danger"); return redirect(url_for("modules.sales_dashboard"))
    receipt_number=f"RCT-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO customer_payments(receipt_number,customer_id,invoice_id,amount_paise,payment_method,payment_date,reference_number,recorded_by) "
        f"VALUES({p},{p},{p},{p},{p},{p},{p},{p})",
        (receipt_number,customer_id,invoice_id,amount,payment_method,payment_date,reference,session["user_id"]),
    )
    cur.execute(f"UPDATE invoices SET outstanding_paise=outstanding_paise-{p} WHERE id={p}",(amount,invoice_id))
    cur.execute(f"SELECT outstanding_paise FROM customers WHERE id={p}",(customer_id,))
    customer_row=cur.fetchone()
    customer_outstanding=dict(customer_row)["outstanding_paise"] if db.is_postgres else customer_row[0]
    customer_outstanding=max(0,int(customer_outstanding or 0)-amount)
    cur.execute(f"UPDATE customers SET outstanding_paise={p} WHERE id={p}",(customer_outstanding,customer_id))
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Sales",receipt_number,new_value=f"Payment {amount} paise")
    flash("Customer payment recorded.","success")
    return redirect(url_for("modules.sales_dashboard"))


def finance_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "ACCOUNTANT / AUDITOR"})


def finance_mutation_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN"})


@modules_bp.get("/finance/workspace")
@require_login
def finance_dashboard():
    if not finance_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute("SELECT * FROM finance_accounts ORDER BY account_type,name")
    accounts=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT ft.*,fa.name AS account_name FROM finance_transactions ft "
        "LEFT JOIN finance_accounts fa ON fa.id=ft.account_id ORDER BY ft.transaction_date DESC,ft.id DESC"
    )
    transactions=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT * FROM expense_records ORDER BY expense_date DESC,id DESC")
    expenses=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM finance_accounts")
    row=cur.fetchone(); account_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM finance_transactions")
    row=cur.fetchone(); transaction_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM expense_records")
    row=cur.fetchone(); expense_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COALESCE(SUM(outstanding_paise),0) AS total FROM invoices")
    row=cur.fetchone(); receivable=dict(row)["total"] if db.is_postgres else row[0]
    cur.execute("SELECT COALESCE(SUM(amount_paise),0) AS total FROM expense_records")
    row=cur.fetchone(); expense_total=dict(row)["total"] if db.is_postgres else row[0]
    cur.execute("SELECT COALESCE(SUM(total_paise),0) AS total FROM sales_orders")
    row=cur.fetchone(); sales_total=dict(row)["total"] if db.is_postgres else row[0]
    con.close()
    return render_template("modules/finance_dashboard.html",accounts=accounts,transactions=transactions,expenses=expenses,
                           account_count=account_count,transaction_count=transaction_count,expense_count=expense_count,
                           receivable=receivable or 0,expense_total=expense_total or 0,sales_total=sales_total or 0)


@modules_bp.route("/finance/accounts",methods=["POST"])
@require_login
def finance_account_create():
    if not finance_mutation_allowed():
        abort(403)
    code=request.form.get("code","").strip().upper()
    name=request.form.get("name","").strip()
    account_type=request.form.get("account_type","ASSET").strip()
    opening=request.form.get("opening_balance_paise","0")
    if not code or not name:
        flash("Account code and name are required.","danger"); return redirect(url_for("modules.finance_dashboard"))
    try:
        opening=int(opening)
    except ValueError:
        flash("Opening balance must be an integer amount.","danger"); return redirect(url_for("modules.finance_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    try:
        cur.execute(
            f"INSERT INTO finance_accounts(code,name,account_type,opening_balance_paise) VALUES({p},{p},{p},{p})",
            (code,name,account_type,opening),
        )
        con.commit()
        if db.is_postgres:
            cur.execute("SELECT id FROM finance_accounts WHERE code=%s",(code,))
            account_id=cur.fetchone()["id"]
        else:
            account_id=cur.lastrowid
        con.close()
        __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Finance",str(account_id),new_value=name)
        flash("Finance account created.","success")
    except Exception:
        con.rollback(); con.close(); flash("Finance account code already exists.","danger")
    return redirect(url_for("modules.finance_dashboard"))


@modules_bp.route("/finance/transactions",methods=["POST"])
@require_login
def finance_transaction_create():
    if not finance_mutation_allowed():
        abort(403)
    account_id=request.form.get("account_id")
    transaction_type=request.form.get("transaction_type","DEBIT").strip()
    amount=request.form.get("amount_paise","0")
    description=request.form.get("description","").strip()
    transaction_date=request.form.get("transaction_date","").strip()
    if not account_id or not transaction_date:
        flash("Account and transaction date are required.","danger"); return redirect(url_for("modules.finance_dashboard"))
    try:
        amount=int(amount)
        if amount<=0: raise ValueError
    except ValueError:
        flash("Transaction amount must be positive.","danger"); return redirect(url_for("modules.finance_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    transaction_number=f"TXN-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO finance_transactions(transaction_number,account_id,transaction_type,amount_paise,reference_type,reference_id,description,transaction_date,created_by) "
        f"VALUES({p},{p},{p},{p},'MANUAL',NULL,{p},{p},{p})",
        (transaction_number,account_id,transaction_type,amount,description,transaction_date,session["user_id"]),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Finance",transaction_number,new_value=f"{transaction_type} {amount} paise")
    flash("Finance transaction recorded.","success")
    return redirect(url_for("modules.finance_dashboard"))


@modules_bp.route("/finance/expenses",methods=["POST"])
@require_login
def finance_expense_create():
    if not finance_mutation_allowed():
        abort(403)
    category=request.form.get("expense_category","").strip()
    amount=request.form.get("amount_paise","0")
    expense_date=request.form.get("expense_date","").strip()
    notes=request.form.get("notes","").strip()
    if not category or not expense_date:
        flash("Expense category and date are required.","danger"); return redirect(url_for("modules.finance_dashboard"))
    try:
        amount=int(amount)
        if amount<=0: raise ValueError
    except ValueError:
        flash("Expense amount must be positive.","danger"); return redirect(url_for("modules.finance_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        f"INSERT INTO expense_records(expense_category,amount_paise,expense_date,reference_type,reference_id,notes,created_by) "
        f"VALUES({p},{p},{p},'MANUAL',NULL,{p},{p})",
        (category,amount,expense_date,notes,session["user_id"]),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Finance","",new_value=f"{category}: {amount} paise")
    flash("Expense recorded.","success")
    return redirect(url_for("modules.finance_dashboard"))


def dispatch_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "WAREHOUSE STAFF", "SALESMAN"})


@modules_bp.get("/warehouse/workspace")
@require_login
def dispatch_dashboard():
    if not dispatch_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(
        "SELECT wd.*,i.invoice_number,c.name AS customer_name,w.name AS warehouse_name "
        "FROM warehouse_dispatches wd LEFT JOIN invoices i ON i.id=wd.invoice_id "
        "LEFT JOIN customers c ON c.id=i.customer_id LEFT JOIN warehouses w ON w.id=wd.warehouse_id "
        "ORDER BY wd.id DESC"
    )
    dispatches=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute(
        "SELECT i.*,c.name AS customer_name FROM invoices i "
        "LEFT JOIN customers c ON c.id=i.customer_id WHERE i.status='POSTED' ORDER BY i.invoice_date DESC"
    )
    invoices=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT id,name,status FROM warehouses WHERE status='ACTIVE' ORDER BY name")
    warehouses=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM warehouse_dispatches")
    row=cur.fetchone(); total=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM warehouse_dispatches WHERE status='AWAITING_PICKING'")
    row=cur.fetchone(); awaiting=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM warehouse_dispatches WHERE status='DISPATCHED'")
    row=cur.fetchone(); dispatched=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM warehouse_dispatches WHERE status='DELIVERED'")
    row=cur.fetchone(); delivered=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM warehouse_activities")
    row=cur.fetchone(); activity_count=dict(row)["c"] if db.is_postgres else row[0]
    con.close()
    return render_template("modules/dispatch_dashboard.html",dispatches=dispatches,invoices=invoices,
                           warehouses=warehouses,total=total,awaiting=awaiting,dispatched=dispatched,
                           delivered=delivered,activity_count=activity_count)


@modules_bp.post("/warehouse/dispatches")
@require_login
def dispatch_create():
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    invoice_id=request.form.get("invoice_id")
    sales_order_id=request.form.get("sales_order_id") or None
    warehouse_id=request.form.get("warehouse_id")
    if not invoice_id or not warehouse_id:
        flash("Invoice and warehouse are required.","danger"); return redirect(url_for("modules.dispatch_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT id,status FROM invoices WHERE id={p}",(invoice_id,))
    invoice=cur.fetchone()
    if not invoice:
        con.close(); abort(404)
    invoice_status=dict(invoice)["status"] if db.is_postgres else invoice[1]
    if invoice_status!="POSTED":
        con.close(); flash("Only posted invoices can create dispatches.","danger"); return redirect(url_for("modules.dispatch_dashboard"))
    if not sales_order_id:
        cur.execute(f"SELECT sales_order_id FROM invoices WHERE id={p}",(invoice_id,))
        row=cur.fetchone()
        sales_order_id=dict(row)["sales_order_id"] if db.is_postgres else row[0]
    dispatch_number=f"DSP-{now().strftime('%Y%m%d-%H%M%S')}"
    cur.execute(
        f"INSERT INTO warehouse_dispatches(dispatch_number,invoice_id,sales_order_id,warehouse_id,status) "
        f"VALUES({p},{p},{p},{p},'AWAITING_PICKING')",
        (dispatch_number,invoice_id,sales_order_id,warehouse_id),
    )
    if db.is_postgres:
        cur.execute("SELECT id FROM warehouse_dispatches WHERE dispatch_number=%s",(dispatch_number,))
        dispatch_id=cur.fetchone()["id"]
    else:
        dispatch_id=cur.lastrowid
    cur.execute(
        f"INSERT INTO warehouse_activities(activity_type,reference_type,reference_id,description,created_by) "
        f"VALUES('DISPATCH_CREATED','DISPATCH',{p},{p},{p})",
        (str(dispatch_id),dispatch_number,session["user_id"]),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("CREATE","Dispatch",str(dispatch_id),new_value=dispatch_number)
    flash("Dispatch created.","success")
    return redirect(url_for("modules.dispatch_dashboard"))


@modules_bp.post("/warehouse/dispatches/<int:dispatch_id>/transition")
@require_login
def dispatch_transition(dispatch_id):
    if "OWNER" not in session.get("roles", []) and "FACTORY ADMIN" not in session.get("roles", []):
        abort(403)
    next_status=request.form.get("status","").strip()
    vehicle=request.form.get("vehicle_number","").strip()
    driver=request.form.get("driver_name","").strip()
    dispatch_date=request.form.get("dispatch_date") or None
    delivery_date=request.form.get("delivery_date") or None
    proof=request.form.get("proof_of_delivery","").strip()
    remarks=request.form.get("remarks","").strip()
    if next_status not in {"PICKING","DISPATCHED","DELIVERED","CANCELLED"}:
        flash("Invalid dispatch status.","danger"); return redirect(url_for("modules.dispatch_dashboard"))
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    cur.execute(f"SELECT status FROM warehouse_dispatches WHERE id={p}",(dispatch_id,))
    row=cur.fetchone()
    if not row:
        con.close(); abort(404)
    current=dict(row)["status"] if db.is_postgres else row[0]
    allowed={
        "AWAITING_PICKING":{"PICKING","CANCELLED"},
        "PICKING":{"DISPATCHED","CANCELLED"},
        "DISPATCHED":{"DELIVERED","CANCELLED"},
        "DELIVERED":set(),
        "CANCELLED":set(),
    }
    if next_status not in allowed.get(current,set()):
        con.close(); flash(f"Cannot change dispatch status from {current} to {next_status}.","danger"); return redirect(url_for("modules.dispatch_dashboard"))
    cur.execute(
        f"UPDATE warehouse_dispatches SET status={p},vehicle_number={p},driver_name={p},dispatch_date={p},"
        f"delivery_date={p},proof_of_delivery={p},remarks={p} WHERE id={p}",
        (next_status,vehicle or None,driver or None,dispatch_date,delivery_date,proof or None,remarks or None,dispatch_id),
    )
    cur.execute(
        f"INSERT INTO warehouse_activities(activity_type,reference_type,reference_id,description,created_by) "
        f"VALUES({p},'DISPATCH',{p},{p},{p})",
        (f"DISPATCH_{next_status}",str(dispatch_id),f"Status changed from {current} to {next_status}",session["user_id"]),
    )
    con.commit(); con.close()
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("UPDATE","Dispatch",str(dispatch_id),previous_value=current,new_value=next_status)
    flash(f"Dispatch moved to {next_status}.","success")
    return redirect(url_for("modules.dispatch_dashboard"))


from flask import Response
import csv
import io


def reports_allowed():
    return bool(set(session.get("roles", [])) & {"OWNER", "FACTORY ADMIN", "ACCOUNTANT / AUDITOR", "PRODUCTION SUPERVISOR"})


@modules_bp.get("/reports/workspace")
@require_login
def reports_dashboard():
    if not reports_allowed():
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor(); p=db.placeholder()
    module=request.args.get("module","").strip()
    action=request.args.get("action","").strip()
    conditions=[]; params=[]
    if module:
        conditions.append(f"module={p}"); params.append(module)
    if action:
        conditions.append(f"action={p}"); params.append(action)
    where=" WHERE "+" AND ".join(conditions) if conditions else ""
    cur.execute(
        f"SELECT id,user_id,user_email,effective_context,action,module,record_id,previous_value,new_value,ip_address,created_at "
        f"FROM audit_logs{where} ORDER BY id DESC LIMIT 500",
        params,
    )
    audit_logs=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS c FROM production_batches")
    row=cur.fetchone(); batch_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM sales_orders")
    row=cur.fetchone(); order_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM invoices")
    row=cur.fetchone(); invoice_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM quality_inspections")
    row=cur.fetchone(); inspection_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM audit_logs")
    row=cur.fetchone(); audit_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT DISTINCT module FROM audit_logs WHERE module IS NOT NULL ORDER BY module")
    modules=[dict(row)["module"] if db.is_postgres else row["module"] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT action FROM audit_logs WHERE action IS NOT NULL ORDER BY action")
    actions=[dict(row)["action"] if db.is_postgres else row["action"] for row in cur.fetchall()]
    con.close()
    return render_template("modules/reports_dashboard.html",audit_logs=audit_logs,batch_count=batch_count,
                           order_count=order_count,invoice_count=invoice_count,inspection_count=inspection_count,
                           audit_count=audit_count,modules=modules,actions=actions,
                           selected_module=module,selected_action=action)


@modules_bp.get("/reports/export/audit.csv")
@require_login
def reports_audit_export():
    if "OWNER" not in session.get("roles",[]) and "FACTORY ADMIN" not in session.get("roles",[]) and "ACCOUNTANT / AUDITOR" not in session.get("roles",[]):
        abort(403)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor()
    cur.execute(
        "SELECT id,user_id,user_email,effective_context,action,module,record_id,previous_value,new_value,ip_address,created_at "
        "FROM audit_logs ORDER BY id DESC"
    )
    rows=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    output=io.StringIO(); writer=csv.DictWriter(output,fieldnames=["id","user_id","user_email","effective_context","action","module","record_id","previous_value","new_value","ip_address","created_at"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("EXPORT","Reports",new_value="Audit log CSV")
    return Response(output.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=audit_log.csv"})


@modules_bp.get("/reports/export/<report_type>.csv")
@require_login
def reports_data_export(report_type):
    if "OWNER" not in session.get("roles",[]) and "ACCOUNTANT / AUDITOR" not in session.get("roles",[]) and "FACTORY ADMIN" not in session.get("roles",[]):
        abort(403)
    report_queries={
        "production":"SELECT batch_number, batch_status, planned_quantity, actual_quantity, damaged_quantity, wastage_quantity, started_at, completed_at FROM production_batches",
        "sales":"SELECT order_number, order_date, status, subtotal_paise, gst_paise, total_paise FROM sales_orders",
        "purchasing":"SELECT order_number, order_date, status, total_paise FROM purchase_orders",
        "quality":"SELECT inspection_number, inspection_type, status, result, inspected_at FROM quality_inspections",
        "inventory":"SELECT item_type, item_id, warehouse_id, quantity, reserved_quantity, batch_lot FROM stock_items",
        "dispatch":"SELECT dispatch_number, status, vehicle_number, driver_name, dispatch_date, delivery_date FROM warehouse_dispatches",
    }
    query=report_queries.get(report_type)
    if not query:
        abort(404)
    db=current_app.extensions["database"]; con=db.connect(); cur=con.cursor()
    cur.execute(query)
    rows=[dict(row) if db.is_postgres else dict(row) for row in cur.fetchall()]
    con.close()
    output=io.StringIO()
    if rows:
        writer=csv.DictWriter(output,fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    else:
        output.write("No records")
    __import__("app.audit.service",fromlist=["add_audit"]).add_audit("EXPORT","Reports",new_value=f"{report_type} CSV")
    return Response(output.getvalue(),mimetype="text/csv",headers={"Content-Disposition":f"attachment; filename={report_type}_report.csv"})


@modules_bp.get("/<slug>")
@require_login
def module_dashboard(slug):
    if slug not in MODULES:
        abort(404)
    if slug == "labour":
        return redirect(url_for("modules.labour_dashboard"))
    if slug == "production-config":
        return redirect(url_for("modules.production_config_dashboard"))
    if slug == "machines":
        return redirect(url_for("modules.machines_dashboard"))
    if slug == "production":
        return redirect(url_for("modules.production_dashboard"))
    if slug == "purchasing":
        return redirect(url_for("modules.purchasing_dashboard"))
    if slug == "quality":
        return redirect(url_for("modules.quality_dashboard"))
    if slug == "maintenance":
        return redirect(url_for("modules.maintenance_dashboard"))
    if slug == "inventory":
        return redirect(url_for("modules.inventory_dashboard"))
    if slug == "sales":
        return redirect(url_for("modules.sales_dashboard"))
    if slug == "finance":
        return redirect(url_for("modules.finance_dashboard"))
    if slug == "warehouse":
        return redirect(url_for("modules.dispatch_dashboard"))
    if slug == "reports":
        return redirect(url_for("modules.reports_dashboard"))
    title, template_name, module_number = MODULES[slug]
    counts = {
        "departments": count_table("departments"), "products": count_table("products"),
        "machines": count_table("machines"), "employees": count_table("employees"),
        "suppliers": count_table("suppliers"), "customers": count_table("customers"),
        "stock": count_table("stock_items"), "batches": count_table("production_batches"),
        "orders": count_table("sales_orders"), "purchases": count_table("purchase_orders"),
        "inspections": count_table("quality_inspections"), "maintenance": count_table("maintenance_work_orders"),
        "dispatches": count_table("warehouse_dispatches"), "invoices": count_table("invoices"),
        "attendance": count_table("attendance"),
    }
    data = db_rows("departments", 100) if slug in {"labour", "production-config", "machines", "production", "quality", "maintenance", "inventory", "warehouse", "initialization"} else []
    return render_template("modules/dashboard.html", title=title, template_name=template_name,
                           module_number=module_number, slug=slug, counts=counts, data=data)


@modules_bp.get("/initialization/wizard")
@require_login
def initialization_wizard():
    if "OWNER" not in session.get("roles", []): abort(403)
    db = current_app.extensions["database"]
    con = db.connect(); cur = con.cursor()
    cur.execute("SELECT * FROM factory_initialization ORDER BY id DESC LIMIT 1")
    row = cur.fetchone(); con.close()
    initialization = dict(row) if db.is_postgres and row else (dict(row) if row else None)
    con = current_app.extensions["database"].connect(); cur = con.cursor()
    cur.execute("SELECT id,name,business_type,status FROM factory ORDER BY id LIMIT 1")
    factory_row = cur.fetchone(); con.close()
    factory = (dict(factory_row) if current_app.extensions["database"].is_postgres else dict(factory_row)) if factory_row else None
    return render_template("modules/initialization_wizard.html", initialization=initialization, factory=factory,
                           departments=db_rows("departments",100), products=db_rows("products",100),
                           machines=db_rows("machines",100), employees=db_rows("employees",100), shifts=db_rows("shifts",100))


@modules_bp.post("/initialization/complete")
@require_login
def initialization_complete():
    if "OWNER" not in session.get("roles", []): abort(403)
    db = current_app.extensions["database"]
    con = db.connect(); p = db.placeholder(); cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM departments WHERE department_type='PRODUCTION'")
    row=cur.fetchone(); production_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM products WHERE is_active=1")
    row=cur.fetchone(); product_count=dict(row)["c"] if db.is_postgres else row[0]
    cur.execute("SELECT COUNT(*) AS c FROM shifts WHERE is_active=1")
    row=cur.fetchone(); shift_count=dict(row)["c"] if db.is_postgres else row[0]
    if production_count < 1 or product_count < 1 or shift_count < 1:
        con.close()
        flash("Initialization cannot be completed: production departments, products and shifts are required.","danger")
        return redirect(url_for("modules.initialization_wizard"))
    initialization_now = now_iso()
    cur.execute(f"UPDATE factory_initialization SET status={p},owner_approved=1,approved_by={p},completed_at={p},wizard_progress=10 WHERE id=(SELECT id FROM factory_initialization ORDER BY id DESC LIMIT 1)", ("COMPLETED",session.get("user_id"),initialization_now))

    machine_templates = [
        ("MUR001","Murukku Extruder","Murukku Production","EXTRUDER",200),
        ("CHI001","Industrial Frying Machine","Potato Chips Production","FRYER",300),
        ("BAN001","Banana Chips Slicing Machine","Banana Chips Production","SLICER",250),
        ("MIX001","Ingredient Mixing Machine","Mixture Production","MIXER",180),
        ("MYS001","Industrial Cooking Vessel","Mysore Pak Production","COOKER",150),
    ]
    for code,name,department_name,machine_type,capacity in machine_templates:
        cur.execute(f"SELECT id FROM departments WHERE name={p}",(department_name,))
        department_row = cur.fetchone()
        department_id = (dict(department_row)["id"] if db.is_postgres else department_row[0]) if department_row else None
        if db.is_postgres:
            cur.execute("INSERT INTO machines(code,name,machine_type,department_id,status,capacity_per_hour) VALUES(%s,%s,%s,%s,'OPERATIONAL',%s) ON CONFLICT(code) DO NOTHING",(code,name,machine_type,department_id,capacity))
        else:
            cur.execute("INSERT OR IGNORE INTO machines(code,name,machine_type,department_id,status,capacity_per_hour) VALUES(?,?,?,?, 'OPERATIONAL',?)",(code,name,machine_type,department_id,capacity))

    worker_positions = [
        ("WRK-SUP-001","Production Supervisor","Murukku Production","PRODUCTION SUPERVISOR"),
        ("WRK-MIX-001","Dough Preparation Operator","Murukku Production","Dough Preparation"),
        ("WRK-FRY-001","Frying Operator","Potato Chips Production","Frying"),
        ("WRK-PKG-001","Packaging Operator","Banana Chips Production","Packaging"),
        ("WRK-QC-001","Quality Assistant","Quality Control","Quality Inspection"),
        ("WRK-MNT-001","Maintenance Assistant","Administration","Maintenance"),
    ]
    for code,name,department_name,designation in worker_positions:
        cur.execute(f"SELECT id FROM departments WHERE name={p}",(department_name,))
        department_row = cur.fetchone()
        department_id = (dict(department_row)["id"] if db.is_postgres else department_row[0]) if department_row else None
        if db.is_postgres:
            cur.execute("INSERT INTO employees(employee_code,name,employment_type,department_id,designation,status,nationality) VALUES(%s,%s,'PERMANENT',%s,%s,'VACANCY','Indian') ON CONFLICT(employee_code) DO NOTHING",(code,name,department_id,designation))
        else:
            cur.execute("INSERT OR IGNORE INTO employees(employee_code,name,employment_type,department_id,designation,status,nationality) VALUES(?,?,?,?, 'VACANCY','Indian')",(code,name,department_id,designation))
    con.commit(); con.close()
    flash("Factory configuration approved and activated.","success")
    return redirect(url_for("modules.module_dashboard",slug="initialization"))


@modules_bp.post("/initialization/save")
@require_login
def initialization_save():
    if "OWNER" not in session.get("roles", []): abort(403)
    progress=request.form.get("progress","1")
    factory_name=request.form.get("factory_name","Smart Food Manufacturing Factory").strip()
    business_type=request.form.get("business_type","South Indian Snacks Manufacturing").strip()
    if not factory_name:
        flash("Factory name is required.","danger"); return redirect(url_for("modules.initialization_wizard"))
    db=current_app.extensions["database"]; con=db.connect(); p=db.placeholder(); cur=con.cursor()
    cur.execute(f"UPDATE factory SET name={p},business_type={p} WHERE id=(SELECT id FROM factory ORDER BY id LIMIT 1)",(factory_name,business_type))
    cur.execute(f"UPDATE factory_initialization SET status={p},wizard_progress={p} WHERE id=(SELECT id FROM factory_initialization ORDER BY id DESC LIMIT 1)",("IN_PROGRESS",progress))
    con.commit(); con.close(); flash("Initialization progress saved.","success")
    return redirect(url_for("modules.initialization_wizard"))


@modules_bp.get("/<slug>/records")
@require_login
def records(slug):
    if slug not in MODULES:
        abort(404)
    title, _, module_number = MODULES[slug]
    table_map = {
        "labour": "employees", "production-config": "products", "machines": "machines",
        "production": "production_batches", "purchasing": "purchase_orders", "quality": "quality_inspections",
        "maintenance": "maintenance_work_orders", "inventory": "stock_items", "sales": "sales_orders",
        "finance": "finance_transactions", "warehouse": "warehouse_dispatches", "reports": "audit_logs",
        "initialization": "factory_initialization", "layout": "departments",
    }
    table = table_map.get(slug)
    rows = db_rows(table, 200) if table else []
    return render_template("modules/records.html", title=title, module_number=module_number, rows=rows, slug=slug)
