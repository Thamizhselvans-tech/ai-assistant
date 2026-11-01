"""Persistent ChromaDB vector store manager with user isolation, cosine metric, and document lifecycle operations."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.app.core.config import settings
from backend.app.rag.text_splitter import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a retrieved document chunk with relevance score."""
    chunk_id: str = ""
    document_id: str = ""
    user_id: int = 0
    filename: str = ""
    file_type: str = "txt"
    page_number: Optional[int] = None
    chunk_index: int = 0
    text: str = ""
    score: float = 0.0  # Cosine similarity score [0.0, 1.0], higher = more similar
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """Encapsulates ChromaDB operations with persistence, user isolation, and lifecycle management."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    @property
    def client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def count(self) -> int:
        """Return the total number of records currently stored in the collection."""
        return self.collection.count()

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> None:
        """
        Insert chunks with dense embeddings and metadata into ChromaDB using batches.
        Handles duplicates via upsert to prevent unique constraint crashes.
        """
        if not chunks:
            return

        total = len(chunks)
        for i in range(0, total, batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]

            ids = [c.id for c in batch_chunks]
            documents = [c.text for c in batch_chunks]
            
            # Format metadata ensuring primitive types supported by ChromaDB
            metadatas = []
            for c in batch_chunks:
                clean_meta: Dict[str, Any] = {
                    "document_id": str(c.document_id),
                    "user_id": int(c.user_id),
                    "filename": str(c.filename),
                    "file_type": str(getattr(c, "file_type", "txt")),
                    "chunk_index": int(c.chunk_index),
                }
                if c.page_number is not None:
                    clean_meta["page_number"] = int(c.page_number)
                if hasattr(c, "upload_timestamp") and c.upload_timestamp:
                    clean_meta["upload_timestamp"] = str(c.upload_timestamp)
                metadatas.append(clean_meta)

            self.collection.upsert(
                ids=ids,
                embeddings=batch_embeddings,
                documents=documents,
                metadatas=metadatas
            )

    def delete_document_chunks(self, document_id: str, user_id: int) -> int:
        """
        Purge all vector chunks belonging to a specific document and user.
        Guarantees no orphaned vectors remain.
        """
        try:
            # Query for IDs owned by user
            res = self.collection.get(
                where={
                    "$and": [
                        {"document_id": {"$eq": str(document_id)}},
                        {"user_id": {"$eq": int(user_id)}}
                    ]
                }
            )
            ids_to_delete = res.get("ids", [])
            count = len(ids_to_delete)
            if count > 0:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {count} vector chunks for document {document_id}")
            return count
        except Exception:
            # Fallback for simpler where filtering
            try:
                res = self.collection.get(where={"document_id": str(document_id)})
                matching_ids = []
                for cid, meta in zip(res.get("ids", []), res.get("metadatas", [])):
                    if meta.get("user_id") == user_id:
                        matching_ids.append(cid)
                if matching_ids:
                    self.collection.delete(ids=matching_ids)
                return len(matching_ids)
            except Exception as e:
                logger.warning(f"Error purging vectors for document {document_id}: {e}")
                return 0

    def reindex_document(
        self,
        document_id: str,
        user_id: int,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> None:
        """Delete old chunks and re-insert new ones for a document."""
        self.delete_document_chunks(document_id=document_id, user_id=user_id)
        self.add_chunks(chunks=chunks, embeddings=embeddings)

    def document_exists(self, document_id: str, user_id: int) -> bool:
        """Check if chunks for this document and user exist in the vector store."""
        try:
            res = self.collection.get(
                where={
                    "$and": [
                        {"document_id": {"$eq": str(document_id)}},
                        {"user_id": {"$eq": int(user_id)}}
                    ]
                },
                limit=1
            )
            return len(res.get("ids", [])) > 0
        except Exception:
            return False

    def search(
        self,
        query_embedding: List[float],
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.35
    ) -> List[SearchResult]:
        """
        Query ChromaDB using dense embedding, strictly isolated by user_id.
        Cosine distance is converted to similarity score: similarity = 1 - distance.
        """
        if self.collection.count() == 0:
            return []

        # Construct isolation filter
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
                n_results=min(top_k * 2, 25),
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.warning(f"Complex where filter failed, falling back to simple user_id filter: {e}")
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k * 2, 25),
                    where={"user_id": int(user_id)},
                    include=["documents", "metadatas", "distances"]
                )
            except Exception as ex:
                logger.error(f"Vector search failed: {ex}")
                return []

        search_results: List[SearchResult] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)

        for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
            # Cosine distance in Chroma: distance = 1 - cosine_similarity
            similarity = max(0.0, 1.0 - float(dist))

            if similarity < similarity_threshold:
                continue

            doc_id = str(meta.get("document_id", ""))
            if document_ids and doc_id not in document_ids:
                continue

            search_results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    user_id=int(meta.get("user_id", user_id)),
                    filename=str(meta.get("filename", "Unknown")),
                    file_type=str(meta.get("file_type", "txt")),
                    page_number=meta.get("page_number"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    text=text,
                    score=round(similarity, 4),
                    metadata=meta
                )
            )

        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results[:top_k]


vector_store = VectorStore()
