from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from .config import FAISS_INDEX_PATH, FAISS_META_PATH


class FaissStore:
    def __init__(self) -> None:
        self.index_path = Path(FAISS_INDEX_PATH)
        self.meta_path = Path(FAISS_META_PATH)
        self.dimension: int | None = None
        self.index: faiss.IndexFlatIP | None = None
        self._load_or_init()

    def _load_or_init(self) -> None:
        if self.index_path.exists() and self.meta_path.exists():
            meta = json.loads(self.meta_path.read_text())
            self.dimension = int(meta["dimension"])
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = None
            self.dimension = None

    def _persist(self) -> None:
        if self.index is None or self.dimension is None:
            return
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps({"dimension": self.dimension}))

    @staticmethod
    def _normalize(vector: list[float]) -> np.ndarray:
        arr = np.array([vector], dtype="float32")
        faiss.normalize_L2(arr)
        return arr

    def add_vector(self, vector: list[float]) -> int:
        if self.index is None:
            self.dimension = len(vector)
            self.index = faiss.IndexFlatIP(self.dimension)
        if len(vector) != self.dimension:
            raise ValueError("Embedding dimension mismatch")

        arr = self._normalize(vector)
        self.index.add(arr)
        embedding_id = self.index.ntotal - 1
        self._persist()
        return int(embedding_id)

    def search(self, vector: list[float], top_k: int = 40) -> list[int]:
        if self.index is None or self.index.ntotal == 0:
            return []
        arr = self._normalize(vector)
        k = min(top_k, self.index.ntotal)
        _, indices = self.index.search(arr, k)
        return [int(i) for i in indices[0] if i != -1]
