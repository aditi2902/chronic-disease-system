"""
services/email_service.py — Send alert emails to doctor via Gmail SMTP or Resend HTTP API.
"""
import smtplib
import os
from datetime import date, datetime, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import httpx
from sqlalchemy.orm import Session
import models

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")


def send_alert_email(
    to_email: str,
    patient_name: str,
    severity: str,
    message: str,
    glucose: float,
) -> bool:
    """
    Send an alert email to the doctor.
    Prioritizes Resend HTTP API (Port 443) to avoid SMTP blocks, falls back to Gmail SMTP.
    """
    recipient = GMAIL_USER if GMAIL_USER else to_email
    subject = f"⚠️ CRITICAL ALERT: {patient_name} glucose is {glucose:.1f} mg/dL"

    header_color = "#dc2626" if severity == "CRITICAL" else "#d97706"
    badge_bg = "#fee2e2" if severity == "CRITICAL" else "#ffedd5"
    badge_text_color = "#991b1b" if severity == "CRITICAL" else "#9a3412"

    body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{severity} Alert</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
  <div style="max-width: 580px; margin: 0 auto; background: white; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    
    <!-- Top Warning Header Banner -->
    <div style="background: linear-gradient(135deg, {header_color}, #7f1d1d); padding: 28px 24px; text-align: center; color: white;">
      <span style="font-size: 28px;">🚨</span>
      <h2 style="margin: 8px 0 0 0; font-size: 20px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{severity} ALERT</h2>
      <p style="margin: 4px 0 0 0; font-size: 14px; color: rgba(255,255,255,0.85);">{patient_name}</p>
    </div>

    <!-- Alert details card -->
    <div style="padding: 24px;">
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 14px; width: 40%;">Patient Name:</td>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-size: 14px; font-weight: 600;">{patient_name}</td>
        </tr>
        <tr>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 14px;">Glucose Reading:</td>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; color: #dc2626; font-size: 18px; font-weight: 700;">{glucose:.1f} mg/dL</td>
        </tr>
        <tr>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 14px;">Status:</td>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
            <span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; background-color: {badge_bg}; color: {badge_text_color}; uppercase;">{severity}</span>
          </td>
        </tr>
      </table>

      <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 14px; border-radius: 4px; margin-bottom: 24px;">
        <h4 style="margin: 0 0 6px 0; color: #991b1b; font-size: 13px; font-weight: 700;">Alert Message:</h4>
        <p style="margin: 0; color: #7f1d1d; font-size: 13px; line-height: 1.5;">{message}</p>
      </div>

      <div style="text-align: center;">
        <p style="font-size: 12px; color: #94a3b8; margin: 0;">
          Please review the patient's dashboard immediately to check their complete readings history.
        </p>
      </div>
    </div>
  </div>
</body>
</html>
"""

    return _send_email_helper(recipient, subject, body)


def send_weekly_report_email(
    to_email: str,
    patient_name: str,
    doctor_summary: str,
    risk_score: float,
    week_start: str,
) -> bool:
    """
    Send weekly AI report email to doctor.
    Prioritizes Resend HTTP API (Port 443) to avoid SMTP blocks, falls back to Gmail SMTP.
    """
    recipient = GMAIL_USER if GMAIL_USER else to_email
    risk_color = "#16a34a" if risk_score < 33 else "#d97706" if risk_score < 66 else "#dc2626"
    risk_bg = "#dcfce7" if risk_score < 33 else "#ffedd5" if risk_score < 66 else "#fee2e2"
    risk_label = "LOW" if risk_score < 33 else "MEDIUM" if risk_score < 66 else "HIGH"
    
    subject = f"📊 Weekly Report: {patient_name} (Risk: {risk_label}) — Week of {week_start}"

    body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Weekly AI Report</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
  <div style="max-width: 580px; margin: 0 auto; background: white; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #1e3a8a, #0f172a); padding: 28px 24px; color: white;">
      <h2 style="margin: 0; font-size: 18px; font-weight: 700; letter-spacing: -0.5px;">📊 Weekly Clinical Summary</h2>
      <p style="margin: 4px 0 0 0; font-size: 13px; color: #93c5fd;">Patient: {patient_name} · Week of {week_start}</p>
    </div>

    <!-- Stats summary section -->
    <div style="padding: 24px;">
      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 20px; display: table; width: 100%; box-sizing: border-box;">
        <div style="display: table-row;">
          <div style="display: table-cell; vertical-align: middle;">
            <span style="font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600;">Overall Risk Score</span>
          </div>
          <div style="display: table-cell; text-align: right; vertical-align: middle;">
            <span style="display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; color: {risk_color}; background-color: {risk_bg};">
              {risk_score}/100 ({risk_label})
            </span>
          </div>
        </div>
      </div>

      <div style="margin-bottom: 24px;">
        <h3 style="color: #334155; font-size: 14px; font-weight: 600; margin: 0 0 10px 0;">AI Generated Clinical Analysis:</h3>
        <div style="padding: 16px; background-color: #f1f5f9; border-left: 4px solid #475569; border-radius: 4px; color: #334155; font-size: 14px; line-height: 1.6; font-style: italic;">
          "{doctor_summary}"
        </div>
      </div>

      <div style="text-align: center; border-top: 1px solid #f1f5f9; padding-top: 20px;">
        <p style="font-size: 11px; color: #94a3b8; margin: 0;">
          This report was generated automatically by Gemini 1.5 Flash using deterministic scoring rules.
        </p>
      </div>
    </div>
  </div>
</body>
</html>
"""

    return _send_email_helper(recipient, subject, body)


