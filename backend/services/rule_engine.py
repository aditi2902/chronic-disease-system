"""
services/rule_engine.py — Threshold checks, trend detection, alert deduplication.
"""
from datetime import date
from typing import List, Optional
import numpy as np

from sqlalchemy.orm import Session
import models

# ── Thresholds ─────────────────────────────────────────────────────────────────
GLUCOSE_CRITICAL = 300.0   # mg/dL — above this → CRITICAL
GLUCOSE_HIGH = 180.0       # mg/dL — above this → HIGH
TREND_SLOPE_THRESHOLD = 5.0  # mg/dL per day — above this → TREND_ALERT
TREND_LOOKBACK = 5         # number of recent readings to consider
TREND_MIN_ASCENDING = 4    # at least this many of last 5 must be ascending


def check_threshold(glucose: float) -> Optional[str]:
    """
    Return severity string if glucose triggers an alert, else None.
    CRITICAL > 300, HIGH 180–300, else None.
    """
    if glucose > GLUCOSE_CRITICAL:
        return "CRITICAL"
    elif glucose > GLUCOSE_HIGH:
        return "HIGH"
    return None


def check_trend(glucose_values: List[float]) -> bool:
    """
    Given an ordered list of glucose readings (oldest → newest),
    return True if there is a statistically significant upward trend.

    Method: np.polyfit linear regression over the last TREND_LOOKBACK readings.
    Slope > TREND_SLOPE_THRESHOLD AND at least TREND_MIN_ASCENDING consecutive
    ascending pairs → TREND_ALERT.
    """
    if len(glucose_values) < TREND_LOOKBACK:
        return False

    recent = glucose_values[-TREND_LOOKBACK:]
    x = list(range(len(recent)))
    slope = np.polyfit(x, recent, 1)[0]

    # Count ascending consecutive pairs
    ascending = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i - 1])

    return slope > TREND_SLOPE_THRESHOLD and ascending >= TREND_MIN_ASCENDING


def has_open_alert(db: Session, patient_id: int, alert_type: str) -> bool:
    """Check if there is already an unresolved alert of the same type for this patient."""
    alert_type_enum = (
        models.AlertType.THRESHOLD if alert_type == "threshold" else models.AlertType.TREND
    )
    return (
        db.query(models.Alert)
        .filter(
            models.Alert.patient_id == patient_id,
            models.Alert.alert_type == alert_type_enum,
            models.Alert.resolved == False,
        )
        .first()
    ) is not None


def create_alert(
    db: Session,
    patient_id: int,
    alert_type: str,
    severity: str,
    message: str,
) -> models.Alert:
    """Write a new alert to the database and return it."""
    alert = models.Alert(
        patient_id=patient_id,
        alert_type=models.AlertType(alert_type),
        severity=models.AlertSeverity(severity),
        message=message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def run_rule_engine(
    db: Session,
    patient_id: int,
    glucose: float,
    all_glucose_values: List[float],
) -> Optional[models.Alert]:
    """
    Run both threshold and trend checks.
    Returns a newly created Alert if one was fired, else None.
    Deduplicates — skips if an unresolved alert of the same type already exists.
    """
    # 1. Threshold check
    severity = check_threshold(glucose)
    if severity in ("CRITICAL", "HIGH"):
        if not has_open_alert(db, patient_id, "threshold"):
            msg = (
                f"Glucose reading of {glucose:.1f} mg/dL is {'dangerously high' if severity == 'CRITICAL' else 'elevated'}."
            )
            alert = create_alert(db, patient_id, "threshold", severity, msg)
            return alert

    # 2. Trend check (runs regardless of threshold)
    if check_trend(all_glucose_values):
        if not has_open_alert(db, patient_id, "trend"):
            msg = (
                f"Upward glucose trend detected over last {TREND_LOOKBACK} readings. "
                f"Latest: {glucose:.1f} mg/dL."
            )
            alert = create_alert(db, patient_id, "trend", "TREND_ALERT", msg)
            return alert

    return None


def compute_risk_score(avg_glucose: float, slope: float, adherence_pct: float) -> float:
    """
    Deterministic risk score 0–100.
    Components:
      - avg_glucose component: 40% weight, normalized against 400 mg/dL ceiling
      - slope component: 30% weight, normalized against 20 mg/dL/day ceiling
      - non-adherence component: 30% weight (1 - adherence_pct)
    """
    glucose_score = min(avg_glucose / 400.0, 1.0) * 40
    slope_score = min(max(slope, 0) / 20.0, 1.0) * 30
    adherence_score = (1.0 - min(max(adherence_pct, 0), 1.0)) * 30
    return round(glucose_score + slope_score + adherence_score, 1)
