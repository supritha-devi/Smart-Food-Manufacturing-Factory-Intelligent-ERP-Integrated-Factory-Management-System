# Smart Food Manufacturing Factory
### Integrated ERP & Intelligent Factory Management System

**A Centralized, Automated and Intelligent Enterprise Resource Planning Platform for Food Manufacturing Industries.**

---

## Project Overview

Smart Food Manufacturing Factory is an integrated Enterprise Resource Planning (ERP) solution designed to digitally manage, monitor, automate and optimize the complete operations of a food manufacturing facility.

The platform connects production, inventory, procurement, workforce, machinery, quality control, sales, finance, warehouse management, maintenance and logistics through a centralized ERP ecosystem.

It transforms traditional manufacturing operations into a connected, data-driven environment where departments share information, operational activities are traceable, and management decisions are supported by real-time business data.

The system also incorporates advanced capabilities such as:

- Interactive 2D factory visualization.
- Tamil and English voice-based factory management.
- Automated date and time calculations.
- Production planning and capacity monitoring.
- Machine and workforce utilization.
- Centralized approval workflows.
- Automated notifications and alerts.
- Batch-level production traceability.
- Integrated financial and operational reporting.
- Role-based access control.
- Centralized audit history.

The platform is designed around the operational requirements of a food manufacturing facility producing traditional Indian snack products.

---

## Project Objectives

- Digitize traditional food manufacturing operations.
- Integrate all departments into a unified ERP platform.
- Improve production planning and resource utilization.
- Maintain accurate raw material and finished goods inventory.
- Monitor machinery, performance and maintenance activities.
- Manage employee attendance, shifts and workforce allocation.
- Automate purchasing, sales, billing and financial operations.
- Maintain food quality and manufacturing traceability.
- Reduce manual data entry and operational errors.
- Provide centralized factory monitoring.
- Enable Tamil and English voice-based interaction.
- Improve business visibility through reports and analytics.
- Maintain accurate transaction history and accountability.

---

# 20 Major Functional Areas

## 1. User Management & Role-Based Access Control

Centralized authentication and permission management for all factory employees.

### Features

- Initial Owner account setup.
- Factory Admin management.
- Production Supervisor accounts.
- Salesman accounts.
- Accountant and Auditor accounts.
- Employee account management.
- Multiple employees under the same role.
- Department-based access.
- Customer assignment for salesmen.
- Production section assignment for supervisors.
- Role-based permissions.
- Additional permissions where authorized.
- Secure login and logout.
- Password hashing.
- Password reset and change.
- Temporary credentials and first-login password change.
- Employee account activation and deactivation.
- User activity tracking.
- Login history.
- Audit logs.

The Owner has factory-wide visibility, while other users access only the information and operations permitted by their assigned roles.

## 2. Factory Initialization & Configuration

A first-time setup process for configuring the factory before operational activities begin.

### Features

- Factory name and business details.
- Factory address and contact information.
- GST and tax configuration.
- Department creation.
- Production section configuration.
- Warehouse configuration.
- Suggested machine templates.
- Suggested workforce templates.
- Product configuration.
- Production stage configuration.
- Shift configuration.
- Daily production targets.
- Resource capacity configuration.
- Initial stock configuration.
- Setup validation.
- Owner review and approval.
- Duplicate initialization prevention.

The initial setup should provide suggested resources for the Owner to review and configure rather than requiring every record to be created from scratch.

## 3. Production Configuration & Manufacturing Setup

Configures products, recipes, production stages, batch sizes and manufacturing requirements.

### Supported Products

| Product Code | Production Section |
|---|---|
| PROD001 | Murukku |
| PROD002 | Potato Chips |
| PROD003 | Banana Chips |
| PROD004 | Mixture |
| PROD005 | Mysore Pak |

### Features

- Product master management.
- Product variants.
- Different packet weights such as 100g, 200g and 500g.
- Product-specific Bill of Materials (BOM).
- Recipe and ingredient configuration.
- Standard batch quantities.
- Packaging requirements.
- Manufacturing stages.
- Machine-to-stage mapping.
- Worker-to-stage mapping.
- Daily production targets.
- Shift-wise production targets.
- Standard production capacity.
- Material requirement calculations.
- Standard production cost estimation.
- BOM versioning.
- Effective dates.
- Configurable wastage allowances.
- Recipe change history.
- Configuration validation.

Each product has its own manufacturing configuration and operational requirements.

## 4. Machine Management

Centralized management of manufacturing machinery and equipment.

### Features

