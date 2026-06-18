"""
dependencies.py — FastAPI dependency injection helpers for auth + role checks.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from auth import decode_token
from database import get_db
import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Decode JWT, look up the user in DB (patient or doctor), return them.
    Raises 401 if token is invalid or user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if role == "doctor":
        user = db.query(models.Doctor).filter(models.Doctor.email == email).first()
    else:
        user = db.query(models.Patient).filter(models.Patient.email == email).first()

    if user is None:
        raise credentials_exception

    # Attach role for downstream use
    user.__role__ = role
    return user


def require_doctor(current_user=Depends(get_current_user)):
    """Guard: only doctors can access this endpoint."""
    if getattr(current_user, "__role__", None) != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required",
        )
    return current_user


def require_patient(current_user=Depends(get_current_user)):
    """Guard: only patients can access this endpoint."""
    if getattr(current_user, "__role__", None) != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access required",
        )
    return current_user
