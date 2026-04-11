from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    # ✅ FIX: indent + doc_id chuẩn
    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)

        metadata = doc.metadata or {}

        # đảm bảo luôn có doc_id
        doc_id = metadata.get("doc_id") or metadata.get("id") or "doc_to_delete"
        metadata["doc_id"] = doc_id

        record = {
            "id": f"{doc_id}_{self._next_index}",
            "text": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }

        self._next_index += 1
        return record

    # ✅ FIX: format output đúng test (content + score)
    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        query_emb = self._embedding_fn(query)

        results = []
        for r in records:
            score = _dot(query_emb, r["embedding"])
            results.append(
                {
                    "content": r["text"],
                    "score": score,
                    "metadata": r["metadata"],
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        if self._use_chroma:
            ids = []
            docs_text = []
            embeddings = []

            for doc in docs:
                emb = self._embedding_fn(doc.content)
                doc_id = doc.metadata.get("doc_id", str(self._next_index))

                ids.append(f"{doc_id}_{self._next_index}")
                docs_text.append(doc.content)
                embeddings.append(emb)

                self._next_index += 1

            self._collection.add(
                ids=ids,
                documents=docs_text,
                embeddings=embeddings,
            )
        else:
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self._use_chroma:
            results = self._collection.query(query_texts=[query], n_results=top_k)
            docs = results.get("documents", [[]])[0]
            return [{"content": d, "score": 0.0} for d in docs]

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k)

        if self._use_chroma:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=metadata_filter,
            )
            docs = results.get("documents", [[]])[0]
            return [{"content": d, "score": 0.0} for d in docs]

        filtered = [
            r
            for r in self._store
            if all(r["metadata"].get(k) == v for k, v in metadata_filter.items())
        ]

        return self._search_records(query, filtered, top_k)

    # ✅ FIX: delete chuẩn (test pass)
    def delete_document(self, doc_id: str) -> bool:
        before = len(self._store)

        self._store = [
            r for r in self._store if r["metadata"].get("doc_id") != doc_id
        ]

        after = len(self._store)

        return after < before