- Machine registration.
- Machine identification codes.
- Machine categories and types.
- Manufacturer and model details.
- Purchase and installation information.
- Warranty details.
- Department assignments.
- Production stage assignments.
- Machine capacity configuration.
- Theoretical and practical capacity.
- Machine availability.
- Running and idle status.
- Maintenance status.
- Breakdown status.
- Machine utilization.
- Operating-hour tracking.
- Downtime tracking.
- Preventive maintenance schedules.
- Breakdown reporting.
- Repair history.
- Spare parts management.
- Machine operating costs.
- Maintenance alerts.
- Machine performance reports.
- Interactive factory layout integration.

### Machine Statuses

- Available.
- Running.
- Idle.
- Under Maintenance.
- Breakdown.
- Inactive.

Machine allocation must consider availability, capacity, maintenance schedules and conflicting assignments.

## 5. Labour & Workforce Management

Complete employee and workforce management across factory departments.

### Features

- Employee registration.
- Employee identification.
- Designation management.
- Skill management.
- Department assignment.
- Machine operator assignment.
- Permanent and temporary workforce.
- Contractor labour management.
- Attendance management.
- Shift allocation.
- Leave management.
- Weekly offs and holidays.
- Overtime tracking.
- Missed punch correction.
- Attendance imports.
- QR-based attendance support.
- Biometric integration support.
- Employee document management.
- Training and safety records.
- PPE issuance records.
- Employee performance tracking.
- Daily workforce allocation.
- Workforce capacity calculation.
- Labour productivity.
- Salary structure management.
- Payroll calculations.
- Labour cost allocation.
- Employee advances and loans.
- Configurable statutory deductions.
- Labour shortage alerts.
- Workforce reports.

## 6. Production Workflow & Manufacturing Operations

Manages the complete manufacturing lifecycle from production planning to finished goods transfer.

### Features

- Daily, weekly and monthly production planning.
- Production demand analysis.
- Production order creation.
- Production approval.
- Batch creation.
- Batch identification.
- Product-specific production stages.
- Raw material requirement calculation.
- BOM-based material issue.
- Machine allocation.
- Workforce allocation.
- Shift allocation.
- Production scheduling.
- Stage-wise progress monitoring.
- Production start, pause, resume and completion.
- Actual material consumption.
- Actual production output.
- Accepted and rejected quantities.
- Wastage tracking.
- Rework management.
- Partial production.
- Incomplete batch carry-forward.
- Production variance analysis.
- Batch costing.
- Packaging management.
- Finished goods transfer.
- Production performance reports.

### Product-Specific Manufacturing Workflows

**Murukku**

Dough Preparation → Dough Mixing → Shaping → Frying → Cooling → Quality Control → Packaging → Finished Goods Transfer.

**Potato Chips**

Washing → Peeling → Slicing → Preparation → Frying → De-oiling → Seasoning → Quality Control → Packaging → Transfer.

**Banana Chips**

Preparation → Peeling → Slicing → Frying → De-oiling → Quality Control → Packaging → Transfer.

**Mixture**

Ingredient Preparation → Mixing → Frying → Ingredient Mixing → Quality Control → Packaging → Transfer.

**Mysore Pak**

Ingredient Preparation → Mixing → Cooking → Cooling → Cutting → Quality Control → Packaging → Transfer.

## 7. Production Overflow & Exception Management

Handles unexpected production requirements and operational deviations.

### Features

- Production target deviation monitoring.
- Additional production requests.
- Production overflow identification.
- Unexpected material consumption.
- Production delays.
- Machine-related interruptions.
- Labour shortages.
- Capacity-related production issues.
- Supervisor review.
- Owner approval.
- Additional resource allocation.
- Exception tracking.
- Production recovery planning.
- Exception history and reports.

Production overflow must remain a controlled approval process and must not silently modify approved production plans.

## 8. Inventory & Warehouse Management

Centralized tracking of all materials and finished products.

### Inventory Categories

- Raw Materials.
- Packaging Materials.
- Work in Progress.
- Finished Goods.
- Spare Parts.

### Features

- Item master management.
- Unit of measurement management.
- Unit conversions.
- Multiple warehouse management.
- Warehouse zones and racks.
- Shelf and bin locations.
- Opening stock configuration.
- Goods receipt.
- Raw material stock tracking.
- Packaging stock tracking.
- Production material issue.
- Material returns.
- Work-in-progress tracking.
- Finished goods inventory.
- Inventory transfers.
- In-transit stock.
- Stock adjustments.
- Stock reconciliation.
- Inventory valuation.
- FIFO and FEFO.
- Weighted average costing.
- Lot and batch tracking.
- Supplier lot traceability.
- Expiry monitoring.
- Reorder-level alerts.
- Damaged stock tracking.
- Quarantine stock.
- Barcode and QR support.
- Stock ageing.
- Inventory ledger.
- Inventory reports.

