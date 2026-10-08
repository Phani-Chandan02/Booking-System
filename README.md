# Secure Appointment Booking System

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Security SAST](https://img.shields.io/badge/Bandit%20SAST-0%20Issues%20(Passed)-brightgreen.svg)](https://bandit.readthedocs.io/)
[![Concurrency Test](https://img.shields.io/badge/CWE--362%20Defense-Verified-success.svg)](#concurrency-security-demonstration-sr-04)
[![Tests Passed](https://img.shields.io/badge/Tests-8%2F8%20Passed-brightgreen.svg)](#automated-testing--verification)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage%20Non--Root-2496ED.svg)](Dockerfile)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Hardened%20Manifests-326CE5.svg)](k8s/)
[![Jira Scrum](https://img.shields.io/badge/Jira%20Cloud-Scrum%20(BOOK)-0052CC.svg)](#jira-scrum-project-management)

An end-to-end engineered, security-first appointment booking platform designed and evaluated for **24CYS401 – Secure Software Engineering Laboratory Examination (Problem 9)**.

The system addresses critical scheduling security challenges, specifically **Time-Of-Check to Time-Of-Use (TOCTOU) race conditions (CWE-362)**, **Broken Object-Level Authorization (BOLA)**, **credential stuffing**, and **data integrity failures** across all 16 DevSecOps phases.

---

## Table of Contents
1. [Core Security Scenario: Race Condition Prevention (SR-04)](#concurrency-security-demonstration-sr-04)
2. [Key Architecture & Security Controls](#key-architecture--security-controls)
3. [User Interface Design (Phase 6)](#user-interface-design)
4. [Jira Scrum Project Management (Phase 9 & 10)](#jira-scrum-project-management)
5. [Automated Testing & Concurrency Verification (Phase 14)](#automated-testing--verification)
6. [Containerization & Kubernetes Hardening (Phase 13)](#containerization--kubernetes-hardening)
7. [DevSecOps CI/CD Pipeline](#devsecops-cicd-pipeline)
8. [Quick Start & Local Execution](#quick-start--local-execution)
9. [Project Structure](#project-structure)
10. [End-to-End Requirement Traceability (SR-04)](#end-to-end-requirement-traceability)

---

## Concurrency Security Demonstration (SR-04)

### The Problem: TOCTOU Double-Booking Vulnerability (CWE-362)
In conventional booking systems, a non-atomic "check-then-act" sequence creates a race window:
```text
User A (Thread 1) ──► Check slot ──► [Available] ──────┐ (Vulnerable Delay)
                                                       ├──► User A Books Slot
User B (Thread 2) ──► Check slot ──► [Available] ──────┴──► User B Books Slot
                                                            ▼
                                           CRITICAL INTEGRITY FAILURE:
                                            ONE SLOT = TWO BOOKINGS!
```

### The Solution: Multi-Layered Atomic Defense
The system implements a defense-in-depth approach ensuring strict serialization:
1. **Database Write Serialization Lock**: `conn.execute("BEGIN IMMEDIATE;")` locks SQLite from other writers before checking availability.
2. **Atomic Conditional Test-and-Set**:
   ```sql
   UPDATE time_slots SET is_booked = 1 WHERE id = ? AND is_booked = 0;
   ```
   If `cursor.rowcount != 1`, another concurrent transaction secured the slot; transaction immediately rolls back and returns **HTTP 409 Conflict**.
3. **Database-Level Storage Engine Invariant**:
   ```sql
   CREATE UNIQUE INDEX idx_unique_confirmed_slot 
   ON appointments(slot_id) WHERE status = 'CONFIRMED';
   ```
   Even in the event of application bugs, the database storage engine physically rejects duplicate active bookings.
4. **Audit Logging**: Emits `BOOKING_CONFLICT_PREVENTED` capturing user ID, source IP address, and timestamp.

---

## Key Architecture & Security Controls

```text
┌─────────────────────────────────────────────────────────────┐
│                    Client Browser UI                        │
│   (HTML5, Vanilla Executive CSS, Nonce/CORS Protected)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / TLS 1.3 (TB-01)
┌──────────────────────────────▼──────────────────────────────┐
│                  FastAPI Security Gateway                   │
│   • Security Headers (HSTS, CSP, X-Frame-Options: DENY)     │
│   • PBKDF2-HMAC (SHA-256) Password Hashing + Salts          │
│   • PyJWT Token Lifecycle & Role Claims                     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Authenticated Bearer JWT (TB-02)
┌──────────────────────────────▼──────────────────────────────┐
│                    Booking Service Layer                    │
│   • Object-Level Authorization (BOLA Prevention)            │
│   • Pydantic StrictInt Input Boundary Sanitization          │
│   • Rescheduling All-or-Nothing Atomic Slot Swapping        │
└──────────────────────────────┬──────────────────────────────┘
                               │ BEGIN IMMEDIATE Lock (TB-03)
┌──────────────────────────────▼──────────────────────────────┐
│                 SQLite Storage Engine (WAL)                 │
│   • UNIQUE(slot_id) WHERE status = 'CONFIRMED'              │
│   • Parameterized Queries (Zero SQL Injection)              │
│   • Append-Only Structured Audit Log Store                  │
└─────────────────────────────────────────────────────────────┘
```

- **Authentication**: Salted password hashing via `hashlib.pbkdf2_hmac` (100,000 iterations). Ephemeral JWT tokens with expiration claims.
- **Role-Based Access Control (RBAC)**:
  - `student`: View services/slots, atomic booking, cancellation, rescheduling, view own history.
  - `faculty`: Define & publish availability slots, view student roster, update fulfillment status.
  - `admin`: System-wide audit inspection, live conflict telemetry, service catalog management.
- **Input Validation**: Pydantic models with `StrictInt` and strict regex patterns. Rejects SQL injection, path traversal, and boolean coercion.
- **Audit Logging**: Every security event (`LOGIN_FAILURE`, `BOOKING_SUCCESS`, `BOOKING_CONFLICT_PREVENTED`, `UNAUTHORIZED_ACCESS`) is logged to disk in structured JSON and persisted in database audit tables.

---

## User Interface Design

The UI is inspired by modern scheduling platforms (Cal.com, Linear) with an executive dark theme, high contrast badges, and zero distracting gimmicks.

1. **Screen 1 – Identity Verification**: Role selector with 1-click test credentials for evaluators, password masking, and generic 401 response masking.
2. **Screen 2 – Available Services & Real-Time Slot Booking**: Service catalog selection, real-time availability chips, and an interactive **Live Concurrency Attack Tester** (simulating simultaneous requests against both the secure and vulnerable paths).
3. **Screen 3 – Large Confirmation Receipt Popup**: Generous 650px executive confirmation receipt displaying Confirmation ID (`#BOOK-2026-00X`), service name, provider, scheduled date & time, and security protocol seal.
4. **Screen 4 – My Appointments & Rescheduling**: Booking history, status chips, cancellation modal, and atomic slot rescheduling.
5. **Screen 5 – Provider Roster & Security Audit Feed**: Appointment fulfillment roster and real-time security telemetry stream for administrators.

*Visual diagrams and screen captures are available in the [`images/`](images/) directory.*

---

## Jira Scrum Project Management

Tracked live in Atlassian Cloud Jira: **Project Key: `BOOK`** (Scrum Board ID: `72`).

### Epics Summary
- **BOOK-1 (`EP-01`)**: Identity & Access Governance
- **BOOK-3 (`EP-02`)**: Service & Catalog Management
- **BOOK-4 (`EP-03`)**: Slot Scheduling & Concurrency Engine
- **BOOK-5 (`EP-04`)**: Lifecycle Management & Rescheduling
- **BOOK-6 (`EP-05`)**: Security Audit, Hardening & DevSecOps

### Sprints & Story Points Breakdown
The project follows two 4-week academic sprints:

| Sprint | Timeline | Status | Story Points | Workflow State |
|---|---|---|---|---|
| **Sprint 1** (*Core Booking*) | Aug 24 – Sep 21, 2026 (4 Weeks) | **CLOSED** | **24 pts** | 24 pts Done (*powers Velocity Report*) |
| **Sprint 2** (*Hardening*) | Sep 22 – Oct 20, 2026 (4 Weeks) | **ACTIVE** | **25 pts** | • 6 pts Done (`US-06`, `US-07`)<br>• 13 pts In Progress (`US-08`, `US-09`, `US-10`)<br>• 6 pts To Do (`US-11`, `US-12`) (*powers Burndown Chart*) |

**Flagship Security Story**: **BOOK-9 (`US-04`)** (*Atomic Appointment Booking & Race Condition Prevention* - 8 Story Points, Critical Priority).

---

## Automated Testing & Verification

The automated test suite in [`tests/`](tests/) rigorously tests all functional, boundary, and concurrency constraints.

```powershell
python -m pytest tests/ -v
```

### Test Suite Execution Output
```text
============================= test session starts =============================
collected 8 items

tests/test_unit.py::test_password_hashing_and_verification        PASSED [ 12%]
tests/test_unit.py::test_jwt_token_generation_and_decoding        PASSED [ 25%]
tests/test_unit.py::test_jwt_expired_token_rejection             PASSED [ 37%]
tests/test_unit.py::test_input_validation_models                 PASSED [ 50%]
tests/test_integration.py::test_full_student_booking_lifecycle   PASSED [ 62%]
tests/test_integration.py::test_rbac_authorization_controls      PASSED [ 75%]
tests/test_concurrency.py::test_concurrent_booking_race_condition_prevention PASSED [ 87%]
tests/test_fuzzing.py::test_input_boundary_fuzzing               PASSED [100%]

======================== 8 passed in 0.91s ====================================
```

- **Concurrency Race Condition Test** ([`tests/test_concurrency.py`](tests/test_concurrency.py)):
  Fires **10 simultaneous worker threads** competing for the exact same slot ID. **Asserts exactly 1 thread receives HTTP 201 Created and 9 threads receive HTTP 409 Conflict**, with exactly 1 confirmed record in the database.
- **Boundary Fuzzing Test** ([`tests/test_fuzzing.py`](tests/test_fuzzing.py)):
  Tests 13 hostile boundary payloads (SQL injection strings, path traversal, negative numbers, giant integers). All safely handled with 400/404/422 status codes and zero 500 server crashes.

### Static Security Analysis (Bandit SAST)
```powershell
python -m bandit -r backend/ -f txt
```
**Result**: 715 lines of code scanned — **0 High, 0 Medium, 0 Low vulnerabilities identified (Clean Pass)**.

---

## Containerization & Kubernetes Hardening

### Docker Security Controls ([`Dockerfile`](Dockerfile))
- **Multi-Stage Build**: Separates compilation dependencies from the runtime image.
- **Minimal Base**: `python:3.11-slim` with apt package caches purged.
- **Non-Root Execution**: Runs under unprivileged user `appuser:appgroup` (UID `10001`).
- **Controlled Exposure**: Listens on dedicated port `8000`.
- **Health Check Probe**: Probes `/api/metrics` every 30 seconds.

### Kubernetes Manifests ([`k8s/`](k8s/))
- **Namespace Isolation**: Deployed in isolated namespace `secure-booking`.
- **Secret Decoupling**: JWT signing key injected via Kubernetes `SecretRef`.
- **Security Context**:
  - `runAsNonRoot: true`
  - `runAsUser: 10001`
  - `allowPrivilegeEscalation: false`
  - `capabilities.drop: ["ALL"]`
- **Resource Quotas**: CPU limit `500m`, Memory limit `256Mi`.

---

## DevSecOps CI/CD Pipeline

The GitHub Actions workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) enforces three sequential pipeline gates on every pull request:
1. **Gate 1: SAST Security Scan** (Bandit recursive scan).
2. **Gate 2: Automated Test Suite** (Pytest unit, integration, fuzzing, and concurrency stress tests).
3. **Gate 3: Container Build Verification** (Docker build and non-root image verification).

---

## Quick Start & Local Execution

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Setup Environment
```powershell
# Clone the repository
git clone https://github.com/Phani-Chandan02/Booking-System.git
cd Booking-System

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080 --reload
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser.

### 4. Evaluation Credentials

| Role | Email | Password | Scope |
|---|---|---|---|
| **Student** | `student@booking.com` | `Student@123` | Book, cancel, reschedule, test concurrency attack |
| **Faculty** | `faculty@booking.com` | `Faculty@123` | Define time slots, view roster, update status |
| **Admin** | `admin@booking.com` | `Admin@123` | Security audit feed, real-time conflict telemetry |

---

## Project Structure

```text
├── .github/
│   └── workflows/
│       └── ci.yml                 # DevSecOps CI/CD GitHub Actions Pipeline
├── backend/
│   ├── .env.example               # Template environment configuration (zero secrets)
│   ├── audit_logger.py            # Structured JSON audit logging & telemetry metrics
│   ├── booking_service.py         # Atomic concurrency engine vs. vulnerable TOCTOU demo
│   ├── database.py                # SQLite WAL initialization & integrity constraints
│   ├── main.py                    # FastAPI application, security headers, endpoints
│   ├── models.py                  # Pydantic validation schemas with StrictInt
│   └── security.py                # PBKDF2 hashing & JWT role authorization
├── frontend/
│   ├── app.js                     # Executive UI state, modal logic, concurrency demo
│   ├── index.html                 # 5-screen interface & large confirmation receipt popup
│   └── styles.css                 # Clean executive dark-theme design tokens
├── images/                        # Architectural, DFD, ER, and Attack Tree diagrams
├── jira/
│   ├── backlog.json               # 12 user stories, 5 epics, 2 sprints, acceptance criteria
│   ├── jira_sync.py               # Automated Jira Cloud REST API sync tool
│   ├── populate_jira_scrum.py     # Script that provisioned Epics & Stories on Jira
│   └── update_jira_sprints_and_points.py # Script that updated story points & sprint lifecycle
├── k8s/
│   ├── deployment.yaml            # Hardened K8s deployment with non-root security context
│   ├── namespace.yaml             # Dedicated secure-booking namespace
│   ├── secret.yaml                # Decoupled Kubernetes secret manifest
│   └── service.yaml               # ClusterIP service configuration
├── tests/
│   ├── test_concurrency.py        # 10-thread simultaneous race-condition security test
│   ├── test_fuzzing.py            # Malicious payload & input boundary fuzzing test
│   ├── test_integration.py        # End-to-end booking, cancel, reschedule & RBAC tests
│   └── test_unit.py               # Password hashing, JWT token, and model unit tests
├── .dockerignore                  # Build context exclusion rules
├── .gitignore                     # Git tracking exclusions
├── Dockerfile                     # Multi-stage hardened non-root container configuration
├── README.md                      # Comprehensive project documentation
└── requirements.txt               # Pinned application dependencies
```

---

## End-to-End Requirement Traceability

Full bidirectional traceability for **SR-04** (*Concurrent Booking Integrity*) across all 16 phases:

$$\begin{aligned}
\text{Requirement SR-04} &\longrightarrow \text{Use Case UC-01 (Atomic Booking Flow)} \\
&\longrightarrow \text{DFD Process P3 (Booking Engine crossing TB-03)} \\
&\longrightarrow \text{STRIDE Threat T-03 (Tampering / TOCTOU Race Condition)} \\
&\longrightarrow \text{Vulnerability VUL-01 (CWE-362 Check-Then-Act Gap)} \\
&\longrightarrow \text{Attack Tree (Sub-goal: Synchronized POST Collision)} \\
&\longrightarrow \text{User Story US-04 / BOOK-9 (8 Story Points, Critical)} \\
&\longrightarrow \text{Sprint 1 Task (Implement SQLite Immediate Lock)} \\
&\longrightarrow \text{Implementation (booking\_service.py: BEGIN IMMEDIATE + UNIQUE index)} \\
&\longrightarrow \text{Test Verification (test\_concurrency.py: 10 threads, 1 success, 9 conflicts)} \\
&\longrightarrow \text{Deployment Control (Docker non-root + K8s resource quotas)}
\end{aligned}$$

---

## Author & Academic Metadata
- **Course**: 24CYS401 – Secure Software Engineering
- **Student**: Elluru Phani Chandan Reddy (CH.SC.U4CYS23007)
- **Problem Statement**: Problem 9 – Secure Appointment Booking System
- **Repository**: [https://github.com/Phani-Chandan02/Booking-System](https://github.com/Phani-Chandan02/Booking-System)
