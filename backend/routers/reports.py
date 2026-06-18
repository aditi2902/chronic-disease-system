"""
routers/reports.py — Weekly report retrieval and on-demand generation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models, schemas
from database import get_db
from dependencies import get_current_user, require_doctor
from services.scheduler import generate_report_for_patient

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{patient_id}/latest", response_model=schemas.WeeklyReportOut)
def get_latest_report(
    patient_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the latest weekly report for a patient.
    Patients can only see their own; doctors can see any of their patients'.
    """
    role = getattr(current_user, "__role__", None)
    if role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Cannot view another patient's report")
    if role == "doctor":
        patient = db.query(models.Patient).filter(
            models.Patient.id == patient_id,
            models.Patient.doctor_id == current_user.id,
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

    report = (
        db.query(models.WeeklyReport)
        .filter(models.WeeklyReport.patient_id == patient_id)
        .order_by(models.WeeklyReport.week_start.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No weekly report found")
    return report


@router.post("/{patient_id}/generate", response_model=schemas.WeeklyReportOut)
def generate_report_now(
    patient_id: int,
    current_doctor: models.Doctor = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    """Doctor-only endpoint to trigger immediate report generation (for demo/testing)."""
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.doctor_id == current_doctor.id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    report = generate_report_for_patient(patient_id)
    if not report:
        raise HTTPException(
            status_code=400,
            detail="No readings in the past 7 days to generate a report from",
        )
    return report