All stock changes must be recorded through controlled inventory transactions.

## 9. Purchasing & Procurement

Manages supplier relationships and the complete procurement process.

### Features

- Supplier registration.
- Supplier contact management.
- Material catalogue.
- Material requirement planning.
- Purchase requisitions.
- Supplier enquiries.
- Supplier quotations.
- Price comparison.
- Purchase order creation.
- Purchase approval.
- Partial deliveries.
- Goods Receipt Notes (GRN).
- Incoming quality inspection.
- Accepted and rejected quantities.
- Supplier invoice management.
- Purchase returns.
- Supplier payment tracking.
- Supplier price history.
- Supplier performance monitoring.
- Purchase reports.

Purchase orders must not directly increase inventory. Stock is updated only after the required goods receipt and acceptance process.

## 10. Sales Management & GST Billing

Manages customer relationships, sales orders, billing and payment collection.

### Features

- Customer registration.
- Retailer management.
- Distributor management.
- Customer addresses.
- Customer GST details.
- Salesman management.
- Customer assignments.
- Product pricing.
- Discount management.
- Sales order creation.
- Order verification.
- Order approval.
- Stock availability checking.
- Stock reservation.
- Credit limit monitoring.
- GST calculation.
- CGST and SGST.
- IGST.
- GST invoice generation.
- Invoice PDF generation.
- E-invoice integration support.
- E-way bill integration support.
- Payment collection.
- Partial payments.
- Customer outstanding balances.
- Customer statements.
- Sales returns.
- Credit notes.
- Offline order capture.
- Safe order synchronization.
- Sales targets.
- Sales performance reports.

GST treatment must be calculated using the applicable tax rules and place of supply.

## 11. Financial Management & Accounting

A centralized accounting system connected to operational transactions.

### Features

- Company financial configuration.
- Financial year management.
- Chart of accounts.
- Double-entry accounting.
- General ledger.
- Sales accounting.
- Purchase accounting.
- Accounts receivable.
- Accounts payable.
- Cash management.
- Bank management.
- Bank reconciliation.
- Expense management.
- GST accounting.
- Payroll accounting.
- Production cost accounting.
- Inventory valuation.
- Fixed asset management.
- Asset depreciation.
- Budget management.
- Financial approvals.
- Trial balance.
- Profit and loss statement.
- Balance sheet.
- Cash flow statement.
- Financial year closing.
- Financial reports.

The Indian financial year must support April 1 to March 31.

Financial postings must remain balanced, traceable and protected from unauthorized modification.

## 12. Quality Control & Food Safety

Maintains product quality, food safety records and batch traceability.

### Features

- Incoming raw material inspection.
- Supplier material quality checks.
- Product-specific quality parameters.
- Stage-wise inspections.
- Finished goods inspection.
- Packaging inspection.
- Label verification.
- Hygiene records.
- Sanitation monitoring.
- Critical control point monitoring.
- Oil quality monitoring.
- Frying temperature monitoring.
- Cooling temperature monitoring.
- Equipment cleaning records.
- Pest control records.
- Rejection management.
- Rework and reinspection.
- Non-conformance reports.
- Corrective and preventive actions.
- Calibration records.
- Laboratory test records.
- Batch quarantine.
- Batch genealogy.
- Product recall management.
- Customer complaint tracking.
- Quality reports.

Failed critical inspections must place affected batches on hold until authorized resolution.

## 13. Maintenance & Equipment Reliability

Manages preventive and corrective maintenance across the factory.

### Features

- Maintenance dashboard.
- Preventive maintenance schedules.
- Maintenance calendar.
- Maintenance work orders.
- Breakdown reporting.
- Diagnosis and repair.
- Technician allocation.
- Downtime recording.
- Corrective maintenance.
- Spare parts consumption.
- Maintenance cost tracking.
- Cleaning schedules.
- Calibration schedules.
- Warranty management.
- Service contracts.
- Machine performance monitoring.
- Mean Time Between Failures (MTBF).
- Mean Time To Repair (MTTR).
- Machine availability.
- Safety verification.
- Lockout/Tagout records.
- Machine release approval.
- Maintenance reports.

Machines must not return to production automatically after maintenance. Required safety checks and release approvals must be completed.

## 14. Warehouse, Dispatch & Logistics

Manages finished goods storage, order fulfilment and product delivery.

### Features