def send_daily_log_email(db: Session, to_email: str) -> bool:
    """
    Query today's readings for all patients and compile them into a daily digest email.
    If no readings are logged, we don't send anything.
    If only one patient logged, the report naturally contains only that person's reading.
    """
    today = date.today()
    readings = db.query(models.Reading).filter(models.Reading.date == today).all()
    if not readings:
        print("[email_service] No patient readings logged today. Skipping daily log email.")
        return False
        
    recipient = GMAIL_USER if GMAIL_USER else to_email
    if not recipient:
        print("[email_service] No recipient email configured.")
        return False
        
    # Calculate summary metrics
    total_logged = len(readings)
    glucose_values = [r.glucose_mg_dl for r in readings]
    avg_glucose = sum(glucose_values) / total_logged if total_logged > 0 else 0.0
    
    # Query alerts triggered today
    today_start = datetime.combine(today, time.min)
    today_alerts = db.query(models.Alert).filter(models.Alert.triggered_at >= today_start).all()
    total_alerts = len(today_alerts)
    
    subject = f"Daily Log Summary: {total_logged} Patient(s) Logged — {today.strftime('%b %d, %Y')}"
    
    # Build HTML rows for each patient using nested tables for solid email client rendering
    cards_html = ""
    for r in readings:
        p = r.patient
        
        # Get alerts triggered today for this specific patient
        p_alerts = [a for a in today_alerts if a.patient_id == p.id]
        
        # Glucose badge style
        if r.glucose_mg_dl > 300:
            badge_color = "#dc2626" # red
            badge_bg = "#fee2e2"
            badge_text = "CRITICAL"
        elif r.glucose_mg_dl > 180:
            badge_color = "#ea580c" # orange
            badge_bg = "#ffedd5"
            badge_text = "HIGH"
        elif r.glucose_mg_dl > 140:
            badge_color = "#ca8a04" # yellow
            badge_bg = "#fef9c3"
            badge_text = "MEDIUM"
        else:
            badge_color = "#16a34a" # green
            badge_bg = "#dcfce7"
            badge_text = "NORMAL"
            
        med_badge_color = "#16a34a" if r.medication_taken else "#dc2626"
        med_badge_bg = "#dcfce7" if r.medication_taken else "#fee2e2"
        med_text = "Taken" if r.medication_taken else "Missed"
        
        alerts_html = ""
        if p_alerts:
            alerts_html += f"""
            <div style="margin-top: 14px; padding: 12px; background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px;">
              <h4 style="margin: 0 0 6px 0; color: #b45309; font-size: 13px; font-weight: 700;">⚠️ Alerts Triggered Today:</h4>
              <ul style="margin: 0; padding-left: 18px; color: #78350f; font-size: 12px; line-height: 1.5;">
            """
            for a in p_alerts:
                alerts_html += f"    <li><strong>{a.severity.value}</strong>: {a.message or 'Triggered trend or limit alert.'}</li>"
            alerts_html += """
              </ul>
            </div>
            """
            
        cards_html += f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
          <!-- Card Header -->
          <table style="width: 100%; border-collapse: collapse; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 16px;">
            <tr>
              <td style="vertical-align: top; padding-bottom: 10px;">
                <h3 style="margin: 0; color: #0f172a; font-size: 16px; font-weight: 700;">{p.name}</h3>
                <span style="color: #64748b; font-size: 12px;">{p.email}</span>
              </td>
              <td style="text-align: right; vertical-align: top; padding-bottom: 10px;">
                <span style="display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; color: {badge_color}; background-color: {badge_bg}; text-transform: uppercase;">
                  {badge_text}
                </span>
              </td>
            </tr>
          </table>
          
          <!-- Card Body -->
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <!-- Glucose stat -->
              <td style="width: 40%; vertical-align: top; padding-right: 15px;">
                <span style="color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Glucose Level</span>
                <div style="font-size: 26px; font-weight: 800; color: #0f172a; margin-top: 4px;">{r.glucose_mg_dl:.1f} <span style="font-size: 13px; font-weight: 400; color: #64748b;">mg/dL</span></div>
              </td>
              
              <!-- Metrics table -->
              <td style="width: 60%; vertical-align: top; border-left: 1px solid #f1f5f9; padding-left: 15px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #334155;">
                  <tr>
                    <td style="padding: 3px 0; color: #64748b; width: 45%;">Medication:</td>
                    <td style="padding: 3px 0; font-weight: 600;"><span style="display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: {med_badge_color}; background-color: {med_badge_bg};">{med_text}</span></td>
                  </tr>
                  <tr>
                    <td style="padding: 3px 0; color: #64748b;">Sleep:</td>
                    <td style="padding: 3px 0; font-weight: 600;">{f"{r.sleep_hrs:.1f} hrs" if r.sleep_hrs is not None else "—"}</td>
                  </tr>
                  <tr>
                    <td style="padding: 3px 0; color: #64748b;">Exercise:</td>
                    <td style="padding: 3px 0; font-weight: 600;">{f"{int(r.exercise_min)} mins" if r.exercise_min is not None else "—"}</td>
                  </tr>
                  <tr>
                    <td style="padding: 3px 0; color: #64748b;">Weight:</td>
                    <td style="padding: 3px 0; font-weight: 600;">{f"{r.weight_kg:.1f} kg" if r.weight_kg is not None else "—"}</td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
          
          {alerts_html}
        </div>
        """
        
    # Outer layout
    body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Patient Log Summary</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased;">
  <div style="max-width: 600px; margin: 0 auto; background: transparent;">
    
    <!-- Premium Header -->
    <div style="background: linear-gradient(135deg, #1e3a8a, #0f172a); border-radius: 16px 16px 0 0; padding: 28px 24px; text-align: center; color: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
      <div style="display: inline-block; font-size: 24px; margin-bottom: 8px;">⚕️</div>
      <h1 style="margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Daily Patient Log Summary</h1>
      <p style="margin: 4px 0 0 0; font-size: 13px; color: #93c5fd; font-weight: 500;">{today.strftime('%A, %B %d, %Y')}</p>
    </div>
    
    <!-- Quick Stats Banner -->
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 16px 16px; padding: 16px 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); display: table; width: 100%; box-sizing: border-box;">
      <div style="display: table-row;">
        <div style="display: table-cell; text-align: center; width: 33.3%;">
          <span style="display: block; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Logged Today</span>
          <span style="font-size: 18px; font-weight: 700; color: #1e3a8a;">{total_logged}</span>
        </div>
        <div style="display: table-cell; text-align: center; width: 33.3%; border-left: 1px solid #e2e8f0;">
          <span style="display: block; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Avg Glucose</span>
          <span style="font-size: 18px; font-weight: 700; color: #1e3a8a;">{avg_glucose:.1f} <span style="font-size: 11px; font-weight: 400; color: #64748b;">mg/dL</span></span>
        </div>
        <div style="display: table-cell; text-align: center; width: 33.3%; border-left: 1px solid #e2e8f0;">
          <span style="display: block; font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Active Alerts</span>
          <span style="font-size: 18px; font-weight: 700; color: { '#dc2626' if total_alerts > 0 else '#16a34a' };">{total_alerts}</span>
        </div>
      </div>
    </div>
    
    <!-- Patient Cards -->
    {cards_html}
    
    <!-- Footer -->
    <div style="text-align: center; padding: 20px 10px; margin-top: 10px;">
      <p style="margin: 0; font-size: 11px; color: #94a3b8; line-height: 1.5;">
        This is an automated clinical daily log summary. Please log into the clinician dashboard to view complete patient histories.
      </p>
    </div>
    
  </div>
</body>
</html>
"""

    return _send_email_helper(recipient, subject, body)


