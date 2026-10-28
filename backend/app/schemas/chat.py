"""Pydantic schemas for chat and RAG QA operations."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SourceCitation(BaseModel):
    document_id: str
    filename: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    excerpt: str
    score: Optional[float] = None


class ChatAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000, description="Natural language question")
    conversation_id: Optional[str] = Field(None, description="Optional existing conversation ID to continue")
    document_ids: Optional[List[str]] = Field(None, description="Optional filter to specific document IDs")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Custom number of chunks to retrieve")


class ChatAskResponse(BaseModel):
    answer: str
    conversation_id: str
    message_id: str
    sources: List[SourceCitation]
    grounded: bool = True


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: List[SourceCitation] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[ChatMessageResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
