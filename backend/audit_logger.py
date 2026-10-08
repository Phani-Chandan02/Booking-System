import os
import json
import logging
from datetime import datetime
from backend.database import get_db_connection

LOG_FILE = os.path.join(os.path.dirname(__file__), "security_audit.log")

# Setup python logger for audit
audit_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
audit_file_handler.setFormatter(logging.Formatter('%(message)s'))
logger = logging.getLogger("security_audit")
logger.setLevel(logging.INFO)
logger.addHandler(audit_file_handler)

def log_security_event(user_id: int | None, action: str, status: str, ip_address: str, details: str = ""):
    timestamp = datetime.utcnow().isoformat() + "Z"
    event_payload = {
        "timestamp": timestamp,
        "user_id": user_id,
        "action": action,
        "status": status,
        "ip_address": ip_address,
        "details": details
    }
    # Write JSON log line
    logger.info(json.dumps(event_payload))

    # Persist in DB audit table
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO audit_logs (user_id, action, status, ip_address, details) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, status, ip_address, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to persist audit log to DB: {e}")

def get_recent_audit_logs(limit: int = 50) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.user_id, u.name as user_name, u.email as user_email, 
               a.action, a.status, a.ip_address, a.details, a.timestamp
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_security_metrics() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action = 'LOGIN_FAILURE';")
    failed_logins = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE action = 'BOOKING_CONFLICT_PREVENTED';")
    concurrency_conflicts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'CONFIRMED';")
    confirmed_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'CANCELLED';")
    cancelled_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'RESCHEDULED';")
    rescheduled_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM time_slots;")
    total_slots = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM time_slots WHERE is_booked = 0;")
    available_slots = cursor.fetchone()[0]
    conn.close()

    return {
        "failed_logins": failed_logins,
        "concurrency_conflicts_prevented": concurrency_conflicts,
        "confirmed_appointments": confirmed_appointments,
        "cancelled_appointments": cancelled_appointments,
        "rescheduled_appointments": rescheduled_appointments,
        "total_slots": total_slots,
        "available_slots": available_slots,
        "system_status": "SECURE",
    }
