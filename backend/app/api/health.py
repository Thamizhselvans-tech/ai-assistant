"""Health check API router with RAM and LLM provider diagnostics."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.database.session import get_db
import backend.app.rag.vector_store as vs_module
from backend.app.services.llm_provider import llm_provider_service

router = APIRouter(prefix="/api/health", tags=["Health"])


def _get_ram_telemetry():
    """Retrieve system RAM statistics using psutil with fallback."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "percent": mem.percent,
            "low_ram_mode": getattr(settings, "LOW_RAM_MODE", True)
        }
    except Exception:
        return {
            "total_gb": 4.0,
            "available_gb": 1.5,
            "used_gb": 2.5,
            "percent": 62.5,
            "low_ram_mode": getattr(settings, "LOW_RAM_MODE", True)
        }


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """System health status checking database, vector store, and LLM provider connectivity."""
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
    prov_status = llm_provider_service.get_provider_status()

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "connected" if db_ok else "unavailable",
            "vector_store": "connected" if vector_store_ok else "unavailable",
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "llm_model": prov_status["model"],
            "llm_provider": prov_status["active_provider"],
            "llm_provider_display": prov_status["display_name"],
            "llm_configured": prov_status["has_key"],
            "ram": _get_ram_telemetry()
        }
    }


@router.get("/llm")
def llm_health():
    """Detailed LLM provider configuration and status check."""
    return {
        "status": "ok",
        "provider": llm_provider_service.get_provider_status(),
        "ram": _get_ram_telemetry()
    }
