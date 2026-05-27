import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from jose import jwt, JWTError

from core.config import get_settings
from core.database import get_db_from_request
from core.prometheus import increment_auth_failure
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    forgot_password_rate_limit,
    get_current_user,
    get_rate_limiter,
    hash_token,
    hash_password,
    login_rate_limit,
    register_rate_limit,
    verify_password,
)
from canonical_models.common import ResponseEnvelope, UserRole, utcnow

router = APIRouter(prefix="/api/auth", tags=["auth"])
rate_limiter = get_rate_limiter()
settings = get_settings()
PHONE_RE = re.compile(r"^\d{10}$")
logger = logging.getLogger(__name__)
optional_bearer = HTTPBearer(auto_error=False)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _normalize_user_role(role: UserRole | str | None) -> UserRole:
    if isinstance(role, UserRole):
        return role
    role_str = str(role or "").strip().lower()
    if role_str == "user":
        role_str = UserRole.CUSTOMER.value
    return UserRole(role_str or UserRole.CUSTOMER.value)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value):
        if isinstance(value, str) and value.strip().lower() == "user":
            return UserRole.CUSTOMER.value
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value in (None, ""):
            return None
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        if not PHONE_RE.fullmatch(digits):
            raise ValueError("Phone must be exactly 10 digits")
        return digits


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(min_length=20)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: Optional[str] = None


