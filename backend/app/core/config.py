from __future__ import annotations

from functools import lru_cache
import os
from typing import List

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _HAS_PYDANTIC_SETTINGS = True
except ModuleNotFoundError:
    from pydantic import BaseModel

    _HAS_PYDANTIC_SETTINGS = False

    class BaseSettings(BaseModel):  # type: ignore[misc]
        pass

    def SettingsConfigDict(**kwargs):  # type: ignore[no-redef]
        return kwargs


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Decision OS for Events"
    app_env: str = "production"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    mongo_uri: str = os.getenv("MONGO_URI", os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"))
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", os.getenv("DB_NAME", "event_ai"))

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    cors_origins: str = "http://localhost:3000"

    decision_score_ttl_seconds: int = 3600
    negotiation_ttl_seconds: int = 1209600
    availability_slot_ttl_seconds: int = 2678400
    calibration_check_interval_seconds: int = 3600

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @classmethod
    def from_env(cls) -> "Settings":
        if _HAS_PYDANTIC_SETTINGS:
            return cls()
        return cls(
            app_name=os.getenv("APP_NAME", "Decision OS for Events"),
            app_env=os.getenv("APP_ENV", "production"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_prefix=os.getenv("API_PREFIX", "/api/v1"),
            mongo_uri=os.getenv("MONGO_URI", os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017")),
            mongo_db_name=os.getenv("MONGO_DB_NAME", os.getenv("DB_NAME", "event_ai")),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24 * 7))),
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000"),
            decision_score_ttl_seconds=int(os.getenv("DECISION_SCORE_TTL_SECONDS", "3600")),
            negotiation_ttl_seconds=int(os.getenv("NEGOTIATION_TTL_SECONDS", "1209600")),
            availability_slot_ttl_seconds=int(os.getenv("AVAILABILITY_SLOT_TTL_SECONDS", "2678400")),
            calibration_check_interval_seconds=int(os.getenv("CALIBRATION_CHECK_INTERVAL_SECONDS", "3600")),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
