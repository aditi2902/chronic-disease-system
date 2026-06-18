# ⚕ Chronic — Diabetic Patient Monitoring System

> A real-time monitoring platform that detects dangerous glucose trends before they become emergencies, and generates AI summaries for both patients and doctors.

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                          │
│   Login → PatientDashboard   │   DoctorDashboard                 │
│   Log Form · Glucose Chart · Report Card · Alert Log             │
└─────────────────────┬────────────────────────────────────────────┘
                      │  HTTP / JWT Bearer
┌─────────────────────▼────────────────────────────────────────────┐
│                       FastAPI Backend                             │
│                                                                   │
│  /auth      /readings    /doctor     /reports                     │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Rule Engine   │  │  Email Service  │  │   AI Service    │  │
│  │ Threshold Check │  │  smtplib+Gmail  │  │ Gemini 1.5 Flash│  │
│  │ Trend (polyfit) │  │ HTML templates  │  │ Patient summary │  │
│  │ Deduplication   │  └─────────────────┘  │ Clinical note   │  │
│  └─────────────────┘                        └─────────────────┘  │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────────────────────────┐   │
│  │   APScheduler   │  │         SQLite (SQLAlchemy)          │   │
│  │ Weekly Sunday   │  │ patients · doctors · readings        │   │
│  │ cron + on-demand│  │ alerts · weekly_reports              │   │
│  └─────────────────┘  └─────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (LTS)

### 1. Backend

```bash
cd chronic/backend

# Create virtual environment
python -m venv ../venv
../venv/Scripts/activate        # Windows
# source ../venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure secrets
copy .env .env.local             # Edit with your Gmail + Gemini keys

# Seed demo data (3 patients + pre-generated reports)
python seed.py

# Start the API server
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd chronic/frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## 🔑 Demo Credentials

| Role | Email | Password | Profile |
|------|-------|----------|---------|
| Doctor | doctor@chronic.dev | doctor123 | Dr. Sarah Mitchell |
| Patient A | alice@chronic.dev | patient123 | Alice Chen — Controlled (glucose 88–110) |
| Patient B | bob@chronic.dev | patient123 | Bob Martinez — **Worsening trend** (↑ 145→210, TREND_ALERT) |
| Patient C | carol@chronic.dev | patient123 | Carol Thompson — **Critical spike** (318 mg/dL) |

---

## 🔧 Environment Variables

Edit `backend/.env`:

```env
# JWT
SECRET_KEY=your-long-random-secret

# Gmail SMTP (generate at https://myaccount.google.com/apppasswords)
GMAIL_USER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=xxxx_xxxx_xxxx_xxxx

# Gemini (free at https://aistudio.google.com)
GEMINI_API_KEY=your_api_key
```

> If `GMAIL_APP_PASSWORD` or `GEMINI_API_KEY` is not set, the app gracefully degrades:
> - Emails are skipped (console warning printed)
> - AI summaries fall back to deterministic templates

---

## 📡 Key API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register/doctor` | — | Register doctor |
| POST | `/auth/register/patient` | — | Register patient |
| POST | `/auth/login` | — | Login (role-aware) |

### Patient
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/readings` | Patient JWT | Submit daily reading, triggers rule engine |
| GET | `/readings/me` | Patient JWT | Last N days of readings |
| GET | `/readings/me/alerts` | Patient JWT | My alert history |

### Doctor
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/doctor/patients` | Doctor JWT | All patients, sorted by risk |
| GET | `/doctor/patients/{id}/readings` | Doctor JWT | 7-day reading history |
| GET | `/doctor/patients/{id}/alerts` | Doctor JWT | Alert log |
| PATCH | `/doctor/alerts/{id}/resolve` | Doctor JWT | Mark alert resolved |

### Reports
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/reports/{patient_id}/latest` | Patient or Doctor | Latest weekly report |
| POST | `/reports/{patient_id}/generate` | Doctor JWT | On-demand report generation |

---

## 🧠 Rule Engine Logic

### Threshold Alerts
```
glucose > 300  →  CRITICAL alert
glucose > 180  →  HIGH alert
else           →  no alert
```

### Trend Detection
Using NumPy linear regression on last 5 readings:
```python
slope = np.polyfit([0,1,2,3,4], last_5_glucose, 1)[0]
# TREND_ALERT if: slope > 5 mg/dL/day AND 4+ ascending pairs
```

**Key demo scenario:** Bob (Patient B) has glucose `[145, 158, 168, 175, 188, 195, 210]` — no single reading exceeds 300, but the worsening trend still triggers `TREND_ALERT`. This is the system's main differentiator.

### Deduplication
If an unresolved alert of the same type already exists for a patient, no new alert is created.

### Risk Score (0–100, deterministic)
```
score = (avg_glucose / 400) × 40
      + (max(slope, 0) / 20) × 30
      + (1 - adherence_pct) × 30
