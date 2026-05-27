from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import get_settings
from core.database import get_db_from_request
from core.prometheus import increment_auth_failure
from canonical_models.common import UserRole

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    _HAS_SLOWAPI = True
except Exception:  # pragma: no cover - safe fallback for envs without slowapi
    _HAS_SLOWAPI = False

    class Limiter:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

        def limit(self, *args, **kwargs):
            def _decorator(func):
                return func

            return _decorator

    def get_remote_address(request: Request) -> str:  # type: ignore[no-redef]
        host = request.client.host if request.client else "unknown"
        return host


settings = get_settings()
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=True)

# Canonical limiter requested in spec:
# - login: 10/minute per IP
# - register: 5/hour per IP
# - forgot-password: 3/hour per IP
rate_limiter = Limiter(key_func=get_remote_address)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def check_jwt_config() -> None:
    secret = settings.JWT_SECRET_KEY
    if len(secret) < 64:
        logger.warning("JWT_SECRET_KEY is less than 64 chars. For production, use a 64+ char random string.")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Handle UnknownHashError and other hash verification errors gracefully
        # Invalid hashes will be fixed by migration script
        return False


def _normalize_role_value(role: UserRole | str) -> str:
    role_value = role.value if isinstance(role, UserRole) else str(role).strip().lower()
    if role_value == "user":
        role_value = UserRole.CUSTOMER.value
    return role_value


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(subject: str, role: UserRole | str, expires_minutes: Optional[int] = None) -> str:
    ttl_minutes = expires_minutes if expires_minutes is not None else settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    expire = utcnow() + timedelta(minutes=ttl_minutes)
    role_value = _normalize_role_value(role)
    payload = {
        "sub": subject,
        "role": role_value,
        "token_type": "access",
        "jti": uuid4().hex,
        "exp": expire,
        "iat": utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    role: UserRole | str,
    *,
    family_id: Optional[str] = None,
    expires_days: Optional[int] = None,
) -> tuple[str, dict[str, Any]]:
    ttl_days = expires_days if expires_days is not None else settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    now = utcnow()
    expire = now + timedelta(days=ttl_days)
    refresh_family_id = family_id or uuid4().hex
    payload = {
        "sub": subject,
        "role": _normalize_role_value(role),
        "token_type": "refresh",
        "jti": uuid4().hex,
        "family_id": refresh_family_id,
        "exp": expire,
        "iat": now,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, payload


def decode_token(token: str, *, expected_type: Optional[str] = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_type = payload.get("token_type", "access")
        if expected_type and token_type != expected_type:
            increment_auth_failure("invalid_token_type", "jwt_decode")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as exc:
        increment_auth_failure("invalid_token", "jwt_decode")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="refresh")


async def is_access_token_revoked(db: Any, payload: dict[str, Any]) -> bool:
    jti = payload.get("jti")
    if not jti:
        return False
    revoked = await db.revoked_tokens.find_one({"jti": str(jti)}, {"_id": 0, "jti": 1})
    return revoked is not None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, Any]:
    """
    Canonical auth dependency:
    - validates JWT
    - loads user from DB
    - enforces is_active and is_blocked checks
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        increment_auth_failure("missing_subject", "get_current_user")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    db = get_db_from_request(request)
    if await is_access_token_revoked(db, payload):
        increment_auth_failure("revoked_token", "get_current_user")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        # fallback: some datasets may use _id string for user id
        user = await db.users.find_one({"_id": user_id}, {"_id": 0})
    if not user:
        increment_auth_failure("user_not_found", "get_current_user")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.get("is_active", True):
        increment_auth_failure("account_inactive", "get_current_user")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    if user.get("is_blocked", False):
        increment_auth_failure("account_blocked", "get_current_user")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account blocked")

    # normalized shape for downstream consumers
    normalized_role = str(user.get("role", UserRole.CUSTOMER.value)).strip().lower()
    if normalized_role == "user":
        normalized_role = UserRole.CUSTOMER.value
    user["role"] = normalized_role
    user["id"] = str(user.get("id") or user_id)
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[dict[str, Any]]:
    if not credentials:
        return None
    try:
        return await get_current_user(request=request, credentials=credentials)
    except HTTPException:
        return None


def require_roles(*allowed_roles: UserRole | str) -> Callable:
    normalized = {
        role.value if isinstance(role, UserRole) else str(role).lower() for role in allowed_roles
    }

    async def _checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        role = str(current_user.get("role", "")).lower()
        if role not in normalized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user

    return _checker


def require_admin() -> Callable:
    return require_roles(UserRole.ADMIN)


async def require_admin_canonical(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Canonical admin role check dependency."""
    role = str(current_user.get("role", "")).lower()
    if role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


async def require_vendor_canonical(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Canonical vendor role check dependency."""
    role = str(current_user.get("role", "")).lower()
    if role != UserRole.VENDOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor role required")
    return current_user


async def require_customer_canonical(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Canonical customer role check dependency."""
    role = str(current_user.get("role", "")).lower()
    if role != UserRole.CUSTOMER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer role required")
    return current_user


def enforce_owner_or_admin(
    *,
    current_user: dict[str, Any],
    owner_user_id: Optional[str],
    resource_name: str = "resource",
) -> None:
    role = str(current_user.get("role", "")).lower()
    if role == UserRole.ADMIN.value:
        return
    if not owner_user_id or str(owner_user_id) != str(current_user.get("id")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have access to this {resource_name}",
        )


def enforce_vendor_or_admin(
    *,
    current_user: dict[str, Any],
    vendor_user_id: Optional[str],
    resource_name: str = "vendor resource",
) -> None:
    role = str(current_user.get("role", "")).lower()
    if role == UserRole.ADMIN.value:
        return
    if role != UserRole.VENDOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor access required")
    if not vendor_user_id or str(vendor_user_id) != str(current_user.get("id")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have access to this {resource_name}",
        )


def get_rate_limiter() -> Limiter:
    return rate_limiter


def login_rate_limit() -> str:
    return "10/minute"


def register_rate_limit() -> str:
    return "5/hour"


def forgot_password_rate_limit() -> str:
    return "3/hour"


def is_slowapi_enabled() -> bool:
    return _HAS_SLOWAPI
