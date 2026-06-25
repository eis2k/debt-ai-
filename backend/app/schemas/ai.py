from pydantic import BaseModel, Field


class AIStatus(BaseModel):
    configured_provider: str
    available_providers: list[str]


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
