from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.ai import AICompletionRequest, AICompletionResponse, AISettings, AISettingsUpdate, AIStatus
from app.services.ai import AIProviderError, available_providers, complete, configured_provider
from app.services.settings_store import current_ai_settings, update_ai_settings

router = APIRouter()


@router.get("/status", response_model=AIStatus)
def get_ai_status() -> AIStatus:
    return AIStatus(
        mode=settings.ai_mode,
        configured_provider=configured_provider(),
        available_providers=available_providers(),
        models={
            "openai": settings.openai_model,
            "gemini": settings.gemini_model,
            "anthropic": settings.anthropic_model,
            "ollama": settings.ollama_model,
        },
    )


@router.get("/settings", response_model=AISettings)
def get_ai_settings() -> AISettings:
    return current_ai_settings()


@router.put("/settings", response_model=AISettings)
def save_ai_settings(payload: AISettingsUpdate) -> AISettings:
    return update_ai_settings(payload)


@router.post("/complete", response_model=AICompletionResponse)
def create_completion(payload: AICompletionRequest) -> AICompletionResponse:
    try:
        provider, model, content = complete(
            payload.messages,
            provider=payload.provider,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
        )
    except AIProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AICompletionResponse(provider=provider, model=model, content=content)
