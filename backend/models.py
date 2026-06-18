"""
models.py — SQLAlchemy ORM models for all tables.
Tables: doctors, patients, readings, alerts, weekly_reports
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, Text, UniqueConstraint, Enum
)
from sqlalchemy.orm import relationship
import enum

from database import Base


class AlertType(str, enum.Enum):
    THRESHOLD = "threshold"
    TREND = "trend"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    TREND_ALERT = "TREND_ALERT"
    OK = "OK"


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patients = relationship("Patient", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="patients")
    readings = relationship("Reading", back_populates="patient", order_by="Reading.date.desc()")
    alerts = relationship("Alert", back_populates="patient", order_by="Alert.triggered_at.desc()")
    weekly_reports = relationship("WeeklyReport", back_populates="patient")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, default=date.today)
    glucose_mg_dl = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=True)
    sleep_hrs = Column(Float, nullable=True)
    exercise_min = Column(Float, nullable=True)
    medication_taken = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="readings")

    __table_args__ = (
        UniqueConstraint("patient_id", "date", name="uq_patient_daily_reading"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

    patient = relationship("Patient", back_populates="alerts")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    json_stats = Column(Text, nullable=False)       # JSON string of computed stats
    llm_summary = Column(Text, nullable=True)       # Patient-friendly Gemini output
    doctor_summary = Column(Text, nullable=True)    # Clinical Gemini output
    risk_score = Column(Float, nullable=True)       # 0–100 deterministic score
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="weekly_reports")

    __table_args__ = (
        UniqueConstraint("patient_id", "week_start", name="uq_patient_weekly_report"),
    )
