"""
routers/readings.py — Patient reading submission and retrieval.
POST /readings — submit daily reading, run rule engine, fire alerts
GET /readings/me — last 7 days for the logged-in patient
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
import models, schemas
from dependencies import require_patient
from services.rule_engine import run_rule_engine
from services.email_service import send_alert_email

router = APIRouter(prefix="/readings", tags=["readings"])


@router.post("", response_model=schemas.ReadingSubmitResponse, status_code=201)
def submit_reading(
    payload: schemas.ReadingCreate,
    current_patient: models.Patient = Depends(require_patient),
    db: Session = Depends(get_db),
):
    reading_date = payload.date or date.today()

    reading = models.Reading(
        patient_id=current_patient.id,
        date=reading_date,
        glucose_mg_dl=payload.glucose_mg_dl,
        weight_kg=payload.weight_kg,
        sleep_hrs=payload.sleep_hrs,
        exercise_min=payload.exercise_min,
        medication_taken=payload.medication_taken,
    )
    db.add(reading)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A reading for {reading_date} already exists for this patient.",
        )
    db.refresh(reading)

    # Fetch all historical glucose values (oldest → newest) for trend detection
    all_readings = (
        db.query(models.Reading)
        .filter(models.Reading.patient_id == current_patient.id)
        .order_by(models.Reading.date.asc())
        .all()
    )
    glucose_history = [r.glucose_mg_dl for r in all_readings]

    # Run rule engine
    alert = run_rule_engine(
        db=db,
        patient_id=current_patient.id,
        glucose=payload.glucose_mg_dl,
        all_glucose_values=glucose_history,
    )

    # Send email if alert is CRITICAL or TREND
    if alert and alert.severity in (
        models.AlertSeverity.CRITICAL,
        models.AlertSeverity.TREND_ALERT,
    ):
        doctor = current_patient.doctor
        if doctor:
            send_alert_email(
                to_email=doctor.email,
                patient_name=current_patient.name,
                severity=alert.severity.value,
                message=alert.message,
                glucose=payload.glucose_mg_dl,
            )

    alert_out = schemas.AlertOut.model_validate(alert) if alert else None
    msg = "Reading submitted."
    if alert:
        msg += f" Alert triggered: {alert.severity.value}."

    return schemas.ReadingSubmitResponse(
        reading=schemas.ReadingOut.model_validate(reading),
        alert=alert_out,
        message=msg,
    )


@router.get("/me", response_model=list[schemas.ReadingOut])
def get_my_readings(
    days: int = 7,
    current_patient: models.Patient = Depends(require_patient),
    db: Session = Depends(get_db),
):
    since = date.today() - timedelta(days=days - 1)
    readings = (
        db.query(models.Reading)
        .filter(
            models.Reading.patient_id == current_patient.id,
            models.Reading.date >= since,
        )
        .order_by(models.Reading.date.asc())
        .all()
    )
    return readings


@router.get("/me/alerts", response_model=list[schemas.AlertOut])
def get_my_alerts(
    current_patient: models.Patient = Depends(require_patient),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Alert)
        .filter(models.Alert.patient_id == current_patient.id)
        .order_by(models.Alert.triggered_at.desc())
        .all()
    )
