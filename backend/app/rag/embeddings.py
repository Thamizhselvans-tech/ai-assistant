"""Sentence Transformers embedding provider optimized for 4GB low-RAM environments."""

import gc
import logging
import threading
from typing import Dict, List, Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_model_instance = None
_model_lock = threading.Lock()
_query_cache: Dict[str, List[float]] = {}
_CACHE_MAX_SIZE = 128


def _apply_low_ram_torch_tuning():
    """Limit PyTorch thread allocations to keep memory working set small on low RAM."""
    try:
        import torch
        num_threads = getattr(settings, "TORCH_NUM_THREADS", 2)
        torch.set_num_threads(num_threads)
        try:
            torch.set_num_interop_threads(1)
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"PyTorch thread tuning skipped: {e}")


def get_embedding_model(model_name: Optional[str] = None):
    """Thread-safe lazy singleton loader for the SentenceTransformer model."""
    global _model_instance
    target_model = model_name or settings.EMBEDDING_MODEL_NAME

    if _model_instance is None:
        with _model_lock:
            if _model_instance is None:
                _apply_low_ram_torch_tuning()
                try:
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"Loading embedding model in low-RAM profile: {target_model}")
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
    """Provides local dense vector embeddings with thread-safe caching and memory throttling."""

    def __init__(self, model_name: Optional[str] = None, normalize: bool = True):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.normalize = normalize

    @property
    def embedding_dimension(self) -> int:
        """Return vector dimensionality (384 for all-MiniLM-L6-v2)."""
        model = get_embedding_model(self.model_name)
        if hasattr(model, "get_embedding_dimension"):
            dim = model.get_embedding_dimension()
        else:
            dim = model.get_sentence_embedding_dimension()
        return int(dim) if dim else 384

    def embed_documents(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Compute normalized dense embeddings for document chunks in throttled batches.
        Uses 16 batch size to minimize memory working set.
        """
        if not texts:
            return []

        bs = batch_size or getattr(settings, "EMBEDDING_BATCH_SIZE", 16)
        model = get_embedding_model(self.model_name)

        try:
            import torch
            with torch.inference_mode():
                embeddings = model.encode(
                    texts,
                    batch_size=bs,
                    convert_to_numpy=True,
                    normalize_embeddings=self.normalize,
                    show_progress_bar=False
                )
            result = embeddings.tolist()
            if getattr(settings, "LOW_RAM_MODE", True):
                gc.collect()
            return result
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            raise RuntimeError(f"Failed to generate document embeddings: {str(e)}")

    def embed_query(self, query: str) -> List[float]:
        """
        Compute normalized dense embedding for a single user query with LRU caching.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        cache_key = f"{self.model_name}:{clean_query}"

        # Check in-memory query cache to avoid duplicate re-encoding
        if cache_key in _query_cache:
            return _query_cache[cache_key]

        model = get_embedding_model(self.model_name)
        try:
            import torch
            with torch.inference_mode():
                embedding = model.encode(
                    clean_query,
                    convert_to_numpy=True,
                    normalize_embeddings=self.normalize,
                    show_progress_bar=False
                )
            result = embedding.tolist()

            # Evict oldest entry if cache is full
            if len(_query_cache) >= _CACHE_MAX_SIZE:
                oldest = next(iter(_query_cache))
                _query_cache.pop(oldest, None)

            _query_cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise RuntimeError(f"Failed to generate query embedding: {str(e)}")


embedding_service = EmbeddingService()

__all__ = ["EmbeddingService", "embedding_service", "get_embedding_model"]
