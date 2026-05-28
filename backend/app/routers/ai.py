from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.llm_service import (
    LLMNotConfiguredError,
    LLMProviderError,
    smoke_test_prompt,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AISmokeTestRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)


class AISmokeTestResponse(BaseModel):
    provider: str
    success: bool
    response: str


def _provider_and_key_status() -> tuple[str, bool, bool, str]:
    settings = get_settings()
    provider = (settings.llm_provider or "").strip().lower()

    if provider == "openai":
        configured = bool(settings.openai_api_key)
        return provider, configured, configured, (
            "AI provider is configured."
            if configured
            else "OpenAI provider selected but OPENAI_API_KEY is not configured."
        )
    if provider == "gemini":
        configured = bool(settings.gemini_api_key)
        return provider, configured, configured, (
            "AI provider is configured."
            if configured
            else "Gemini provider selected but GEMINI_API_KEY is not configured."
        )
    if not provider:
        return "", False, False, (
            "LLM provider is not configured. Set LLM_PROVIDER to 'openai' or 'gemini'."
        )
    return provider, False, False, (
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Use 'openai' or 'gemini'."
    )


@router.get("/health")
def ai_health() -> dict:
    provider, api_key_configured, ai_features_available, message = _provider_and_key_status()
    return {
        "llm_provider": provider or "unconfigured",
        "api_key_configured": api_key_configured,
        "ai_features_available": ai_features_available,
        "message": message,
    }


@router.post("/smoke-test", response_model=AISmokeTestResponse)
def ai_smoke_test(payload: AISmokeTestRequest) -> AISmokeTestResponse:
    settings = get_settings()
    provider = (settings.llm_provider or "").strip().lower() or "unconfigured"

    try:
        text = smoke_test_prompt(payload.prompt, timeout_seconds=30)
        return AISmokeTestResponse(provider=provider, success=True, response=text)
    except LLMNotConfiguredError as exc:
        return AISmokeTestResponse(
            provider=provider,
            success=False,
            response=str(exc),
        )
    except LLMProviderError as exc:
        lower = str(exc).lower()
        if "quota" in lower or "rate limit" in lower or "429" in lower:
            message = "Provider quota/rate-limit error. Check usage limits and billing."
        elif "timed out" in lower or "timeout" in lower:
            message = "Provider request timed out. Retry and confirm network/API status."
        elif "401" in lower or "403" in lower or "auth" in lower or "key" in lower:
            message = "Provider authentication error. Check API key and project permissions."
        else:
            message = f"Provider error: {exc}"
        return AISmokeTestResponse(provider=provider, success=False, response=message)
