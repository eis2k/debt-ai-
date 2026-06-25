from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.ai import AIMessage
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.ai import AIProviderError, complete

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat_with_sources(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    documents = _find_documents(db, payload.question)
    sources = [
        ChatSource(document_id=document.id, filename=document.filename, snippet=_snippet(document.ocr_text or ""))
        for document in documents
    ]
    context = "\n\n".join(
        f"Quelle {index + 1}: {source.filename}\n{source.snippet}" for index, source in enumerate(sources)
    )
    try:
        provider, model, answer = complete(
            [
                AIMessage(
                    role="system",
                    content=(
                        "Du beantwortest Fragen zu Schuldendokumenten. Nutze nur die angegebenen Quellen. "
                        "Wenn die Quellen nicht reichen, sage das klar."
                    ),
                ),
                AIMessage(role="user", content=f"Frage: {payload.question}\n\nQuellen:\n{context}"),
            ],
            provider=payload.provider,
            max_tokens=1200,
            temperature=0.1,
        )
    except AIProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatResponse(answer=answer, provider=provider, model=model, sources=sources)


def _find_documents(db: Session, question: str) -> list[Document]:
    words = [word for word in question.split() if len(word) >= 4][:6]
    query = select(Document).where(Document.ocr_text.is_not(None)).order_by(Document.document_date.desc().nullslast())
    if words:
        query = query.where(or_(*[Document.ocr_text.ilike(f"%{word}%") for word in words]))
    return list(db.scalars(query.limit(5)).all())


def _snippet(text: str) -> str:
    compact = " ".join(text.split())
    return compact[:1200]
