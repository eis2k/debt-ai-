from pydantic import BaseModel


class ImportRequest(BaseModel):
    limit: int | None = None


class ImportResult(BaseModel):
    imported: int
    created: int
    updated: int
    skipped: int