```
LLM only writes the human-language explanation; scoring stays auditable.

---

## 🤖 AI Reports (Gemini 1.5 Flash)

Every Sunday at 23:59, or on-demand via `POST /reports/{id}/generate`:

1. Collect 7 readings → compute stats (avg, max, slope, adherence)
2. Patient prompt → 150-word friendly summary
3. Doctor prompt → concise clinical note + recommended action
4. Compute risk score (deterministic)
5. Store in `weekly_reports` table
6. Email doctor the clinical note

---

## 🧪 Tests

```bash
# Run from project root
pytest tests/ -v
```

10 known-answer test cases covering:
- Threshold rule: 320 → CRITICAL, 210 → HIGH, 115 → None
- Exact boundary: 300.0 → no CRITICAL (exclusive), 300.1 → CRITICAL
- Trend: Bob's escalating profile → TREND_ALERT
- Trend: stable/declining → no alert
- Insufficient data (< 5 readings) → no trend alert
- Risk score bounds: always 0–100

---

## 📁 Project Structure

```
chronic/
├── backend/
│   ├── main.py              # FastAPI app, CORS, lifespan scheduler
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models.py            # ORM: patients, doctors, readings, alerts, reports
│   ├── schemas.py           # Pydantic request/response models
│   ├── auth.py              # JWT create/verify, bcrypt hashing
│   ├── dependencies.py      # FastAPI deps: get_current_user, require_doctor/patient
│   ├── seed.py              # 3 realistic patient profiles + pre-generated reports
│   ├── routers/
│   │   ├── auth.py          # Registration + login
│   │   ├── readings.py      # Daily input + rule engine trigger
│   │   ├── doctor.py        # Patient management endpoints
│   │   └── reports.py       # Weekly report retrieval + on-demand generation
│   └── services/
│       ├── rule_engine.py   # Threshold, trend (polyfit), deduplication, risk score
│       ├── email_service.py # smtplib Gmail HTML alerts + weekly digests
│       ├── ai_service.py    # Gemini Flash integration with fallback
│       └── scheduler.py     # APScheduler weekly cron + on-demand helper
│
├── frontend/
│   └── src/
│       ├── api/client.js              # Axios + JWT interceptor
│       ├── auth/AuthContext.jsx       # Auth state + localStorage
│       ├── pages/
│       │   ├── Login.jsx              # Role toggle + demo quick-fill
│       │   ├── PatientDashboard.jsx   # Log form, chart, alerts, report
│       │   └── DoctorDashboard.jsx    # Patient grid, detail view
│       └── components/
│           ├── GlucoseChart.jsx       # Recharts with threshold reference lines
│           ├── RiskBadge.jsx          # Color-coded severity badge
│           ├── AlertLog.jsx           # Alert list with resolve button
│           └── ReportCard.jsx         # Weekly stats + AI summary
│
└── tests/
    └── test_rule_engine.py    # 10 known-answer test cases
```

---

## 💬 Interview Talking Points

**"Why rule-based alerts instead of ML?"**
> 7 readings is statistically insufficient training data. Rules are clinically precise (exact glucose thresholds from ADA guidelines) and fully auditable — a doctor can trace exactly why an alert fired.

**"What does the LLM actually add?"**
> Translation. It converts numbers (`avg: 195 mg/dL, slope: +12/day, adherence: 57%`) into human language that a patient can understand or a doctor can skim in 10 seconds. The risk scoring stays deterministic and reproducible.

**"What would Phase 2 look like?"**
> A population-level XGBoost model trained on the PIMA Indians dataset to generate a prior risk estimate, then fine-tuned per-patient after 30 days of readings. 7 readings isn't enough for individual ML; 30-day rolling windows are. I didn't add it because it would add complexity without improving the MVP's core value proposition.

---

*Built with FastAPI · SQLite · React · Recharts · Gemini 1.5 Flash · smtplib*
