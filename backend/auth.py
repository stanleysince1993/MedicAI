import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, UserType
from .database import db

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, password_hash = hashed_password.split(":", 1)
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except ValueError:
        return False


def create_token(user_id: str) -> str:
    """Create a simple token for authentication"""
    # In production, use JWT tokens
    return f"token_{user_id}_{secrets.token_hex(16)}"


def verify_token(token: str) -> Optional[str]:
    """Verify token and return user ID"""
    if not token.startswith("token_"):
        return None
    
    try:
        parts = token.split("_")
        if len(parts) >= 3:
            user_id = parts[1]
            # Verify user exists and is active
            user = db.get_user_by_id(user_id)
            if user and user.is_active:
                return user_id
    except Exception:
        pass
    
    return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_doctor(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is a doctor"""
    if current_user.user_type != UserType.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required"
        )
    return current_user


async def get_current_patient(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is a patient"""
    if current_user.user_type != UserType.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access required"
        )
    return current_user
