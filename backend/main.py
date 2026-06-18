"""
main.py — FastAPI application entry point.
Registers all routers, creates DB tables, starts APScheduler.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from database import engine
import models
from routers import auth, readings, doctor, reports
from services.scheduler import start_scheduler

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    _scheduler = start_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(
    title="Chronic — Diabetic Patient Monitoring System",
    description="Real-time glucose monitoring with rule-based alerts and AI-generated weekly summaries.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(readings.router)
app.include_router(doctor.router)
app.include_router(reports.router)


@app.get("/", tags=["health"])
def root():
    return {
        "status": "ok",
        "app": "Chronic — Diabetic Patient Monitoring System",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
