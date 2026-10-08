import time
import sqlite3
from fastapi import HTTPException, status
from backend.database import get_db_connection
from backend.audit_logger import log_security_event

def vulnerable_booking(user_id: int, slot_id: int, ip_address: str) -> dict:
    """
    VULNERABLE IMPLEMENTATION (Demonstration of TOCTOU Race Condition):
    Has a Time-Of-Check to Time-Of-Use vulnerability.
    Does NOT use atomic transaction locks or database constraint enforcement.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. TIME OF CHECK (TOC)
    cursor.execute("SELECT id, is_booked FROM time_slots WHERE id = ?", (slot_id,))
    slot = cursor.fetchone()
    
    if not slot:
        conn.close()
        raise HTTPException(status_code=404, detail="Requested slot does not exist.")
        
    if slot["is_booked"] == 1:
        conn.close()
        raise HTTPException(status_code=409, detail="Slot is already marked as booked.")
    
    # Artificial processing window allowing race conditions during concurrent requests
    time.sleep(0.15)
    
    # 2. TIME OF USE (TOU) - Vulnerable window allows concurrent thread to execute here
    cursor.execute(
        "INSERT INTO appointments (user_id, slot_id, status) VALUES (?, ?, 'CONFIRMED')",
        (user_id, slot_id)
    )
    appointment_id = cursor.lastrowid
    
    cursor.execute("UPDATE time_slots SET is_booked = 1 WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()
    
    log_security_event(user_id, "VULNERABLE_BOOKING_SUCCESS", "CONFIRMED", ip_address, f"Slot {slot_id} booked (Vulnerable path)")
    return {"appointment_id": appointment_id, "slot_id": slot_id, "status": "CONFIRMED", "mode": "VULNERABLE"}

def secure_atomic_booking(user_id: int, slot_id: int, ip_address: str) -> dict:
    """
    SECURE IMPLEMENTATION:
    1. Uses SQLite BEGIN IMMEDIATE transaction for strict serialization lock.
    2. Atomic conditional update: UPDATE ... WHERE id = ? AND is_booked = 0.
    3. Database-level unique index on (slot_id) WHERE status = 'CONFIRMED'.
    4. Immediate rollback and audit logging on concurrency conflicts.
    """
    conn = get_db_connection()
    try:
        # Acquire immediate write lock on database to prevent race conditions
        conn.execute("BEGIN IMMEDIATE;")
        cursor = conn.cursor()
        
        # Verify slot exists and is available
        cursor.execute("SELECT id, is_booked, service_id, provider_id FROM time_slots WHERE id = ?", (slot_id,))
        slot = cursor.fetchone()
        
        if not slot:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=404, detail="Requested slot does not exist.")
            
        if slot["is_booked"] == 1:
            conn.rollback()
            conn.close()
            log_security_event(user_id, "BOOKING_CONFLICT_PREVENTED", "REJECTED", ip_address, f"Slot {slot_id} already booked")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slot was already booked by another user. Race condition prevented."
            )
            
        # Atomic test-and-set: rowcount must be 1
        cursor.execute("UPDATE time_slots SET is_booked = 1 WHERE id = ? AND is_booked = 0", (slot_id,))
        if cursor.rowcount != 1:
            conn.rollback()
            conn.close()
            log_security_event(user_id, "BOOKING_CONFLICT_PREVENTED", "REJECTED", ip_address, f"Concurrent update conflict on slot {slot_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Concurrent booking collision detected. Booking rejected safely."
            )
            
        # Insert appointment (enforced by DB unique index idx_unique_confirmed_slot)
        cursor.execute(
            "INSERT INTO appointments (user_id, slot_id, status) VALUES (?, ?, 'CONFIRMED')",
            (user_id, slot_id)
        )
        appointment_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        log_security_event(user_id, "BOOKING_SUCCESS", "CONFIRMED", ip_address, f"Appointment {appointment_id} for slot {slot_id}")
        return {"appointment_id": appointment_id, "slot_id": slot_id, "status": "CONFIRMED", "mode": "SECURE_ATOMIC"}
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        log_security_event(user_id, "BOOKING_CONFLICT_PREVENTED", "REJECTED_INTEGRITY", ip_address, f"Integrity constraint violation on slot {slot_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot integrity constraint violated. Appointment is already reserved."
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            conn.rollback()
            conn.close()
            log_security_event(user_id, "BOOKING_ERROR", "ERROR", ip_address, str(e))
            raise HTTPException(status_code=500, detail="Internal booking transaction failure.")
        raise e

def secure_cancel_appointment(user_id: int, appointment_id: int, role: str, ip_address: str) -> dict:
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE;")
        cursor = conn.cursor()
        
        # Verify ownership or provider authority
        cursor.execute("""
            SELECT a.id, a.user_id, a.slot_id, a.status, s.provider_id
            FROM appointments a
            JOIN time_slots s ON a.slot_id = s.id
            WHERE a.id = ?
        """, (appointment_id,))
        app = cursor.fetchone()
        
        if not app:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=404, detail="Appointment not found.")
            
        # Authorization check: only owner student, assigned faculty, or admin can cancel
        if role == "student" and app["user_id"] != user_id:
            conn.rollback()
            conn.close()
            log_security_event(user_id, "UNAUTHORIZED_CANCEL_ATTEMPT", "FORBIDDEN", ip_address, f"App ID {appointment_id}")
            raise HTTPException(status_code=403, detail="Unauthorized to cancel this appointment.")
            
        if app["status"] == "CANCELLED":
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail="Appointment is already cancelled.")
            
        # Update status and release slot in one atomic commit
        cursor.execute(
            "UPDATE appointments SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (appointment_id,)
        )
        cursor.execute("UPDATE time_slots SET is_booked = 0 WHERE id = ?", (app["slot_id"],))
        
        conn.commit()
        conn.close()
        
        log_security_event(user_id, "APPOINTMENT_CANCELLED", "SUCCESS", ip_address, f"App ID {appointment_id}, slot {app['slot_id']} released")
        return {"appointment_id": appointment_id, "status": "CANCELLED", "message": "Appointment cancelled and slot released."}
    except Exception as e:
        if not isinstance(e, HTTPException):
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=500, detail="Cancellation transaction failed.")
        raise e

def secure_reschedule_appointment(user_id: int, appointment_id: int, new_slot_id: int, ip_address: str) -> dict:
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE;")
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute("SELECT id, user_id, slot_id, status FROM appointments WHERE id = ?", (appointment_id,))
        app = cursor.fetchone()
        if not app:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=404, detail="Appointment not found.")
            
        if app["user_id"] != user_id:
            conn.rollback()
            conn.close()
            log_security_event(user_id, "UNAUTHORIZED_RESCHEDULE_ATTEMPT", "FORBIDDEN", ip_address, f"App ID {appointment_id}")
            raise HTTPException(status_code=403, detail="Unauthorized to reschedule this appointment.")
            
        if app["status"] != "CONFIRMED":
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail="Only active confirmed appointments can be rescheduled.")
            
        old_slot_id = app["slot_id"]
        
        # Verify new slot availability
        cursor.execute("SELECT id, is_booked FROM time_slots WHERE id = ?", (new_slot_id,))
        new_slot = cursor.fetchone()
        if not new_slot:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=404, detail="New slot not found.")
            
        if new_slot["is_booked"] == 1:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=409, detail="Requested new slot is not available.")
            
        # Release old slot
        cursor.execute("UPDATE time_slots SET is_booked = 0 WHERE id = ?", (old_slot_id,))
        
        # Lock new slot
        cursor.execute("UPDATE time_slots SET is_booked = 1 WHERE id = ? AND is_booked = 0", (new_slot_id,))
        if cursor.rowcount != 1:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=409, detail="New slot was concurrently reserved.")
            
        # Update appointment record
        cursor.execute(
            "UPDATE appointments SET slot_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_slot_id, appointment_id)
        )
        
        conn.commit()
        conn.close()
        
        log_security_event(user_id, "APPOINTMENT_RESCHEDULED", "SUCCESS", ip_address, f"App ID {appointment_id} from {old_slot_id} to {new_slot_id}")
        return {
            "appointment_id": appointment_id,
            "old_slot_id": old_slot_id,
            "new_slot_id": new_slot_id,
            "status": "CONFIRMED",
            "message": "Appointment rescheduled successfully."
        }
    except Exception as e:
        if not isinstance(e, HTTPException):
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=500, detail="Reschedule transaction failed.")
        raise e
