"""Sentence Transformers embedding provider with lazy-loading, batching, and vector normalization."""

import logging
from typing import List, Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_model_instance = None


def get_embedding_model(model_name: Optional[str] = None):
    """Lazy singleton loader for the SentenceTransformer model."""
    global _model_instance
    target_model = model_name or settings.EMBEDDING_MODEL_NAME
    if _model_instance is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {target_model}")
            try:
                _model_instance = SentenceTransformer(target_model, local_files_only=True)
            except Exception:
                _model_instance = SentenceTransformer(target_model)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model '{target_model}': {e}")
            raise RuntimeError(f"Could not initialize embedding model '{target_model}': {str(e)}")
    return _model_instance


class EmbeddingService:
    """Provides local dense vector embeddings for texts and queries."""

    def __init__(self, model_name: Optional[str] = None, normalize: bool = True):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.normalize = normalize

    @property
    def embedding_dimension(self) -> int:
        """Return the vector dimensionality (384 for all-MiniLM-L6-v2)."""
        model = get_embedding_model(self.model_name)
        if hasattr(model, "get_embedding_dimension"):
            dim = model.get_embedding_dimension()
        else:
            dim = model.get_sentence_embedding_dimension()
        return int(dim) if dim else 384

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Compute normalized dense embeddings for document chunks in batches.
        """
        if not texts:
            return []
        model = get_embedding_model(self.model_name)
        try:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=self.normalize,
                show_progress_bar=False
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            raise RuntimeError(f"Failed to generate document embeddings: {str(e)}")

    def embed_query(self, query: str) -> List[float]:
        """
        Compute normalized dense embedding for a single user query.
        """
        if not query or not query.strip():
            return []
        model = get_embedding_model(self.model_name)
        try:
            embedding = model.encode(
                query.strip(),
                convert_to_numpy=True,
                normalize_embeddings=self.normalize,
                show_progress_bar=False
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise RuntimeError(f"Failed to generate query embedding: {str(e)}")


embedding_service = EmbeddingService()
