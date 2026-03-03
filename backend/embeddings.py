from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from .config import EMBEDDING_MODEL, OPENAI_API_KEY


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_text(text: str) -> list[float]:
    client = _client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding
