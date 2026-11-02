"""Semantic retrieval module converting questions into vector embeddings and searching ChromaDB."""

import logging
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.rag.embeddings import embedding_service, EmbeddingService
import backend.app.rag.vector_store as vs_module
from backend.app.rag.vector_store import SearchResult, VectorStore

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Retrieves relevant document chunks using dense semantic vector search."""

    def __init__(
        self,
        default_top_k: int = 5,
        default_threshold: Optional[float] = None,
        vector_store_instance: Optional[VectorStore] = None,
        embedding_service_instance: Optional[EmbeddingService] = None
    ):
        self.default_top_k = default_top_k
        self.default_threshold = default_threshold if default_threshold is not None else settings.SIMILARITY_THRESHOLD
        self._custom_vector_store = vector_store_instance
        self._custom_embedding_service = embedding_service_instance

    @property
    def vector_store(self) -> VectorStore:
        return self._custom_vector_store or vs_module.vector_store

    @property
    def embedding_service(self) -> EmbeddingService:
        return self._custom_embedding_service or embedding_service

    def retrieve(
        self,
        question: str,
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Embed the user's question, search ChromaDB with user isolation,
        and return the top matching chunks that exceed the similarity threshold.
        """
        q = (question or "").strip()
        if not q:
            logger.debug("Empty query passed to retriever.")
            return []

        k = top_k or self.default_top_k
        threshold = similarity_threshold if similarity_threshold is not None else self.default_threshold

        try:
            query_vector = self.embedding_service.embed_query(q)
            if not query_vector:
                return []

            results = self.vector_store.search(
                query_embedding=query_vector,
                user_id=user_id,
                document_ids=document_ids,
                top_k=k,
                similarity_threshold=threshold
            )
            return results
        except Exception as e:
            logger.error(f"Error during semantic retrieval: {e}")
            return []


semantic_retriever = SemanticRetriever(
    default_top_k=settings.TOP_K_RETRIEVAL,
    default_threshold=settings.SIMILARITY_THRESHOLD
)
