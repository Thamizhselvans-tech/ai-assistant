"""Admin service handling metrics aggregation, system health monitoring, and administrative listings."""

from typing import Any, Dict, List, Tuple
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.chat import Conversation, ChatMessage
from backend.app.rag.embeddings import embedding_service
import backend.app.rag.vector_store as vs_module
from backend.app.schemas.admin import (
    AdminDashboardResponse,
    AdminUserResponse,
    AdminDocumentResponse,
    AdminRecentConversationResponse,
    AdminSystemHealthResponse,
)


class AdminService:
    """Provides system monitoring and management services for administrators."""

    @staticmethod
    def get_dashboard(db: Session) -> AdminDashboardResponse:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_documents = db.query(func.count(Document.id)).scalar() or 0
        total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
        total_messages = db.query(func.count(ChatMessage.id)).scalar() or 0

        # Status breakdown
        status_rows = db.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
        breakdown = {status: count for status, count in status_rows}
        for s in ["completed", "processing", "failed", "warning", "pending"]:
            breakdown.setdefault(s, 0)

        # ChromaDB chunk count
        try:
            total_chunks = vs_module.vector_store.count()
        except Exception:
            total_chunks = 0

        # Recent documents
        recent_docs_records = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
        recent_documents = [
            AdminDocumentResponse(
                id=d.id,
                user_id=d.user_id,
                username=d.user.username if d.user else None,
                filename=d.filename,
                original_filename=d.original_filename,
                file_type=d.file_type,
                file_size_bytes=d.file_size_bytes,
                status=d.status,
                status_message=d.status_message,
                page_count=d.page_count,
                chunk_count=d.chunk_count,
                created_at=d.created_at
            )
            for d in recent_docs_records
        ]

        # Recent conversations
        recent_convs_records = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(5).all()
        recent_conversations = [
            AdminRecentConversationResponse(
                id=c.id,
                user_id=c.user_id,
                title=c.title,
                updated_at=c.updated_at
            )
            for c in recent_convs_records
        ]

        return AdminDashboardResponse(
            total_users=total_users,
            total_documents=total_documents,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_vector_chunks=total_chunks,
            document_status_breakdown=breakdown,
            recent_documents=recent_documents,
            recent_conversations=recent_conversations,
            system_status="healthy"
        )

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[AdminUserResponse], int]:
        total = db.query(func.count(User.id)).scalar() or 0
        users_records = db.query(User).order_by(User.id.asc()).offset(skip).limit(limit).all()

        results: List[AdminUserResponse] = []
        for u in users_records:
            doc_cnt = db.query(func.count(Document.id)).filter(Document.user_id == u.id).scalar() or 0
            conv_cnt = db.query(func.count(Conversation.id)).filter(Conversation.user_id == u.id).scalar() or 0
            results.append(
                AdminUserResponse(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    is_active=u.is_active,
                    is_admin=bool(getattr(u, "is_admin", False)),
                    role=getattr(u, "role", "user"),
                    created_at=u.created_at,
                    document_count=doc_cnt,
                    conversation_count=conv_cnt
                )
            )
        return results, total

    @staticmethod
    def get_documents(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[AdminDocumentResponse], int]:
        total = db.query(func.count(Document.id)).scalar() or 0
        docs_records = db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

        results = [
            AdminDocumentResponse(
                id=d.id,
                user_id=d.user_id,
                username=d.user.username if d.user else None,
                filename=d.filename,
                original_filename=d.original_filename,
                file_type=d.file_type,
                file_size_bytes=d.file_size_bytes,
                status=d.status,
                status_message=d.status_message,
                page_count=d.page_count,
                chunk_count=d.chunk_count,
                created_at=d.created_at
            )
            for d in docs_records
        ]
        return results, total

    @staticmethod
    def get_system_health(db: Session) -> AdminSystemHealthResponse:
        # SQLite Database Health
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # ChromaDB Vector Store Health
        try:
            chunk_count = vs_module.vector_store.count()
            chroma_status = "healthy"
        except Exception as e:
            chunk_count = 0
            chroma_status = f"unhealthy: {str(e)}"

        # Embedding Service
        emb_dim = embedding_service.embedding_dimension
        emb_status = {
            "status": "ready",
            "model_name": embedding_service.model_name,
            "dimension": emb_dim
        }

        # LLM Service
        raw_key = settings.OPENAI_API_KEY.strip()
        is_configured = bool(raw_key and raw_key != "your-openai-api-key-here")
        llm_status = {
            "status": "configured" if is_configured else "unconfigured",
            "model": settings.OPENAI_MODEL,
            "base_url": settings.OPENAI_BASE_URL,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
            "temperature": settings.OPENAI_TEMPERATURE,
            "api_key_configured": is_configured
        }

        overall = "healthy" if db_status == "connected" and chroma_status == "healthy" else "degraded"

        return AdminSystemHealthResponse(
            overall_status=overall,
            database={
                "status": db_status,
                "engine": "sqlite",
                "database_url": settings.DATABASE_URL
            },
            vector_store={
                "status": chroma_status,
                "engine": "chromadb",
                "collection_name": settings.CHROMA_COLLECTION_NAME,
                "total_chunks": chunk_count,
                "persist_directory": settings.CHROMA_PERSIST_DIRECTORY
            },
            embedding_engine=emb_status,
            llm_service=llm_status
        )


admin_service = AdminService()
