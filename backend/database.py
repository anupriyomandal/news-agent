import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from .config import DATABASE_PATH

Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection_ctx():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connection_ctx() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                content TEXT,
                url TEXT UNIQUE,
                source TEXT,
                published_at DATETIME,
                embedding_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_embedding_id ON articles(embedding_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at)")


def insert_article_if_new(
    title: str,
    description: str,
    content: str,
    url: str,
    source: str,
    published_at: datetime | None,
) -> int | None:
    with connection_ctx() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO articles (title, description, content, url, source, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, content, url, source, published_at),
        )
        if cursor.rowcount == 0:
            return None
        return int(cursor.lastrowid)


def update_article_embedding_id(article_id: int, embedding_id: int) -> None:
    with connection_ctx() as conn:
        conn.execute(
            "UPDATE articles SET embedding_id = ? WHERE id = ?",
            (embedding_id, article_id),
        )


def get_articles_by_embedding_ids(embedding_ids: Sequence[int]) -> list[sqlite3.Row]:
    if not embedding_ids:
        return []
    placeholders = ",".join(["?"] * len(embedding_ids))
    with connection_ctx() as conn:
        rows = conn.execute(
            f"SELECT * FROM articles WHERE embedding_id IN ({placeholders})",  # noqa: S608
            tuple(embedding_ids),
        ).fetchall()
    row_map = {int(r["embedding_id"]): r for r in rows if r["embedding_id"] is not None}
    return [row_map[eid] for eid in embedding_ids if eid in row_map]


def count_articles() -> int:
    with connection_ctx() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM articles").fetchone()
        return int(row["c"])


def latest_articles(limit: int = 20) -> Iterable[sqlite3.Row]:
    with connection_ctx() as conn:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY published_at DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows
