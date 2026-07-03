from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, chat, comparisons, creditors, dashboard, documents, exports, extractions, imports
from app.core.config import settings

app = FastAPI(title="DebtAI", version="1.0.0")

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
app.include_router(creditors.router, prefix="/api/creditors", tags=["creditors"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
app.include_router(comparisons.router, prefix="/api/comparisons", tags=["comparisons"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
