import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import field_validator

    _HAS_PYDANTIC_SETTINGS = True
except ModuleNotFoundError:
    from pydantic import BaseModel, field_validator

    _HAS_PYDANTIC_SETTINGS = False

    class BaseSettings(BaseModel):  # type: ignore[misc]
        pass

    def SettingsConfigDict(**kwargs):  # type: ignore[no-redef]
        return kwargs


_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE_PATH = _BACKEND_DIR / ".env"

DEFAULT_ALLOWED_ORIGINS = (
    "https://shadiro.com,"
    "https://www.shadiro.com,"
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173"
)

DEFAULT_SECURITY_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)

WEAK_JWT_SECRET_VALUES = {"secret", "changeme", "password", "your_secret_key", "supersecret"}


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class SettingsMixin:
    def allowed_origins_list(self) -> list[str]:
        raw = getattr(self, "ALLOWED_ORIGINS", "") or getattr(self, "CORS_ORIGINS", "")
        origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
        if "*" in origins:
            raise ValueError("Wildcard CORS origin '*' is not allowed")
        return list(dict.fromkeys(origins))

    @property
    def is_production(self) -> bool:
        return str(getattr(self, "APP_ENV", "production")).strip().lower() == "production"


if _HAS_PYDANTIC_SETTINGS:
    class Settings(SettingsMixin, BaseSettings):
        model_config = SettingsConfigDict(
            env_file=str(_ENV_FILE_PATH),
            env_file_encoding="utf-8",
            extra="ignore",
        )

        APP_NAME: str = "Event Marketplace API"
        APP_ENV: str = "production"
        LOG_LEVEL: str = "INFO"

        MONGO_URL: str
        DB_NAME: str
        MONGO_MIN_POOL_SIZE: int = 5
        MONGO_MAX_POOL_SIZE: int = 100
        MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 5000

        JWT_SECRET_KEY: str
        JWT_ALGORITHM: str = "HS256"
        JWT_EXPIRE_MINUTES: int = 30
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

        RAZORPAY_KEY_ID: str
        RAZORPAY_KEY_SECRET: str
        RAZORPAY_WEBHOOK_SECRET: str = ""
        RAZORPAY_PAYOUT_ACCOUNT_NUMBER: str = ""

        CORS_ORIGINS: str = DEFAULT_ALLOWED_ORIGINS
        ALLOWED_ORIGINS: str = DEFAULT_ALLOWED_ORIGINS

        REQUEST_MAX_BODY_SIZE_BYTES: int = 2 * 1024 * 1024
        SECURITY_CSP: str = DEFAULT_SECURITY_CSP

        REDIS_URL: str = ""
        DELIVERY_QR_HMAC_SECRET: str = ""
        GROCERY_DELIVERY_AUTO_ENABLED: bool = True
        GROCERY_DELIVERY_DEFAULT_EARNING_PAISE: int = 12000
        GROCERY_DELIVERY_DEFAULT_ETA_MINUTES: int = 40
        GROCERY_DELIVERY_DISTANCE_HINT_KM: float = 5.0
        RATE_LIMIT_ENABLED: bool = True
        RATE_LIMIT_AUTH_PER_MINUTE: int = 10
        RATE_LIMIT_AUTH_BURST: int = 5
        RATE_LIMIT_PUBLIC_PER_MINUTE: int = 120
        RATE_LIMIT_PUBLIC_BURST: int = 40
        RATE_LIMIT_BURST_WINDOW_SECONDS: int = 10
        SENTRY_DSN: str = ""

        @field_validator("JWT_SECRET_KEY")
        @classmethod
        def validate_jwt_key(cls, v: str) -> str:
            if len(v) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be at least 32 characters. Current length is too short to be secure."
                )
            if v in WEAK_JWT_SECRET_VALUES:
                raise ValueError("JWT_SECRET_KEY is a known weak value. Use a random 64+ character string.")
            return v
else:
    class Settings(SettingsMixin, BaseSettings):
        APP_NAME: str = "Event Marketplace API"
        APP_ENV: str = "production"
        LOG_LEVEL: str = "INFO"

        MONGO_URL: str
        DB_NAME: str
        MONGO_MIN_POOL_SIZE: int = 5
        MONGO_MAX_POOL_SIZE: int = 100
        MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 5000

        JWT_SECRET_KEY: str
        JWT_ALGORITHM: str = "HS256"
        JWT_EXPIRE_MINUTES: int = 30
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

        RAZORPAY_KEY_ID: str
        RAZORPAY_KEY_SECRET: str
        RAZORPAY_WEBHOOK_SECRET: str = ""
        RAZORPAY_PAYOUT_ACCOUNT_NUMBER: str = ""

        CORS_ORIGINS: str = DEFAULT_ALLOWED_ORIGINS
        ALLOWED_ORIGINS: str = DEFAULT_ALLOWED_ORIGINS

        REQUEST_MAX_BODY_SIZE_BYTES: int = 2 * 1024 * 1024
        SECURITY_CSP: str = DEFAULT_SECURITY_CSP

        REDIS_URL: str = ""
        DELIVERY_QR_HMAC_SECRET: str = ""
        GROCERY_DELIVERY_AUTO_ENABLED: bool = True
        GROCERY_DELIVERY_DEFAULT_EARNING_PAISE: int = 12000
        GROCERY_DELIVERY_DEFAULT_ETA_MINUTES: int = 40
        GROCERY_DELIVERY_DISTANCE_HINT_KM: float = 5.0
        RATE_LIMIT_ENABLED: bool = True
        RATE_LIMIT_AUTH_PER_MINUTE: int = 10
        RATE_LIMIT_AUTH_BURST: int = 5
        RATE_LIMIT_PUBLIC_PER_MINUTE: int = 120
        RATE_LIMIT_PUBLIC_BURST: int = 40
        RATE_LIMIT_BURST_WINDOW_SECONDS: int = 10
        SENTRY_DSN: str = ""

        @field_validator("JWT_SECRET_KEY")
        @classmethod
        def validate_jwt_key(cls, v: str) -> str:
            if len(v) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be at least 32 characters. Current length is too short to be secure."
                )
            if v in WEAK_JWT_SECRET_VALUES:
                raise ValueError("JWT_SECRET_KEY is a known weak value. Use a random 64+ character string.")
            return v

        @classmethod
        def from_env(cls) -> "Settings":
            # fallback path: load .env manually when pydantic-settings is unavailable
            load_dotenv(_ENV_FILE_PATH)

            env_map: Dict[str, Any] = {
                "APP_NAME": os.getenv("APP_NAME", "Event Marketplace API"),
                "APP_ENV": os.getenv("APP_ENV", "production"),
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
                "MONGO_URL": os.getenv("MONGO_URL"),
                "DB_NAME": os.getenv("DB_NAME"),
                "MONGO_MIN_POOL_SIZE": int(os.getenv("MONGO_MIN_POOL_SIZE", "5")),
                "MONGO_MAX_POOL_SIZE": int(os.getenv("MONGO_MAX_POOL_SIZE", "100")),
                "MONGO_SERVER_SELECTION_TIMEOUT_MS": int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000")),
                "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY"),
                "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM", "HS256"),
                "JWT_EXPIRE_MINUTES": int(os.getenv("JWT_EXPIRE_MINUTES", "30")),
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
                "JWT_REFRESH_TOKEN_EXPIRE_DAYS": int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
                "RAZORPAY_KEY_ID": os.getenv("RAZORPAY_KEY_ID"),
                "RAZORPAY_KEY_SECRET": os.getenv("RAZORPAY_KEY_SECRET"),
                "RAZORPAY_WEBHOOK_SECRET": os.getenv("RAZORPAY_WEBHOOK_SECRET", ""),
                "RAZORPAY_PAYOUT_ACCOUNT_NUMBER": os.getenv("RAZORPAY_PAYOUT_ACCOUNT_NUMBER", ""),
                "CORS_ORIGINS": os.getenv("CORS_ORIGINS", DEFAULT_ALLOWED_ORIGINS),
                "ALLOWED_ORIGINS": os.getenv("ALLOWED_ORIGINS", os.getenv("CORS_ORIGINS", DEFAULT_ALLOWED_ORIGINS)),
                "REQUEST_MAX_BODY_SIZE_BYTES": int(os.getenv("REQUEST_MAX_BODY_SIZE_BYTES", str(2 * 1024 * 1024))),
                "SECURITY_CSP": os.getenv("SECURITY_CSP", DEFAULT_SECURITY_CSP),
                "REDIS_URL": os.getenv("REDIS_URL", ""),
                "DELIVERY_QR_HMAC_SECRET": os.getenv("DELIVERY_QR_HMAC_SECRET", ""),
                "GROCERY_DELIVERY_AUTO_ENABLED": _parse_bool(os.getenv("GROCERY_DELIVERY_AUTO_ENABLED"), True),
                "GROCERY_DELIVERY_DEFAULT_EARNING_PAISE": int(os.getenv("GROCERY_DELIVERY_DEFAULT_EARNING_PAISE", "12000")),
                "GROCERY_DELIVERY_DEFAULT_ETA_MINUTES": int(os.getenv("GROCERY_DELIVERY_DEFAULT_ETA_MINUTES", "40")),
                "GROCERY_DELIVERY_DISTANCE_HINT_KM": float(os.getenv("GROCERY_DELIVERY_DISTANCE_HINT_KM", "5")),
                "RATE_LIMIT_ENABLED": _parse_bool(os.getenv("RATE_LIMIT_ENABLED"), True),
                "RATE_LIMIT_AUTH_PER_MINUTE": int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "10")),
                "RATE_LIMIT_AUTH_BURST": int(os.getenv("RATE_LIMIT_AUTH_BURST", "5")),
                "RATE_LIMIT_PUBLIC_PER_MINUTE": int(os.getenv("RATE_LIMIT_PUBLIC_PER_MINUTE", "120")),
                "RATE_LIMIT_PUBLIC_BURST": int(os.getenv("RATE_LIMIT_PUBLIC_BURST", "40")),
                "RATE_LIMIT_BURST_WINDOW_SECONDS": int(os.getenv("RATE_LIMIT_BURST_WINDOW_SECONDS", "10")),
                "SENTRY_DSN": os.getenv("SENTRY_DSN", ""),
            }
            missing = [k for k in ("MONGO_URL", "DB_NAME", "JWT_SECRET_KEY", "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET") if not env_map.get(k)]
            if missing:
                raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
            return cls(**env_map)


@lru_cache
def get_settings() -> Settings:
    if _HAS_PYDANTIC_SETTINGS:
        return Settings()
    return Settings.from_env()
