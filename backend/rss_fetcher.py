from __future__ import annotations

from datetime import datetime, timezone

import feedparser
import requests

from .database import insert_article_if_new, update_article_embedding_id
from .embeddings import embed_text
from .faiss_index import FaissStore


def _parse_published(entry: feedparser.FeedParserDict) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime(*parsed[:6], tzinfo=timezone.utc)


def _entry_to_text(entry: feedparser.FeedParserDict) -> tuple[str, str, str]:
    title = (entry.get("title") or "").strip()
    description = (entry.get("summary") or "").strip()
    content_blocks = entry.get("content") or []
    content = "\n".join(block.get("value", "") for block in content_blocks if isinstance(block, dict)).strip()
    if not content:
        content = description
    return title, description, content


def ingest_sources(sources: list[dict[str, str]], faiss_store: FaissStore) -> dict[str, int]:
    inserted = 0
    skipped = 0

    for src in sources:
        try:
            response = requests.get(
                src["url"],
                timeout=20,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/128.0.0.0 Safari/537.36"
                    )
                },
            )
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
        except Exception as exc:  # noqa: BLE001
            print(f"[ingest] source='{src['name']}' url='{src['url']}' fetch_error='{exc}'")
            continue

        if not parsed.entries:
            print(f"[ingest] source='{src['name']}' parsed 0 entries")
            continue

        for entry in parsed.entries:
            link = (entry.get("link") or "").strip()
            if not link:
                skipped += 1
                continue

            title, description, content = _entry_to_text(entry)
            article_id = insert_article_if_new(
                title=title,
                description=description,
                content=content,
                url=link,
                source=src["name"],
                published_at=_parse_published(entry),
            )
            if article_id is None:
                skipped += 1
                continue

            embedding_text = "\n\n".join([title, description, content]).strip()
            embedding = embed_text(embedding_text)
            embedding_id = faiss_store.add_vector(embedding)
            update_article_embedding_id(article_id, embedding_id)
            inserted += 1

    return {"inserted": inserted, "skipped": skipped}
