# DEPRECATED — Do not import from this file.
# Use: from core.security import get_current_user, require_roles, require_admin
import warnings
warnings.warn("auth.py is deprecated. Use core.security instead.", DeprecationWarning, stacklevel=2)

"""Legacy auth compatibility layer.

Canonical auth implementation lives in core.security.
"""

from datetime import timedelta
from typing import Optional

from canonical_models.common import UserRole
from core.security import (
    decode_access_token,
    get_current_user,
    get_current_user_optional,
    hash_password,
    require_roles,
    verify_password,
    create_access_token as create_core_access_token,
)


def get_password_hash(password: str) -> str:
    return hash_password(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    subject = str(data.get("sub") or data.get("id") or "")
    role_value = str(data.get("role") or UserRole.CUSTOMER.value).lower()
    if role_value == "user":
        role_value = UserRole.CUSTOMER.value
    role = UserRole(role_value)
    expires_minutes = int(expires_delta.total_seconds() // 60) if expires_delta else None
    return create_core_access_token(subject=subject, role=role, expires_minutes=expires_minutes)


def decode_token(token: str) -> dict:
    return decode_access_token(token)


def require_role(required_roles: list):
    return require_roles(*required_roles)


__all__ = [
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
]
