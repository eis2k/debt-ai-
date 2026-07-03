from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="postgresql+psycopg://debtai:debtai@localhost:5432/debtai")
    paperless_api_url: str | None = None
    paperless_api_token: str | None = None
    paperless_username: str | None = None
    paperless_password: str | None = None
    cors_origins: str = "http://localhost:3000"
    ai_mode: str = "none"
    ai_provider: str = "none"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_api_base_url: str = "https://api.openai.com/v1"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-haiku-latest"
    anthropic_api_base_url: str = "https://api.anthropic.com/v1"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:14b"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()


def reload_settings() -> Settings:
    fresh = Settings()
    for key, value in fresh.model_dump().items():
        setattr(settings, key, value)
    return settings
