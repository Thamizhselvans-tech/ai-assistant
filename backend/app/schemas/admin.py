"""Pydantic schemas for administrator dashboards, monitoring, and audit views."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class AdminRecentConversationResponse(BaseModel):
    id: str
    user_id: int
    title: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    role: str
    created_at: datetime
    document_count: int = 0
    conversation_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]
    total: int


class AdminDocumentResponse(BaseModel):
    id: str
    user_id: int
    username: Optional[str] = None
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    status: str
    status_message: Optional[str] = None
    page_count: int
    chunk_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminDocumentListResponse(BaseModel):
    documents: List[AdminDocumentResponse]
    total: int


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_documents: int
    total_conversations: int
    total_messages: int
    total_vector_chunks: int
    document_status_breakdown: Dict[str, int]
    recent_documents: List[AdminDocumentResponse]
    recent_conversations: List[AdminRecentConversationResponse]
    system_status: str


class AdminSystemHealthResponse(BaseModel):
    overall_status: str
    database: Dict[str, Any]
    vector_store: Dict[str, Any]
    embedding_engine: Dict[str, Any]
    llm_service: Dict[str, Any]
