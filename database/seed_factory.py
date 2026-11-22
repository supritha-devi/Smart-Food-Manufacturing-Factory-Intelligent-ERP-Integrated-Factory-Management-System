import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Database, init_schema

DEPARTMENTS = [
("PROD001","Murukku Production","PRODUCTION"),("PROD002","Potato Chips Production","PRODUCTION"),
("PROD003","Banana Chips Production","PRODUCTION"),("PROD004","Mixture Production","PRODUCTION"),
("PROD005","Mysore Pak Production","PRODUCTION"),("WH001","Raw Material Warehouse","WAREHOUSE"),
("WH002","Packaging Warehouse","WAREHOUSE"),("WH003","Finished Goods Warehouse","WAREHOUSE"),
("QC001","Quality Control","QUALITY_CONTROL"),("DISP001","Dispatch","DISPATCH"),("ADMIN001","Administration","ADMINISTRATION")]

PRODUCTS = [
("PRD001","Murukku","Snack","kg","packet",200,3),("PRD002","Potato Chips","Snack","kg","packet",200,2),
("PRD003","Banana Chips","Snack","kg","packet",200,2),("PRD004","Mixture","Snack","kg","packet",200,2),
("PRD005","Mysore Pak","Sweet","kg","packet",200,2)]

SHIFTS=[("A","Shift A","06:00","14:00",30),("B","Shift B","14:00","22:00",30),("C","Shift C","22:00","06:00",30)]

STAGES={
"Murukku":["Dough Preparation","Mixing","Shaping","Frying","Cooling","Quality Checking","Packaging"],
"Potato Chips":["Washing","Peeling","Slicing","Preparation","Frying","De-oiling","Seasoning","Quality Checking","Packaging"],
"Banana Chips":["Preparation","Peeling","Slicing","Frying","De-oiling","Quality Checking","Packaging"],
"Mixture":["Ingredient Preparation","Mixing","Frying","Ingredient Mixing","Quality Checking","Packaging"],
"Mysore Pak":["Ingredient Preparation","Mixing","Cooking","Cooling","Cutting","Quality Checking","Packaging"]}

MATERIALS=[("RM001","Rice Flour","RAW_MATERIAL","kg",100,70),("RM002","Cooking Oil","RAW_MATERIAL","litre",50,180),
("RM003","Salt","RAW_MATERIAL","kg",20,25),("RM004","Spices","RAW_MATERIAL","kg",10,300),("RM005","Packaging Pouch","PACKAGING","piece",5000,3),("RM006","Carton","PACKAGING","piece",500,25)]


