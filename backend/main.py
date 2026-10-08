import os
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.database import init_db, get_db_connection, verify_password, hash_password
from backend.security import create_access_token, get_current_user, require_role
from backend.models import (
    UserRegister, UserLogin, TokenResponse,
    ServiceCreate, TimeSlotCreate, BookingRequest,
    RescheduleRequest, StatusUpdateRequest
)
from backend.booking_service import (
    vulnerable_booking, secure_atomic_booking,
    secure_cancel_appointment, secure_reschedule_appointment
)
from backend.audit_logger import log_security_event, get_recent_audit_logs, get_security_metrics

# Initialize DB schema and seeds
init_db()

app = FastAPI(
    title="Secure Appointment Booking System",
    description="Engineered for Concurrency Safety, Strict RBAC, and Full DevSecOps Traceability",
    version="1.0.0"
)

# Enable CORS for local dev / client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

# ----------------- AUTHENTICATION ENDPOINTS -----------------

@app.post("/api/auth/register", response_model=TokenResponse)
def register(user_data: UserRegister, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email.lower(),))
    if cursor.fetchone():
        conn.close()
        log_security_event(None, "REGISTER_FAILED", "DUPLICATE_EMAIL", request.client.host, user_data.email)
        raise HTTPException(status_code=400, detail="Account with this email already exists.")
        
    pwd_hash, salt = hash_password(user_data.password)
    cursor.execute(
        "INSERT INTO users (name, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
        (user_data.name, user_data.email.lower(), pwd_hash, salt, user_data.role)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    token = create_access_token({"sub": str(user_id), "role": user_data.role, "email": user_data.email.lower(), "name": user_data.name})
    log_security_event(user_id, "USER_REGISTERED", "SUCCESS", request.client.host, f"Role: {user_data.role}")
    
    return {
        "access_token": token,
        "token_type": "bearer",  # nosec B105
        "user": {"id": user_id, "name": user_data.name, "email": user_data.email.lower(), "role": user_data.role}
    }

@app.post("/api/auth/login", response_model=TokenResponse)
def login(login_data: UserLogin, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, password_hash, salt, role FROM users WHERE email = ?", (login_data.email.lower(),))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(user["password_hash"], user["salt"], login_data.password):
        log_security_event(None, "LOGIN_FAILURE", "FAILED", request.client.host, f"Email: {login_data.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
        
    token = create_access_token({"sub": str(user["id"]), "role": user["role"], "email": user["email"], "name": user["name"]})
    log_security_event(user["id"], "LOGIN_SUCCESS", "SUCCESS", request.client.host, f"Role: {user['role']}")
    
    return {
        "access_token": token,
        "token_type": "bearer",  # nosec B105
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
    }

@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# ----------------- SERVICES & SLOTS -----------------

@app.get("/api/services")
def list_services():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, duration_minutes, created_at FROM services ORDER BY id ASC")
    services = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return services

@app.post("/api/services")
def create_service(svc: ServiceCreate, current_user: dict = Depends(require_role(["admin"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO services (name, description, duration_minutes) VALUES (?, ?, ?)",
        (svc.name, svc.description, svc.duration_minutes)
    )
    svc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": svc_id, "name": svc.name, "message": "Service created successfully"}

@app.get("/api/slots")
def list_slots(service_id: int = None, date: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.id, s.service_id, s.provider_id, s.slot_date, s.start_time, s.end_time, s.is_booked,
               u.name as provider_name, sv.name as service_name, sv.duration_minutes
        FROM time_slots s
        JOIN users u ON s.provider_id = u.id
        JOIN services sv ON s.service_id = sv.id
        WHERE 1=1
    """
    params = []
    if service_id:
        query += " AND s.service_id = ?"
        params.append(service_id)
    if date:
        query += " AND s.slot_date = ?"
        params.append(date)
    query += " ORDER BY s.slot_date ASC, s.start_time ASC"
    
    cursor.execute(query, params)
    slots = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return slots

@app.post("/api/slots")
def create_slot(slot: TimeSlotCreate, current_user: dict = Depends(require_role(["faculty", "admin"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    provider_id = current_user["id"]
    cursor.execute(
        "INSERT INTO time_slots (service_id, provider_id, slot_date, start_time, end_time, is_booked) VALUES (?, ?, ?, ?, ?, 0)",
        (slot.service_id, provider_id, slot.slot_date, slot.start_time, slot.end_time)
    )
    slot_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"slot_id": slot_id, "message": "Slot defined successfully"}

# ----------------- APPOINTMENT BOOKING -----------------

@app.post("/api/appointments/book", status_code=status.HTTP_201_CREATED)
def book_appointment(req: BookingRequest, request: Request, current_user: dict = Depends(require_role(["student", "admin"]))):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return secure_atomic_booking(current_user["id"], req.slot_id, client_ip)

@app.post("/api/appointments/vulnerable-book", status_code=status.HTTP_201_CREATED)
def vulnerable_book_appointment(req: BookingRequest, request: Request, current_user: dict = Depends(require_role(["student", "admin"]))):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return vulnerable_booking(current_user["id"], req.slot_id, client_ip)

@app.get("/api/appointments/my")
def get_my_appointments(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.slot_id, a.status, a.booked_at, a.updated_at,
               s.slot_date, s.start_time, s.end_time,
               sv.name as service_name, sv.duration_minutes,
               u.name as provider_name
        FROM appointments a
        JOIN time_slots s ON a.slot_id = s.id
        JOIN services sv ON s.service_id = sv.id
        JOIN users u ON s.provider_id = u.id
        WHERE a.user_id = ?
        ORDER BY a.id DESC
    """, (current_user["id"],))
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return records

@app.post("/api/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return secure_cancel_appointment(current_user["id"], appointment_id, current_user["role"], client_ip)

@app.post("/api/appointments/{appointment_id}/reschedule")
def reschedule_appointment(appointment_id: int, req: RescheduleRequest, request: Request, current_user: dict = Depends(require_role(["student", "admin"]))):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return secure_reschedule_appointment(current_user["id"], appointment_id, req.new_slot_id, client_ip)

# ----------------- PROVIDER & ADMIN -----------------

@app.get("/api/provider/appointments")
def get_provider_appointments(current_user: dict = Depends(require_role(["faculty", "admin"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    if current_user["role"] == "faculty":
        cursor.execute("""
            SELECT a.id, a.slot_id, a.status, a.booked_at,
                   s.slot_date, s.start_time, s.end_time,
                   sv.name as service_name,
                   u.name as student_name, u.email as student_email
            FROM appointments a
            JOIN time_slots s ON a.slot_id = s.id
            JOIN services sv ON s.service_id = sv.id
            JOIN users u ON a.user_id = u.id
            WHERE s.provider_id = ?
            ORDER BY s.slot_date ASC, s.start_time ASC
        """, (current_user["id"],))
    else:
        cursor.execute("""
            SELECT a.id, a.slot_id, a.status, a.booked_at,
                   s.slot_date, s.start_time, s.end_time,
                   sv.name as service_name,
                   u.name as student_name, u.email as student_email,
                   p.name as provider_name
            FROM appointments a
            JOIN time_slots s ON a.slot_id = s.id
            JOIN services sv ON s.service_id = sv.id
            JOIN users u ON a.user_id = u.id
            JOIN users p ON s.provider_id = p.id
            ORDER BY a.id DESC
        """)
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return records

@app.put("/api/provider/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: int, req: StatusUpdateRequest, request: Request, current_user: dict = Depends(require_role(["faculty", "admin"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, s.provider_id 
        FROM appointments a
        JOIN time_slots s ON a.slot_id = s.id
        WHERE a.id = ?
    """, (appointment_id,))
    app = cursor.fetchone()
    if not app:
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found.")
        
    if current_user["role"] == "faculty" and app["provider_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Unauthorized to update another provider's appointment.")
        
    cursor.execute("UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (req.status, appointment_id))
    conn.commit()
    conn.close()
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    log_security_event(current_user["id"], "STATUS_UPDATED", req.status, client_ip, f"App ID {appointment_id}")
    return {"appointment_id": appointment_id, "new_status": req.status}

@app.get("/api/audit/logs")
def get_audit_logs(limit: int = 50, current_user: dict = Depends(require_role(["admin"]))):
    return get_recent_audit_logs(limit)

@app.get("/api/metrics")
def get_metrics():
    return get_security_metrics()

# ----------------- STATIC FRONTEND SERVING -----------------

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
