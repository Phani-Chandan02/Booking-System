import pytest
from datetime import timedelta
import jwt
from pydantic import ValidationError
from backend.database import hash_password, verify_password
from backend.security import create_access_token, decode_token, SECRET_KEY, ALGORITHM
from backend.models import UserRegister, TimeSlotCreate, BookingRequest

def test_password_hashing_and_verification():
    raw_pwd = "SecureStudentPass@2026"
    pwd_hash, salt = hash_password(raw_pwd)
    
    # Assert hash is not plaintext and salt is present
    assert pwd_hash != raw_pwd
    assert len(salt) == 32
    
    # Assert correct verification
    assert verify_password(pwd_hash, salt, raw_pwd) is True
    # Assert incorrect password fails
    assert verify_password(pwd_hash, salt, "WrongPassword@123") is False

def test_jwt_token_generation_and_decoding():
    claims = {"sub": "42", "role": "student", "email": "test@student.edu", "name": "Test Student"}
    token = create_access_token(claims, expires_delta=timedelta(minutes=15))
    
    decoded = decode_token(token)
    assert decoded["sub"] == "42"
    assert decoded["role"] == "student"
    assert decoded["email"] == "test@student.edu"
    assert "exp" in decoded

def test_jwt_expired_token_rejection():
    claims = {"sub": "99", "role": "student"}
    expired_token = create_access_token(claims, expires_delta=timedelta(seconds=-10))
    with pytest.raises(Exception):
        decode_token(expired_token)

def test_input_validation_models():
    # Valid register data
    valid_data = UserRegister(name="Alice Doe", email="alice@test.com", password="Password@123", role="student")
    assert valid_data.role == "student"

    # Invalid email rejection
    with pytest.raises(ValidationError):
        UserRegister(name="Alice", email="not-an-email", password="Password@123", role="student")

    # Short password rejection
    with pytest.raises(ValidationError):
        UserRegister(name="Alice", email="alice@test.com", password="short", role="student")

    # Invalid time slot format rejection
    with pytest.raises(ValidationError):
        TimeSlotCreate(service_id=1, slot_date="invalid-date", start_time="9am", end_time="10am")

    # Valid time slot format
    valid_slot = TimeSlotCreate(service_id=1, slot_date="2026-10-20", start_time="09:00", end_time="09:30")
    assert valid_slot.slot_date == "2026-10-20"
