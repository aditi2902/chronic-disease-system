"""
seed.py — Seeds 3 realistic patient profiles + 1 doctor into the DB.

Patient profiles:
  A — Alice (controlled, all green): stable glucose 85–110
  B — Bob (worsening trend): escalating glucose over 7 days, triggers TREND_ALERT
  C — Carol (recent critical spike): one reading >300, triggers CRITICAL

Run: python seed.py  (from the backend/ directory)
"""
import sys
import os
import json
from datetime import date, timedelta, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal
import models
from auth import hash_password
from services.rule_engine import run_rule_engine, compute_risk_score
from services.ai_service import generate_patient_summary, generate_doctor_summary

models.Base.metadata.create_all(bind=engine)


def clear_db(db):
    db.query(models.WeeklyReport).delete()
    db.query(models.Alert).delete()
    db.query(models.Reading).delete()
    db.query(models.Patient).delete()
    db.query(models.Doctor).delete()
    db.commit()


def seed():
    db = SessionLocal()
    try:
        print("Clearing existing data...")
        clear_db(db)

        # ── Doctor ───────────────────────────────────────────────────────────
        doctor = models.Doctor(
            name="Dr. Sarah Mitchell",
            email="doctor@chronic.dev",
            hashed_password=hash_password("doctor123"),
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        print(f"Created doctor: {doctor.name} (id={doctor.id})")

        # ── Patient A — Alice (controlled) ───────────────────────────────────
        alice = models.Patient(
            name="Alice Chen",
            email="alice@chronic.dev",
            hashed_password=hash_password("patient123"),
            doctor_id=doctor.id,
        )
        db.add(alice)
        db.commit()
        db.refresh(alice)

        # Alice: 7 days of stable glucose (85–115, clinically normal/borderline)
        alice_glucose = [92, 88, 105, 97, 110, 95, 102]
        for i, glucose in enumerate(alice_glucose):
            d = date.today() - timedelta(days=6 - i)
            reading = models.Reading(
                patient_id=alice.id,
                date=d,
                glucose_mg_dl=glucose,
                weight_kg=62.0,
                sleep_hrs=7.5,
                exercise_min=30,
                medication_taken=True,
            )
            db.add(reading)
        db.commit()
        print(f"Created Patient A: {alice.name} - controlled (glucose {min(alice_glucose)}-{max(alice_glucose)})")

        # ── Patient B — Bob (worsening trend) ────────────────────────────────
        bob = models.Patient(
            name="Bob Martinez",
            email="bob@chronic.dev",
            hashed_password=hash_password("patient123"),
            doctor_id=doctor.id,
        )
        db.add(bob)
        db.commit()
        db.refresh(bob)

        # Bob: escalating glucose over 7 days — triggers TREND_ALERT even though no single reading >300
        bob_glucose = [145, 158, 168, 175, 188, 195, 210]
        bob_readings = []
        for i, glucose in enumerate(bob_glucose):
            d = date.today() - timedelta(days=6 - i)
            reading = models.Reading(
                patient_id=bob.id,
                date=d,
                glucose_mg_dl=glucose,
                weight_kg=88.0,
                sleep_hrs=5.5,
                exercise_min=0,
                medication_taken=(i % 2 == 0),  # sporadic adherence
            )
            db.add(reading)
            db.commit()
            bob_readings.append(reading)

        # Run rule engine for Bob's last reading to create the trend alert
        all_bob_glucose = [r.glucose_mg_dl for r in bob_readings]
        alert = run_rule_engine(
            db=db,
            patient_id=bob.id,
            glucose=bob_glucose[-1],
            all_glucose_values=all_bob_glucose,
        )
        if alert:
            print(f"  -> Alert triggered for Bob: {alert.severity.value}")
        print(f"Created Patient B: {bob.name} -- worsening trend (glucose {bob_glucose[0]}->{bob_glucose[-1]})")

        # -- Patient C -- Carol (critical spike) -------------------------------------------
        carol = models.Patient(
            name="Carol Thompson",
            email="carol@chronic.dev",
            hashed_password=hash_password("patient123"),
            doctor_id=doctor.id,
        )
        db.add(carol)
        db.commit()
        db.refresh(carol)

        # Carol: mostly normal, then a critical spike on the last day
        carol_glucose = [120, 135, 128, 142, 155, 170, 318]
        carol_readings = []
        for i, glucose in enumerate(carol_glucose):
            d = date.today() - timedelta(days=6 - i)
            reading = models.Reading(
                patient_id=carol.id,
                date=d,
                glucose_mg_dl=glucose,
                weight_kg=74.0,
                sleep_hrs=6.5,
                exercise_min=15,
                medication_taken=(i != 6),  # missed meds on spike day
            )
            db.add(reading)
            db.commit()
            carol_readings.append(reading)

        # Run rule engine for Carol's critical reading
        all_carol_glucose = [r.glucose_mg_dl for r in carol_readings]
        alert = run_rule_engine(
            db=db,
            patient_id=carol.id,
            glucose=carol_glucose[-1],
            all_glucose_values=all_carol_glucose,
        )
        if alert:
            print(f"  -> Alert triggered for Carol: {alert.severity.value}")
        print(f"Created Patient C: {carol.name} -- critical spike (last reading: {carol_glucose[-1]} mg/dL)")

        # ── Pre-generate weekly reports for all patients ──────────────────────
        print("\nGenerating weekly reports...")
        today = date.today()
        week_start = today - timedelta(days=6)

        for patient, glucose_vals in [
            (alice, alice_glucose),
            (bob, bob_glucose),
            (carol, carol_glucose),
        ]:
            readings_objs = (
                db.query(models.Reading)
                .filter(models.Reading.patient_id == patient.id)
                .order_by(models.Reading.date.asc())
                .all()
            )
            med_taken = [r.medication_taken for r in readings_objs]
            adherence = sum(med_taken) / len(med_taken)
            avg_glucose = sum(glucose_vals) / len(glucose_vals)

            import numpy as np
            slope = float(np.polyfit(range(len(glucose_vals)), glucose_vals, 1)[0])
            risk_score = compute_risk_score(avg_glucose, slope, adherence)

            stats = {
                "avg_glucose": round(avg_glucose, 1),
                "max_glucose": max(glucose_vals),
                "min_glucose": min(glucose_vals),
                "readings_count": len(glucose_vals),
                "adherence_pct": round(adherence, 2),
                "trend_slope": round(slope, 3),
                "avg_sleep_hrs": round(
                    sum(r.sleep_hrs for r in readings_objs if r.sleep_hrs) / max(
                        sum(1 for r in readings_objs if r.sleep_hrs), 1
                    ), 1
                ),
                "avg_exercise_min": round(
                    sum(r.exercise_min for r in readings_objs if r.exercise_min) / max(
                        sum(1 for r in readings_objs if r.exercise_min), 1
                    ), 1
                ),
                "patient_name": patient.name,
            }

            llm_summary = generate_patient_summary(stats)
            doc_summary = generate_doctor_summary(stats)

            report = models.WeeklyReport(
                patient_id=patient.id,
                week_start=week_start,
                json_stats=json.dumps(stats),
                llm_summary=llm_summary,
                doctor_summary=doc_summary,
                risk_score=risk_score,
            )
            db.add(report)
            db.commit()
            print(f"  -> {patient.name}: risk_score={risk_score}, summary generated")

        print("\n[OK] Seed complete!")
        print("\nTest credentials:")
        print("  Doctor:    doctor@chronic.dev / doctor123")
        print("  Patient A: alice@chronic.dev  / patient123  (controlled)")
        print("  Patient B: bob@chronic.dev    / patient123  (worsening trend)")
        print("  Patient C: carol@chronic.dev  / patient123  (critical spike)")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