- Warehouse location management.
- Finished goods receiving.
- Picking operations.
- Order verification.
- Packing operations.
- Product labelling.
- Barcode and QR support.
- Dispatch staging.
- Vehicle registration.
- Driver management.
- Transport provider management.
- Route management.
- Shipment creation.
- Loading management.
- Dispatch authorization.
- Delivery tracking.
- Proof of delivery.
- Delivery confirmation.
- Failed delivery handling.
- Customer returns.
- Logistics cost management.
- Dispatch reports.

Dispatch must be connected to approved sales orders and confirmed finished goods inventory.

## 15. Interactive 2D Factory Layout

Provides a visual representation of the entire manufacturing facility.

### Factory Locations

- Raw Material Warehouse.
- Packaging Warehouse.
- Murukku Production Section.
- Potato Chips Production Section.
- Banana Chips Production Section.
- Mixture Production Section.
- Mysore Pak Production Section.
- Quality Control Area.
- Work-in-Progress Area.
- Finished Goods Warehouse.
- Dispatch Area.
- Maintenance Room.
- Administrative Office.

### Features

- Interactive factory map.
- Clickable departments.
- Department-specific information.
- Production status visualization.
- Machine status visualization.
- Workforce information.
- Department capacity information.
- Factory location identifiers.
- Department-level notifications.
- Location-based voice recording.
- Department activity history.

The factory layout must connect to actual ERP records rather than displaying static sample information.

## 16. Smart Tamil & English Voice Assistant

A factory-wide voice interaction system that enables the Owner and authorized employees to communicate with the ERP using natural speech.

### Supported Languages

- Tamil.
- English.
- Tamil-English mixed speech.

### Voice Capabilities

- Start and stop recording.
- Pause and resume recording.
- Audio playback.
- Audio upload.
- Speech-to-text transcription.
- Language identification.
- Transcript editing.
- Natural language command recognition.
- Product identification.
- Department identification.
- Employee identification.
- Machine identification.
- Batch identification.
- Quantity extraction.
- Date and amount extraction.
- Voice-based reporting.
- Voice-based operational updates.
- Confirmation workflow.

### Supported Voice Operations

**Production**

- Start production.
- Report production completion.
- Report batch output.
- Report wastage.
- Report production delays.
- Report material consumption.

**Labour**

- Report employee attendance.
- Report absenteeism.
- Report overtime.
- Report workforce shortages.
- Request workforce allocation.

**Machines**

- Report breakdowns.
- Report unusual sounds.
- Report temperature issues.
- Request maintenance.
- Check machine status.

**Inventory**

- Report stock shortages.
- Report goods receipts.
- Report damaged materials.
- Request stock information.
- Report material consumption.

**Quality Control**

- Report inspection results.
- Report quality failures.
- Request batch quarantine.
- Report rejected quantities.
- Request reinspection.

**Purchasing and Sales**

- Report purchase requirements.
- Request supplier information.
- Report customer orders.
- Request invoice information.
- Check payment status.

**Finance**

- Request expenses.
- Report payment receipts.
- Check outstanding amounts.
- Request financial reports.

**Warehouse and Dispatch**

- Report finished goods transfers.
- Request picking operations.
- Report loading completion.
- Report dispatch status.
- Confirm delivery information.

### Three Voice Recording Methods

**A. Global Voice Assistant**

A floating microphone available throughout the ERP.

It should identify the current module and ask for clarification if the context is uncertain.

**B. Factory Location-Based Voice Recording**

The Owner selects a department from the interactive 2D factory map and records a message specifically for that location.

**C. Record-Based Voice Recording**

Voice recording is available inside existing business records such as:

- Employee records.
- Attendance records.
- Production batches.
- Machine records.
- Maintenance work orders.
- Inventory transactions.
- Quality inspection records.
- Sales orders.
- Purchase orders.
- Customer records.
- Supplier records.
- Shipment records.
- Delivery records.

### Central Voice Records Library

Every recording must maintain:

- Unique recording ID.
- Original audio.
- Tamil transcript.
- English translation when generated.
- Detected language.
- Employee identity.
- Employee role.
- Department ID.
- Factory location ID.
- Related module.
- Related record ID.
- Recording date.
- Recording time.
- Recording duration.
- Processing status.
- Confirmation status.
- Approval history.

### Voice Processing Workflow

Recording → Speech Recognition → Transcription → Language Identification → Context Identification → Department Identification → Record Identification → Information Extraction → Owner Review → Confirmation → ERP Update → Audit History.

Unclear voice messages must trigger clarification instead of guessed transactions.

Original audio must remain available even when a transcript is corrected.

Voice records must be shared across modules using the same recording ID rather than duplicated.

## 17. Automated Date & Time Management

