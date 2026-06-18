"""
routers/auth.py — Registration and login endpoints for both roles.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
import models, schemas
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/doctor", response_model=schemas.TokenResponse, status_code=201)
def register_doctor(payload: schemas.DoctorRegister, db: Session = Depends(get_db)):
    if db.query(models.Doctor).filter(models.Doctor.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    doctor = models.Doctor(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    token = create_access_token(
        email=doctor.email, role="doctor", user_id=doctor.id, name=doctor.name
    )
    return schemas.TokenResponse(access_token=token, role="doctor", user_id=doctor.id, name=doctor.name)


@router.post("/register/patient", response_model=schemas.TokenResponse, status_code=201)
def register_patient(payload: schemas.PatientRegister, db: Session = Depends(get_db)):
    if db.query(models.Patient).filter(models.Patient.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    patient = models.Patient(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        doctor_id=payload.doctor_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    token = create_access_token(
        email=patient.email, role="patient", user_id=patient.id, name=patient.name
    )
    return schemas.TokenResponse(access_token=token, role="patient", user_id=patient.id, name=patient.name)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    if payload.role == "doctor":
        user = db.query(models.Doctor).filter(models.Doctor.email == payload.email).first()
    elif payload.role == "patient":
        user = db.query(models.Patient).filter(models.Patient.email == payload.email).first()
    else:
        raise HTTPException(status_code=400, detail="role must be 'patient' or 'doctor'")

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(
        email=user.email, role=payload.role, user_id=user.id, name=user.name
    )
    return schemas.TokenResponse(
        access_token=token, role=payload.role, user_id=user.id, name=user.name
    )
