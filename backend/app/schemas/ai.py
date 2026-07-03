from pydantic import BaseModel, Field


class AIStatus(BaseModel):
    mode: str
    configured_provider: str
    available_providers: list[str]
    models: dict[str, str]


class AISettings(BaseModel):
    mode: str
    provider: str
    openai_model: str
    openai_api_base_url: str
    openai_api_key_set: bool
    gemini_model: str
    gemini_api_base_url: str
    gemini_api_key_set: bool
    anthropic_model: str
    anthropic_api_base_url: str
    anthropic_api_key_set: bool
    ollama_model: str
    ollama_base_url: str


class AISettingsUpdate(BaseModel):
    mode: str
    provider: str
    openai_model: str
    openai_api_base_url: str
    openai_api_key: str | None = None
    gemini_model: str
    gemini_api_base_url: str
    gemini_api_key: str | None = None
    anthropic_model: str
    anthropic_api_base_url: str
    anthropic_api_key: str | None = None
    ollama_model: str
    ollama_base_url: str


class AIMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str


class AICompletionRequest(BaseModel):
    messages: list[AIMessage]
    provider: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float = Field(default=0.2, ge=0, le=2)


class AICompletionResponse(BaseModel):
    provider: str
    model: str
    content: str
