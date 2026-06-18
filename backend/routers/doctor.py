"""
routers/doctor.py — Doctor-only endpoints for patient management.
All routes are JWT-gated with require_doctor dependency.
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models, schemas
from database import get_db
from dependencies import require_doctor

router = APIRouter(prefix="/doctor", tags=["doctor"])


def _risk_badge(risk_score: float | None, latest_glucose: float | None) -> str:
    """Derive a simple risk badge from risk score or latest glucose."""
    if risk_score is not None:
        if risk_score >= 66:
            return "HIGH"
        elif risk_score >= 33:
            return "MEDIUM"
        else:
            return "LOW"
    if latest_glucose is None:
        return "NO DATA"
    if latest_glucose > 300:
        return "CRITICAL"
    if latest_glucose > 180:
        return "HIGH"
    if latest_glucose > 140:
        return "MEDIUM"
    return "LOW"


@router.get("/patients", response_model=list[schemas.PatientSummary])
def list_patients(
    current_doctor: models.Doctor = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Return all patients under this doctor with latest reading + risk badge."""
    patients = (
        db.query(models.Patient)
        .filter(models.Patient.doctor_id == current_doctor.id)
        .all()
    )

    result = []
    for patient in patients:
        latest_reading = (
            db.query(models.Reading)
            .filter(models.Reading.patient_id == patient.id)
            .order_by(models.Reading.date.desc())
            .first()
        )
        open_alerts = (
            db.query(models.Alert)
            .filter(
                models.Alert.patient_id == patient.id,
                models.Alert.resolved == False,
            )
            .count()
        )
        latest_report = (
            db.query(models.WeeklyReport)
            .filter(models.WeeklyReport.patient_id == patient.id)
            .order_by(models.WeeklyReport.week_start.desc())
            .first()
        )

        latest_glucose = latest_reading.glucose_mg_dl if latest_reading else None
        risk_score = latest_report.risk_score if latest_report else None

        result.append(
            schemas.PatientSummary(
                id=patient.id,
                name=patient.name,
                email=patient.email,
                doctor_id=patient.doctor_id,
                latest_glucose=latest_glucose,
                latest_date=latest_reading.date if latest_reading else None,
                risk_badge=_risk_badge(risk_score, latest_glucose),
                open_alerts=open_alerts,
            )
        )

    # Sort: HIGH/CRITICAL first
    badge_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "NO DATA": 4}
    result.sort(key=lambda p: badge_order.get(p.risk_badge, 5))
    return result


@router.get("/patients/{patient_id}/readings", response_model=list[schemas.ReadingOut])
def get_patient_readings(
    patient_id: int,
    days: int = 7,
    current_doctor: models.Doctor = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_doctor.id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not under your care")

    since = date.today() - timedelta(days=days - 1)
    return (
        db.query(models.Reading)
        .filter(
            models.Reading.patient_id == patient_id,
            models.Reading.date >= since,
        )
        .order_by(models.Reading.date.asc())
        .all()
    )


@router.get("/patients/{patient_id}/alerts", response_model=list[schemas.AlertOut])
def get_patient_alerts(
    patient_id: int,
    current_doctor: models.Doctor = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_doctor.id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return (
        db.query(models.Alert)
        .filter(models.Alert.patient_id == patient_id)
        .order_by(models.Alert.triggered_at.desc())
        .all()
    )


@router.patch("/alerts/{alert_id}/resolve", response_model=schemas.AlertOut)
def resolve_alert(
    alert_id: int,
    current_doctor: models.Doctor = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify the alert belongs to a patient under this doctor
    patient = db.query(models.Patient).filter(
        models.Patient.id == alert.patient_id,
        models.Patient.doctor_id == current_doctor.id,
    ).first()
    if not patient:
        raise HTTPException(status_code=403, detail="Not authorized to resolve this alert")

    alert.resolved = True
    db.commit()
    db.refresh(alert)
    return alert
