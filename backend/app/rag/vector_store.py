"""Persistent ChromaDB vector store manager with user isolation and filtered search."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import chromadb
from backend.app.core.config import settings
from backend.app.rag.chunker import DocumentChunk


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    user_id: int
    filename: str
    page_number: Optional[int]
    chunk_index: int
    text: str
    score: float  # similarity score (higher is more similar)


class VectorStore:
    """Encapsulates ChromaDB operations with persistence and user filtering."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self._client = None
        self._collection = None

    @property
    def client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """Index chunks with embeddings and metadata into ChromaDB."""
        if not chunks:
            return

        ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # ChromaDB allows adding in batches
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def delete_document_chunks(self, document_id: str, user_id: int) -> int:
        """Remove all chunks belonging to a specific document and user."""
        try:
            # First find existing chunk count
            res = self.collection.get(
                where={
                    "$and": [
                        {"document_id": {"$eq": str(document_id)}},
                        {"user_id": {"$eq": int(user_id)}}
                    ]
                }
            )
            count = len(res.get("ids", []))
            if count > 0:
                self.collection.delete(
                    ids=res["ids"]
                )
            return count
        except Exception:
            # Fallback if $and is not supported in simple where
            try:
                res = self.collection.get(where={"document_id": str(document_id)})
                valid_ids = [
                    cid for cid, meta in zip(res.get("ids", []), res.get("metadatas", []))
                    if meta.get("user_id") == user_id
                ]
                if valid_ids:
                    self.collection.delete(ids=valid_ids)
                return len(valid_ids)
            except Exception:
                return 0

    def search(
        self,
        query_embedding: List[float],
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: int = 4,
        similarity_threshold: float = 0.35
    ) -> List[SearchResult]:
        """Query ChromaDB with semantic vector, filtering by user and documents."""
        # Ensure collection has items
        if self.collection.count() == 0:
            return []

        # Construct where filter enforcing user isolation
        where_filter: Dict[str, Any]
        if document_ids and len(document_ids) == 1:
            where_filter = {
                "$and": [
                    {"user_id": {"$eq": int(user_id)}},
                    {"document_id": {"$eq": str(document_ids[0])}}
                ]
            }
        elif document_ids and len(document_ids) > 1:
            where_filter = {
                "$and": [
                    {"user_id": {"$eq": int(user_id)}},
                    {"document_id": {"$in": [str(d) for d in document_ids]}}
                ]
            }
        else:
            where_filter = {"user_id": {"$eq": int(user_id)}}

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k * 2, 20),  # Fetch extra to filter by similarity score
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            # If where query with $eq / $in fails on certain Chroma versions, try simple where
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k * 2, 20),
                    where={"user_id": int(user_id)},
                    include=["documents", "metadatas", "distances"]
                )
            except Exception:
                return []

        search_results: List[SearchResult] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)

        for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
            # In ChromaDB cosine distance: distance = 1 - cosine_similarity
            # cosine_similarity = 1.0 - distance
            similarity = max(0.0, 1.0 - float(dist))

            if similarity < similarity_threshold:
                continue

            # Additional client-side check for document filter if needed
            doc_id = str(meta.get("document_id", ""))
            if document_ids and doc_id not in document_ids:
                continue

            search_results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    user_id=int(meta.get("user_id", user_id)),
                    filename=str(meta.get("filename", "Unknown")),
                    page_number=meta.get("page_number"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    text=text,
                    score=round(similarity, 4)
                )
            )

        # Sort descending by similarity score and truncate to top_k
        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results[:top_k]


vector_store = VectorStore()