A centralized automatic time calculation system integrated across every ERP module.

### Time and Date Configuration

- Factory timezone: `Asia/Kolkata`.
- Date display: `DD-MM-YYYY`.
- Time display: 12-hour format with AM/PM.
- Official timestamps: Server-generated.
- Duration calculations: Server-side.
- Historical timestamps: Immutable.

### Automatic Calculations

**Attendance**

- Employee check-in time.
- Employee check-out time.
- Working hours.
- Break duration.
- Overtime.
- Late arrival.
- Early departure.
- Absence duration.

**Shift Management**

- Shift start and end.
- Shift duration.
- Overnight shifts.
- Shift overlap validation.
- Attendance within shifts.

**Production**

- Production start time.
- Production completion time.
- Batch duration.
- Stage duration.
- Production delay.
- Production cycle time.
- Carry-forward duration.

**Machine Management**

- Machine running time.
- Machine idle time.
- Machine downtime.
- Maintenance duration.
- Machine utilization.
- Next maintenance due date.

**Inventory**

- Stock ageing.
- Material expiry countdown.
- Batch shelf-life tracking.
- Reorder monitoring.

**Sales and Finance**

- Order processing duration.
- Invoice due dates.
- Payment ageing.
- Overdue invoice duration.
- Customer outstanding ageing.
- Supplier payment due dates.

**Dispatch and Logistics**

- Loading duration.
- Dispatch time.
- Delivery duration.
- Delivery delay.
- Expected delivery date.

### Additional Features

- Live factory clock.
- Real-time dashboard timers.
- Automatic timestamp generation.
- Scheduled background checks.
- Date-based notifications.
- Time-based alerts.
- Configurable working calendars.
- Holidays and weekly offs.
- Historical time tracking.

Important transaction times must never depend solely on the browser or device clock.

## 18. Owner Dashboard & Factory Monitoring

A centralized dashboard providing a complete overview of factory operations.

### Dashboard Information

- Total production.
- Department-wise production.
- Daily production targets.
- Production completion percentage.
- Pending production batches.
- Raw material availability.
- Finished goods availability.
- Machine operational status.
- Machine breakdowns.
- Machine utilization.
- Workforce attendance.
- Labour allocation.
- Pending approvals.
- Quality inspection status.
- Rejected production.
- Sales performance.
- Purchase performance.
- Financial summaries.
- Customer outstanding balances.
- Supplier outstanding balances.
- Maintenance alerts.
- Low-stock alerts.
- Expiry alerts.
- Production exceptions.

Dashboard values must be calculated from actual database records.

## 19. Notifications, Approvals & Audit Management

A shared notification and authorization system across all modules.

### Notifications

- Production alerts.
- Machine breakdown alerts.
- Labour shortage alerts.
- Inventory shortage alerts.
- Expiry notifications.
- Quality rejection alerts.
- Purchase approval notifications.
- Sales order approval notifications.
- Financial approval notifications.
- Maintenance reminders.
- Delivery delay notifications.
- Pending task reminders.

### Approval Management

- Production approvals.
- Purchase approvals.
- Sales order approvals.
- Financial approvals.
- Inventory adjustment approvals.
- Maintenance approvals.
- Quality release approvals.
- Dispatch approvals.

### Audit Management

- User activity history.
- Transaction history.
- Approval history.
- Rejection history.
- Record modification history.
- Voice recording history.
- Timestamp tracking.
- Employee accountability.

## 20. Reports, Analytics & Business Intelligence

A centralized reporting system covering all operational and financial departments.

### Production Reports

- Daily production.
- Weekly production.
- Monthly production.
- Product-wise production.
- Department-wise production.
- Batch performance.
- Yield variance.
- Material consumption variance.
- Production costing.

### Workforce Reports

- Attendance.
- Overtime.
- Leave.
- Labour allocation.
- Employee productivity.
- Payroll.
- Labour costs.

### Machine Reports

- Machine utilization.
- Operating hours.
- Downtime.
- Maintenance history.
- Breakdown frequency.
- Machine availability.
- MTBF and MTTR.

### Inventory Reports

- Current stock.
- Stock movement.
- Stock valuation.
- Raw material consumption.
- Finished goods availability.
- Expiry reports.
- Damaged stock.
- Inventory ageing.

### Purchasing Reports

- Purchase orders.
- Supplier performance.
- Material purchase history.
- Price comparison.
- Supplier outstanding balances.

### Sales Reports

- Sales orders.
- Sales performance.
- Product-wise sales.
- Customer-wise sales.
- Salesman performance.
- GST invoices.
- Customer outstanding balances.
- Sales returns.

