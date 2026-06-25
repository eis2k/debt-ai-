from fastapi import APIRouter, HTTPException

from app.schemas.ai import AICompletionRequest, AICompletionResponse, AIStatus
from app.services.ai import AIProviderError, available_providers, complete, configured_provider

router = APIRouter()


@router.get("/status", response_model=AIStatus)
def get_ai_status() -> AIStatus:
    return AIStatus(configured_provider=configured_provider(), available_providers=available_providers())


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
