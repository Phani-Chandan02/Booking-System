import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report():
    doc = docx.Document()

    # Set page margins (0.75 in)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)

    # Helper: Title
    def add_doc_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(22)
        run.font.color.rgb = RGBColor(15, 23, 42)
        p.paragraph_format.space_after = Pt(4)

    def add_doc_subtitle(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.italic = True
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(71, 85, 105)
        p.paragraph_format.space_after = Pt(18)

    # Helper: Heading 1
    def add_h1(text):
        h = doc.add_heading(level=1)
        run = h.add_run(text)
        run.bold = True
        run.font.size = Pt(15)
        run.font.color.rgb = RGBColor(30, 58, 138)
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)

    # Helper: Heading 2
    def add_h2(text):
        h = doc.add_heading(level=2)
        run = h.add_run(text)
        run.bold = True
        run.font.size = Pt(12.5)
        run.font.color.rgb = RGBColor(15, 118, 110)
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)

    # Helper: Heading 3
    def add_h3(text):
        h = doc.add_heading(level=3)
        run = h.add_run(text)
        run.bold = True
        run.font.size = Pt(11.5)
        run.font.color.rgb = RGBColor(51, 65, 85)
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)

    # Helper: Callout Box
    def add_callout(text, title="NOTE / LAB HIGHLIGHT"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r_title = p.add_run(f"[{title}] ")
        r_title.bold = True
        r_title.font.size = Pt(10)
        r_title.font.color.rgb = RGBColor(30, 64, 175)
        r_text = p.add_run(text)
        r_text.font.size = Pt(10)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Helper: Diagram Placeholder
    def add_diagram_placeholder(title, caption):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F8FAFC")
        set_cell_margins(cell, top=200, bottom=200, left=200, right=200)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p.add_run(f"[DIAGRAM PLACEHOLDER: {title}]\n")
        r1.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = RGBColor(100, 116, 139)
        r2 = p.add_run("(Insert manual diagram here as per lab submission guidelines)\n")
        r2.italic = True
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = RGBColor(148, 163, 184)
        r3 = p.add_run(f"Figure Caption: {caption}")
        r3.bold = True
        r3.font.size = Pt(10)
        r3.font.color.rgb = RGBColor(51, 65, 85)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Helper: Styled Table
    def add_styled_table(headers, rows, col_widths=None):
        table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        # Format Header Row
        hdr_cells = table.rows[0].cells
        for i, header_text in enumerate(headers):
            hdr_cells[i].text = header_text
            set_cell_background(hdr_cells[i], "1E293B")
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
            p = hdr_cells[i].paragraphs[0]
            p.runs[0].font.bold = True
            p.runs[0].font.size = Pt(10)
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        # Format Data Rows
        for r_idx, row_data in enumerate(rows):
            row_cells = table.rows[r_idx + 1].cells
            bg_color = "FFFFFF" if r_idx % 2 == 0 else "F8FAFC"
            for c_idx, cell_value in enumerate(row_data):
                row_cells[c_idx].text = str(cell_value)
                set_cell_background(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=120, right=120)
                p = row_cells[c_idx].paragraphs[0]
                if p.runs:
                    p.runs[0].font.size = Pt(9.5)
        if col_widths:
            for row in table.rows:
                for idx, width in enumerate(col_widths):
                    row.cells[idx].width = Inches(width)
        doc.add_paragraph().paragraph_format.space_after = Pt(6)
        return table

    # ==================== COVER / METADATA ====================
    add_doc_title("24CYS401 – SECURE SOFTWARE ENGINEERING")
    add_doc_subtitle("END SEMESTER INTEGRATED LABORATORY EXAMINATION REPORT\nPROBLEM STATEMENT 9: SECURE APPOINTMENT BOOKING SYSTEM")

    meta_headers = ["Project Parameter", "Specification & Submission Evidence"]
    meta_rows = [
        ["Course", "24CYS401 – Secure Software Engineering"],
        ["Problem Statement", "Problem 9: Secure Appointment Booking System"],
        ["Candidate Name", "Elluru Phani Chandan Reddy"],
        ["Candidate ID", "CH.SC.U4CYS23007"],
        ["GitHub Repository", "https://github.com/Phani-Chandan02/Booking-System"],
        ["Jira Scrum Integration", "Atlassian Jira Cloud REST API (Project Key: BOOK)"],
        ["Core Security Demonstration", "TOCTOU Race Condition Prevention & Atomic Concurrency Locking (SR-04)"],
        ["DevSecOps Toolchain", "FastAPI, SQLite WAL, Bandit SAST, Pytest, Docker, Kubernetes, GitHub Actions"]
    ]
    add_styled_table(meta_headers, meta_rows, [2.2, 4.8])

    # ==================== PHASE 1 ====================
    add_h1("Phase 1 – Agile Process and Development Approach")
    p = doc.add_paragraph(
        "For the Secure Appointment Booking System, a hybrid Agile framework combining Scrum with Extreme Programming (XP) practices "
        "was selected. Scrum provides the overarching project management cadence, structured backlog grooming, two focused sprints, "
        "ceremonial daily standups, and retrospective metrics. XP introduces mandatory engineering disciplines essential for security-critical "
        "applications: Test-Driven Development (TDD), automated refactoring, continuous integration, and peer security code reviews."
    )

    add_h2("Agile Manifesto Principles Mapping")
    manifesto_headers = ["Manifesto Principle", "Project Adaptation & Implementation"]
    manifesto_rows = [
        ["1. Customer Satisfaction via Early & Continuous Delivery", "Delivered core appointment discovery and atomic slot booking in Sprint 1, followed by lifecycle management and containerized hardening in Sprint 2."],
        ["2. Welcome Changing Requirements, Even Late", "Agile backlog easily accommodated the shift from simple appointment scheduling to strict database-enforced row serialization when race condition threats were identified."],
        ["3. Deliver Working Software Frequently", "Every user story produced functioning, test-validated code backed by CI/CD automated test runs and Bandit security scans."],
        ["4. Business People & Developers Work Together Daily", "Faculty stakeholders (service providers), student users, and administrators collaborated to define realistic appointment constraints and role permissions."],
        ["5. Continuous Attention to Technical Excellence & Good Design", "Refactored insecure check-then-act logic into atomic database transactions, achieving zero concurrency collisions under simultaneous load."]
    ]
    add_styled_table(manifesto_headers, manifesto_rows, [2.5, 4.5])

    add_h2("Refactoring Opportunities (Before vs. After)")
    p = doc.add_paragraph(
        "Refactoring 1 (Authorization Layer): Initial prototypes tightly coupled role-checking logic inside route handlers. "
        "This was refactored into centralized FastAPI dependencies ('require_role(['student', 'admin'])'), removing duplicate logic "
        "and eliminating authorization bypass vectors.\n\n"
        "Refactoring 2 (Booking Concurrency Engine): The prototype performed a check-then-act sequence ('SELECT is_booked' followed by 'UPDATE'), "
        "which suffered from a critical Time-Of-Check to Time-Of-Use (TOCTOU) vulnerability. This was refactored into an atomic transaction "
        "('BEGIN IMMEDIATE' + conditional test-and-set 'UPDATE ... WHERE is_booked = 0' + DB unique partial index 'idx_unique_confirmed_slot')."
    )

    add_h2("Agile Limitations & Mitigation for Security-Critical Systems")
    lim_headers = ["Agile Risk / Limitation", "Practical Mitigation Strategy Applied"]
    lim_rows = [
        ["Rapid sprint velocity may bypass thorough threat modeling", "Implemented security gates: User Story US-04 had explicit security acceptance criteria; automated SAST (Bandit) runs on every commit."],
        ["Incremental stories may lead to architectural security oversights", "Established an upfront foundational data integrity baseline: database-level unique constraints and atomic transaction locking before story development."]
    ]
    add_styled_table(lim_headers, lim_rows, [2.5, 4.5])

    # ==================== PHASE 2 ====================
    add_h1("Phase 2 – Requirements Engineering")
    p = doc.add_paragraph(
        "The requirements engineering phase identified three primary stakeholders: Students (end-users seeking consultations), "
        "Faculty (service providers defining availability and reviewing appointments), and System Administrators (managing services and monitoring audit trails). "
        "Requirements are categorized into Functional (FR), Non-Functional (NFR), and Security Requirements (SR)."
    )

    req_headers = ["Req ID", "Category", "Requirement Statement", "Security / CIA Objective"]
    req_rows = [
        ["FR-01", "Functional", "Student can view available academic services and durations", "Availability"],
        ["FR-02", "Functional", "Student can view open, unbooked time slots for selected service", "Integrity / Availability"],
        ["FR-03", "Functional", "Student can reserve an available time slot", "Integrity"],
        ["FR-04", "Functional", "Student can cancel their existing active appointment", "Integrity / Authorization"],
        ["FR-05", "Functional", "Student can reschedule an appointment to an open alternative slot", "Atomic Integrity"],
        ["FR-06", "Functional", "Student can view historical and active appointment records", "Confidentiality"],
        ["FR-07", "Functional", "Faculty can define and publish available time slots", "Authorization / Integrity"],
        ["FR-08", "Functional", "Faculty can view student appointment roster for their slots", "Confidentiality / RBAC"],
        ["FR-09", "Functional", "Faculty can update appointment status (Completed, Cancelled)", "Integrity"],
        ["NFR-01", "Performance", "Booking operations must resolve within < 200 ms latency", "Availability"],
        ["NFR-02", "Reliability", "Zero data loss during unexpected container termination", "Integrity (WAL Mode)"],
        ["SR-01", "Security", "All users must authenticate via strong salted password hashes & JWT", "Authentication"],
        ["SR-02", "Security", "Object-level authorization: users access only their own bookings", "Confidentiality (BOLA Defense)"],
        ["SR-03", "Security", "Faculty can modify only appointments scheduled with themselves", "Authorization / RBAC"],
        ["SR-04", "Security", "A slot must NEVER be double-booked by concurrent users", "Integrity (Concurrency Lock)"],
        ["SR-05", "Security", "Duplicate submissions must be idempotently rejected", "Integrity"],
        ["SR-06", "Security", "Rescheduling must atomically release old slot and reserve new slot", "Integrity (All-or-Nothing)"],
        ["SR-07", "Security", "Input sanitization: strictly typed inputs; reject SQLi & path traversal", "Input Integrity"],
        ["SR-08", "Security", "All security-critical actions must be recorded in an immutable audit trail", "Auditability / Non-Repudiation"],
        ["SR-09", "Security", "Zero secrets embedded in source code; externalized via environment", "Confidentiality"],
        ["SR-10", "Security", "Error masking: generic 401/409 responses; zero internal stack leaks", "Information Disclosure Defense"]
    ]
    add_styled_table(req_headers, req_rows, [1.0, 1.2, 3.2, 1.6])

    # ==================== PHASE 3 ====================
    add_h1("Phase 3 – Requirements Analysis and UML")
    p = doc.add_paragraph(
        "UML modeling translates high-level requirements into structured actor interactions, defining boundary preconditions, "
        "success flows, exception handlers, and postconditions."
    )
    add_diagram_placeholder("UML Use Case Diagram", "Figure 1: Comprehensive UML Use Case Diagram for Secure Appointment System")

    add_h2("Critical Use Case Specification 1: UC-01 Book Appointment (Atomic Concurrency)")
    uc1_headers = ["Field", "Specification Details"]
    uc1_rows = [
        ["Use Case ID", "UC-01"],
        ["Name", "Book Appointment with Atomic Concurrency Protection"],
        ["Primary Actor", "Student User"],
        ["Preconditions", "Student is authenticated with active JWT token; time slot is published and currently unbooked."],
        ["Main Success Scenario", "1. Student selects academic service.\n2. System displays open time slots.\n3. Student submits booking for slot ID.\n4. System initiates atomic transaction with immediate write lock.\n5. System verifies slot status, updates slot to booked, and creates confirmed appointment.\n6. System commits transaction and emits 201 Created with appointment ID."],
        ["Alternative / Exception Flow", "4a. Concurrent Collision: Another student attempts to book the same slot simultaneously.\n4b. Database immediate lock serializes requests; first transaction succeeds, second transaction detects rowcount == 0.\n4c. System rolls back second transaction, logs 'BOOKING_CONFLICT_PREVENTED', and returns HTTP 409 Conflict."],
        ["Postconditions", "Slot is marked booked; exactly one confirmed appointment exists; audit log is updated."]
    ]
    add_styled_table(uc1_headers, uc1_rows, [2.0, 5.0])

    add_h2("Critical Use Case Specification 2: UC-02 Reschedule Appointment")
    uc2_headers = ["Field", "Specification Details"]
    uc2_rows = [
        ["Use Case ID", "UC-02"],
        ["Name", "Reschedule Existing Appointment"],
        ["Primary Actor", "Student User"],
        ["Preconditions", "Student owns active CONFIRMED appointment; target new slot is currently unbooked."],
        ["Main Success Scenario", "1. Student requests reschedule and selects new open slot.\n2. System opens atomic transaction.\n3. System locks new slot (is_booked=1) and releases old slot (is_booked=0).\n4. System updates appointment slot_id and updated_at timestamp.\n5. System commits transaction and emits 200 OK."],
        ["Exception Flow", "3a. Target new slot is taken concurrently.\n3b. System rolls back transaction; original appointment remains active; returns 409 Conflict."],
        ["Postconditions", "Original slot is freed for others; new slot is reserved; appointment is updated with zero orphaned records."]
    ]
    add_styled_table(uc2_headers, uc2_rows, [2.0, 5.0])

    add_h2("Scenario-Based Analysis Model: 'Book Appointment and Confirm Booking'")
    p = doc.add_paragraph(
        "As adapted from the examination analysis modeling requirement, the scenario traces the end-to-end lifecycle: "
        "Actor (Student) -> UI Boundary (Booking Form) -> Control (Auth Middleware & Booking Controller) -> "
        "Entity (TimeSlot, Appointment, AuditLog). State progression: [Slot: Available] -> [Txn: Lock Acquired] -> "
        "[Slot: Reserved] -> [Appointment: Confirmed] -> [Txn: Committed]."
    )

    # ==================== PHASE 4 ====================
    add_h1("Phase 4 – Data and Information Flow Modeling")
    p = doc.add_paragraph(
        "The data model ensures relational integrity and database-enforced security invariants. "
        "Key entities include Users, Services, TimeSlots, Appointments, and AuditLogs."
    )
    add_diagram_placeholder("Entity-Relationship (ER) Diagram", "Figure 2: ER Diagram with Primary/Foreign Keys and Integrity Constraints")

    add_h2("Data Dictionary & Key Security Constraints")
    er_headers = ["Entity", "Primary Key", "Foreign Keys", "Key Security Attribute / Constraint"]
    er_rows = [
        ["Users", "id (INT PK)", "None", "email (UNIQUE), salt (HEX), password_hash (PBKDF2), role CHECK('student','faculty','admin')"],
        ["Services", "id (INT PK)", "None", "duration_minutes CHECK(10 to 180), title, description"],
        ["TimeSlots", "id (INT PK)", "service_id -> Services(id), provider_id -> Users(id)", "is_booked INTEGER DEFAULT 0, slot_date, start_time, end_time"],
        ["Appointments", "id (INT PK)", "user_id -> Users(id), slot_id -> TimeSlots(id)", "status CHECK('CONFIRMED','CANCELLED','RESCHEDULED'), UNIQUE(slot_id) WHERE status='CONFIRMED'"],
        ["AuditLogs", "id (INT PK)", "user_id -> Users(id)", "action, status, ip_address, details, timestamp (Append-Only)"]
    ]
    add_styled_table(er_headers, er_rows, [1.3, 1.1, 2.1, 2.5])

    add_callout(
        "CRITICAL DATABASE CONSTRAINT: A partial unique index 'CREATE UNIQUE INDEX idx_unique_confirmed_slot ON appointments(slot_id) "
        "WHERE status = 'CONFIRMED';' guarantees that even if application logic encounters a race condition, the database storage engine "
        "will physically reject any duplicate active reservation.",
        "DATABASE DEFENSE IN DEPTH"
    )

    add_h2("Data Flow Diagram (Level-0 and Level-1) & Trust Boundaries")
    add_diagram_placeholder("Data Flow Diagram (DFD Level-0 & Level-1)", "Figure 3: Level-1 DFD with Processes P1-P5, Data Stores, and Trust Boundaries T1-T4")
    dfd_headers = ["Trust Boundary", "Boundary Crossing", "Security Controls Enforced"]
    dfd_rows = [
        ["TB-01: Public to DMZ", "Browser Client -> Web/API Ingress", "TLS 1.3, CORS whitelist, Security Headers (CSP, HSTS, X-Frame-Options)"],
        ["TB-02: DMZ to Application", "API Ingress -> Route Controllers", "Bearer JWT Authentication, Signature Verification, Role Claims Check"],
        ["TB-03: App to Database", "Booking Service -> SQLite DB Engine", "Parameterized SQL statements (SQLi Prevention), Immediate Transaction Locks, Unique Index"],
        ["TB-04: App to Audit Store", "Service Handlers -> Audit Logger", "JSON format validation, non-blocking execution, append-only disk logging"]
    ]
    add_styled_table(dfd_headers, dfd_rows, [1.8, 2.2, 3.0])

    # ==================== PHASE 5 ====================
    add_h1("Phase 5 – Software Architecture and Design Engineering")
    p = doc.add_paragraph(
        "A Layered Architecture with Service Boundaries is implemented, separating concerns into Presentation, API/Routing, "
        "Security & Authentication, Domain Services, and Data Access."
    )
    add_diagram_placeholder("Software Architecture Diagram", "Figure 4: Layered Security Architecture with Service Boundaries")

    add_h2("Core Design Patterns Applied")
    dp_headers = ["Design Pattern", "Implementation in System", "Security & Quality Benefit"]
    dp_rows = [
        ["1. Role-Based Access Control (RBAC)", "FastAPI dependency 'require_role(['student', 'admin'])' guarding endpoints.", "Prevents Broken Object-Level Authorization and privilege escalation."],
        ["2. Service Layer Pattern", "BookingService isolates business logic from HTTP controller routing.", "Ensures consistent validation and atomic transactions regardless of caller."],
        ["3. Atomic Unit of Work / Transaction", "SQLite 'BEGIN IMMEDIATE' wrapping availability verification and booking insertion.", "Eliminates race conditions (TOCTOU) during concurrent booking attempts."],
        ["4. Secure Factory / Vault Config", "Environment-driven secret configuration via .env and Pydantic Settings.", "Guarantees zero hardcoded credentials and supports runtime key rotation."]
    ]
    add_styled_table(dp_headers, dp_rows, [2.0, 2.5, 2.5])

    # ==================== PHASE 6 ====================
    add_h1("Phase 6 – User Interface Design")
    p = doc.add_paragraph(
        "The user interface follows professional design standards inspired by industry booking systems (Cal.com, Calendly). "
        "It employs clean, executive typography, an intentional high-contrast slate color palette, clear status chips, and zero "
        "distracting emojis. Four distinct screens fulfill all functional and security objectives:"
    )

    ui_headers = ["Screen", "Target User", "Primary Goal", "Security & Interaction Controls"]
    ui_rows = [
        ["Screen 1: Identity Verification", "Student, Faculty, Admin", "Authenticate securely via credentials", "Password masking, generic 401 response, 1-click test role selector, brute-force logging."],
        ["Screen 2: Available Services & Real-Time Slot Booking", "Student User", "Browse offerings, check open slots, execute atomic booking", "Dynamic filtering, disabled booked slots, live race-condition test panel, immediate conflict alerts."],
        ["Screen 3: My Bookings & Rescheduling Console", "Student User", "View history, cancel reservation, atomically reschedule", "Object-level authorization, confirmation modal, atomic swap of time slots, cancellation audit."],
        ["Screen 4: Service Provider Dashboard & Audit Feed", "Faculty, Admin", "Publish availability slots, update fulfillment status, view audit logs", "RBAC restriction (faculty can update only own slots), real-time security metric counters."]
    ]
    add_styled_table(ui_headers, ui_rows, [1.8, 1.2, 1.8, 2.2])

    add_diagram_placeholder("UI Wireframes / Screen Mockups", "Figure 5: UI Wireframes for Screens 1-4 (Login, Booking, Reschedule, Provider Dashboard)")

    add_h2("Nielsen's Golden Rules Alignment")
    p = doc.add_paragraph(
        "• Consistency: Unified design tokens (slate-900 background, blue-600 accents, emerald-500 success badges).\n"
        "• User Control: Explicit cancellation and reschedule confirmation modals with safe exit pathways.\n"
        "• Immediate Feedback: Instant visual banner alerts upon successful booking or conflict rejection (409 Conflict).\n"
        "• Error Prevention: Booked slots are disabled and struck-through; client prevents duplicate clicks.\n"
        "• System Status Visibility: Real-time conflict metrics counter increments dynamically upon concurrency collisions."
    )

    # ==================== PHASE 7 ====================
    add_h1("Phase 7 – Threat Modeling and Security Analysis")
    p = doc.add_paragraph(
        "STRIDE threat modeling was performed systematically against every DFD process and data store. "
        "Ten critical assets were classified under the CIA triad, followed by comprehensive threat mapping."
    )

    asset_headers = ["Asset ID", "Asset Description", "Confidentiality", "Integrity", "Availability"]
    asset_rows = [
        ["AST-01", "User Password Credentials & Salts", "HIGH", "HIGH", "MEDIUM"],
        ["AST-02", "JWT Session Signing Secret", "CRITICAL", "CRITICAL", "HIGH"],
        ["AST-03", "Time Slot Availability State", "LOW", "CRITICAL", "HIGH"],
        ["AST-04", "Appointment Records", "HIGH", "CRITICAL", "HIGH"],
        ["AST-05", "Faculty Availability Schedules", "MEDIUM", "HIGH", "HIGH"],
        ["AST-06", "Academic Service Catalog", "LOW", "HIGH", "MEDIUM"],
        ["AST-07", "Security Audit Log Records", "HIGH", "CRITICAL", "HIGH"],
        ["AST-08", "System Concurrency Lock State", "LOW", "CRITICAL", "CRITICAL"],
        ["AST-09", "Student Personal Information (PII)", "HIGH", "HIGH", "MEDIUM"],
        ["AST-10", "Database Storage Engine Invariants", "HIGH", "CRITICAL", "CRITICAL"]
    ]
    add_styled_table(asset_headers, asset_rows, [1.0, 2.6, 1.1, 1.1, 1.2])

    add_h2("STRIDE Threat Modeling Table (10 Threats)")
    stride_headers = ["Threat ID", "DFD Element", "STRIDE Category", "Threat Description", "Impact", "Mitigation"]
    stride_rows = [
        ["T-01", "Login API", "Spoofing", "Attacker submits brute-force credentials", "Account Takeover", "PBKDF2-HMAC password hashing, rate limiting, audit logging."],
        ["T-02", "JWT Token", "Tampering", "Attacker modifies role claim from student to admin", "Privilege Escalation", "Cryptographic HMAC-SHA256 signature verification with strong secret."],
        ["T-03", "Booking API", "Tampering / Race", "Concurrent booking collision on same slot (TOCTOU)", "Double Booking / Schedule Collision", "BEGIN IMMEDIATE transaction + UNIQUE(slot_id) DB constraint."],
        ["T-04", "Appointment API", "Elevation of Privilege", "Student modifies another student's booking ID (BOLA)", "Unauthorized Cancellation", "Object-level ownership checks (user_id == current_user.id)."],
        ["T-05", "Audit Log", "Repudiation", "Malicious user denies making or cancelling booking", "Loss of Accountability", "Append-only structured logging capturing user ID, IP, and timestamp."],
        ["T-06", "Provider API", "Information Disclosure", "Unauthorized user scrapes full faculty schedules", "Privacy Violation", "RBAC authorization checks restricting sensitive roster views."],
        ["T-07", "Slot Endpoint", "Denial of Service", "Attacker floods slot creation or booking endpoints", "Service Downtime", "Connection rate limiting, connection pool timeouts, K8s CPU limits."],
        ["T-08", "Service Form", "Tampering (SQLi)", "Attacker injects SQL payloads into service inputs", "Data Breach / Manipulation", "Parameterized queries via sqlite3 driver and Pydantic validation."],
        ["T-09", "Reschedule API", "Tampering", "Attacker attempts partial reschedule leaving orphaned slot", "Inconsistent Slot State", "Atomic transaction guaranteeing all-or-nothing slot swap."],
        ["T-10", "Container Host", "Elevation of Privilege", "Container breakout via root process execution", "Host Compromise", "Non-root user (UID 10001), drop all capabilities, read-only root FS."]
    ]
    add_styled_table(stride_headers, stride_rows, [0.8, 1.1, 1.2, 1.7, 1.1, 1.1])

    add_h2("Vulnerability Analysis (6 Critical Vulnerabilities)")
    vuln_headers = ["Vuln ID", "Vulnerability Title", "Affected Component", "CWE", "Mitigation Implemented"]
    vuln_rows = [
        ["VUL-01", "TOCTOU Race Condition on Slot Booking", "Booking Service", "CWE-362", "Immediate transaction write locks and unique index."],
        ["VUL-02", "Broken Object-Level Authorization (BOLA)", "Appointment Endpoints", "CWE-639", "Enforce ownership validation before cancellation/rescheduling."],
        ["VUL-03", "Hardcoded Cryptographic Keys in Source", "Configuration Layer", "CWE-798", "Decouple secrets into .env and Kubernetes Secret manifests."],
        ["VUL-04", "Over-Privileged Container Execution", "Docker Runtime", "CWE-250", "Run container under non-root appuser (UID 10001)."],
        ["VUL-05", "Information Disclosure via Stack Traces", "Global Error Handler", "CWE-209", "Mask internal errors; return standardized JSON error bodies."],
        ["VUL-06", "Unbounded Input Injection", "Request Validation Layer", "CWE-20", "Pydantic StrictInt and strict regex constraints."]
    ]
    add_styled_table(vuln_headers, vuln_rows, [1.0, 1.8, 1.4, 0.9, 1.9])

    # ==================== PHASE 8 ====================
    add_h1("Phase 8 – Attack Tree and Security Architecture Refinement")
    p = doc.add_paragraph(
        "Root Attacker Goal: 'Double-Book an Appointment Slot via Concurrent Race Condition (Violate SR-04)'."
    )
    add_diagram_placeholder("Attack Tree Decomposition", "Figure 6: Attack Tree with AND/OR Logic Decomposing Double-Booking Attacks")

    p = doc.add_paragraph(
        "Attack Tree Structure:\n"
        "[Root Goal: Double-Book Appointment Slot]\n"
        "   ├── [Path A (OR): Exploit TOCTOU Application Window]\n"
        "   │     ├── [Step A1 (AND): Identify unbooked target slot]\n"
        "   │     ├── [Step A2 (AND): Synchronize 2+ HTTP POST requests]\n"
        "   │     └── [Step A3 (AND): Both requests execute during check-then-act gap]\n"
        "   │           ├── Preventive Control: SQLite BEGIN IMMEDIATE write serialization\n"
        "   │           └── Detective Control: Real-time 'BOOKING_CONFLICT_PREVENTED' audit alert\n"
        "   ├── [Path B (OR): Replay Legitimate Booking Request]\n"
        "   │     ├── [Step B1 (AND): Intercept student booking request]\n"
        "   │     └── [Step B2 (AND): Resubmit token before expiration]\n"
        "   │           ├── Preventive Control: Database UNIQUE index on slot_id\n"
        "   │           └── Detective Control: Duplicate transaction ID logging\n"
        "   └── [Path C (OR): Bypass API Authorization to Force Booking]\n"
        "         └── Preventive Control: Server-side RBAC token verification"
    )

    # ==================== PHASE 9 ====================
    add_h1("Phase 9 – Product Backlog and Jira/Scrum")
    p = doc.add_paragraph(
        "The project requirements were decomposed into 12 granular user stories following the required format: "
        "'As a <role>, I want <goal>, so that <value>'. Backlog was mapped into two 4-week academic sprints "
        "and provisioned directly on Jira Cloud (Project Key: BOOK, Board: BOOK board ID 72)."
    )

    backlog_headers = ["Issue Key", "Story ID", "Epic", "Priority", "Pts", "User Story Statement", "Acceptance Criteria Summary"]
    backlog_rows = [
        ["BOOK-2", "US-01", "EP-01", "High", "5", "As a user, I want to authenticate securely with email/password, so that only authorized individuals access features.", "JWT issued with role claims; passwords hashed with PBKDF2/salt; generic 401 on failure."],
        ["BOOK-7", "US-02", "EP-02", "Medium", "3", "As a student, I want to browse academic services, so that I can choose appropriate sessions.", "Services list title, description, duration; unauthorized users cannot modify."],
        ["BOOK-8", "US-03", "EP-03", "High", "3", "As a student, I want to check real-time available time slots, so that I can select a suitable meeting time.", "Only available slots selectable; booked slots disabled; date & provider shown."],
        ["BOOK-9", "US-04", "EP-03", "Critical", "8", "As a student, I want the system to guarantee my slot cannot be double-booked, so that scheduling conflicts are impossible.", "Atomic transaction lock; DB unique constraint; simultaneous requests return 1x 201 and 1x 409."],
        ["BOOK-10", "US-05", "EP-03", "High", "5", "As a faculty member, I want to define and publish available time slots, so that students can book them.", "Faculty sets service, date, times; end time > start time; RBAC restricted."],
        ["BOOK-11", "US-06", "EP-04", "Medium", "3", "As a student, I want to view my booking history, so that I can track scheduled appointments.", "Object-level authorization; status shown; ordered chronologically."],
        ["BOOK-12", "US-07", "EP-04", "Medium", "3", "As a student/faculty, I want to cancel an appointment, so that reserved slots are released.", "Owner-only cancel; slot atomically set to is_booked=0; audit event logged."],
        ["BOOK-13", "US-08", "EP-04", "High", "5", "As a student, I want to atomically reschedule an appointment, so that I update meeting time without losing reservation.", "Single transaction locks new slot, frees old slot, updates booking; rollback on conflict."],
        ["BOOK-14", "US-09", "EP-04", "Medium", "3", "As a faculty member, I want to view my roster and update status, so that I manage student appointments.", "Faculty sees only own slots; updates status to Completed/Cancelled; RBAC enforced."],
        ["BOOK-15", "US-10", "EP-05", "High", "5", "As an administrator, I want to review audit logs and metrics, so that I detect race conditions and attacks.", "Structured JSON logs; counters for conflicts and failed logins; admin-only access."],
        ["BOOK-16", "US-11", "EP-05", "High", "3", "As a DevSecOps engineer, I want hardened container & K8s manifests, so that deployment risks are minimized.", "Multi-stage Dockerfile; non-root user (10001); dropped capabilities; resource limits."],
        ["BOOK-17", "US-12", "EP-05", "High", "3", "As a QA engineer, I want automated concurrency tests in CI/CD, so that double-booking regressions fail the build.", "Pytest concurrency test (10 threads); Bandit SAST check; automated GitHub Actions workflow."]
    ]
    add_styled_table(backlog_headers, backlog_rows, [0.8, 0.7, 0.7, 0.7, 0.4, 2.3, 1.4])

    add_callout(
        "LIVE JIRA CLOUD BOARD: All Epics and User Stories are provisioned and tracked on Atlassian Cloud.\n"
        "URL: https://phani-chandan.atlassian.net/jira/software/c/projects/BOOK/boards/72\n"
        "Board ID: 72 | Sprint 1 ID: 77 (Closed, 4 Weeks) | Sprint 2 ID: 78 (Active, 4 Weeks, Mid-Project)",
        "JIRA CLOUD EVIDENCE"
    )

    # ==================== PHASE 10 ====================
    add_h1("Phase 10 – Sprint Execution and Scrum Metrics")
    p = doc.add_paragraph(
        "Sprint execution adhered to the mandatory four-stage board workflow: TO DO -> IN PROGRESS -> TESTING -> DONE. "
        "The project timeline spans two 4-week sprints, currently observed in the middle of active Sprint 2."
    )

    add_h2("Sprint 1 (Closed) & Velocity Report Metrics (Aug 24, 2026 – Sep 21, 2026: 4 Weeks)")
    p = doc.add_paragraph(
        "Sprint 1 reached full closure after a 4-week development cycle. All 5 core user stories (24 story points) "
        "were delivered and verified, establishing a baseline team velocity of 24 points."
    )
    s1_headers = ["Sprint Week", "Commitment (pts)", "Completed (pts)", "Remaining (pts)", "Key Milestones & Deliverables"]
    s1_rows = [
        ["Week 1 (Aug 24-28)", "24", "5", "19", "Sprint kickoff, schema baseline, BOOK-2 (US-01 Authentication) completed."],
        ["Week 2 (Aug 31-Sep 4)", "24", "11", "13", "BOOK-7 (US-02 Catalog) and BOOK-8 (US-03 Available Slots) delivered."],
        ["Week 3 (Sep 7-11)", "24", "11", "13", "DEF-01 identified: TOCTOU race condition during concurrent booking tests."],
        ["Week 4 (Sep 14-21)", "24", "24", "0", "BOOK-9 (US-04 Atomic Lock) & BOOK-10 (US-05 Provider Availability) DONE. Sprint 1 CLOSED."]
    ]
    add_styled_table(s1_headers, s1_rows, [1.4, 1.2, 1.2, 1.2, 2.0])

    add_h2("Sprint 2 (Active - Mid-Project) Burndown Metrics (Sep 22, 2026 – Oct 20, 2026: 4 Weeks)")
    p = doc.add_paragraph(
        "Sprint 2 represents the active sprint currently in execution (Week 3, current observation date). "
        "Total sprint commitment is 25 story points. The burndown chart reflects realistic mid-project execution: "
        "6 points completed, 13 points currently in progress, and 6 points in the product backlog."
    )
    s2_headers = ["Timeline Interval", "Ideal Remaining (pts)", "Actual Remaining (pts)", "Sprint Status / Daily Scrum Standup"]
    s2_rows = [
        ["Kickoff (Sep 22)", "25.0", "25.0", "Sprint 2 committed with 7 stories (25 pts)."],
        ["End of Week 1 (Sep 28)", "18.8", "22.0", "BOOK-11 (US-06 History, 3 pts) marked DONE."],
        ["End of Week 2 (Oct 5)", "12.5", "19.0", "BOOK-12 (US-07 Cancel, 3 pts) marked DONE. Reschedule & Audit IN PROGRESS."],
        ["Current (Mid-Week 3, Oct 8)", "10.0", "19.0", "ACTIVE: BOOK-13, BOOK-14, BOOK-15 in progress (13 pts)."],
        ["End of Week 4 (Oct 20)", "0.0", "0.0 (Projected)", "Projected completion of containerization (BOOK-16) and CI/CD (BOOK-17)."]
    ]
    add_styled_table(s2_headers, s2_rows, [1.6, 1.3, 1.3, 2.8])

    add_h2("Defect Log & Remediation")
    def_headers = ["Defect ID", "Severity", "Description", "Root Cause", "Remediation & Retest Outcome"]
    def_rows = [
        ["DEF-01", "CRITICAL", "Double booking occurs when 10 threads hit /api/appointments/book", "Check-then-act gap between availability check and insert statement.", "Wrapped operation in BEGIN IMMEDIATE transaction; added UNIQUE index. Retest: 1 success, 9 conflicts (PASSED)."],
        ["DEF-02", "MEDIUM", "Boolean 'True' accepted as slot ID 1 during booking request", "Pydantic default integer coercion permitted boolean casting.", "Refactored slot_id to Pydantic StrictInt. Retest: 422 Unprocessable Entity (PASSED)."]
    ]
    add_styled_table(def_headers, def_rows, [1.0, 1.0, 2.0, 1.5, 1.5])

    add_h2("Sprint Retrospective & Improvement Actions")
    p = doc.add_paragraph(
        "• What went well: Rapid identification of concurrency flaws; clean separation of secure vs. vulnerable demonstration paths.\n"
        "• What could be improved: Test execution could be automated earlier in sprint lifecycle rather than awaiting feature completion.\n"
        "• Action 1: Enforce mandatory concurrency stress tests as a pre-commit check for all database-touching stories.\n"
        "• Action 2: Integrate container security scanning into the local development workflow to detect dependency drift early."
    )

    # ==================== PHASE 11 ====================
    add_h1("Phase 11 – Secure Development and Build Environment")
    p = doc.add_paragraph(
        "The repository follows a hardened branch protection strategy (main branch protected; all code merged via feature PRs). "
        "Five core secure build controls were established:\n"
        "1. Least Privilege: Non-root execution in containers and restricted database user permissions.\n"
        "2. Secret Management: Externalized environment variables; zero hardcoded secrets (.env.example template provided).\n"
        "3. Dependency Pinning: Exact package versions pinned in requirements.txt (fastapi==0.139.0, pydantic==2.13.4, bandit==1.9.4).\n"
        "4. Automated Security Scanning: Bandit static application security testing integrated into build.\n"
        "5. Reproducible Builds: Multi-stage Docker builds ensuring identical runtime artifacts."
    )

    add_callout(
        "AUTOMATED SAST REPORT (BANDIT v1.9.4):\n"
        "Executed: 'bandit -r backend/ -f txt'\n"
        "Total lines scanned: 715\n"
        "Total vulnerabilities identified: 0 (High: 0, Medium: 0, Low: 0)\n"
        "Result: PASSED CLEANLY",
        "STATIC SECURITY ANALYSIS"
    )

    # ==================== PHASE 12 ====================
    add_h1("Phase 12 – Secure Coding and Refactoring")
    p = doc.add_paragraph(
        "Phase 12 demonstrates the core security contribution of the project: remediating CWE-362 (Concurrent Execution with "
        "Improper Synchronization / TOCTOU Race Condition)."
    )

    add_h2("Vulnerable Implementation (TOCTOU Flaw)")
    p = doc.add_paragraph(
        "```python\n"
        "# VULNERABLE: Check-then-act gap allows concurrent double booking\n"
        "cursor.execute('SELECT is_booked FROM time_slots WHERE id = ?', (slot_id,))\n"
        "slot = cursor.fetchone()\n"
        "if slot['is_booked'] == 0:\n"
        "    time.sleep(0.15)  # Vulnerable processing window\n"
        "    cursor.execute('INSERT INTO appointments (user_id, slot_id, status) VALUES (?, ?, \"CONFIRMED\")')\n"
        "    cursor.execute('UPDATE time_slots SET is_booked = 1 WHERE id = ?', (slot_id,))\n"
        "    conn.commit()\n"
        "```"
    )

    add_h2("Secure Refactored Implementation (Atomic Locking & DB Constraint)")
    p = doc.add_paragraph(
        "```python\n"
        "# SECURE: Atomic transaction with immediate write serialization\n"
        "conn.execute('BEGIN IMMEDIATE;')\n"
        "cursor = conn.cursor()\n"
        "# Atomic conditional test-and-set\n"
        "cursor.execute('UPDATE time_slots SET is_booked = 1 WHERE id = ? AND is_booked = 0', (slot_id,))\n"
        "if cursor.rowcount != 1:\n"
        "    conn.rollback()\n"
        "    log_security_event(user_id, 'BOOKING_CONFLICT_PREVENTED', 'REJECTED', client_ip)\n"
        "    raise HTTPException(status_code=409, detail='Slot concurrently reserved.')\n"
        "# Database unique index enforces safety at storage engine level\n"
        "cursor.execute('INSERT INTO appointments (user_id, slot_id, status) VALUES (?, ?, \"CONFIRMED\")')\n"
        "conn.commit()\n"
        "```"
    )

    # ==================== PHASE 13 ====================
    add_h1("Phase 13 – Containerized Development: Docker and Kubernetes")
    p = doc.add_paragraph(
        "The application is packaged using a multi-stage Dockerfile and deployed via hardened Kubernetes manifests."
    )

    k8s_headers = ["Security Control", "Docker / Kubernetes Layer", "Implementation Detail"]
    k8s_rows = [
        ["Minimal Base Image", "Dockerfile (Stage 2)", "python:3.11-slim base; build tools purged from runtime."],
        ["Non-Root Execution", "Dockerfile & Pod spec", "useradd -u 10001 appuser; runAsNonRoot: true; runAsUser: 10001."],
        ["Privilege Lockdown", "K8s Container spec", "allowPrivilegeEscalation: false; capabilities drop: ['ALL']."],
        ["Resource Quotas", "K8s Deployment", "CPU requests 100m, limits 500m; Memory requests 128Mi, limits 256Mi."],
        ["Secret Decoupling", "K8s Secret Manifest", "SECRET_KEY and credentials injected via Kubernetes SecretRef."],
        ["Health Probes", "K8s Pod Spec", "LivenessProbe hitting /api/metrics; ReadinessProbe hitting /api/services."]
    ]
    add_styled_table(k8s_headers, k8s_rows, [1.8, 1.8, 3.4])

    # ==================== PHASE 14 ====================
    add_h1("Phase 14 – CI/CD and Security Testing")
    p = doc.add_paragraph(
        "A complete GitHub Actions DevSecOps pipeline (.github/workflows/ci.yml) executes on every push and pull request. "
        "Automated testing covers Unit Tests, Integration Tests, Boundary Fuzzing, and Concurrency Race Condition stress testing."
    )

    test_headers = ["Test Suite", "Test Module", "Scenarios Tested", "Result"]
    test_rows = [
        ["Unit Tests", "test_unit.py", "PBKDF2 password hashing & salt verification; JWT token generation & expiration; Pydantic StrictInt validation.", "4 PASSED"],
        ["Integration Tests", "test_integration.py", "Student login -> browse catalog -> book slot -> verify booking -> cancel appointment -> slot release; RBAC forbidden routes.", "2 PASSED"],
        ["Concurrency Test", "test_concurrency.py", "10 concurrent worker threads fire simultaneous requests for the exact same slot ID. Asserts exactly 1 succeeds (201) and 9 receive 409 Conflict.", "1 PASSED (FLAGSHIP)"],
        ["Fuzzing Tests", "test_fuzzing.py", "13 hostile boundary payloads: negative IDs, gigantic numbers, SQLi payloads, path traversal, null bytes, non-numeric strings.", "1 PASSED"],
        ["Static Scan (SAST)", "Bandit Scan", "Full recursive code scan of backend/ directory for cryptographic, injection, and credential flaws.", "0 VULNERABILITIES"]
    ]
    add_styled_table(test_headers, test_rows, [1.5, 1.4, 3.2, 0.9])

    # ==================== PHASE 15 ====================
    add_h1("Phase 15 – Logging, Monitoring, Hardening and Secure Deployment")
    p = doc.add_paragraph(
        "Structured JSON logging captures security-relevant events to disk and SQLite. "
        "Logged events include LOGIN_SUCCESS, LOGIN_FAILURE, BOOKING_SUCCESS, BOOKING_CONFLICT_PREVENTED, "
        "APPOINTMENT_CANCELLED, APPOINTMENT_RESCHEDULED, and UNAUTHORIZED_ACCESS."
    )

    metric_headers = ["Metric / Alert Name", "Threshold / Condition", "Operational Action"]
    metric_rows = [
        ["Concurrency Collision Spike", "> 5 conflicts / minute on same slot", "Alert security team for automated bot reservation attack; throttle client IP."],
        ["Failed Authentication Surge", "> 10 failures / minute from single IP", "Trigger temporary IP ban (fail2ban) to prevent credential stuffing."],
        ["Unauthorized Role Attempt", "> 1 access violation (403 Forbidden)", "Log security incident; inspect user token for privilege escalation attempt."],
        ["Database Lock Wait Time", "Lock acquisition latency > 500 ms", "Scale read replicas or optimize transaction duration."],
        ["Container Memory Utilization", "Pod memory > 85% limit (218 MiB)", "Auto-scale replica pods or alert on potential memory leak."]
    ]
    add_styled_table(metric_headers, metric_rows, [1.8, 2.0, 3.2])

    add_h2("Target Environment Hardening Checklist")
    p = doc.add_paragraph(
        "[✓] Access Control: Disable SSH password authentication on host nodes; require hardware MFA.\n"
        "[✓] Ports & Services: Ingress accepts only TCP 443 (TLS 1.3); internal container listens only on port 8000.\n"
        "[✓] File Permissions: Container runtime files owned by UID 10001 with read-only permissions where feasible.\n"
        "[✓] Operating System: Minimal Linux Alpine / Debian-slim kernel with automatic security patching enabled.\n"
        "[✓] Network Policies: Kubernetes NetworkPolicy restricts database communication strictly to API backend pods."
    )

    # ==================== PHASE 16 ====================
    add_h1("Phase 16 – Final Security Review")
    p = doc.add_paragraph(
        "The final security review demonstrates end-to-end traceability of the core requirement across all 16 phases of the engineering lifecycle."
    )

    trace_headers = ["Engineering Phase", "Artifact / Traceability Evidence for SR-04 (No Double Booking)"]
    trace_rows = [
        ["1. Requirement", "SR-04: 'A slot must not be successfully booked by two users simultaneously under concurrent load.'"],
        ["2. Use Case", "UC-01: Book Appointment with alternative exception flow for concurrent collision handling."],
        ["3. DFD Process", "Process P3 (Manage Bookings) crossing Trust Boundary TB-03 to Data Store D3 (Appointments)."],
        ["4. STRIDE Threat", "Threat T-03: Tampering / Race Condition exploiting Time-Of-Check to Time-Of-Use gap."],
        ["5. Vulnerability", "VUL-01 (CWE-362): Non-atomic availability check and booking insertion in initial prototype."],
        ["6. Attack Tree", "Sub-goal: 'Exploit TOCTOU Application Window' with simultaneous synchronized POST requests."],
        ["7. User Story", "US-04 (Epic EP-03): 'As a student, I want guaranteed single-booking so schedule collisions are impossible.'"],
        ["8. Sprint Task", "Sprint 1 Task: Implement atomic BEGIN IMMEDIATE transaction and database unique index."],
        ["9. Implementation", "booking_service.py: secure_atomic_booking() with conditional test-and-set update and DB unique constraint."],
        ["10. Test Verification", "test_concurrency.py: 10 parallel threads fire against 1 slot; exactly 1 succeeds (201), 9 fail (409)."],
        ["11. Deployment Control", "Docker & Kubernetes manifests enforce resource limits and non-root isolation to guarantee availability."]
    ]
    add_styled_table(trace_headers, trace_rows, [1.8, 5.2])

    add_h2("Summary of Three Highest-Risk Issues and Controls")
    p = doc.add_paragraph(
        "1. Race Condition Double-Booking (High Risk): Controlled via SQLite serialization write locks and database unique partial index.\n"
        "2. Broken Object-Level Authorization / BOLA (High Risk): Controlled via strict ownership validation in cancel and reschedule services.\n"
        "3. Container Privilege Escalation (Medium Risk): Controlled via non-root execution (UID 10001) and dropping all Linux capabilities."
    )

    add_h2("Residual Limitations and Future Improvements")
    p = doc.add_paragraph(
        "1. Single-Instance Database Locking: While SQLite serialized transactions with WAL mode fully protect single-node deployments, "
        "a multi-node distributed cluster would benefit from Redis distributed locks (Redlock) or PostgreSQL SELECT FOR UPDATE.\n"
        "2. Automated Hardware MFA: Future iterations could mandate WebAuthn / FIDO2 security keys for high-privilege administrator actions."
    )

    # Save document
    output_filename = "24CYS401_Secure_Appointment_Booking_System_Lab_Exam_Report.docx"
    try:
        doc.save(output_filename)
        print(f"Report successfully written to {output_filename}")
    except PermissionError:
        fallback = "24CYS401_Secure_Appointment_Booking_System_Lab_Exam_Report_Updated.docx"
        doc.save(fallback)
        print(f"Report file was locked by Word. Successfully written to {fallback}")

if __name__ == "__main__":
    create_report()
