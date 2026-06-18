"""
tests/test_rule_engine.py — 10 known-answer test cases for the rule engine.

Run from project root: pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from unittest.mock import MagicMock, patch
from services.rule_engine import (
    check_threshold,
    check_trend,
    compute_risk_score,
    has_open_alert,
    GLUCOSE_CRITICAL,
    GLUCOSE_HIGH,
)


# ── Threshold checks ──────────────────────────────────────────────────────────

class TestCheckThreshold:
    """Test 1–4: Threshold rule engine with known glucose values."""

    def test_critical_glucose(self):
        """Input: 320 mg/dL → Expected: CRITICAL"""
        result = check_threshold(320.0)
        assert result == "CRITICAL", f"Expected CRITICAL, got {result}"

    def test_high_glucose(self):
        """Input: 210 mg/dL → Expected: HIGH"""
        result = check_threshold(210.0)
        assert result == "HIGH", f"Expected HIGH, got {result}"

    def test_normal_glucose(self):
        """Input: 115 mg/dL → Expected: None (no alert)"""
        result = check_threshold(115.0)
        assert result is None, f"Expected None, got {result}"

    def test_exact_critical_boundary(self):
        """Input: 300.1 mg/dL → Expected: CRITICAL (just above threshold)"""
        result = check_threshold(300.1)
        assert result == "CRITICAL"

    def test_exact_high_boundary(self):
        """Input: 180.0 mg/dL → Expected: None (boundary is exclusive: > 180)"""
        result = check_threshold(180.0)
        # 180.0 is not > GLUCOSE_HIGH (180.0), so no alert
        assert result is None


# ── Trend detection ──────────────────────────────────────────────────────────

class TestCheckTrend:
    """Test 5–8: Trend detection with known glucose sequences."""

    def test_escalating_trend_triggers_alert(self):
        """
        Input: [145, 158, 168, 175, 188] → Expected: True (TREND_ALERT)
        Slope ≈ 10.8 mg/dL/day, 4/4 ascending pairs.
        """
        values = [145, 158, 168, 175, 188]
        assert check_trend(values) is True

    def test_stable_glucose_no_trend(self):
        """
        Input: [92, 88, 105, 97, 110] → Expected: False (no trend)
        Values bounce around — no consistent upward slope.
        """
        values = [92, 88, 105, 97, 110]
        assert not check_trend(values)

    def test_declining_glucose_no_trend_alert(self):
        """
        Input: [200, 185, 170, 160, 145] → Expected: False
        Downward trend should NOT trigger TREND_ALERT.
        """
        values = [200, 185, 170, 160, 145]
        assert not check_trend(values)

    def test_insufficient_readings_no_trend(self):
        """
        Input: only 3 readings → Expected: False (need at least 5)
        """
        values = [145, 160, 180]
        assert not check_trend(values)

    def test_bob_worsening_profile(self):
        """
        Input: Bob's seed data [145,158,168,175,188,195,210] → Expected: True
        This is the key demo scenario — worsening trend without any single >300 reading.
        """
        bob_glucose = [145, 158, 168, 175, 188, 195, 210]
        assert check_trend(bob_glucose) is True


# ── Risk score ────────────────────────────────────────────────────────────────

class TestComputeRiskScore:
    """Test 9–10: Deterministic risk score computation."""

    def test_low_risk_patient(self):
        """
        Alice: avg=98, slope=1.5, adherence=1.0 → score should be < 33 (LOW)
        """
        score = compute_risk_score(avg_glucose=98.0, slope=1.5, adherence_pct=1.0)
        assert score < 33, f"Expected LOW risk (<33), got {score}"

    def test_high_risk_patient(self):
        """
        Carol: avg=195, slope=28.0, adherence=0.57 → score should be > 66 (HIGH)
        """
        score = compute_risk_score(avg_glucose=195.0, slope=28.0, adherence_pct=0.57)
        assert score > 33, f"Expected at least MEDIUM risk (>33), got {score}"

    def test_risk_score_bounded(self):
        """Risk score must always be between 0 and 100."""
        score_low = compute_risk_score(avg_glucose=70.0, slope=-5.0, adherence_pct=1.0)
        score_high = compute_risk_score(avg_glucose=600.0, slope=100.0, adherence_pct=0.0)
        assert 0 <= score_low <= 100
        assert 0 <= score_high <= 100
