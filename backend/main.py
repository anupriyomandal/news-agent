from __future__ import annotations

import hashlib
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import (
    CORS_ORIGINS,
    ENABLE_INTERNAL_SCHEDULER,
    FRESH_SEARCH_ONLY,
    INGEST_API_TOKEN,
    INGEST_ON_STARTUP,
    PIPELINE_MAX_ARTICLES,
    QUERY_CACHE_TTL_SECONDS,
    RSS_SOURCES,
    SEARCH_TOP_K,
)
from .database import count_articles, get_articles_by_embedding_ids, init_db
from .embeddings import embed_text
from .faiss_index import FaissStore
from .models import HealthResponse, IngestResponse, SearchRequest, SearchResponse
from .pipeline import run_pipeline
from .query_routing import allowed_source_names
from .rss_fetcher import ingest_sources
from .scheduler import build_scheduler


class TTLCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            record = self._data.get(key)
            if not record:
                return None
            expires, value = record
            if now > expires:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._data[key] = (time.time() + self.ttl_seconds, value)


app = FastAPI(title="Anupriyo Mandal's News Intelligence Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

faiss_store = FaissStore()
query_cache = TTLCache(ttl_seconds=QUERY_CACHE_TTL_SECONDS)
report_store: dict[str, dict[str, Any]] = {}
report_lock = threading.Lock()
ingest_lock = threading.Lock()
ingest_status_lock = threading.Lock()
last_ingest_status: dict[str, Any] | None = None
scheduler = None
auth_scheme = HTTPBearer(auto_error=False)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "for",
    "from",
    "in",
    "is",
    "news",
    "of",
    "on",
    "or",
    "the",
    "to",
    "vs",
    "war",
    "with",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_ingest_auth(credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme)) -> None:
    if not INGEST_API_TOKEN:
        raise HTTPException(status_code=503, detail="INGEST_API_TOKEN is not configured")
    if credentials is None or credentials.credentials != INGEST_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid ingestion token")


def _run_ingestion(trigger: str) -> dict[str, Any]:
    global last_ingest_status
    started_at = _utc_now_iso()
    start_ts = time.time()

    if not ingest_lock.acquire(blocking=False):
        return {
            "status": "running",
            "trigger": trigger,
            "inserted": 0,
            "skipped": 0,
            "duration_seconds": 0.0,
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "source_count": len(RSS_SOURCES),
            "detail": "Ingestion already in progress",
        }

    try:
        stats = ingest_sources(RSS_SOURCES, faiss_store)
        result = {
            "status": "ok",
            "trigger": trigger,
            "inserted": int(stats.get("inserted", 0)),
            "skipped": int(stats.get("skipped", 0)),
            "duration_seconds": round(time.time() - start_ts, 3),
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "source_count": len(RSS_SOURCES),
            "detail": None,
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "error",
            "trigger": trigger,
            "inserted": 0,
            "skipped": 0,
            "duration_seconds": round(time.time() - start_ts, 3),
            "started_at": started_at,
            "finished_at": _utc_now_iso(),
            "source_count": len(RSS_SOURCES),
            "detail": str(exc),
        }
    finally:
        ingest_lock.release()

    with ingest_status_lock:
        last_ingest_status = result
    return result


def _report_id(query: str, sources: list[dict[str, Any]]) -> str:
    seed = query + "|" + "|".join(sorted(s.get("url", "") for s in sources))
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1]


