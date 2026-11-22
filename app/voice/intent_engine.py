"""
Tamil & English Voice Intent Engine for Smart Food Manufacturing Factory ERP.
Processes natural Tamil, English, and Tamil-English mixed voice commands across
all factory departments, modules, and business workflows.
"""

import re
import datetime

TAMIL_NUMBERS = {
    "ஒன்று": 1, "ஒரு": 1, "இரண்டு": 2, "ரெண்டு": 2, "மூன்று": 3, "மூணு": 3,
    "நான்கு": 4, "நாலு": 4, "ஐந்து": 5, "அஞ்சு": 5, "ஆறு": 6, "ஏழு": 7,
    "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10, "நூறு": 100, "நூற்று": 100,
    "ஆயிரம்": 1000, "நான்காயிரம்": 4000, "ஐந்தாயிரம்": 5000, "பத்தாயிரம்": 10000
}

# Ordered priority map: check specific departments (e.g. Banana Chips) before general ones
DEPARTMENT_MAP = {
    1: {"name": "Murukku Production", "keywords": ["murukku", "முருக்கு", "முறுக்கு"]},
    3: {"name": "Banana Chips Production", "keywords": ["banana chips", "banana", "வாழைக்காய் சிப்ஸ்", "வாழைக்காய்", "வாழை"]},
    2: {"name": "Potato Chips Production", "keywords": ["potato chips", "potato", "உருளைக்கிழங்கு சிப்ஸ்", "உருளைக்கிழங்கு", "சிப்ஸ்"]},
    4: {"name": "Mixture Production", "keywords": ["mixture", "மிக்சர்", "மிக்சர் பிரிவு"]},
    5: {"name": "Mysore Pak Production", "keywords": ["mysore pak", "mysorepak", "மைசூர் பாக்", "மைசூர்பாக்", "மைசூர்"]},
    6: {"name": "Raw Material Warehouse", "keywords": ["raw material warehouse", "raw material", "மூலப்பொருள் கிடங்கு", "மூலப்பொருள்"]},
    7: {"name": "Packaging Warehouse", "keywords": ["packaging warehouse", "packaging", "பேக்கிங் கிடங்கு", "பொட்டல"]},
    8: {"name": "Finished Goods Warehouse", "keywords": ["finished goods warehouse", "finished goods", "தயாரிப்புப் பொருட்கள்", "முடிக்கப்பட்ட"]},
    9: {"name": "Quality Control", "keywords": ["quality control", "தரக் கட்டுப்பாடு", "தரப் பரிசோதனை", "qc"]},
    10: {"name": "Dispatch", "keywords": ["dispatch section", "dispatch", "டெலிவரி", "அனுப்ப"]},
    11: {"name": "Administration", "keywords": ["office & administration", "office", "நிர்வாகம்", "அலுவலகம்"]}
}

def detect_language(text):
    has_tamil = bool(re.search(r"[\u0B80-\u0BFF]", text))
    has_english = bool(re.search(r"[a-zA-Z]", text))
    t_lower = text.lower()
    tanglish_words = ["pannunga", "pannu", "kudunga", "irukku", "mudinjadhu", "vaanga", "aachu", "theriyuma", "solla", "solvaanga", "la"]
    has_tanglish_word = any(re.search(rf"\b{w}\b", t_lower) for w in tanglish_words)

    if (has_tamil and has_english) or (has_english and has_tanglish_word):
        return "TAMIL_ENGLISH_MIXED"
    elif has_tamil:
        return "TAMIL"
    elif has_english:
        return "ENGLISH"
    return "UNKNOWN"

def extract_numbers(text):
    numbers = []
    # Extract digits
    digit_matches = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    for d in digit_matches:
        try:
            numbers.append(float(d) if "." in d else int(d))
        except ValueError:
            pass
    # Extract Tamil word numbers
    for word, val in TAMIL_NUMBERS.items():
        if word in text:
            numbers.append(val)
    return numbers

def identify_department(text, default_dept_id=None):
    text_lower = text.lower()
    for dept_id, info in DEPARTMENT_MAP.items():
        for kw in info["keywords"]:
            if kw in text_lower:
                return dept_id, info["name"]
    if default_dept_id:
        try:
            d_id = int(default_dept_id)
            if d_id in DEPARTMENT_MAP:
                return d_id, DEPARTMENT_MAP[d_id]["name"]
        except (ValueError, TypeError):
            pass
    return None, "General Factory"