### Financial Reports

- General ledger.
- Trial balance.
- Profit and loss.
- Balance sheet.
- Cash flow.
- Expenses.
- Accounts receivable.
- Accounts payable.
- GST summaries.

### Additional Reporting Features

- Date-range filtering.
- Department filtering.
- Product filtering.
- Employee filtering.
- Customer filtering.
- Supplier filtering.
- Interactive charts.
- PDF export.
- Excel export.
- Monthly audit reports.

---

# Integrated Factory Workflow

The system connects the complete manufacturing and business lifecycle.

```text
SUPPLIER MANAGEMENT
        |
        v
PURCHASING & PROCUREMENT
        |
        v
GOODS RECEIPT & QUALITY INSPECTION
        |
        v
RAW MATERIAL INVENTORY
        |
        v
PRODUCTION PLANNING
        |
        v
MACHINE & WORKFORCE ALLOCATION
        |
        v
MANUFACTURING OPERATIONS
        |
        v
STAGE-WISE QUALITY CONTROL
        |
        v
PACKAGING
        |
        v
FINISHED GOODS WAREHOUSE
        |
        v
SALES ORDER & APPROVAL
        |
        v
GST INVOICE GENERATION
        |
        v
PICKING, PACKING & DISPATCH
        |
        v
DELIVERY CONFIRMATION
        |
        v
CUSTOMER PAYMENT
        |
        v
FINANCIAL ACCOUNTING
        |
        v
REPORTS & BUSINESS ANALYTICS
```

All departments share centralized records and controlled transaction workflows.

---

# Manufacturing Benchmark Scenario

The project includes a representative Murukku manufacturing scenario to validate operational accuracy.

### Product Configuration

- Product: Murukku.
- Variant: 200g.
- Standard batch target: 200 packets.

### Standard Bill of Materials

| Material | Standard Quantity |
|---|---:|
| Flour | 40 kg |
| Cooking Oil | 10 L |
| Salt and Spice Mix | 1.2 kg |
| Packaging Pouches | 200 |
| Cartons | 10 |

### Opening Inventory

| Material | Opening Quantity |
|---|---:|
| Flour | 100 kg |
| Cooking Oil | 30 L |
| Salt and Spice Mix | 5 kg |
| Packaging Pouches | 500 |
| Cartons | 30 |
| Finished Murukku 200g | 50 packets |

### Purchase Transaction

- Purchase 60 kg of flour.
- Purchase price: ₹45 per kg.
- Existing flour valuation: ₹42 per kg.

### Production Transaction

- Flour consumed: 40 kg.
- Cooking oil consumed: 10.5 L.
- Salt and spice consumed: 1.2 kg.
- Actual good output: 188 packets.
- Damaged pouches: 6.
- Cartons used: 9.

### Expected Production Results

- Standard output: 200 packets.
- Actual good output: 188 packets.
- Yield variance: -6%.
- Oil consumption variance: +5%.
- Finished goods after production: 238 packets.
- Finished goods after dispatch of 150 packets: 88 packets.

### Sales Transaction

Retailer A:

- Quantity: 150 packets.
- Selling price: ₹50 per packet.
- Taxable value: ₹7,500.
- CGST: ₹187.50.
- SGST: ₹187.50.
- Invoice total: ₹7,875.
- Payment received: ₹4,000.
- Outstanding amount: ₹3,875.

Distributor B:

- Requested quantity: 120 packets.
- Available stock after Retailer A dispatch: 88 packets.
- Shortage: 32 packets.

The system must block an insufficient-stock dispatch.

### Production Costing

The system should calculate actual batch costs from confirmed material consumption, packaging, labour and overhead transactions.

Illustrative expected costing:

| Cost Component | Amount |
|---|---:|
| Flour | ₹1,725 |
| Cooking Oil | ₹1,470 |
| Salt and Spice Mix | ₹240 |
| Packaging Pouches | ₹485 |
| Cartons | ₹135 |
| Labour | ₹1,200 |
| Gas and Electricity | ₹600 |
| Total | ₹5,855 |

Estimated cost per good packet: ₹31.14.

All benchmark calculations must be validated against actual ledger and transaction records.

---

# Business Rules & Data Integrity

## Inventory Integrity

- Purchase orders must not directly increase inventory.
- Accepted goods receipts increase inventory.
- Confirmed material issues decrease warehouse inventory.
- Production reservations do not physically consume stock.
- Finished goods increase only after production confirmation, QC approval and warehouse transfer.
- Confirmed dispatch decreases finished goods inventory.
- Inventory changes must be recorded through ledger transactions.
- Negative stock must be prevented unless an explicitly authorized policy permits it.
- Reversals must preserve historical transaction records.

