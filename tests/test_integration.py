import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database import get_db_connection

client = TestClient(app)

def test_full_student_booking_lifecycle():
    # 1. Login as student
    login_res = client.post("/api/auth/login", json={
        "email": "student@booking.com",
        "password": "Student@123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Query available services
    services_res = client.get("/api/services")
    assert services_res.status_code == 200
    services = services_res.json()
    assert len(services) > 0
    service_id = services[0]["id"]

    # 3. Create a clean dedicated test slot in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO time_slots (service_id, provider_id, slot_date, start_time, end_time, is_booked) VALUES (?, 2, '2026-10-25', '16:00', '16:30', 0)",
        (service_id,)
    )
    test_slot_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 4. Book the slot
    book_res = client.post("/api/appointments/book", json={"slot_id": test_slot_id}, headers=headers)
    assert book_res.status_code == 201
    booking_data = book_res.json()
    appointment_id = booking_data["appointment_id"]
    assert booking_data["status"] == "CONFIRMED"

    # 5. Verify appointment appears in My Bookings
    my_res = client.get("/api/appointments/my", headers=headers)
    assert my_res.status_code == 200
    my_bookings = my_res.json()
    matching = [b for b in my_bookings if b["id"] == appointment_id]
    assert len(matching) == 1
    assert matching[0]["slot_id"] == test_slot_id

    # 6. Cancel the appointment
    cancel_res = client.post(f"/api/appointments/{appointment_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # 7. Verify slot is released back to available (is_booked == 0)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_booked FROM time_slots WHERE id = ?", (test_slot_id,))
    assert cursor.fetchone()[0] == 0
    conn.close()

def test_rbac_authorization_controls():
    # Login as Student
    login_res = client.post("/api/auth/login", json={
        "email": "student@booking.com",
        "password": "Student@123"
    })
    token = login_res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {token}"}

    # Attempt to access provider roster endpoint as student (should be FORBIDDEN 403)
    roster_res = client.get("/api/provider/appointments", headers=student_headers)
    assert roster_res.status_code == 403

    # Attempt to create a service as student (should be FORBIDDEN 403, requires admin)
    create_svc_res = client.post("/api/services", json={
        "name": "Unauthorized Service",
        "description": "Exploit attempt",
        "duration_minutes": 30
    }, headers=student_headers)
    assert create_svc_res.status_code == 403

    # Access without Bearer token (should be UNAUTHORIZED 401)
    unauth_res = client.get("/api/appointments/my")
    assert unauth_res.status_code == 401
