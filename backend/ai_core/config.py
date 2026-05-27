from __future__ import annotations

from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _HAS_PYDANTIC_SETTINGS = True
except ModuleNotFoundError:
    from pydantic import BaseModel
    import os

    _HAS_PYDANTIC_SETTINGS = False

    class BaseSettings(BaseModel):  # type: ignore[misc]
        pass

    def SettingsConfigDict(**kwargs):  # type: ignore[no-redef]
        return kwargs


class AIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ai_module_name: str = "decision-os-ai-core"
    ai_api_key: str = "dev-ai-key"
    ai_rate_limit_per_minute: int = 120
    ai_rate_limit_window_seconds: int = 60
    ai_rate_limit_ttl_seconds: int = 120
    ai_request_timeout_ms: int = 2000

    @classmethod
    def from_env(cls) -> "AIConfig":
        if _HAS_PYDANTIC_SETTINGS:
            return cls()
        return cls(
            ai_module_name=os.getenv("AI_MODULE_NAME", "decision-os-ai-core"),
            ai_api_key=os.getenv("AI_API_KEY", "dev-ai-key"),
            ai_rate_limit_per_minute=int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "120")),
            ai_rate_limit_window_seconds=int(os.getenv("AI_RATE_LIMIT_WINDOW_SECONDS", "60")),
            ai_rate_limit_ttl_seconds=int(os.getenv("AI_RATE_LIMIT_TTL_SECONDS", "120")),
            ai_request_timeout_ms=int(os.getenv("AI_REQUEST_TIMEOUT_MS", "2000")),
        )


@lru_cache
def get_ai_config() -> AIConfig:
    return AIConfig.from_env()