## Production Integrity

- Production must follow configured BOMs.
- Production must follow configured manufacturing stages.
- Machine availability must be validated.
- Workforce availability must be validated.
- Production capacity must consider bottlenecks.
- Actual material consumption must be recorded.
- Rejected, accepted, damaged and reworked quantities must be tracked separately.
- Production completion must be confirmed by authorized personnel.
- Incomplete batches must support controlled carry-forward.

## Quality Integrity

- Rejected raw materials must not be available for production.
- Failed critical inspections must place affected batches on hold.
- Quarantined finished goods must not be dispatched.
- Rework must retain original batch traceability.
- Product recall must identify affected batches and customers.

## Sales Integrity

- Sales orders must not directly reduce physical inventory.
- Approved orders must follow stock validation.
- Reservations must be separate from physical dispatch.
- Invoices must follow authorization rules.
- Posted invoices must be corrected through credit notes or valid reversal procedures.
- Customer payments must be linked to the correct invoices.

## Financial Integrity

- All financial postings must follow double-entry accounting.
- Debit and credit totals must remain balanced.
- Financial transactions must not be duplicated.
- Posted transactions must not be deleted.
- Corrections must use appropriate reversal entries.
- GST must be accounted for separately.
- Production costs must flow correctly from raw materials to work in progress and finished goods.

## Voice Integrity

- Voice commands must follow existing role permissions.
- Important transactions require explicit confirmation.
- Financial approvals must verify authenticated identity.
- Voice recordings must preserve original audio.
- Transcripts must be editable without replacing the original audio.
- Unclear quantities or identities must trigger clarification.
- Voice commands must not bypass operational approval workflows.
- Shared recordings must use one unique recording ID.

---

# User Interface & Design

The application follows a professional and consistent ERP dashboard design.

### Design Direction

**Premium Warm Industrial ERP Dashboard**

### Color Palette

| Design Element | Color |
|---|---|
| Primary Caramel | `#B77950` |
| Mocha Brown | `#795548` |
| Baby Pink | `#F4C6CF` |
| Light Pink | `#FBE8EC` |
| Warm Cream | `#FFF9F5` |
| White Cards | `#FFFFFF` |
| Dark Cocoa Text | `#49352D` |
| Secondary Text | `#8A7B74` |
| Borders | `#EADDD5` |

### UI Characteristics

- Caramel-based navigation.
- Baby-pink active indicators.
- Warm cream page backgrounds.
- White dashboard cards.
- Professional typography.
- Consistent spacing.
- Reusable components.
- Responsive layouts.
- Interactive tables.
- Clear status indicators.
- Interactive charts.
- Subtle shadows.
- Rounded corners.
- Smooth transitions.
- Mobile and tablet support.

The visual design should remain professional and suitable for an industrial ERP application.

---

# Technology Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| Database | PostgreSQL |
| Database Connectivity | Psycopg2 |
| Frontend | HTML5 |
| Styling | CSS3 |
| UI Framework | Bootstrap |
| Client-Side Logic | JavaScript |
| Data Visualization | Chart.js |
| PDF Generation | ReportLab |
| Excel Processing | Pandas / OpenPyXL |
| Factory Visualization | HTML, CSS, JavaScript, SVG |
| Voice Recognition | Configurable Tamil-capable Speech-to-Text Service |
| Version Control | Git |
| Repository Hosting | GitHub |

---

# Database Architecture

PostgreSQL serves as the centralized relational database.

The database maintains relationships between:

- Users and roles.
- Employees and departments.
- Products and product variants.
- Production configurations and BOMs.
- Machines and maintenance records.
- Workforce and attendance.
- Production orders and batches.
- Raw materials and inventory transactions.
- Suppliers and purchase orders.
- Customers and sales orders.
- Invoices and payments.
- Quality inspections and batch records.
- Warehouses and dispatch transactions.
- Financial accounts and ledger entries.
- Voice recordings and ERP records.
- Notifications and audit logs.

### Database Requirements

- Referential integrity.
- Foreign key relationships.
- Appropriate indexes.
- Transaction management.
- Unique identifiers.
- Decimal-based monetary calculations.
- Secure database access.
- Migration support.
- Backup and recovery.
- Duplicate transaction prevention.
- Inventory concurrency protection.

---

# Security & Reliability

- Secure password hashing.
- Role-based authorization.
- Server-side permission validation.
- Parameterized SQL queries.
- Environment-based configuration.
- Secure session handling.
- Input validation.
- File upload validation.
- Protected audio storage.
- Audit logging.
- Database transaction management.
- Duplicate submission prevention.
- Error handling.
- Backup and recovery procedures.
- Access-controlled reports.
- Protection of confidential employee and financial records.

