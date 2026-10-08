import urllib.request
import urllib.error
import json
import base64
import time

JIRA_URL = "https://phani-chandan.atlassian.net"
JIRA_EMAIL = "phanichandan02@gmail.com"
API_TOKEN = "ATATT3xFfGF0Yd-nihrGQR7tnwkdnp17IyT8Hs5XDNh-6__i2a--IKivtVQseiKbPy8rWdJTpa6_VADnMW3xQU3-Vc9cncxrEnipi7qI_pDb26jp3uOWotA_yknJAcJ3QKeJXTQQwbXk7nJJkdLC8B8anwTopZa30psHBm5A4rv5PjuGZ_8Xzto=A91797EA"
PROJECT_KEY = "BOOK"
SPRINT_1_ID = 77
SPRINT_2_ID = 78

auth_str = base64.b64encode(f"{JIRA_EMAIL}:{API_TOKEN}".encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {auth_str}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def api_post(endpoint, payload):
    req = urllib.request.Request(f"{JIRA_URL}{endpoint}", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def api_get(endpoint):
    req = urllib.request.Request(f"{JIRA_URL}{endpoint}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def transition_issue(issue_key, transition_id):
    req = urllib.request.Request(
        f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions",
        data=json.dumps({"transition": {"id": transition_id}}).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"  [!] Transition error on {issue_key}: {e}")

print("==================================================")
print("POPOPULATING JIRA SCRUM PROJECT 'BOOK'")
print("==================================================")

# Epics definition
epics_data = [
    ("EP-01", "Identity & Access Governance", "Authentication, Role-Based Access Control, and credential protection"),
    ("EP-02", "Service & Catalog Management", "Service definition, duration management, and provider offerings"),
    ("EP-03", "Slot Scheduling & Concurrency Engine", "Time slot publishing, atomic reservations, and race condition prevention"),
    ("EP-04", "Lifecycle Management & Rescheduling", "Appointment cancellation, atomic rescheduling, and status updates"),
    ("EP-05", "Security Audit, Hardening & DevSecOps", "Audit trails, container hardening, CI/CD pipelines, and vulnerability mitigation"),
]

epic_keys = {"EP-01": "BOOK-1"}  # BOOK-1 already created
for code, name, desc in epics_data[1:]:
    p = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": f"{code} {name}",
            "issuetype": {"name": "Epic"},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": desc}]}]
            }
        }
    }
    res = api_post("/rest/api/3/issue", p)
    epic_keys[code] = res["key"]
    print(f"Created Epic [{code}]: {res['key']}")

