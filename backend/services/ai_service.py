"""
services/ai_service.py — Gemini Flash integration for weekly summaries.
"""
import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_model = None


def _get_model():
    global _model
    if _model is None:
        if not GEMINI_API_KEY:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            _model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            print(f"[ai_service] Failed to init Gemini: {e}")
            return None
    return _model


def generate_patient_summary(stats: dict) -> str:
    """
    Generate a 150-word patient-friendly summary from weekly stats.
    Falls back to a deterministic summary if Gemini is unavailable.
    """
    model = _get_model()
    if not model:
        return _fallback_patient_summary(stats)

    prompt = f"""You are a diabetes care assistant speaking directly to a patient.
Given this week's health data, write a warm, encouraging, and clear 150-word summary.
Highlight what's going well and what needs attention. Avoid medical jargon.
Use simple language.

Weekly data:
{json.dumps(stats, indent=2)}

Write the summary now (150 words max):"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[ai_service] Gemini patient summary failed: {e}")
        return _fallback_patient_summary(stats)


def generate_doctor_summary(stats: dict) -> str:
    """
    Generate a clinical note for the doctor from weekly stats.
    Falls back to a deterministic summary if Gemini is unavailable.
    """
    model = _get_model()
    if not model:
        return _fallback_doctor_summary(stats)

    prompt = f"""You are writing a concise clinical note for a physician reviewing a diabetic patient's weekly data.
Be precise, use clinical terminology, and include a recommended action.
Keep it under 150 words.

Weekly data:
{json.dumps(stats, indent=2)}

Clinical note:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[ai_service] Gemini doctor summary failed: {e}")
        return _fallback_doctor_summary(stats)


def _fallback_patient_summary(stats: dict) -> str:
    avg = stats.get("avg_glucose", 0)
    adherence = stats.get("adherence_pct", 0) * 100
    return (
        f"This week your average glucose was {avg:.1f} mg/dL. "
        f"You took your medication {adherence:.0f}% of days. "
        f"{'Keep up the great work!' if avg < 140 else 'Please consult your doctor about your glucose levels.'}"
    )


def _fallback_doctor_summary(stats: dict) -> str:
    avg = stats.get("avg_glucose", 0)
    slope = stats.get("trend_slope", 0)
    adherence = stats.get("adherence_pct", 0) * 100
    trend = "upward" if slope > 0 else "stable/downward"
    return (
        f"Patient weekly summary: avg glucose {avg:.1f} mg/dL, {trend} trend "
        f"(slope {slope:.2f} mg/dL/day), medication adherence {adherence:.0f}%. "
        f"{'Recommend follow-up.' if avg > 180 else 'Continue current management.'}"
    )