class AuthUser(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    is_active: bool = True
    is_blocked: bool = False
    created_at: datetime
    updated_at: datetime


class AuthPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUser


def _hash_token(token: str) -> str:
    return hash_token(token)


def _jwt_exp_to_datetime(exp: object) -> datetime:
    if isinstance(exp, datetime):
        return exp.astimezone(timezone.utc)
    if isinstance(exp, (int, float)):
        return datetime.fromtimestamp(exp, timezone.utc)
    return utcnow()


async def _store_refresh_token(
    *,
    db,
    token: str,
    payload: dict,
    request: Request,
) -> None:
    await db.refresh_tokens.insert_one(
        {
            "id": f"rt_{uuid4().hex}",
            "user_id": str(payload["sub"]),
            "role": str(payload.get("role", UserRole.CUSTOMER.value)),
            "jti": str(payload["jti"]),
            "family_id": str(payload["family_id"]),
            "token_hash": _hash_token(token),
            "issued_at": _jwt_exp_to_datetime(payload.get("iat")),
            "expires_at": _jwt_exp_to_datetime(payload.get("exp")),
            "revoked_at": None,
            "revoked_reason": None,
            "replaced_by_jti": None,
            "created_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )


async def _issue_token_pair(*, db, user_id: str, role: UserRole | str, request: Request) -> tuple[str, str]:
    normalized_role = _normalize_user_role(role)
    access_token = create_access_token(subject=user_id, role=normalized_role)
    refresh_token, refresh_payload = create_refresh_token(subject=user_id, role=normalized_role)
    await _store_refresh_token(db=db, token=refresh_token, payload=refresh_payload, request=request)
    logger.info(
        "security_event",
        extra={
            "event": "auth_token_pair_issued",
            "user_id": user_id,
            "request_id": _request_id(request),
        },
    )
    return access_token, refresh_token


async def _revoke_refresh_family(db, family_id: str, reason: str) -> None:
    await db.refresh_tokens.update_many(
        {"family_id": family_id, "revoked_at": None},
        {"$set": {"revoked_at": utcnow(), "revoked_reason": reason}},
    )


async def _rotate_refresh_token(*, db, refresh_token: str, request: Request) -> tuple[str, str, str]:
    decoded = decode_refresh_token(refresh_token)
    user_id = str(decoded.get("sub") or "")
    role = _normalize_user_role(decoded.get("role", UserRole.CUSTOMER.value)).value
    jti = str(decoded.get("jti") or "")
    family_id = str(decoded.get("family_id") or "")
    if not user_id or not jti or not family_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    now = utcnow()
    token_hash = _hash_token(refresh_token)
    stored = await db.refresh_tokens.find_one(
        {
            "jti": jti,
            "user_id": user_id,
            "token_hash": token_hash,
            "revoked_at": None,
            "expires_at": {"$gt": now},
        }
    )
    if not stored:
        reused = await db.refresh_tokens.find_one({"jti": jti}, {"_id": 0, "family_id": 1, "revoked_at": 1})
        if reused and reused.get("family_id"):
            await _revoke_refresh_family(db, str(reused["family_id"]), "reuse_detected")
            logger.warning(
                "security_event",
                extra={"event": "refresh_token_reuse_detected", "user_id": user_id, "request_id": _request_id(request)},
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = create_access_token(subject=user_id, role=role)
    new_refresh_token, new_payload = create_refresh_token(subject=user_id, role=role, family_id=family_id)
    await _store_refresh_token(db=db, token=new_refresh_token, payload=new_payload, request=request)

    await db.refresh_tokens.update_one(
        {"jti": jti, "revoked_at": None},
        {
            "$set": {
                "revoked_at": now,
                "revoked_reason": "rotated",
                "replaced_by_jti": str(new_payload["jti"]),
            }
        },
    )
    return access_token, new_refresh_token, role


async def _revoke_access_token(db, token: str, reason: str = "logout") -> None:
    payload = decode_access_token(token)
    jti = payload.get("jti")
    if not jti:
        return
    await db.revoked_tokens.update_one(
        {"jti": str(jti)},
        {
            "$setOnInsert": {
                "id": f"rjt_{uuid4().hex}",
                "jti": str(jti),
                "user_id": str(payload.get("sub") or ""),
                "token_type": "access",
                "reason": reason,
                "expires_at": _jwt_exp_to_datetime(payload.get("exp")),
                "created_at": utcnow(),
            }
        },
        upsert=True,
    )


@router.post("/register", response_model=ResponseEnvelope[AuthPayload])
@rate_limiter.limit(register_rate_limit())
async def register(request: Request, payload: RegisterRequest):
    db = get_db_from_request(request)
    email = payload.email.lower().strip()

    existing = await db.users.find_one({"email": email}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    now = utcnow()
    user_id = f"usr_{uuid4().hex}"
    role = _normalize_user_role(payload.role).value
    user_doc = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": email,
        "phone": payload.phone,
        "role": role,
        "password_hash": hash_password(payload.password),
        "is_active": True,
        "is_blocked": False,
        "created_at": now,
        "updated_at": now,
    }
    await db.users.insert_one(user_doc)

    access_token, refresh_token = await _issue_token_pair(
        db=db,
        user_id=user_id,
        role=role,
        request=request,
    )
    auth_user = AuthUser(**{k: v for k, v in user_doc.items() if k != "password_hash"})
    data = AuthPayload(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=auth_user,
    )
    return ResponseEnvelope[AuthPayload](
        success=True,
        data=data,
        message="Registered successfully",
        request_id=_request_id(request),
    )


@router.post("/login", response_model=ResponseEnvelope[AuthPayload])
@rate_limiter.limit(login_rate_limit())
async def login(request: Request, payload: LoginRequest):
    db = get_db_from_request(request)
    email = payload.email.lower().strip()

    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        increment_auth_failure("invalid_credentials", "auth_login")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Handle field name inconsistency - consolidate to password_hash
    stored_hash = user.get("password_hash") or user.get("hashed_password")
    if not stored_hash or not verify_password(payload.password, stored_hash):
        increment_auth_failure("invalid_credentials", "auth_login")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Check if user needs to reset password (from migration)
    if user.get("password_reset_required"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password reset required - please use forgot password to set a new password"
        )
    if not user.get("is_active", True):
        increment_auth_failure("account_inactive", "auth_login")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    if user.get("is_blocked", False):
        increment_auth_failure("account_blocked", "auth_login")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account blocked")

    role = _normalize_user_role(user.get("role", UserRole.CUSTOMER.value)).value
    user_id = str(user.get("id"))
    access_token, refresh_token = await _issue_token_pair(
        db=db,
        user_id=user_id,
        role=role,
        request=request,
    )

    if not isinstance(user.get("created_at"), datetime):
        user["created_at"] = datetime.now(timezone.utc)
    if not isinstance(user.get("updated_at"), datetime):
        user["updated_at"] = datetime.now(timezone.utc)

    auth_user = AuthUser(
        id=user_id,
        name=user.get("name", ""),
        email=user.get("email", email),
        phone=user.get("phone"),
        role=role,
        is_active=bool(user.get("is_active", True)),
        is_blocked=bool(user.get("is_blocked", False)),
        created_at=user["created_at"],
        updated_at=user["updated_at"],
    )
    data = AuthPayload(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=auth_user,
    )
    return ResponseEnvelope[AuthPayload](
        success=True,
        data=data,
        message="Login successful",
        request_id=_request_id(request),
    )


@router.post("/refresh", response_model=ResponseEnvelope[dict])
async def refresh_token(request: Request, payload: RefreshRequest):
    try:
        access_token, refresh_token, role = await _rotate_refresh_token(
            db=get_db_from_request(request),
            refresh_token=payload.refresh_token,
            request=request,
        )
        decoded = decode_refresh_token(refresh_token)
        user_id = decoded.get("sub")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    db = get_db_from_request(request)
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "id": 1, "is_active": 1, "is_blocked": 1})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    if user.get("is_blocked", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account blocked")
    return ResponseEnvelope[dict](
        success=True,
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
        message="Token refreshed",
        request_id=_request_id(request),
    )


@router.post("/logout", response_model=ResponseEnvelope[dict])
async def logout(
    request: Request,
    payload: LogoutRequest,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
):
    db = get_db_from_request(request)
    if credentials:
        await _revoke_access_token(db, credentials.credentials, reason="logout")

    if payload.refresh_token:
        try:
            decoded = decode_refresh_token(payload.refresh_token)
            family_id = str(decoded.get("family_id") or "")
            if family_id:
                await _revoke_refresh_family(db, family_id, "logout")
        except HTTPException:
            pass

    logger.info(
        "security_event",
        extra={"event": "user_logout", "user_id": str(current_user.get("id")), "request_id": _request_id(request)},
    )
    return ResponseEnvelope[dict](
        success=True,
        data={"user_id": str(current_user.get("id"))},
        message="Logged out",
        request_id=_request_id(request),
    )


@router.post("/forgot-password", response_model=ResponseEnvelope[dict])
@rate_limiter.limit(forgot_password_rate_limit())
async def forgot_password(request: Request, payload: ForgotPasswordRequest):
    db = get_db_from_request(request)
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1, "role": 1, "is_active": 1, "is_blocked": 1})
    if user and user.get("is_active", True) and not user.get("is_blocked", False):
        now = utcnow()
        role = _normalize_user_role(user.get("role", UserRole.CUSTOMER.value))
        reset_token = jwt.encode(
            {
                "sub": str(user["id"]),
                "role": role.value,
                "purpose": "password_reset",
                "iat": now,
                "exp": now + timedelta(minutes=15),
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        token_hash = _hash_token(reset_token)
        await db.password_reset_tokens.insert_one(
            {
                "id": f"prt_{uuid4().hex}",
                "user_id": str(user["id"]),
                "token_hash": token_hash,
                "expires_at": now + timedelta(minutes=15),
                "used_at": None,
                "created_at": now,
            }
        )
        # Email delivery intentionally omitted; token is persisted for standard out-of-band delivery.

    return ResponseEnvelope[dict](
        success=True,
        data={"message": "If the email exists, a reset link has been generated."},
        message="Forgot password request accepted",
        request_id=_request_id(request),
    )


@router.post("/reset-password", response_model=ResponseEnvelope[dict])
async def reset_password(request: Request, payload: ResetPasswordRequest):
    db = get_db_from_request(request)
    now = utcnow()
    try:
        decoded = jwt.decode(payload.token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired reset token") from exc

    if decoded.get("purpose") != "password_reset":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token purpose")

    user_id = str(decoded.get("sub") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token subject")

    token_hash = _hash_token(payload.token)
    token_doc = await db.password_reset_tokens.find_one_and_update(
        {
            "token_hash": token_hash,
            "user_id": user_id,
            "used_at": None,
            "expires_at": {"$gt": now},
        },
        {"$set": {"used_at": now}},
        projection={"_id": 0},
    )
    if not token_doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Reset token already used or expired")

    update_result = await db.users.update_one(
        {"id": user_id, "is_active": True, "is_blocked": {"$ne": True}},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": now}},
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or inactive")

    return ResponseEnvelope[dict](
        success=True,
        data={"user_id": user_id},
        message="Password reset successful",
        request_id=_request_id(request),
    )


@router.get("/me", response_model=ResponseEnvelope[AuthUser])
async def me(request: Request, current_user: dict = Depends(get_current_user)):
    db = get_db_from_request(request)
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "password_hash": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not isinstance(user.get("created_at"), datetime):
        user["created_at"] = utcnow()
    if not isinstance(user.get("updated_at"), datetime):
        user["updated_at"] = utcnow()
    user["role"] = _normalize_user_role(user.get("role", UserRole.CUSTOMER.value)).value

    return ResponseEnvelope[AuthUser](
        success=True,
        data=AuthUser(**user),
        message="Current user profile",
        request_id=_request_id(request),
    )