# User Stories definition
stories_data = [
    # Sprint 1 Stories
    ("US-01", "EP-01", "Role-Based User Authentication",
     "As a user (Student/Faculty/Admin), I want to authenticate securely with email and password, so that only authorized individuals can access system features.",
     ["Given valid credentials, system issues a signed JWT token with user role claims.",
      "Given invalid credentials, system returns a generic 401 Unauthorized without user enumeration.",
      "Passwords must be hashed with PBKDF2/SHA-256 and unique salt."],
     "High", SPRINT_1_ID, "Done"),

    ("US-02", "EP-02", "Browse Service Catalog",
     "As a student, I want to view available academic services, so that I can choose the appropriate mentoring or lab evaluation session.",
     ["User can view list of services with title, description, and duration in minutes.",
      "Unauthorized users cannot modify service catalog entries."],
     "Medium", SPRINT_1_ID, "Done"),

    ("US-03", "EP-03", "Check Real-Time Available Time Slots",
     "As a student, I want to check real-time available time slots for a selected service, so that I can find an open meeting time that fits my schedule.",
     ["Only available (unbooked) slots are displayed as selectable.",
      "Booked slots must be visually distinguished and non-interactive."],
     "High", SPRINT_1_ID, "Done"),

    ("US-04", "EP-03", "Atomic Appointment Booking & Race Condition Prevention",
     "As a student, I want the system to guarantee that my selected slot cannot be double-booked by another student, so that appointment conflicts and schedule collisions are impossible.",
     ["Booking operation must execute within an atomic transaction with immediate serialization locking.",
      "Database unique constraint must enforce that no slot ID can have more than one CONFIRMED appointment.",
      "If two students attempt to book the same slot simultaneously, exactly one succeeds (201 Created) and the other is safely rejected with 409 Conflict.",
      "Attempted double-booking race condition must trigger an audit log event 'BOOKING_CONFLICT_PREVENTED'."],
     "Critical", SPRINT_1_ID, "Done"),

    ("US-05", "EP-03", "Faculty Availability Slot Definition",
     "As a faculty member, I want to define and publish available time slots for my services, so that students can view and schedule appointments with me.",
     ["Faculty can select service, date, start time, and end time.",
      "System validates that end time is strictly after start time.",
      "Only faculty and admin roles can publish availability slots (RBAC enforced)."],
     "High", SPRINT_1_ID, "Done"),

    # Sprint 2 Stories
    ("US-06", "EP-04", "Personal Booking History View",
     "As a student, I want to view my booking history, so that I can track past and upcoming scheduled appointments.",
     ["Student sees only their own appointments (enforcing SR-02 / Object-Level Authorization).",
      "History displays status: CONFIRMED, COMPLETED, CANCELLED, or RESCHEDULED."],
     "Medium", SPRINT_2_ID, "Done"),

    ("US-07", "EP-04", "Appointment Cancellation with Slot Release",
     "As a student or faculty member, I want to cancel an existing appointment, so that the reserved time slot is freed for other students to book.",
     ["Student can cancel only their own appointments.",
      "Upon cancellation, slot is atomically marked available (is_booked = 0).",
      "Audit event APPOINTMENT_CANCELLED is recorded with timestamp."],
     "Medium", SPRINT_2_ID, "Done"),

    ("US-08", "EP-04", "Atomic Appointment Rescheduling",
     "As a student, I want to reschedule an existing appointment to a new open slot, so that I can update my meeting without risking losing my reservation.",
     ["Rescheduling executes in a single atomic transaction: locks new slot, releases old slot, updates appointment.",
      "If new slot is concurrently booked by another user, transaction rolls back and old appointment remains intact."],
     "High", SPRINT_2_ID, "Done"),

    ("US-09", "EP-04", "Faculty Appointment Roster & Status Updates",
     "As a faculty member, I want to view my scheduled appointments and update their status (Completed/Cancelled), so that I can manage my student meeting workflow.",
     ["Faculty can view only appointments booked for their own slots.",
      "Faculty can update status to COMPLETED, CONFIRMED, or CANCELLED."],
     "Medium", SPRINT_2_ID, "Done"),

    ("US-10", "EP-05", "Security Event Audit Logging & Metrics",
     "As a security administrator, I want to review an immutable audit log of security events and real-time metrics, so that I can detect brute-force attacks and race condition attempts.",
     ["Structured audit logs capture user_id, action, status, ip_address, and timestamp.",
      "Key events tracked: LOGIN_FAILURE, BOOKING_SUCCESS, BOOKING_CONFLICT_PREVENTED, UNAUTHORIZED_ACCESS."],
     "High", SPRINT_2_ID, "Done"),

    ("US-11", "EP-05", "Containerized Hardened Deployment",
     "As a DevSecOps engineer, I want the application to be packaged in a non-root, minimal container with Kubernetes security contexts, so that deployment risks and host privilege escalations are prevented.",
     ["Dockerfile uses multi-stage build and minimal python:3.11-slim base.",
      "Container executes as non-root user (UID 10001).",
      "Kubernetes manifest applies runAsNonRoot: true, drops all capabilities, and enforces resource limits."],
     "High", SPRINT_2_ID, "In Progress"),

    ("US-12", "EP-05", "Automated Concurrency Testing & CI/CD Pipeline",
     "As a quality assurance engineer, I want automated regression and concurrency race-condition tests integrated into CI/CD, so that builds fail immediately if double-booking regressions are introduced.",
     ["CI/CD workflow triggers on pull request and executes automated concurrency suite.",
      "Test simulates 10 concurrent requests for the same slot ID and asserts exactly 1 succeeds.",
      "Build is rejected if any double booking occurs."],
     "High", SPRINT_2_ID, "In Progress"),
]

sprint_issues_map = {SPRINT_1_ID: ["BOOK-2"], SPRINT_2_ID: []}

# Update BOOK-2 transition to Done
transition_issue("BOOK-2", "21") # In Progress
transition_issue("BOOK-2", "31") # Done
print("Updated BOOK-2 (US-01) -> Done")

for code, epic_code, title, user_story, ac_list, prio, sprint_id, target_status in stories_data[1:]:
    parent_epic = epic_keys[epic_code]
    
    # Build ADF description
    desc_paragraphs = [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": user_story, "marks": [{"type": "strong"}]}]
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Acceptance Criteria:"}]
        }
    ]
    ac_bullet_items = []
    for ac in ac_list:
        ac_bullet_items.append({
            "type": "listItem",
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": ac}]
            }]
        })
    desc_paragraphs.append({
        "type": "bulletList",
        "content": ac_bullet_items
    })

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": f"{code} {title}",
            "issuetype": {"name": "Story"},
            "parent": {"key": parent_epic},
            "priority": {"name": prio if prio in ["High", "Medium"] else "Highest"},
            "description": {
                "type": "doc",
                "version": 1,
                "content": desc_paragraphs
            }
        }
    }

    res = api_post("/rest/api/3/issue", payload)
    issue_key = res["key"]
    print(f"Created Story [{code}]: {issue_key} (Parent: {parent_epic})")
    sprint_issues_map[sprint_id].append(issue_key)

    # Workflow status transitions
    if target_status == "In Progress":
        transition_issue(issue_key, "21")
    elif target_status == "Done":
        transition_issue(issue_key, "21")
        transition_issue(issue_key, "31")

    time.sleep(0.2)

# Assign issues to Sprints
for s_id, issues in sprint_issues_map.items():
    print(f"Assigning {len(issues)} issues to Sprint {s_id}...")
    try:
        api_post(f"/rest/agile/1.0/sprint/{s_id}/issue", {"issues": issues})
        print(f"  >> Successfully linked issues to Sprint {s_id}!")
    except Exception as e:
        print(f"  [!] Sprint linking error: {e}")

print("\n" + "=" * 60)
print("JIRA SCRUM POPULATION COMPLETE!")
print(f"Project URL: {JIRA_URL}/jira/software/c/projects/{PROJECT_KEY}/boards/72")
print("=" * 60)
