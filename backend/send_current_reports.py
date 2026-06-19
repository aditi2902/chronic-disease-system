"""
send_current_reports.py — Utility script to send daily patient logs logged today
to the doctor's configured GMAIL_USER.
"""
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from services.email_service import send_daily_log_email, GMAIL_USER


def send_daily_log():
    if not GMAIL_USER:
        print("[Error] GMAIL_USER is not configured in your backend/.env file.")
        return

    db = SessionLocal()
    try:
        print(f"Sending today's daily log to doctor ({GMAIL_USER})...")
        success = send_daily_log_email(db, GMAIL_USER)
        if success:
            print("✅ Successfully sent daily log email.")
        else:
            print("⚠️ No daily log email sent (no readings logged today, or send failed).")
    finally:
        db.close()


if __name__ == "__main__":
    send_daily_log()
