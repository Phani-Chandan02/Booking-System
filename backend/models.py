from pydantic import BaseModel, Field, StrictInt
from typing import Optional

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field("student", pattern="^(student|faculty|admin)$")

class UserLogin(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=5, max_length=500)
    duration_minutes: StrictInt = Field(..., ge=10, le=180)

class TimeSlotCreate(BaseModel):
    service_id: StrictInt = Field(..., ge=1)
    slot_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")

class BookingRequest(BaseModel):
    slot_id: StrictInt = Field(..., ge=1)

class RescheduleRequest(BaseModel):
    new_slot_id: StrictInt = Field(..., ge=1)

class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(CONFIRMED|COMPLETED|CANCELLED)$")
