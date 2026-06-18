"""
services/scheduler.py — APScheduler weekly cron for AI report generation.
Runs every Sunday at 23:59 local time.
"""
import json
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
import numpy as np

from database import SessionLocal
import models
from services.rule_engine import compute_risk_score
from services.ai_service import generate_patient_summary, generate_doctor_summary
from services.email_service import send_weekly_report_email


def _compute_weekly_stats(readings: list) -> dict:
    """Build stats dict from a list of Reading ORM objects."""
    if not readings:
        return {}

    glucose_vals = [r.glucose_mg_dl for r in readings]
    med_taken = [r.medication_taken for r in readings]
    adherence = sum(med_taken) / len(med_taken) if med_taken else 0.0

    x = list(range(len(glucose_vals)))
    slope = float(np.polyfit(x, glucose_vals, 1)[0]) if len(glucose_vals) > 1 else 0.0

    return {
        "avg_glucose": round(sum(glucose_vals) / len(glucose_vals), 1),
        "max_glucose": max(glucose_vals),
        "min_glucose": min(glucose_vals),
        "readings_count": len(readings),
        "adherence_pct": round(adherence, 2),
        "trend_slope": round(slope, 3),
        "avg_sleep_hrs": round(
            sum(r.sleep_hrs for r in readings if r.sleep_hrs) / max(
                sum(1 for r in readings if r.sleep_hrs), 1
            ), 1
        ),
        "avg_exercise_min": round(
            sum(r.exercise_min for r in readings if r.exercise_min) / max(
                sum(1 for r in readings if r.exercise_min), 1
            ), 1
        ),
    }


def generate_weekly_reports():
    """
    Called every Sunday. Generates weekly AI reports for all patients
    who have at least one reading in the past 7 days.
    """
    print("[scheduler] Running weekly report generation...")
    db = SessionLocal()
    try:
        today = date.today()
        week_start = today - timedelta(days=6)

        patients = db.query(models.Patient).all()
        for patient in patients:
            readings = (
                db.query(models.Reading)
                .filter(
                    models.Reading.patient_id == patient.id,
                    models.Reading.date >= week_start,
                    models.Reading.date <= today,
                )
                .order_by(models.Reading.date.asc())
                .all()
            )
            if not readings:
                continue

            # Skip if report already exists for this week
            existing = (
                db.query(models.WeeklyReport)
                .filter(
                    models.WeeklyReport.patient_id == patient.id,
                    models.WeeklyReport.week_start == week_start,
                )
                .first()
            )
            if existing:
                continue

            stats = _compute_weekly_stats(readings)
            risk_score = compute_risk_score(
                avg_glucose=stats["avg_glucose"],
                slope=stats["trend_slope"],
                adherence_pct=stats["adherence_pct"],
            )
            llm_summary = generate_patient_summary(stats)
            doctor_summary = generate_doctor_summary(stats)

            report = models.WeeklyReport(
                patient_id=patient.id,
                week_start=week_start,
                json_stats=json.dumps(stats),
                llm_summary=llm_summary,
                doctor_summary=doctor_summary,
                risk_score=risk_score,
            )
            db.add(report)
            db.commit()

            # Email doctor
            if patient.doctor:
                send_weekly_report_email(
                    to_email=patient.doctor.email,
                    patient_name=patient.name,
                    doctor_summary=doctor_summary,
                    risk_score=risk_score,
                    week_start=str(week_start),
                )

            print(f"[scheduler] Report generated for {patient.name} (risk={risk_score})")
    finally:
        db.close()


def generate_report_for_patient(patient_id: int):
    """
    On-demand version: generate a weekly report for a single patient right now.
    Used by demo endpoints and testing.
    """
    db = SessionLocal()
    try:
        today = date.today()
        week_start = today - timedelta(days=6)

        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            return None

        readings = (
            db.query(models.Reading)
            .filter(
                models.Reading.patient_id == patient_id,
                models.Reading.date >= week_start,
            )
            .order_by(models.Reading.date.asc())
            .all()
        )
        if not readings:
            return None

        stats = _compute_weekly_stats(readings)
        risk_score = compute_risk_score(
            avg_glucose=stats["avg_glucose"],
            slope=stats["trend_slope"],
            adherence_pct=stats["adherence_pct"],
        )
        llm_summary = generate_patient_summary(stats)
        doctor_summary = generate_doctor_summary(stats)

        # Upsert
        existing = (
            db.query(models.WeeklyReport)
            .filter(
                models.WeeklyReport.patient_id == patient_id,
                models.WeeklyReport.week_start == week_start,
            )
            .first()
        )
        if existing:
            existing.json_stats = json.dumps(stats)
            existing.llm_summary = llm_summary
            existing.doctor_summary = doctor_summary
            existing.risk_score = risk_score
            db.commit()
            db.refresh(existing)
            return existing
        else:
            report = models.WeeklyReport(
                patient_id=patient_id,
                week_start=week_start,
                json_stats=json.dumps(stats),
                llm_summary=llm_summary,
                doctor_summary=doctor_summary,
                risk_score=risk_score,
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
    finally:
        db.close()


def start_scheduler():
    """Initialize and start the APScheduler background scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        generate_weekly_reports,
        trigger="cron",
        day_of_week="sun",
        hour=23,
        minute=59,
        id="weekly_reports",
    )
    scheduler.start()
    print("[scheduler] APScheduler started — weekly reports every Sunday 23:59")
    return scheduler
