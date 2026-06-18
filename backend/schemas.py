"""
schemas.py — Pydantic request/response models.
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class DoctorRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class PatientRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    doctor_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "patient" or "doctor"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str


# ── Readings ──────────────────────────────────────────────────────────────────

class ReadingCreate(BaseModel):
    date: Optional[date] = None
    glucose_mg_dl: float
    weight_kg: Optional[float] = None
    sleep_hrs: Optional[float] = None
    exercise_min: Optional[float] = None
    medication_taken: bool = False

    @field_validator("glucose_mg_dl")
    @classmethod
    def glucose_must_be_positive(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError("glucose_mg_dl must be between 1 and 1000")
        return v


class ReadingOut(BaseModel):
    id: int
    patient_id: int
    date: date
    glucose_mg_dl: float
    weight_kg: Optional[float]
    sleep_hrs: Optional[float]
    exercise_min: Optional[float]
    medication_taken: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: int
    patient_id: int
    alert_type: str
    severity: str
    message: Optional[str]
    triggered_at: datetime
    resolved: bool

    model_config = {"from_attributes": True}


# ── Doctor views ──────────────────────────────────────────────────────────────

class PatientSummary(BaseModel):
    id: int
    name: str
    email: str
    doctor_id: Optional[int]
    latest_glucose: Optional[float]
    latest_date: Optional[date]
    risk_badge: str          # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "NO DATA"
    open_alerts: int

    model_config = {"from_attributes": True}


class PatientDetail(BaseModel):
    id: int
    name: str
    email: str
    doctor_id: Optional[int]
    readings: List[ReadingOut]
    alerts: List[AlertOut]

    model_config = {"from_attributes": True}


# ── Weekly Reports ────────────────────────────────────────────────────────────

class WeeklyReportOut(BaseModel):
    id: int
    patient_id: int
    week_start: date
    json_stats: str
    llm_summary: Optional[str]
    doctor_summary: Optional[str]
    risk_score: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Reading submit response ───────────────────────────────────────────────────

class ReadingSubmitResponse(BaseModel):
    reading: ReadingOut
    alert: Optional[AlertOut]
    message: str
