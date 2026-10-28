"""Pydantic schemas for document operations."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: str
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


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class DocumentDeleteResponse(BaseModel):
    id: str
    message: str
