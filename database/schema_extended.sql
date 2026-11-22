CREATE TABLE IF NOT EXISTS departments (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 department_type TEXT NOT NULL DEFAULT 'PRODUCTION', status TEXT NOT NULL DEFAULT 'ACTIVE',
 description TEXT, area_x INTEGER, area_y INTEGER, area_width INTEGER, area_height INTEGER
);
CREATE TABLE IF NOT EXISTS products (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 category TEXT, packet_weight NUMERIC DEFAULT 0, unit TEXT DEFAULT 'packet', selling_unit TEXT DEFAULT 'packet',
 department_id INTEGER REFERENCES departments(id), is_active INTEGER DEFAULT 1,
 standard_batch_output INTEGER DEFAULT 0, daily_target_batches INTEGER DEFAULT 0,
 selling_price_paise INTEGER DEFAULT 0, gst_percent NUMERIC DEFAULT 5
);
CREATE TABLE IF NOT EXISTS recipes (
 id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
 version TEXT NOT NULL DEFAULT 'V1', batch_quantity NUMERIC DEFAULT 1, is_active INTEGER DEFAULT 1,
 yield_packets INTEGER DEFAULT 0, notes TEXT, UNIQUE(product_id,version)
);
CREATE TABLE IF NOT EXISTS recipe_items (
 id SERIAL PRIMARY KEY, recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
 item_name TEXT NOT NULL, item_category TEXT DEFAULT 'RAW_MATERIAL', quantity NUMERIC NOT NULL, unit TEXT NOT NULL,
 wastage_percent NUMERIC DEFAULT 0
);
CREATE TABLE IF NOT EXISTS production_stages (
 id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
 stage_order INTEGER NOT NULL, stage_name TEXT NOT NULL, department_id INTEGER REFERENCES departments(id),
 UNIQUE(product_id,stage_order)
);
CREATE TABLE IF NOT EXISTS shifts (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 start_time TEXT NOT NULL, end_time TEXT NOT NULL, break_minutes INTEGER DEFAULT 30, is_active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS machines (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 machine_type TEXT, department_id INTEGER REFERENCES departments(id), capacity_per_hour NUMERIC DEFAULT 0,
 capacity_unit TEXT DEFAULT 'units', status TEXT DEFAULT 'OPERATIONAL', hourly_cost_paise INTEGER DEFAULT 0,
 last_maintenance_at TEXT, next_maintenance_at TEXT
);
CREATE TABLE IF NOT EXISTS machine_downtime (
 id SERIAL PRIMARY KEY, machine_id INTEGER NOT NULL REFERENCES machines(id),
 started_at TEXT NOT NULL, ended_at TEXT, reason TEXT, status TEXT DEFAULT 'OPEN'
);
CREATE TABLE IF NOT EXISTS employees (
 id SERIAL PRIMARY KEY, employee_code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 gender TEXT, phone TEXT, email TEXT, address TEXT, date_joining TEXT,
 employment_type TEXT DEFAULT 'PERMANENT', department_id INTEGER REFERENCES departments(id),
 designation TEXT, production_section TEXT, production_stage TEXT, shift_id INTEGER REFERENCES shifts(id),
 skill_category TEXT, experience_years NUMERIC DEFAULT 0, salary_type TEXT DEFAULT 'MONTHLY',
 salary_paise INTEGER DEFAULT 0, status TEXT DEFAULT 'ACTIVE', emergency_contact TEXT, remarks TEXT,
 photo_url TEXT, nationality TEXT, state TEXT, district TEXT, caste TEXT, religion TEXT,
 blood_group TEXT, date_of_birth TEXT, aadhaar_number TEXT, pan_number TEXT,
 voter_id_number TEXT, ration_card_number TEXT, id_card_type TEXT, id_card_number TEXT,
 permanent_address TEXT, emergency_contact_name TEXT
);
CREATE TABLE IF NOT EXISTS attendance (
 id SERIAL PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(id),
 attendance_date TEXT NOT NULL, status TEXT NOT NULL, shift_id INTEGER REFERENCES shifts(id),
 check_in TEXT, check_out TEXT, overtime_minutes INTEGER DEFAULT 0, total_working_minutes INTEGER DEFAULT 0,
 break_minutes INTEGER DEFAULT 30, standard_minutes INTEGER DEFAULT 480, leave_type TEXT,
 UNIQUE(employee_id,attendance_date)
);
CREATE TABLE IF NOT EXISTS employee_leave (
 id SERIAL PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(id),
 leave_type TEXT NOT NULL, from_date TEXT NOT NULL, to_date TEXT NOT NULL, status TEXT DEFAULT 'PENDING', reason TEXT
);
CREATE TABLE IF NOT EXISTS raw_materials (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 category TEXT, unit TEXT NOT NULL, reorder_level NUMERIC DEFAULT 0,
 standard_cost_paise INTEGER DEFAULT 0, expiry_tracking INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS warehouses (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 warehouse_type TEXT NOT NULL, address TEXT, capacity_units NUMERIC DEFAULT 0, status TEXT DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS warehouse_zones (
 id SERIAL PRIMARY KEY, warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
 code TEXT NOT NULL, name TEXT NOT NULL, zone_type TEXT, capacity_units NUMERIC DEFAULT 0, UNIQUE(warehouse_id,code)
);
CREATE TABLE IF NOT EXISTS stock_items (
 id SERIAL PRIMARY KEY, item_type TEXT NOT NULL, item_id INTEGER NOT NULL,
 warehouse_id INTEGER REFERENCES warehouses(id), quantity NUMERIC NOT NULL DEFAULT 0,
 reserved_quantity NUMERIC NOT NULL DEFAULT 0, batch_lot TEXT, expiry_date TEXT,
 UNIQUE(item_type,item_id,warehouse_id,batch_lot)
);
CREATE TABLE IF NOT EXISTS stock_ledger (
 id SERIAL PRIMARY KEY, item_type TEXT NOT NULL, item_id INTEGER NOT NULL,
 warehouse_id INTEGER REFERENCES warehouses(id), movement_type TEXT NOT NULL, quantity NUMERIC NOT NULL,
 balance_quantity NUMERIC NOT NULL, reference_type TEXT, reference_id TEXT, remarks TEXT,
 created_by INTEGER REFERENCES users(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS stock_adjustments (
 id SERIAL PRIMARY KEY, item_type TEXT NOT NULL, item_id INTEGER NOT NULL,
 warehouse_id INTEGER REFERENCES warehouses(id), adjustment NUMERIC NOT NULL, reason TEXT NOT NULL,
 status TEXT DEFAULT 'PENDING', approved_by INTEGER REFERENCES users(id), created_by INTEGER REFERENCES users(id), created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS suppliers (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 contact_person TEXT, phone TEXT, email TEXT, gstin TEXT, address TEXT, credit_days INTEGER DEFAULT 0,
 outstanding_paise INTEGER DEFAULT 0, status TEXT DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS purchase_orders (
 id SERIAL PRIMARY KEY, order_number TEXT UNIQUE NOT NULL, supplier_id INTEGER REFERENCES suppliers(id),
 order_date TEXT NOT NULL, status TEXT DEFAULT 'DRAFT', total_paise INTEGER DEFAULT 0,
 notes TEXT, created_by INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS purchase_order_items (
 id SERIAL PRIMARY KEY, purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
 item_type TEXT DEFAULT 'RAW_MATERIAL', item_id INTEGER NOT NULL, quantity NUMERIC NOT NULL,
 unit TEXT NOT NULL, unit_price_paise INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS goods_receipts (
 id SERIAL PRIMARY KEY, receipt_number TEXT UNIQUE NOT NULL, purchase_order_id INTEGER REFERENCES purchase_orders(id),
 received_date TEXT NOT NULL, status TEXT DEFAULT 'PENDING_QC', warehouse_id INTEGER REFERENCES warehouses(id),
 created_by INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS production_plans (
 id SERIAL PRIMARY KEY, plan_date TEXT NOT NULL, department_id INTEGER REFERENCES departments(id),
 product_id INTEGER REFERENCES products(id), planned_quantity INTEGER NOT NULL, planned_batches INTEGER DEFAULT 0,
 shift_id INTEGER REFERENCES shifts(id), priority INTEGER DEFAULT 1, status TEXT DEFAULT 'PLANNED',
 notes TEXT, created_by INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS production_batches (
 id SERIAL PRIMARY KEY, batch_number TEXT UNIQUE NOT NULL, plan_id INTEGER REFERENCES production_plans(id),
 product_id INTEGER NOT NULL REFERENCES products(id), department_id INTEGER REFERENCES departments(id),
 shift_id INTEGER REFERENCES shifts(id), recipe_id INTEGER REFERENCES recipes(id), batch_status TEXT DEFAULT 'PLANNED',
 planned_quantity INTEGER DEFAULT 0, actual_quantity NUMERIC DEFAULT 0, damaged_quantity NUMERIC DEFAULT 0,
 wastage_quantity NUMERIC DEFAULT 0, started_at TEXT, completed_at TEXT, supervisor_id INTEGER,
 reason TEXT, created_by INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS batch_stage_records (
 id SERIAL PRIMARY KEY, batch_id INTEGER NOT NULL REFERENCES production_batches(id),
 stage_id INTEGER REFERENCES production_stages(id), status TEXT DEFAULT 'PENDING', started_at TEXT, completed_at TEXT,
 machine_id INTEGER REFERENCES machines(id), employee_id INTEGER REFERENCES employees(id), notes TEXT
);
CREATE TABLE IF NOT EXISTS batch_material_issues (
 id SERIAL PRIMARY KEY, batch_id INTEGER NOT NULL REFERENCES production_batches(id),
 material_id INTEGER NOT NULL REFERENCES raw_materials(id), quantity NUMERIC NOT NULL, unit TEXT NOT NULL,
 issued_by INTEGER REFERENCES users(id), issued_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS quality_inspections (
 id SERIAL PRIMARY KEY, inspection_number TEXT UNIQUE NOT NULL, inspection_type TEXT NOT NULL,
 reference_type TEXT, reference_id TEXT, product_id INTEGER REFERENCES products(id),
 inspector_id INTEGER REFERENCES users(id), status TEXT DEFAULT 'PENDING', result TEXT,
 parameters TEXT, notes TEXT, inspected_at TEXT
);
CREATE TABLE IF NOT EXISTS quality_complaints (
 id SERIAL PRIMARY KEY, complaint_number TEXT UNIQUE NOT NULL, customer_name TEXT,
 product_id INTEGER REFERENCES products(id), complaint_type TEXT, description TEXT, severity TEXT DEFAULT 'MEDIUM',
 status TEXT DEFAULT 'OPEN', created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS capa_records (
 id SERIAL PRIMARY KEY, complaint_id INTEGER REFERENCES quality_complaints(id),
 corrective_action TEXT, preventive_action TEXT, owner TEXT, due_date TEXT, status TEXT DEFAULT 'OPEN'
);
CREATE TABLE IF NOT EXISTS maintenance_plans (
 id SERIAL PRIMARY KEY, machine_id INTEGER NOT NULL REFERENCES machines(id),
 plan_type TEXT DEFAULT 'PREVENTIVE', frequency_days INTEGER NOT NULL, last_done_at TEXT, next_due_at TEXT,
 status TEXT DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS maintenance_work_orders (
 id SERIAL PRIMARY KEY, work_order_number TEXT UNIQUE NOT NULL, machine_id INTEGER REFERENCES machines(id),
 work_order_type TEXT DEFAULT 'CORRECTIVE', title TEXT NOT NULL, description TEXT,
 assigned_employee_id INTEGER REFERENCES employees(id), status TEXT DEFAULT 'OPEN', priority TEXT DEFAULT 'MEDIUM',
 opened_at TIMESTAMPTZ DEFAULT NOW(), completed_at TEXT, expense_paise INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS customers (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 contact_person TEXT, phone TEXT, email TEXT, gstin TEXT, address TEXT,
 credit_limit_paise INTEGER DEFAULT 0, outstanding_paise INTEGER DEFAULT 0, assigned_salesman_id INTEGER REFERENCES users(id), status TEXT DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS prices (
 id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
 unit_price_paise INTEGER NOT NULL, effective_from TEXT NOT NULL, effective_to TEXT
);
CREATE TABLE IF NOT EXISTS sales_orders (
 id SERIAL PRIMARY KEY, order_number TEXT UNIQUE NOT NULL, customer_id INTEGER REFERENCES customers(id),
 salesman_id INTEGER REFERENCES users(id), order_date TEXT NOT NULL, status TEXT DEFAULT 'SUBMITTED',
 subtotal_paise INTEGER DEFAULT 0, gst_paise INTEGER DEFAULT 0, total_paise INTEGER DEFAULT 0,
 notes TEXT, offline_uuid TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS sales_order_items (
 id SERIAL PRIMARY KEY, sales_order_id INTEGER NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
 product_id INTEGER NOT NULL REFERENCES products(id), quantity NUMERIC NOT NULL, unit_price_paise INTEGER NOT NULL,
 gst_percent NUMERIC DEFAULT 5
);
CREATE TABLE IF NOT EXISTS invoices (
 id SERIAL PRIMARY KEY, invoice_number TEXT UNIQUE NOT NULL, sales_order_id INTEGER REFERENCES sales_orders(id),
 customer_id INTEGER REFERENCES customers(id), invoice_date TEXT NOT NULL, status TEXT DEFAULT 'POSTED',
 subtotal_paise INTEGER DEFAULT 0, cgst_paise INTEGER DEFAULT 0, sgst_paise INTEGER DEFAULT 0,
 igst_paise INTEGER DEFAULT 0, total_paise INTEGER DEFAULT 0, outstanding_paise INTEGER DEFAULT 0,
 cancellation_reason TEXT
);
CREATE TABLE IF NOT EXISTS customer_payments (
 id SERIAL PRIMARY KEY, receipt_number TEXT UNIQUE NOT NULL, customer_id INTEGER REFERENCES customers(id),
 invoice_id INTEGER REFERENCES invoices(id), amount_paise INTEGER NOT NULL, payment_method TEXT,
 payment_date TEXT NOT NULL, reference_number TEXT, recorded_by INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS finance_accounts (
 id SERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 account_type TEXT NOT NULL, opening_balance_paise INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS finance_transactions (
 id SERIAL PRIMARY KEY, transaction_number TEXT UNIQUE NOT NULL, account_id INTEGER REFERENCES finance_accounts(id),
 transaction_type TEXT NOT NULL, amount_paise INTEGER NOT NULL, reference_type TEXT, reference_id TEXT,
 description TEXT, transaction_date TEXT NOT NULL, created_by INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS expense_records (
 id SERIAL PRIMARY KEY, expense_category TEXT NOT NULL, amount_paise INTEGER NOT NULL,
 expense_date TEXT NOT NULL, reference_type TEXT, reference_id TEXT, notes TEXT,
 created_by INTEGER REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS warehouse_dispatches (
 id SERIAL PRIMARY KEY, dispatch_number TEXT UNIQUE NOT NULL, invoice_id INTEGER REFERENCES invoices(id),
 sales_order_id INTEGER REFERENCES sales_orders(id), warehouse_id INTEGER REFERENCES warehouses(id),
 status TEXT DEFAULT 'AWAITING_PICKING', vehicle_number TEXT, driver_name TEXT, dispatch_date TEXT,
 delivery_date TEXT, proof_of_delivery TEXT, damage_quantity NUMERIC DEFAULT 0, remarks TEXT
);
CREATE TABLE IF NOT EXISTS warehouse_activities (
 id SERIAL PRIMARY KEY, activity_type TEXT NOT NULL, reference_type TEXT, reference_id TEXT,
 description TEXT, created_by INTEGER REFERENCES users(id), created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS factory_initialization (
 id SERIAL PRIMARY KEY, factory_name TEXT, status TEXT DEFAULT 'NOT_STARTED', template_version TEXT DEFAULT '1.0',
 owner_approved INTEGER DEFAULT 0, approved_by INTEGER REFERENCES users(id), completed_at TEXT,
 wizard_progress INTEGER DEFAULT 0, draft_data TEXT
);
CREATE TABLE IF NOT EXISTS configuration_history (
 id SERIAL PRIMARY KEY, version TEXT NOT NULL, action TEXT NOT NULL,
 changed_by INTEGER REFERENCES users(id), record_summary TEXT, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS factory (
 id SERIAL PRIMARY KEY, name TEXT NOT NULL, business_type TEXT,
 address TEXT, status TEXT NOT NULL DEFAULT 'ACTIVE', created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS production_sections (
 id SERIAL PRIMARY KEY, department_id INTEGER UNIQUE REFERENCES departments(id) ON DELETE CASCADE,
 code TEXT UNIQUE NOT NULL, product_id INTEGER REFERENCES products(id), daily_target_batches INTEGER DEFAULT 0,
 current_status TEXT DEFAULT 'OPERATIONAL'
);
CREATE TABLE IF NOT EXISTS department_status_history (
 id SERIAL PRIMARY KEY, department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
 previous_status TEXT, new_status TEXT NOT NULL, changed_by INTEGER REFERENCES users(id),
 changed_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS department_assignments (
 id SERIAL PRIMARY KEY, department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 assigned_role TEXT, UNIQUE(department_id,user_id)
);
CREATE TABLE IF NOT EXISTS factory_layout_positions (
 department_id INTEGER PRIMARY KEY REFERENCES departments(id) ON DELETE CASCADE,
 area_x INTEGER NOT NULL DEFAULT 0, area_y INTEGER NOT NULL DEFAULT 0,
 area_width INTEGER NOT NULL DEFAULT 200, area_height INTEGER NOT NULL DEFAULT 150,
 display_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS production_targets (
 id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
 shift_id INTEGER REFERENCES shifts(id), target_date TEXT, target_batches INTEGER NOT NULL DEFAULT 0,
 reason TEXT, approval_status TEXT NOT NULL DEFAULT 'DRAFT',
 UNIQUE(product_id,shift_id,target_date)
);
CREATE TABLE IF NOT EXISTS voice_recordings (
 id SERIAL PRIMARY KEY, recording_code TEXT UNIQUE NOT NULL,
 title TEXT NOT NULL, original_audio_path TEXT NOT NULL, mime_type TEXT,
 employee_id INTEGER REFERENCES users(id), department_id INTEGER REFERENCES departments(id),
 location_id INTEGER, module_name TEXT, related_record_type TEXT, related_record_id TEXT,
 language TEXT DEFAULT 'UNKNOWN', recording_date TEXT NOT NULL, start_time TEXT,
 end_time TEXT, duration_seconds INTEGER DEFAULT 0, server_timestamp TEXT NOT NULL,
 processing_status TEXT DEFAULT 'PENDING', confirmation_status TEXT DEFAULT 'PENDING',
 archive_status TEXT DEFAULT 'ACTIVE', retention_until TEXT, remarks TEXT
);
CREATE TABLE IF NOT EXISTS voice_transcriptions (
 id SERIAL PRIMARY KEY, recording_id INTEGER NOT NULL REFERENCES voice_recordings(id) ON DELETE CASCADE,
 transcript_text TEXT NOT NULL, is_original INTEGER DEFAULT 0, revision_number INTEGER DEFAULT 1,
 edited_by INTEGER REFERENCES users(id), edited_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS voice_extracted_entities (
 id SERIAL PRIMARY KEY, recording_id INTEGER NOT NULL REFERENCES voice_recordings(id) ON DELETE CASCADE,
 entity_key TEXT NOT NULL, entity_value TEXT, confidence REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS voice_record_links (
 id SERIAL PRIMARY KEY, recording_id INTEGER NOT NULL REFERENCES voice_recordings(id) ON DELETE CASCADE,
 target_module TEXT NOT NULL, target_record_type TEXT, target_record_id TEXT,
 UNIQUE(recording_id,target_module,target_record_type,target_record_id)
);
CREATE TABLE IF NOT EXISTS voice_processing_history (
 id SERIAL PRIMARY KEY, recording_id INTEGER NOT NULL REFERENCES voice_recordings(id) ON DELETE CASCADE,
 action TEXT NOT NULL, status TEXT, detail TEXT, performed_by INTEGER REFERENCES users(id),
 performed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS voice_permissions (
 id SERIAL PRIMARY KEY, recording_id INTEGER NOT NULL REFERENCES voice_recordings(id) ON DELETE CASCADE,
 role_name TEXT, user_id INTEGER REFERENCES users(id), permission TEXT NOT NULL,
 UNIQUE(recording_id,role_name,user_id,permission)
);
CREATE TABLE IF NOT EXISTS voice_shift_handovers (
 id SERIAL PRIMARY KEY, recording_id INTEGER NOT NULL REFERENCES voice_recordings(id) ON DELETE CASCADE,
 department_id INTEGER REFERENCES departments(id), shift_id INTEGER REFERENCES shifts(id),
 handover_date TEXT NOT NULL, supervisor_id INTEGER REFERENCES users(id),
 structured_text TEXT, status TEXT DEFAULT 'DRAFT'
);
