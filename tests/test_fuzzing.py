import pytest
from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_input_boundary_fuzzing():
    # Login as student
    res = client.post("/api/auth/login", json={"email": "student@booking.com", "password": "Student@123"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fuzz_slot_payloads = [
        -1,
        0,
        999999999999999999,
        "1; DROP TABLE appointments;--",
        "' OR '1'='1",
        "../../../../etc/passwd",
        "%00%00%00",
        {"evil": "dict"},
        [1, 2, 3],
        None,
        True,
        "NaN",
        "Infinity"
    ]

    fuzz_results = []
    for payload in fuzz_slot_payloads:
        resp = client.post("/api/appointments/book", json={"slot_id": payload}, headers=headers)
        # Verify: All malformed / hostile inputs must be rejected safely with 422 or 404, never 500 crash or SQL execution
        fuzz_results.append((payload, resp.status_code))
        assert resp.status_code in [400, 404, 422], f"Unexpected response code {resp.status_code} for payload: {payload}"
        assert "Internal Server Error" not in resp.text
        assert "syntax error" not in resp.text.lower()

    print("\n[FUZZING TEST RESULTS]")
    for payload, status in fuzz_results:
        print(f"Payload: {str(payload)[:30]:<30} -> Handled Safely with Status {status}")

if __name__ == "__main__":
    test_input_boundary_fuzzing()
    print("Fuzzing suite PASSED cleanly!")
