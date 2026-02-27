"""
LoreRetriever: in-memory semantic search using sentence-transformers + numpy cosine similarity.

This implementation provides the same public API as a chromadb-backed retriever but avoids
the chromadb/pydantic v1 compatibility issue on Python 3.14+.
"""
from __future__ import annotations

import uuid
import numpy as np
from pathlib import Path


class LoreRetriever:
    def __init__(self, persist_dir: str = "./data/chroma"):
        # persist_dir is accepted for API compatibility; in-memory mode is always used
        self.persist_dir = persist_dir
        self._documents: list[str] = []
        self._metadatas: list[dict] = []
        self._ids: list[str] = []
        self._embeddings: list[np.ndarray] = []
        self._model = None  # lazy-loaded

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def _embed(self, text: str) -> np.ndarray:
        model = self._get_model()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vec = model.encode([text], show_progress_bar=False)[0]
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def add_document(self, text: str, metadata: dict | None = None) -> None:
        doc_id = str(uuid.uuid4())
        embedding = self._embed(text)
        self._documents.append(text)
        self._metadatas.append(metadata or {})
        self._ids.append(doc_id)
        self._embeddings.append(embedding)

    def add_documents_from_file(self, filepath: str, source: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = [p.strip() for p in content.split("\n\n") if p.strip()]
        for chunk in chunks:
            self.add_document(chunk, metadata={"source": source})

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        if not self._documents:
            return []

        query_vec = self._embed(query)
        # Compute cosine distances (1 - cosine similarity) for each stored doc
        scores = []
        for emb in self._embeddings:
            similarity = float(np.dot(query_vec, emb))
            distance = 1.0 - similarity
            scores.append(distance)

        n = min(top_k, len(self._documents))
        indices = np.argsort(scores)[:n]

        return [
            {
                "text": self._documents[i],
                "source": self._metadatas[i].get("source", ""),
                "distance": scores[i],
            }
            for i in indices
        ]
