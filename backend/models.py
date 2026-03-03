from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)


class SourceItem(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime | None = None


class SearchResponse(BaseModel):
    report_id: str
    headline: str
    metadata: str
    tldr: list[str]
    sections: dict[str, str]
    implications: str
    sources: list[SourceItem]


class HealthResponse(BaseModel):
    status: str
    article_count: int


class IngestResponse(BaseModel):
    status: str
    trigger: str
    inserted: int = 0
    skipped: int = 0
    duration_seconds: float = 0
    started_at: str
    finished_at: str
    source_count: int
    detail: str | None = None


class ReportPayload(BaseModel):
    headline: str
    metadata: str
    tldr: list[str]
    sections: dict[str, str]
    implications: str
    sources: list[dict[str, Any]]
