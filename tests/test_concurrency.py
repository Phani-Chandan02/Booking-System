import concurrent.futures
from starlette.testclient import TestClient
from backend.main import app
from backend.database import get_db_connection

client = TestClient(app)

def test_concurrent_booking_race_condition_prevention():
    """
    SECURITY TEST: SR-04 (Double Booking / TOCTOU Race Condition Prevention)
    Fires 10 concurrent requests from multiple students competing for the exact same slot.
    Asserts: Exactly 1 succeeds (201 Created), 9 fail (409 Conflict), DB records exactly 1 confirmed booking.
    """
    # Create two students tokens
    res1 = client.post("/api/auth/login", json={"email": "student@booking.com", "password": "Student@123"})
    token1 = res1.json()["access_token"]
    res2 = client.post("/api/auth/login", json={"email": "student2@booking.com", "password": "Student@123"})
    token2 = res2.json()["access_token"]

    tokens = [token1, token2] * 5  # 10 requests total

    # Setup a fresh dedicated slot
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO time_slots (service_id, provider_id, slot_date, start_time, end_time, is_booked) VALUES (1, 2, '2026-10-30', '10:00', '10:30', 0)"
    )
    target_slot_id = cursor.lastrowid
    conn.commit()
    conn.close()

    def attempt_booking(auth_token):
        return client.post(
            "/api/appointments/book",
            json={"slot_id": target_slot_id},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

    # Launch 10 simultaneous threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(attempt_booking, tokens))

    status_codes = [r.status_code for r in responses]
    success_count = status_codes.count(201)
    conflict_count = status_codes.count(409)

    print(f"\n[CONCURRENCY TEST] Total: 10, Success (201): {success_count}, Rejected (409): {conflict_count}")

    # Core assertion: EXACTLY 1 booking succeeded, no double bookings!
    assert success_count == 1, f"Expected exactly 1 booking to succeed, but {success_count} succeeded!"
    assert conflict_count == 9, f"Expected 9 requests to be rejected with 409 Conflict, but got {conflict_count}"

    # Verify Database Integrity
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE slot_id = ? AND status = 'CONFIRMED'", (target_slot_id,))
    db_confirmed_count = cursor.fetchone()[0]
    cursor.execute("SELECT is_booked FROM time_slots WHERE id = ?", (target_slot_id,))
    slot_is_booked = cursor.fetchone()[0]
    conn.close()

    assert db_confirmed_count == 1, "Database integrity violated! More than one confirmed booking found!"
    assert slot_is_booked == 1, "Slot should be marked as booked."

if __name__ == "__main__":
    test_concurrent_booking_race_condition_prevention()
    print("Concurrency race-condition test PASSED cleanly!")
