from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMResult:
    content: str
    provider: str
    metadata: Dict[str, Any]


class BaseLLMProvider:
    name = "base"

    def is_ready(self) -> bool:
        return False

    async def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 400) -> Optional[LLMResult]:
        return None


class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    def is_ready(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    async def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 400) -> Optional[LLMResult]:
        if not self.is_ready():
            return None
        # Placeholder for future OpenAI integration
        return None


class AzureOpenAIProvider(BaseLLMProvider):
    name = "azure"

    def is_ready(self) -> bool:
        return bool(os.environ.get("AZURE_OPENAI_ENDPOINT") and os.environ.get("AZURE_OPENAI_API_KEY"))

    async def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 400) -> Optional[LLMResult]:
        if not self.is_ready():
            return None
        # Placeholder for future Azure OpenAI integration
        return None


class LocalStubProvider(BaseLLMProvider):
    name = "local"

    def is_ready(self) -> bool:
        return bool(os.environ.get("LOCAL_LLM_ENDPOINT"))

    async def generate(self, prompt: str, system: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 400) -> Optional[LLMResult]:
        if not self.is_ready():
            return None
        # Placeholder for local model integration
        return None


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    name = (provider_name or os.environ.get("ASSISTANT_COPILOT_PROVIDER") or "rules").lower()
    if name == "openai":
        return OpenAIProvider()
    if name == "azure":
        return AzureOpenAIProvider()
    if name == "local":
        return LocalStubProvider()
    return BaseLLMProvider()
