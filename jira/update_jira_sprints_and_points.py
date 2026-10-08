import urllib.request
import urllib.error
import json
import base64
import time

JIRA_URL = "https://phani-chandan.atlassian.net"
JIRA_EMAIL = "phanichandan02@gmail.com"
API_TOKEN = "ATATT3xFfGF0Yd-nihrGQR7tnwkdnp17IyT8Hs5XDNh-6__i2a--IKivtVQseiKbPy8rWdJTpa6_VADnMW3xQU3-Vc9cncxrEnipi7qI_pDb26jp3uOWotA_yknJAcJ3QKeJXTQQwbXk7nJJkdLC8B8anwTopZa30psHBm5A4rv5PjuGZ_8Xzto=A91797EA"

auth_str = base64.b64encode(f"{JIRA_EMAIL}:{API_TOKEN}".encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {auth_str}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def set_story_points(issue_key, points):
    payload = {
        "fields": {
            "customfield_10052": float(points),
            "customfield_10016": float(points)
        }
    }
    req = urllib.request.Request(f"{JIRA_URL}/rest/api/3/issue/{issue_key}", data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Set {issue_key} -> {points} Story Points")
    except Exception as e:
        print(f"Error setting points on {issue_key}: {e}")

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
        print(f"Transition error on {issue_key}: {e}")

# 1. Update Story Points for Sprint 1 (24 total points)
sprint_1_points = {
    "BOOK-2": 5,   # US-01 Auth
    "BOOK-7": 3,   # US-02 Catalog
    "BOOK-8": 3,   # US-03 Slots
    "BOOK-9": 8,   # US-04 Atomic Concurrency Lock
    "BOOK-10": 5,  # US-05 Provider Availability
}

print("--- Updating Sprint 1 Story Points ---")
for k, pts in sprint_1_points.items():
    set_story_points(k, pts)

# 2. Update Story Points for Sprint 2 (25 total points)
sprint_2_points = {
    "BOOK-11": 3,  # US-06 History
    "BOOK-12": 3,  # US-07 Cancel
    "BOOK-13": 5,  # US-08 Reschedule
    "BOOK-14": 3,  # US-09 Provider Roster
    "BOOK-15": 5,  # US-10 Audit Logging
    "BOOK-16": 3,  # US-11 Docker Hardening
    "BOOK-17": 3,  # US-12 Concurrency CI/CD
}

print("\n--- Updating Sprint 2 Story Points ---")
for k, pts in sprint_2_points.items():
    set_story_points(k, pts)

# 3. Transition Sprint 2 issues to realistic "in the middle of the project" state
# Transitions: 11 = To Do, 21 = In Progress, 31 = Done
print("\n--- Transitioning Sprint 2 issues to mid-project status ---")
# BOOK-11, BOOK-12 -> Done
transition_issue("BOOK-11", "21"); transition_issue("BOOK-11", "31")
transition_issue("BOOK-12", "21"); transition_issue("BOOK-12", "31")
print("BOOK-11 (US-06) -> Done (3 pts)")
print("BOOK-12 (US-07) -> Done (3 pts)")

# BOOK-13, BOOK-14, BOOK-15 -> In Progress
transition_issue("BOOK-13", "21")
transition_issue("BOOK-14", "21")
transition_issue("BOOK-15", "21")
print("BOOK-13 (US-08) -> In Progress (5 pts)")
print("BOOK-14 (US-09) -> In Progress (3 pts)")
print("BOOK-15 (US-10) -> In Progress (5 pts)")

# BOOK-16, BOOK-17 -> To Do
transition_issue("BOOK-16", "11")
transition_issue("BOOK-17", "11")
print("BOOK-16 (US-11) -> To Do (3 pts)")
print("BOOK-17 (US-12) -> To Do (3 pts)")

# 4. Activate Sprint 2 (4 weeks duration: Sep 22, 2026 to Oct 20, 2026)
p2 = {
    "name": "Sprint 2 - Hardening",
    "state": "active",
    "startDate": "2026-09-22T09:00:00.000Z",
    "endDate": "2026-10-20T18:00:00.000Z",
    "goal": "Implement rescheduling, audit logging, containerization and concurrency CI testing."
}
req2 = urllib.request.Request(f"{JIRA_URL}/rest/agile/1.0/sprint/78", data=json.dumps(p2).encode("utf-8"), headers=headers, method="PUT")
try:
    with urllib.request.urlopen(req2) as resp:
        print("\nSuccessfully Activated Sprint 2 (ID: 78) across 4-week timeline!")
except urllib.error.HTTPError as e:
    print(f"\nError activating Sprint 2: {e.code} - {e.read().decode('utf-8')}")

print("\nDone! Jira Burndown Chart and Velocity Report are now fully populated!")