def _rank_relevant_articles(query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terms = [t for t in _tokenize(query) if t not in STOPWORDS]
    if not terms:
        return rows

    scored: list[tuple[float, dict[str, Any], int, float]] = []
    total = max(len(rows), 1)
    for rank, row in enumerate(rows):
        title = str(row.get("title") or "").lower()
        description = str(row.get("description") or "").lower()
        title_hits = sum(1 for term in terms if term in title)
        desc_hits = sum(1 for term in terms if term in description)
        hit_count = len({term for term in terms if term in (title + " " + description)})
        coverage = hit_count / len(terms)
        lexical = (title_hits * 1.5 + desc_hits) / len(terms)
        semantic_rank_bonus = (total - rank) / total
        score = lexical + (coverage * 1.8) + (semantic_rank_bonus * 0.35)
        scored.append((score, row, hit_count, coverage))

    min_hits = 1 if len(terms) <= 2 else 2
    filtered = [item for item in scored if item[2] >= min_hits or item[3] >= 0.5]
    if not filtered:
        filtered = sorted(scored, key=lambda item: item[0], reverse=True)[: max(4, min(len(scored), 8))]
    else:
        filtered = sorted(filtered, key=lambda item: item[0], reverse=True)
    return [row for _, row, _, _ in filtered]


@app.on_event("startup")
def on_startup() -> None:
    global scheduler
    init_db()
    if ENABLE_INTERNAL_SCHEDULER:
        scheduler = build_scheduler(lambda: _run_ingestion("scheduled"))
        if not scheduler.running:
            scheduler.start()
    if INGEST_ON_STARTUP:
        # Do not block app startup on slow/unreachable RSS feeds.
        threading.Thread(target=lambda: _run_ingestion("startup"), daemon=True).start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", article_count=count_articles())


@app.get("/ingest/status", response_model=IngestResponse)
def ingest_status(_: None = Depends(_require_ingest_auth)) -> IngestResponse:
    with ingest_status_lock:
        status = last_ingest_status
    if status is None:
        now = _utc_now_iso()
        status = {
            "status": "idle",
            "trigger": "none",
            "inserted": 0,
            "skipped": 0,
            "duration_seconds": 0.0,
            "started_at": now,
            "finished_at": now,
            "source_count": len(RSS_SOURCES),
            "detail": "No ingestion has run yet",
        }
    return IngestResponse(**status)


@app.post("/ingest/now", response_model=IngestResponse)
def ingest_now(_: None = Depends(_require_ingest_auth)) -> IngestResponse:
    result = _run_ingestion("manual")
    if result["status"] == "error":
        raise HTTPException(status_code=502, detail=f"Ingestion failed: {result['detail']}")
    return IngestResponse(**result)


@app.get("/report/{report_id}", response_model=SearchResponse)
def get_report(report_id: str) -> SearchResponse:
    with report_lock:
        report = report_store.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return SearchResponse(**report)


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        if not FRESH_SEARCH_ONLY:
            cached = query_cache.get(query.lower())
            if cached:
                return SearchResponse(**cached)

        query_vector = embed_text(query)
        embedding_ids = faiss_store.search(query_vector, top_k=SEARCH_TOP_K)
        rows = [dict(row) for row in get_articles_by_embedding_ids(embedding_ids)]
        selected_sources = allowed_source_names(query)
        routed_rows = [row for row in rows if str(row.get("source") or "") in selected_sources]
        if routed_rows:
            rows = routed_rows

        if not rows:
            raise HTTPException(status_code=404, detail="No relevant articles found. Wait for ingestion to populate data.")

        ranked = _rank_relevant_articles(query, rows)
        articles = ranked[:PIPELINE_MAX_ARTICLES]
        if not articles:
            raise HTTPException(status_code=404, detail="No relevant articles found for this specific query.")
        result = run_pipeline(query, articles)

        sources = []
        seen = set()
        for article in articles:
            url = article.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            sources.append(
                {
                    "title": article.get("title") or "Untitled",
                    "url": url,
                    "source": article.get("source") or "Unknown",
                    "published_at": article.get("published_at"),
                }
            )

        report_id = _report_id(query, sources)
        payload = {
            "report_id": report_id,
            "headline": result["headline"],
            "metadata": result["metadata"],
            "tldr": result["tldr"],
            "sections": result["sections"],
            "implications": result["implications"],
            "sources": sources,
        }

        with report_lock:
            report_store[report_id] = payload

        if not FRESH_SEARCH_ONLY:
            query_cache.set(query.lower(), payload)
        return SearchResponse(**payload)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Search pipeline failed: {exc}") from exc