---

# Installation & Setup

## Prerequisites

- Python 3.
- PostgreSQL.
- Git.
- pip.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file using the project's configuration template.

Example:

```env
FLASK_APP=app.py
FLASK_ENV=development

DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_food_factory
DB_USER=postgres
DB_PASSWORD=your_database_password

SECRET_KEY=your_secure_secret_key

TIMEZONE=Asia/Kolkata
```

Replace example values with the actual project configuration.

Never upload real passwords, API keys or secret credentials to GitHub.

### 5. Configure PostgreSQL

Create the project database and execute the SQL initialization scripts or migrations provided by the project.

### 6. Configure Voice Recognition

Configure the selected Tamil-capable speech recognition provider using the required environment variables or secure configuration settings.

Do not expose API keys in frontend code.

Provide manual transcript correction when speech recognition is unavailable.

### 7. Run the Application

```bash
python app.py
```

Open the local application address displayed by Flask.

Use the actual startup instructions provided by the repository if they differ from this example.

---

# Project Architecture

The application follows a modular ERP architecture.

Recommended logical organization:

```text
Smart-Food-Manufacturing-Factory/
│
├── app/
│   ├── authentication/
│   ├── dashboard/
│   ├── factory_setup/
│   ├── production/
│   ├── production_overflow/
│   ├── inventory/
│   ├── procurement/
│   ├── sales/
│   ├── finance/
│   ├── workforce/
│   ├── machines/
│   ├── quality/
│   ├── maintenance/
│   ├── warehouse/
│   ├── dispatch/
│   ├── voice_assistant/
│   ├── reports/
│   ├── notifications/
│   └── audit/
│
├── templates/
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── audio/
│
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── migrations/
│
├── services/
├── utils/
├── tests/
│
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py
└── README.md
```

This is a recommended logical structure. The actual implementation should follow the existing repository architecture without creating unnecessary duplicate folders or modules.

---

# Testing & Validation

The system should be tested using real operational workflows and integrated business scenarios.

### Functional Testing

- User authentication.
- Role permissions.
- Factory initialization.
- Product configuration.
- BOM management.
- Machine allocation.
- Workforce allocation.
- Production execution.
- Inventory movements.
- Procurement.
- Goods receipt.
- Quality inspection.
- Sales orders.
- GST billing.
- Customer payments.
- Financial accounting.
- Warehouse operations.
- Dispatch.
- Maintenance.
- Automatic date and time calculations.
- Tamil voice recording.
- English voice recording.
- Tamil-English mixed speech.
- Location-based recording.
- Record-based recording.
- Voice confirmation.
- Approval workflows.
- Reports and exports.
- Audit history.

### Data Integrity Testing

- Duplicate transaction prevention.
- Negative inventory prevention.
- Inventory ledger reconciliation.
- Financial debit-credit balancing.
- Correct GST calculations.
- Batch traceability.
- Permission validation.
- Transaction rollback.
- Historical timestamp preservation.

---

# Future Enhancements

Potential future improvements include:

- Advanced production forecasting.
- IoT-based machine monitoring.
- Sensor-based temperature and humidity monitoring.
- Predictive maintenance.
- Advanced production analytics.
- Deeper Tamil voice automation.
- Mobile-friendly factory operations.
- Integration with external accounting services.
- Eligible GST compliance integrations.
- Advanced business intelligence.

---

# Project Scope & Development Philosophy

Smart Food Manufacturing Factory is designed as one unified ERP ecosystem rather than a collection of independent management applications.

All modules share:

- Centralized authentication.
- Common database architecture.
- Shared business records.
- Consistent role permissions.
- Common approval workflows.
- Centralized notifications.
- Unified audit history.
- Shared reporting services.
- Automated date and time management.
- Factory-wide voice interaction.

The system prioritizes operational accuracy, data integrity, traceability, automation, usability and centralized decision-making.

---

# Project Information

| Attribute | Details |
|---|---|
| Project Name | Smart Food Manufacturing Factory |
| Project Type | Integrated Enterprise Resource Planning System |
| Domain | Food Manufacturing |
| Backend | Python Flask |
| Database | PostgreSQL |
| Frontend | HTML, CSS, Bootstrap, JavaScript |
| Voice Support | Tamil and English |
| Timezone | Asia/Kolkata |
| Repository | GitHub |

---


**Smart Food Manufacturing Factory**

*Connecting People, Production, Resources and Business Operations.*