def _send_email_helper(recipient: str, subject: str, body: str) -> bool:
    """Helper function to deliver email via Resend API or fallback to Gmail SMTP."""
    # --- Method 1: Try Resend API (HTTP POST on Port 443) ---
    if RESEND_API_KEY:
        try:
            print("[email_service] Attempting to send email via Resend API...")
            headers = {
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            }
            # Resend onboarding domain requires sending from onboarding@resend.dev
            payload = {
                "from": "Chronic Monitor <onboarding@resend.dev>",
                "to": [recipient],
                "subject": subject,
                "html": body,
            }
            response = httpx.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            if response.status_code in (200, 201):
                print(f"[email_service] Email sent successfully via Resend to {recipient}")
                return True
            else:
                print(f"[email_service] Resend API failed (status={response.status_code}): {response.text}")
        except Exception as e:
            print(f"[email_service] Resend API error: {e}")

    # --- Method 2: Fallback to Gmail SMTP ---
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[email_service] SMTP credentials not set and Resend unavailable — skipping email.")
        return False

    print("[email_service] Attempting to send email via Gmail SMTP...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = recipient
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipient, msg.as_string())
        print(f"[email_service] Email sent successfully via SMTP to {recipient}")
        return True
    except Exception as e:
        print(f"[email_service] Failed to send email via SMTP: {e}")
        return False
