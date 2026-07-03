from typing import Any

import requests

from app.core.config import settings
from app.schemas.ai import AIMessage


class AIProviderError(RuntimeError):
    pass


def available_providers() -> list[str]:
    providers: list[str] = []
    if settings.ai_mode == "offline":
        providers.append("ollama")
        return providers
    if settings.openai_api_key:
        providers.append("openai")
    if settings.gemini_api_key:
        providers.append("gemini")
    if settings.anthropic_api_key:
        providers.append("anthropic")
    return providers


def configured_provider() -> str:
    mode = settings.ai_mode.lower().strip()
    if mode == "offline":
        return "ollama"
    if mode == "none":
        return "none"
    configured = settings.ai_provider.lower().strip()
    if configured != "none":
        return configured
    providers = available_providers()
    return providers[0] if providers else "none"


def complete(
    messages: list[AIMessage],
    provider: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.2,
) -> tuple[str, str, str]:
    selected = (provider or configured_provider()).lower().strip()
    if selected == "openai":
        return _complete_openai(messages, max_tokens=max_tokens, temperature=temperature)
    if selected == "gemini":
        return _complete_gemini(messages, max_tokens=max_tokens, temperature=temperature)
    if selected in {"anthropic", "claude"}:
        return _complete_anthropic(messages, max_tokens=max_tokens, temperature=temperature)
    if selected == "ollama":
        return _complete_ollama(messages, max_tokens=max_tokens, temperature=temperature)
    raise AIProviderError("No AI provider is configured.")


def _complete_openai(messages: list[AIMessage], max_tokens: int, temperature: float) -> tuple[str, str, str]:
    if not settings.openai_api_key:
        raise AIProviderError("OpenAI API key is missing.")

    payload = {
        "model": settings.openai_model,
        "messages": [message.model_dump() for message in messages],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    data = _post_json(
        f"{settings.openai_api_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json=payload,
    )
    content = data["choices"][0]["message"]["content"]
    return "openai", settings.openai_model, content


def _complete_gemini(messages: list[AIMessage], max_tokens: int, temperature: float) -> tuple[str, str, str]:
    if not settings.gemini_api_key:
        raise AIProviderError("Gemini API key is missing.")

    system_instruction = _system_instruction(messages)
    contents = [
        {
            "role": "model" if message.role == "assistant" else "user",
            "parts": [{"text": message.content}],
        }
        for message in messages
        if message.role != "system"
    ]
    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    data = _post_json(
        f"{settings.gemini_api_base_url.rstrip('/')}/models/{settings.gemini_model}:generateContent",
        params={"key": settings.gemini_api_key},
        json=payload,
    )
    content = data["candidates"][0]["content"]["parts"][0]["text"]
    return "gemini", settings.gemini_model, content


def _complete_anthropic(messages: list[AIMessage], max_tokens: int, temperature: float) -> tuple[str, str, str]:
    if not settings.anthropic_api_key:
        raise AIProviderError("Anthropic API key is missing.")

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role != "system"
        ],
    }
    system_instruction = _system_instruction(messages)
    if system_instruction:
        payload["system"] = system_instruction

    data = _post_json(
        f"{settings.anthropic_api_base_url.rstrip('/')}/messages",
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        },
        json=payload,
    )
    content = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    return "anthropic", settings.anthropic_model, content


def _complete_ollama(messages: list[AIMessage], max_tokens: int, temperature: float) -> tuple[str, str, str]:
    payload = {
        "model": settings.ollama_model,
        "messages": [message.model_dump() for message in messages],
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature},
    }
    data = _post_json(f"{settings.ollama_base_url.rstrip('/')}/api/chat", json=payload)
    content = data.get("message", {}).get("content", "")
    return "ollama", settings.ollama_model, content


def _system_instruction(messages: list[AIMessage]) -> str:
    return "\n\n".join(message.content for message in messages if message.role == "system")


def _post_json(url: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.post(url, timeout=60, **kwargs)
    if response.status_code >= 400:
        raise AIProviderError(f"AI provider request failed with status {response.status_code}: {response.text}")
    return response.json()
