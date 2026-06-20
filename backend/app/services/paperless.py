from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import urljoin

import requests
from dateutil.parser import isoparse
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.schemas.imports import ImportResult


@dataclass
class PaperlessDocument:
    paperless_id: int
    filename: str
    created_at: datetime | None
    document_date: date | None
    document_type: str | None
    ocr_text: str | None
    checksum: str | None
    confidence_score: float | None
    paperless_url: str | None


class PaperlessImporter:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.base_url = (settings.paperless_api_url or "").rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

        if settings.paperless_api_token:
            self.session.headers.update({"Authorization": f"Token {settings.paperless_api_token}"})
        elif settings.paperless_username and settings.paperless_password:
            self.session.auth = (settings.paperless_username, settings.paperless_password)

    def import_documents(self, limit: int | None = None) -> ImportResult:
        if not self.base_url:
            raise HTTPException(status_code=400, detail="PAPERLESS_API_URL is not configured")
        if not (settings.paperless_api_token or (settings.paperless_username and settings.paperless_password)):
            raise HTTPException(status_code=400, detail="Paperless credentials are not configured")

        created = 0
        updated = 0
        skipped = 0
        imported = 0

        for payload in self._iter_document_payloads(limit=limit):
            try:
                parsed = self._parse_document(payload)
            except (KeyError, TypeError, ValueError):
                skipped += 1
                continue

            existing = self.db.scalar(select(Document).where(Document.paperless_id == parsed.paperless_id))
            if existing is None:
                existing = Document(paperless_id=parsed.paperless_id, filename=parsed.filename)
                self.db.add(existing)
                created += 1
            else:
                updated += 1

            existing.filename = parsed.filename
            existing.created_at = parsed.created_at
            existing.document_date = parsed.document_date
            existing.document_type = parsed.document_type
            existing.ocr_text = parsed.ocr_text
            existing.checksum = parsed.checksum
            existing.confidence_score = parsed.confidence_score
            existing.paperless_url = parsed.paperless_url
            imported += 1

        self.db.commit()
        return ImportResult(imported=imported, created=created, updated=updated, skipped=skipped)

    def _iter_document_payloads(self, limit: int | None) -> list[dict[str, Any]]:
        url = self._api_url("/api/documents/")
        params: dict[str, Any] = {"page_size": 100, "ordering": "-created"}
        collected: list[dict[str, Any]] = []

        while url:
            response = self.session.get(url, params=params, timeout=60)
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Paperless authentication failed")
            response.raise_for_status()
            data = response.json()

            results = data.get("results", data if isinstance(data, list) else [])
            for item in results:
                detail = self._load_detail(item)
                collected.append(detail)
                if limit and len(collected) >= limit:
                    return collected

            next_url = data.get("next") if isinstance(data, dict) else None
            url = next_url
            params = {}

        return collected

    def _load_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        document_id = item.get("id")
        if not document_id:
            return item
        response = self.session.get(self._api_url(f"/api/documents/{document_id}/"), timeout=60)
        response.raise_for_status()
        detail = response.json()
        return {**item, **detail}

    def _parse_document(self, payload: dict[str, Any]) -> PaperlessDocument:
        paperless_id = int(payload["id"])
        content = payload.get("content") or payload.get("ocr_text") or ""
        filename = (
            payload.get("original_file_name")
            or payload.get("archived_file_name")
            or payload.get("title")
            or f"paperless-{paperless_id}"
        )

        checksum = payload.get("checksum") or payload.get("archive_checksum")
        if not checksum and content:
            checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

        return PaperlessDocument(
            paperless_id=paperless_id,
            filename=str(filename),
            created_at=self._parse_datetime(payload.get("created")),
            document_date=self._parse_date(payload.get("created_date") or payload.get("document_date")),
            document_type=self._name_from_nested(payload.get("document_type")),
            ocr_text=content,
            checksum=checksum,
            confidence_score=self._parse_confidence(payload),
            paperless_url=f"{self.base_url}/documents/{paperless_id}/details",
        )

    def _api_url(self, path: str) -> str:
        return urljoin(f"{self.base_url}/", path.lstrip("/"))

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        return isoparse(str(value))

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if not value:
            return None
        return isoparse(str(value)).date()

    @staticmethod
    def _name_from_nested(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get("name") or value.get("slug") or str(value.get("id"))
        return str(value)

    @staticmethod
    def _parse_confidence(payload: dict[str, Any]) -> float | None:
        value = payload.get("confidence") or payload.get("confidence_score")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