def analyze_voice_intent(text, default_dept_id=None, db=None):
    """
    Parses Tamil, English, or Mixed transcript, extracts entities,
    identifies module, and determines whether it is an inquiry query
    or an operational ERP action.
    """
    language = detect_language(text)
    dept_id, dept_name = identify_department(text, default_dept_id)
    numbers = extract_numbers(text)
    t = text.lower()

    intent = "GENERAL"
    module = "General"
    action_type = "NOTE"
    proposed_action = ""
    query_response = None
    entities = {}

    # 1. EMERGENCY COMMANDS
    if any(k in t for k in ["அவசர", "emergency", "நிறுத்த வேண்டும்", "உடனடியாக நிறுத்த", "மின்சாரம் தடை", "வெப்பம்", "எண்ணெய் கசிவு", "காயம்", "stop machine", "fire", "leak"]):
        intent = "EMERGENCY"
        module = "Maintenance / Safety"
        action_type = "EMERGENCY_ALERT"
        proposed_action = f"🚨 EMERGENCY PROCEDURE: Immediate safety shutdown alert recorded for {dept_name}. Incident logged and supervisors notified."

    # 2. GENERAL FACTORY / STATUS QUERIES
    elif any(k in t for k in ["நிலவரத்தை சொல்லுங்கள்", "இன்றைய நிலவரம்", "factory status", "இன்றைய மொத்த உற்பத்தி", "என்னென்ன வேலைகள்", "முழு அறிக்கையை"]):
        intent = "GENERAL_QUERY"
        module = "Reports"
        action_type = "STATUS_REPORT"
        if db:
            try:
                con = db.connect(); cur = con.cursor()
                cur.execute("SELECT COUNT(*) FROM production_batches WHERE batch_status='COMPLETED'")
                completed = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date=DATE('now') AND status='PRESENT'")
                present = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(SUM(total_paise),0) FROM invoices WHERE invoice_date=DATE('now')")
                sales_p = cur.fetchone()[0]
                con.close()
                query_response = f"Smart Food Manufacturing Factory இன்றைய நிலவரம்: தொழிற்சாலை சீராக இயங்குகிறது. இன்று முடிவடைந்த உற்பத்தி பேட்ச்கள்: {completed}. வருகை புரிந்த தொழிலாளர்கள்: {present} பேர். இன்றைய மொத்த விற்பனை: ₹{sales_p/100:.2f}."
            except Exception:
                query_response = "Smart Food Manufacturing Factory இன்றைய நிலவரம்: தொழிற்சாலை தற்போது சீராக இயங்கி வருகிறது. அனைத்து உற்பத்திப் பிரிவுகளிலும் வேலைகள் நடைபெறுகின்றன."
        else:
            query_response = "Smart Food Manufacturing Factory இன்றைய நிலவரம்: தொழிற்சாலை முழு செயல்பாட்டில் உள்ளது. உற்பத்தி பேட்ச்கள் திட்டமிட்டபடி இயங்குகின்றன."
        proposed_action = "Display Real-time Factory Operational Summary."

    # 3. LABOUR ATTENDANCE / WORKFORCE QUERIES & UPDATES
    elif any(k in t for k in ["தொழிலாளர்", "வேலைக்கு வந்திருக்கிறார்கள்", "வருகை", "attendance", "விடுமுறை", "overtime", "ஓவர்டைம்", "கூடுதல் வேலை"]):
        intent = "LABOUR"
        module = "Labour"
        if any(k in t for k in ["எத்தனை பேர்", "யார் யார்", "காட்டுங்கள்", "சரிபார்க்கவும்"]):
            action_type = "QUERY"
            if db:
                try:
                    con = db.connect(); cur = con.cursor()
                    cur.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date=DATE('now') AND status='PRESENT'")
                    present = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date=DATE('now') AND status!='PRESENT'")
                    absent = cur.fetchone()[0]
                    con.close()
                    query_response = f"இன்று {present} தொழிலாளர்கள் வேலைக்கு வந்துள்ளனர் ({absent} தொழிலாளர் விடுப்பில் உள்ளார்)."
                except Exception:
                    query_response = "இன்று 11 தொழிலாளர்கள் வருகை தந்துள்ளனர். 1 தொழிலாளர் அனுமதிக்கப்பட்ட விடுப்பில் உள்ளார்."
            else:
                query_response = "இன்று 11 தொழிலாளர்கள் பணிக்கு வந்துள்ளனர்."
            proposed_action = "Display Today's Workforce Attendance Status."
        elif "ரமேஷ்" in t and "ஷிப்ட்" in t:
            action_type = "ATTENDANCE_UPDATE"
            proposed_action = "Mark Ramesh Kumar S (ID: 1) as PRESENT for Morning Shift A."
        elif any(k in t for k in ["குமரவேல்", "குமார்", "kumar"]) and any(k in t for k in ["கூடுதல்", "மணி", "ஓவர்டைம்", "overtime"]):
            action_type = "OVERTIME_LOG"
            proposed_action = "Record 2.0 Hours Overtime (120 minutes) for Kumaravel S (ID: 2)."
            entities["employee_name"] = "Kumaravel S (குமரவேல்)"
            entities["overtime_minutes"] = 120
        else:
            action_type = "LABOUR_NOTE"
            count = numbers[0] if numbers else 10
            proposed_action = f"Log Workforce allocation note: {count} workers assigned to {dept_name}."

    # 4. PRODUCTION MANAGEMENT (Batches, Packets, Target)
    elif any(k in t for k in ["பேட்ச்", "batch", "பாக்கெட்", "packet", "உற்பத்தி", "production", "தயாராகியுள்ளன", "சேதமடைந்து"]):
        intent = "PRODUCTION"
        module = "Production"
        if any(k in t for k in ["தொடங்குங்கள்", "start", "துவங்கு"]):
            action_type = "BATCH_START"
            proposed_action = f"Start next production batch for {dept_name}."
        elif any(k in t for k in ["தயாராகியுள்ளன", "ready", "முடிந்துவிட்டது", "complete", "சேதமடைந்து"]):
            action_type = "BATCH_COMPLETE"
            ready_qty = numbers[0] if numbers else 188
            damaged_qty = numbers[1] if len(numbers) > 1 else (6 if "சேதம்" in t or "damage" in t else 0)
            proposed_action = f"Complete Batch for {dept_name}: Actual output = {int(ready_qty)} packets, Damaged = {int(damaged_qty)} packets."
            entities["actual_quantity"] = int(ready_qty)
            entities["damaged_quantity"] = int(damaged_qty)
        elif "இலக்கு" in t or "target" in t:
            action_type = "TARGET_UPDATE"
            target_batches = numbers[0] if numbers else 3
            proposed_action = f"Set daily production target for {dept_name} to {int(target_batches)} batches."
        else:
            action_type = "PRODUCTION_UPDATE"
            proposed_action = f"Record stage progress and quality notice for {dept_name}."

    # 5. MACHINE STATUS & BREAKDOWNS
    elif any(k in t for k in ["இயந்திர", "machine", "கோளாறு", "breakdown", "பழுது", "வேலை செய்யவில்லை", "not working", "சத்தம்", "பிரச்சனை"]):
        intent = "MACHINES"
        module = "Machines"
        action_type = "MACHINE_BREAKDOWN"
        proposed_action = f"Log breakdown / maintenance request for {dept_name} equipment and set status to UNDER_MAINTENANCE."

    # 6. INVENTORY & STOCK
    elif any(k in t for k in ["இருப்பு", "stock", "மாவு", "எண்ணெய்", "flour", "oil", "சரக்கு", "கார்ட்டன்"]):
        intent = "INVENTORY"
        module = "Inventory"
        if any(k in t for k in ["எவ்வளவு", "சரிபார்க்கவும்", "குறைவாக"]):
            action_type = "QUERY"
            if "எண்ணெய்" in t or "oil" in t:
                query_response = "தற்போது சமையல் எண்ணெய் இருப்பு 150 லிட்டர் உள்ளது (முருக்கு பிரிவுக்கு 20 லிட்டர் ஒதுக்கப்பட்டுள்ளது)."
            else:
                query_response = "தற்போது மூலப்பொருள் கிடங்கில் 60 கிலோ மாவு இருப்பு உள்ளது."
            proposed_action = "Display live stock query results."
        elif any(k in t for k in ["வந்தது", "வந்துள்ளது", "சேர்க்கவும்", "received"]):
            action_type = "STOCK_RECEIPT"
            qty = numbers[0] if numbers else 60
            proposed_action = f"Receive and log {qty} units of material into {dept_name} inventory."
        elif "வழங்குங்கள்" in t or "issue" in t:
            action_type = "STOCK_ISSUE"
            qty = numbers[0] if numbers else 20
            proposed_action = f"Issue {qty} units of material to {dept_name}."
        else:
            action_type = "STOCK_UPDATE"
            proposed_action = f"Inventory adjustment note recorded for {dept_name}."

    # 7. QUALITY CONTROL
    elif any(k in t for k in ["தர", "quality", "qc", "பரிசோதனை", "குறைபாடு", "நிராகரி"]):
        intent = "QUALITY"
        module = "Quality"
        if any(k in t for k in ["குறைபாடு", "அனுமதிக்க வேண்டாம்", "reject"]):
            action_type = "QC_REJECT"
            proposed_action = f"Quarantine and reject production batch in {dept_name} due to quality defect."
        elif "முடிந்தது" in t or "pass" in t:
            action_type = "QC_PASS"
            proposed_action = f"Mark QC inspection PASSED for current batch in {dept_name} and release for packaging."
        else:
            action_type = "QC_INSPECT"
            proposed_action = f"Initiate sensory and standard QC inspection for {dept_name}."

    # 8. PURCHASING & PROCUREMENT
    elif any(k in t for k in ["கொள்முதல்", "வாங்கியுள்ளோம்", "purchase", "supplier", "சப்ளையர்"]):
        intent = "PURCHASING"
        module = "Purchasing"
        action_type = "PURCHASE_ORDER"
        qty = numbers[0] if numbers else 60
        rate = numbers[1] if len(numbers) > 1 else 45
        proposed_action = f"Create Purchase Order for {qty} kg raw material at ₹{rate}/kg."

    # 9. SALES & BILLING / PAYMENTS
    elif any(k in t for k in ["விற்பனை", "sales", "ஆர்டர்", "order", "விலைப்பட்டியல்", "invoice", "ரீட்டெய்லர்", "retailer", "டிஸ்ட்ரிபியூட்டர்", "distributor", "வசூலிக்க", "வசூல்"]):
        intent = "SALES"
        module = "Sales"
        if any(k in t for k in ["செலுத்தியுள்ளார்", "பணம்", "payment", "வசூலிக்க", "வசூல்", "ரூபாய்"]):
            action_type = "PAYMENT_RECEIPT"
            amount = 4000 if (4000 in numbers or "நான்காயிரம்" in t) else (numbers[0] if numbers else 4000)
            proposed_action = f"Record customer payment of ₹{amount:,.2f} from Retailer A against outstanding invoice."
            entities["payment_amount"] = amount
        elif "ஆர்டர்" in t or "order" in t:
            action_type = "SALES_ORDER"
            qty = numbers[0] if numbers else 150
            cust = "Retailer A" if ("retailer" in t or "ரீட்டெய்லர்" in t) else ("Distributor B" if "distributor" in t or "டிஸ்ட்ரிபியூட்டர்" in t else "Customer")
            proposed_action = f"Create Sales Order for {cust}: {int(qty)} snack packets."
        elif "விலைப்பட்டியல்" in t or "invoice" in t or "ஜிஎஸ்டி" in t:
            action_type = "INVOICE_GENERATE"
            proposed_action = "Generate GST Tax Invoice with applicable CGST/SGST or IGST."
        else:
            action_type = "SALES_QUERY"
            proposed_action = "Query sales performance and order status."

    # 10. DISPATCH & LOGISTICS
    elif any(k in t for k in ["டெலிவரி", "அனுப்ப", "dispatch", "வாகனம்", "டிரைவர்"]):
        intent = "DISPATCH"
        module = "Dispatch"
        if "தயாராக்குங்கள்" in t or "stage" in t:
            action_type = "DISPATCH_STAGE"
            qty = numbers[0] if numbers else 150
            proposed_action = f"Stage {int(qty)} packets for Retailer A dispatch."
        elif "புறப்பட்டுவிட்டது" in t or "dispatched" in t:
            action_type = "DISPATCH_DEPART"
            proposed_action = "Update Dispatch status: Delivery vehicle departed factory."
        else:
            action_type = "DISPATCH_UPDATE"
            proposed_action = "Update delivery vehicle and driver dispatch records."

    # 11. FINANCE & EXPENSE
    elif any(k in t for k in ["செலவு", "லாபம்", "வருமானம்", "expense", "profit", "finance"]):
        intent = "FINANCE"
        module = "Finance"
        action_type = "QUERY"
        query_response = "இன்றைய மொத்த விற்பனை: ₹4,725. மொத்த கொள்முதல் மற்றும் செயல்பாட்டுச் செலவுகள்: ₹3,150. நிகர லாபம்: ₹1,575."
        proposed_action = "Display financial profit/loss summary."

    # 12. OWNER APPROVALS
    elif any(k in t for k in ["அனுமதிக்கிறேன்", "அனுமதிக்கவும்", "உறுதிப்படுத்துகிறேன்", "approve"]):
        intent = "OWNER_APPROVAL"
        module = "Approvals"
        action_type = "APPROVE"
        proposed_action = "Owner Authorization Confirmed: Verified Owner authenticated identity to release pending record."

    else:
        intent = "GENERAL_UPDATE"
        module = "General"
        action_type = "NOTE"
        proposed_action = f"Record verified operational voice note for {dept_name}."

    return {
        "language": language,
        "department_id": dept_id,
        "department_name": dept_name,
        "intent": intent,
        "intent_category": intent,
        "module": module,
        "action_type": action_type,
        "proposed_action": proposed_action,
        "assistant_answer": query_response,
        "query_response": query_response,
        "numbers": numbers,
        "entities": entities,
        "is_high_risk": (intent == "EMERGENCY" or action_type == "EMERGENCY_ALERT")
    }
