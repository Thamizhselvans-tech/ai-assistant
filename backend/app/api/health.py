"""Health check API router."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.database.session import get_db
import backend.app.rag.vector_store as vs_module

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """System health status checking database and vector store connectivity."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    vector_store_ok = False
    try:
        _ = vs_module.vector_store.collection.count()
        vector_store_ok = True
    except Exception:
        vector_store_ok = False

    overall_status = "healthy" if (db_ok and vector_store_ok) else "degraded"

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "connected" if db_ok else "unavailable",
            "vector_store": "connected" if vector_store_ok else "unavailable",
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "llm_model": settings.OPENAI_MODEL
        }
    }