def seed():
    db=Database(); init_schema(db); con=db.connect(); p=db.placeholder(); cur=con.cursor()
    if db.is_postgres:
        cur.execute("INSERT INTO factory(name,business_type,status) SELECT %s,%s,'ACTIVE' WHERE NOT EXISTS (SELECT 1 FROM factory)", ("Smart Food Manufacturing Factory","South Indian Snacks Manufacturing"))
    else:
        cur.execute("INSERT OR IGNORE INTO factory(id,name,business_type,status) VALUES(1,?,?, 'ACTIVE')", ("Smart Food Manufacturing Factory","South Indian Snacks Manufacturing"))
        cur.execute("UPDATE factory SET name=?, business_type=? WHERE id=1", ("Smart Food Manufacturing Factory","South Indian Snacks Manufacturing"))
    if db.is_postgres:
        cur.execute("INSERT INTO factory_initialization (factory_name,status,template_version,wizard_progress,draft_data) SELECT %s,%s,%s,%s,%s WHERE NOT EXISTS (SELECT 1 FROM factory_initialization)",("Smart Food Manufacturing Factory","NOT_STARTED","1.0",0,"{}"))
    else:
        cur.execute("INSERT OR IGNORE INTO factory_initialization (id,factory_name,status,template_version,wizard_progress,draft_data) VALUES (1,?,?,?,?,?)",("Smart Food Manufacturing Factory","NOT_STARTED","1.0",0,"{}"))
        cur.execute("UPDATE factory_initialization SET factory_name=? WHERE id=1", ("Smart Food Manufacturing Factory",))

    dept_ids={}
    for code,name,kind in DEPARTMENTS:
        if db.is_postgres:
            cur.execute("INSERT INTO departments(code,name,department_type,status) VALUES(%s,%s,%s,'ACTIVE') ON CONFLICT(code) DO NOTHING",(code,name,kind)); cur.execute("SELECT id FROM departments WHERE code=%s",(code,)); row=cur.fetchone(); dept_ids[code]=row["id"]
        else:
            cur.execute("INSERT OR IGNORE INTO departments(code,name,department_type,status) VALUES(?,?,?, 'ACTIVE')",(code,name,kind)); cur.execute("SELECT id FROM departments WHERE code=?",(code,)); dept_ids[code]=cur.fetchone()[0]

    positions={
        "PROD001":(330,55,190,205,3),"PROD002":(535,55,190,205,4),"PROD003":(330,300,190,205,5),
        "PROD004":(535,300,190,205,6),"PROD005":(750,55,265,205,7),"WH001":(55,55,230,220,1),
        "WH002":(55,315,230,260,2),"WH003":(750,420,265,155,8),"QC001":(750,300,265,95,9),
        "DISP001":(55,585,960,48,11),"ADMIN001":(55,275,230,30,10),
    }
    for code,position in positions.items():
        department_id=dept_ids[code]; x,y,width,height,display_order=position
        if db.is_postgres:
            cur.execute("INSERT INTO factory_layout_positions(department_id,area_x,area_y,area_width,area_height,display_order) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(department_id) DO NOTHING",(department_id,x,y,width,height,display_order))
        else:
            cur.execute("INSERT OR IGNORE INTO factory_layout_positions(department_id,area_x,area_y,area_width,area_height,display_order) VALUES(?,?,?,?,?,?)",(department_id,x,y,width,height,display_order))

    product_ids={}
    for index,(code,name,category,packet_unit,selling_unit,output,target) in enumerate(PRODUCTS):
        department_code=f"PROD00{index+1}"
        values=(code,name,category,packet_unit,selling_unit,dept_ids[department_code],output,target)
        if db.is_postgres:
            pg_values=(code,name,category,packet_unit,selling_unit,dept_ids[department_code],output,target)
            cur.execute("INSERT INTO products(code,name,category,packet_weight,unit,selling_unit,department_id,standard_batch_output,daily_target_batches) VALUES(%s,%s,%s,0,%s,%s,%s,%s,%s) ON CONFLICT(code) DO NOTHING",pg_values); cur.execute("SELECT id FROM products WHERE code=%s",(code,)); product_ids[name]=cur.fetchone()["id"]
        else:
            cur.execute("INSERT OR IGNORE INTO products(code,name,category,unit,selling_unit,department_id,standard_batch_output,daily_target_batches) VALUES(?,?,?,?,?,?,?,?)",values); cur.execute("SELECT id FROM products WHERE code=?",(code,)); product_ids[name]=cur.fetchone()[0]

    for index,(code,name,category,packet_unit,selling_unit,output,target) in enumerate(PRODUCTS,1):
        department_code=f"PROD00{index}"
        department_id=dept_ids[department_code]
        product_id=product_ids[name]
        section_code=department_code
        if db.is_postgres:
            cur.execute("INSERT INTO production_sections(department_id,code,product_id,daily_target_batches,current_status) VALUES(%s,%s,%s,%s,'OPERATIONAL') ON CONFLICT(department_id) DO NOTHING",(department_id,section_code,product_id,target))
        else:
            cur.execute("INSERT OR IGNORE INTO production_sections(department_id,code,product_id,daily_target_batches,current_status) VALUES(?,?,?,?, 'OPERATIONAL')",(department_id,section_code,product_id,target))

    for code,name,start,end,break_minutes in SHIFTS:
        if db.is_postgres:
            cur.execute("INSERT INTO shifts(code,name,start_time,end_time,break_minutes) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(code) DO NOTHING",(code,name,start,end,break_minutes))
        else:
            cur.execute("INSERT OR IGNORE INTO shifts(code,name,start_time,end_time,break_minutes) VALUES(?,?,?,?,?)",(code,name,start,end,break_minutes))

    default_machines=[
        ("MUR001","Murukku Extruder","Murukku Production","EXTRUDER",200),
        ("CHI001","Industrial Frying Machine","Potato Chips Production","FRYER",300),
        ("BAN001","Banana Chips Slicing Machine","Banana Chips Production","SLICER",250),
        ("MIX001","Ingredient Mixing Machine","Mixture Production","MIXER",180),
        ("MYS001","Industrial Cooking Vessel","Mysore Pak Production","COOKER",150),
    ]
    for code,name,department_name,machine_type,capacity in default_machines:
        cur.execute(f"SELECT id FROM departments WHERE name={p}",(department_name,))
        department_row=cur.fetchone()
        department_id=(dict(department_row)["id"] if db.is_postgres else department_row[0]) if department_row else None
        if db.is_postgres:
            cur.execute("INSERT INTO machines(code,name,machine_type,department_id,status,capacity_per_hour) VALUES(%s,%s,%s,%s,'OPERATIONAL',%s) ON CONFLICT(code) DO NOTHING",(code,name,machine_type,department_id,capacity))
        else:
            cur.execute("INSERT OR IGNORE INTO machines(code,name,machine_type,department_id,status,capacity_per_hour) VALUES(?,?,?,?, 'OPERATIONAL',?)",(code,name,machine_type,department_id,capacity))

    worker_positions=[
        ("WRK-SUP-001","Production Supervisor","Murukku Production","PRODUCTION SUPERVISOR"),
        ("WRK-MIX-001","Dough Preparation Operator","Murukku Production","Dough Preparation"),
        ("WRK-FRY-001","Frying Operator","Potato Chips Production","Frying"),
        ("WRK-PKG-001","Packaging Operator","Banana Chips Production","Packaging"),
        ("WRK-QC-001","Quality Assistant","Quality Control","Quality Inspection"),
        ("WRK-MNT-001","Maintenance Assistant","Administration","Maintenance"),
    ]
    for code,name,department_name,designation in worker_positions:
        cur.execute(f"SELECT id FROM departments WHERE name={p}",(department_name,))
        department_row=cur.fetchone()
        department_id=(dict(department_row)["id"] if db.is_postgres else department_row[0]) if department_row else None
        if db.is_postgres:
            cur.execute("INSERT INTO employees(employee_code,name,employment_type,department_id,designation,status,date_joining,nationality) VALUES(%s,%s,'PERMANENT',%s,%s,'VACANCY',NULL,'Indian') ON CONFLICT(employee_code) DO NOTHING",(code,name,department_id,designation))
        else:
            cur.execute("INSERT OR IGNORE INTO employees(employee_code,name,employment_type,department_id,designation,status,date_joining,nationality) VALUES(?,?,'PERMANENT',?,?,'VACANCY',NULL,'Indian')",(code,name,department_id,designation))

    for product_name,stages in STAGES.items():
        product_id=product_ids[product_name]
        department_id=dept_ids[{"Murukku":"PROD001","Potato Chips":"PROD002","Banana Chips":"PROD003","Mixture":"PROD004","Mysore Pak":"PROD005"}[product_name]]
        for order,stage_name in enumerate(stages,1):
            if db.is_postgres:
                cur.execute("INSERT INTO production_stages(product_id,stage_order,stage_name,department_id) VALUES(%s,%s,%s,%s) ON CONFLICT(product_id,stage_order) DO NOTHING",(product_id,order,stage_name,department_id))
            else:
                cur.execute("INSERT OR IGNORE INTO production_stages(product_id,stage_order,stage_name,department_id) VALUES(?,?,?,?)",(product_id,order,stage_name,department_id))

    for code,name,category,unit,reorder,cost in MATERIALS:
        if db.is_postgres:
            cur.execute("INSERT INTO raw_materials(code,name,category,unit,reorder_level,standard_cost_paise) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(code) DO NOTHING",(code,name,category,unit,reorder,cost))
        else:
            cur.execute("INSERT OR IGNORE INTO raw_materials(code,name,category,unit,reorder_level,standard_cost_paise) VALUES(?,?,?,?,?,?)",(code,name,category,unit,reorder,cost))

    for product_name in ["Murukku","Potato Chips","Banana Chips","Mixture","Mysore Pak"]:
        product_id = product_ids[product_name]
        if db.is_postgres:
            cur.execute("INSERT INTO recipes(product_id,version,batch_quantity,is_active,yield_packets,notes) VALUES(%s,'V1',1,1,200,'Initial standard configuration') ON CONFLICT(product_id,version) DO NOTHING",(product_id,))
            cur.execute("SELECT id FROM recipes WHERE product_id=%s AND version='V1'",(product_id,))
            recipe_id=cur.fetchone()["id"]
        else:
            cur.execute("INSERT OR IGNORE INTO recipes(product_id,version,batch_quantity,is_active,yield_packets,notes) VALUES(?, 'V1', 1, 1, 200, 'Initial standard configuration')",(product_id,))
            cur.execute("SELECT id FROM recipes WHERE product_id=? AND version='V1'",(product_id,))
            recipe_id=cur.fetchone()[0]
        recipe_items=[
            ("RM001","Rice Flour",40 if product_name=="Murukku" else 30,"kg"),
            ("RM002","Cooking Oil",10 if product_name=="Murukku" else 8,"litre"),
            ("RM003","Salt",1.2,"kg"),
            ("RM005","Packaging Pouch",200,"piece"),
            ("RM006","Carton",10,"piece"),
        ]
        for _,item_name,quantity,unit in recipe_items:
            if db.is_postgres:
                cur.execute("INSERT INTO recipe_items(recipe_id,item_name,item_category,quantity,unit) SELECT %s,%s,%s,%s,%s WHERE NOT EXISTS (SELECT 1 FROM recipe_items WHERE recipe_id=%s AND item_name=%s)",(recipe_id,item_name,"RAW_MATERIAL" if unit!="piece" else "PACKAGING",quantity,unit,recipe_id,item_name))
            else:
                cur.execute("INSERT OR IGNORE INTO recipe_items(recipe_id,item_name,item_category,quantity,unit) VALUES(?,?,?,?,?)",(recipe_id,item_name,"RAW_MATERIAL" if unit!="piece" else "PACKAGING",quantity,unit))

    warehouses=[("WH-RM","Raw Material Warehouse","RAW_MATERIAL"),("WH-PKG","Packaging Warehouse","PACKAGING"),("WH-FG","Finished Goods Warehouse","FINISHED_GOODS")]
    for code,name,kind in warehouses:
        if db.is_postgres:
            cur.execute("INSERT INTO warehouses(code,name,warehouse_type,status) VALUES(%s,%s,%s,'ACTIVE') ON CONFLICT(code) DO NOTHING",(code,name,kind))
        else:
            cur.execute("INSERT OR IGNORE INTO warehouses(code,name,warehouse_type,status) VALUES(?, ?, ?, 'ACTIVE')",(code,name,kind))

    con.commit(); con.close(); print("Smart Food Manufacturing Factory defaults initialized.")

if __name__ == "__main__": seed()
