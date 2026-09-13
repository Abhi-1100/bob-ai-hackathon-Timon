"""
Authentication Router for D2 Threat Intelligence Correlation & Alert Prioritisation Assistant.
Provides enterprise registration, login, JWT token issuance, password reset, and user profiling.
"""

import hashlib
import hmac
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import UserDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

JWT_SECRET = os.getenv("JWT_SECRET", "d2_threat_intel_soc_jwt_secret_key_2026_super_secure")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


# ---------------------------------------------------------------------------
# Password Hashing & Verification (PBKDF2-HMAC-SHA256)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Generate a secure PBKDF2-HMAC-SHA256 salted password hash."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored PBKDF2 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        stored_hash = parts[2]
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return hmac.compare_digest(key.hex(), stored_hash)
    except Exception as exc:
        logger.error(f"Password verification error: {exc}")
        return False


def create_access_token(user_id: str, email: str, role: str, full_name: str) -> str:
    """Generate a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "name": full_name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please authenticate again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid security token.",
        )


# In-memory user fallback cache if database is temporarily unavailable
_MEM_USERS = {}

# Seed default analyst account
_DEFAULT_USER_EMAIL = "analyst@sentinelforge.mil"
_MEM_USERS[_DEFAULT_USER_EMAIL] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "email": _DEFAULT_USER_EMAIL,
    "hashed_password": hash_password("SentinelForge#2026"),
    "full_name": "Chief SOC Analyst",
    "organization": "Sentinel Defense Command",
    "role": "Tier 3 Incident Responder",
    "reset_token": None,
    "reset_token_expires": None,
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    organization: Optional[str] = "Security Operations Center"
    role: Optional[str] = "SOC Analyst"


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    organization: str
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new enterprise operator account."""
    clean_email = req.email.strip().lower()

    # Check database
    try:
        existing_user = db.query(UserDB).filter(UserDB.email == clean_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An operator account with this email already exists.",
            )

        new_user = UserDB(
            id=uuid.uuid4(),
            email=clean_email,
            hashed_password=hash_password(req.password),
            full_name=req.name.strip(),
            organization=req.organization or "Security Operations Center",
            role=req.role or "SOC Analyst",
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        user_id = str(new_user.id)
        user_name = new_user.full_name
        user_org = new_user.organization
        user_role = new_user.role

    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Database registration fallback to memory: {exc}")
        if clean_email in _MEM_USERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An operator account with this email already exists.",
            )
        user_id = str(uuid.uuid4())
        _MEM_USERS[clean_email] = {
            "id": user_id,
            "email": clean_email,
            "hashed_password": hash_password(req.password),
            "full_name": req.name.strip(),
            "organization": req.organization or "Security Operations Center",
            "role": req.role or "SOC Analyst",
            "reset_token": None,
            "reset_token_expires": None,
        }
        user_name = req.name.strip()
        user_org = req.organization or "Security Operations Center"
        user_role = req.role or "SOC Analyst"

    token = create_access_token(user_id, clean_email, user_role, user_name)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            name=user_name,
            email=clean_email,
            organization=user_org,
            role=user_role,
        ),
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate an operator and issue a JWT access token."""
    clean_email = req.email.strip().lower()

    user_record = None
    try:
        user_record = db.query(UserDB).filter(UserDB.email == clean_email).first()
    except Exception as exc:
        logger.warning(f"Database query error, checking memory: {exc}")

    if user_record:
        if not verify_password(req.password, user_record.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid operator credentials. Access denied.",
            )
        user_id = str(user_record.id)
        user_name = user_record.full_name
        user_org = user_record.organization or "Security Operations Center"
        user_role = user_record.role or "SOC Analyst"
    elif clean_email in _MEM_USERS:
        mem_user = _MEM_USERS[clean_email]
        if not verify_password(req.password, mem_user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid operator credentials. Access denied.",
            )
        user_id = mem_user["id"]
        user_name = mem_user["full_name"]
        user_org = mem_user["organization"]
        user_role = mem_user["role"]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator account not found. Please verify your credentials or register.",
        )

    token = create_access_token(user_id, clean_email, user_role, user_name)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            name=user_name,
            email=clean_email,
            organization=user_org,
            role=user_role,
        ),
    )


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Initiate an operator password reset flow and issue a reset token."""
    clean_email = req.email.strip().lower()
    reset_token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    try:
        user = db.query(UserDB).filter(UserDB.email == clean_email).first()
        if user:
            user.reset_token = reset_token
            user.reset_token_expires = expires
            db.commit()
    except Exception as exc:
        logger.warning(f"Database update error in forgot-password: {exc}")
        if clean_email in _MEM_USERS:
            _MEM_USERS[clean_email]["reset_token"] = reset_token
            _MEM_USERS[clean_email]["reset_token_expires"] = expires

    # Return standard enterprise response (prevent account enumeration)
    return {
        "status": "success",
        "message": f"If an operator account exists for {clean_email}, instructions have been dispatched.",
        "reset_token_demo": reset_token,  # Provided for immediate hackathon testing
        "reset_url": f"/reset-password?token={reset_token}",
    }


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset account password using verified token."""
    now = datetime.now(timezone.utc)
    found = False

    try:
        user = db.query(UserDB).filter(UserDB.reset_token == req.token).first()
        if user:
            # Check expiry
            if user.reset_token_expires and user.reset_token_expires > now:
                user.hashed_password = hash_password(req.new_password)
                user.reset_token = None
                user.reset_token_expires = None
                db.commit()
                found = True
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password reset token has expired. Please request a new link.",
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Database error in reset-password: {exc}")

    if not found:
        # Check memory store
        for email, u in _MEM_USERS.items():
            if u.get("reset_token") == req.token:
                u["hashed_password"] = hash_password(req.new_password)
                u["reset_token"] = None
                u["reset_token_expires"] = None
                found = True
                break

    if not found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    return {
        "status": "success",
        "message": "Operator credentials successfully updated. Please authenticate.",
    }


@router.get("/me", response_model=UserResponse)
def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Validate bearer access token and return current operator profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    email = payload.get("email")

    return UserResponse(
        id=user_id or "default-operator-id",
        name=payload.get("name", "Chief SOC Analyst"),
        email=email or "analyst@sentinelforge.mil",
        organization="Sentinel Defense Command",
        role=payload.get("role", "SOC Analyst"),
    )
