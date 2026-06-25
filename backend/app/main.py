from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, documents, extractions, imports
from app.core.config import settings

app = FastAPI(title="DebtAI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(imports.router, prefix="/api/import", tags=["import"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(extractions.router, prefix="/api/extractions", tags=["extractions"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
