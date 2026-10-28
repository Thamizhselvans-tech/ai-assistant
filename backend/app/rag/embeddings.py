"""Sentence Transformers embedding provider with lazy-loading and batching."""

from typing import List, Optional
from backend.app.core.config import settings

_model_instance = None


def get_embedding_model():
    """Lazy singleton loader for the SentenceTransformer model."""
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer
        _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model_instance


class EmbeddingService:
    """Provides vector embeddings for texts and queries."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a list of document chunks."""
        if not texts:
            return []
        model = get_embedding_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Compute embedding for a single user search query."""
        if not query:
            return []
        model = get_embedding_model()
        embedding = model.encode(query, convert_to_numpy=True, show_progress_bar=False)
        return embedding.tolist()


embedding_service = EmbeddingService()
