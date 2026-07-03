from pathlib import Path

from app.core.config import reload_settings, settings
from app.schemas.ai import AISettings, AISettingsUpdate

ENV_PATH = Path(".env")


def current_ai_settings() -> AISettings:
    return AISettings(
        mode=settings.ai_mode,
        provider=settings.ai_provider,
        openai_model=settings.openai_model,
        openai_api_base_url=settings.openai_api_base_url,
        openai_api_key_set=bool(settings.openai_api_key),
        gemini_model=settings.gemini_model,
        gemini_api_base_url=settings.gemini_api_base_url,
        gemini_api_key_set=bool(settings.gemini_api_key),
        anthropic_model=settings.anthropic_model,
        anthropic_api_base_url=settings.anthropic_api_base_url,
        anthropic_api_key_set=bool(settings.anthropic_api_key),
        ollama_model=settings.ollama_model,
        ollama_base_url=settings.ollama_base_url,
    )


def update_ai_settings(payload: AISettingsUpdate) -> AISettings:
    mode = _clean_choice(payload.mode, {"none", "offline", "online"}, "none")
    provider = _clean_choice(payload.provider, {"none", "openai", "gemini", "anthropic"}, "none")
    if mode == "offline":
        provider = "none"
    if mode == "online" and provider == "none":
        provider = "openai"

    values = _read_env()
    values.update(
        {
            "AI_MODE": mode,
            "AI_PROVIDER": provider,
            "OPENAI_MODEL": payload.openai_model.strip() or "gpt-4.1-mini",
            "OPENAI_API_BASE_URL": payload.openai_api_base_url.strip() or "https://api.openai.com/v1",
            "GEMINI_MODEL": payload.gemini_model.strip() or "gemini-2.5-flash",
            "GEMINI_API_BASE_URL": payload.gemini_api_base_url.strip() or "https://generativelanguage.googleapis.com/v1beta",
            "ANTHROPIC_MODEL": payload.anthropic_model.strip() or "claude-3-5-haiku-latest",
            "ANTHROPIC_API_BASE_URL": payload.anthropic_api_base_url.strip() or "https://api.anthropic.com/v1",
            "OLLAMA_MODEL": payload.ollama_model.strip() or "qwen3:14b",
            "OLLAMA_BASE_URL": payload.ollama_base_url.strip() or "http://ollama:11434",
        }
    )
    _set_secret(values, "OPENAI_API_KEY", payload.openai_api_key)
    _set_secret(values, "GEMINI_API_KEY", payload.gemini_api_key)
    _set_secret(values, "ANTHROPIC_API_KEY", payload.anthropic_api_key)
    _write_env(values)
    fresh = reload_settings()
    return AISettings(
        mode=fresh.ai_mode,
        provider=fresh.ai_provider,
        openai_model=fresh.openai_model,
        openai_api_base_url=fresh.openai_api_base_url,
        openai_api_key_set=bool(fresh.openai_api_key),
        gemini_model=fresh.gemini_model,
        gemini_api_base_url=fresh.gemini_api_base_url,
        gemini_api_key_set=bool(fresh.gemini_api_key),
        anthropic_model=fresh.anthropic_model,
        anthropic_api_base_url=fresh.anthropic_api_base_url,
        anthropic_api_key_set=bool(fresh.anthropic_api_key),
        ollama_model=fresh.ollama_model,
        ollama_base_url=fresh.ollama_base_url,
    )


def _read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    values: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _write_env(values: dict[str, str]) -> None:
    preferred_order = [
        "PAPERLESS_API_URL",
        "PAPERLESS_API_TOKEN",
        "PAPERLESS_USERNAME",
        "PAPERLESS_PASSWORD",
        "CORS_ORIGINS",
        "VITE_API_BASE_URL",
        "AI_MODE",
        "AI_PROVIDER",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_API_BASE_URL",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_API_BASE_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
        "ANTHROPIC_API_BASE_URL",
        "OLLAMA_MODEL",
        "OLLAMA_BASE_URL",
    ]
    keys = preferred_order + sorted(key for key in values if key not in preferred_order)
    lines = [f"{key}={values.get(key, '')}" for key in keys if key in values]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _set_secret(values: dict[str, str], key: str, value: str | None) -> None:
    if value is not None and value.strip():
        values[key] = value.strip()


def _clean_choice(value: str, allowed: set[str], default: str) -> str:
    cleaned = value.lower().strip()
    return cleaned if cleaned in allowed else default
