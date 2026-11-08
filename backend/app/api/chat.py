"""Chat and RAG QA API router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.chat import (
    ChatAskRequest,
    ChatAskResponse,
    ConversationResponse,
    ConversationListResponse
)
from backend.app.services.chat_service import chat_service
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])


@router.post("/ask", response_model=ChatAskResponse)
def ask_question(
    req: ChatAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question against indexed documents using Retrieval-Augmented Generation."""
    try:
        response = chat_service.ask(db=db, user_id=current_user.id, req=req)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing QA pipeline: {str(e)}"
        )


@router.get("/history", response_model=ConversationListResponse)
def get_conversations(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Limit for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List paginated chat conversations for the current user."""
    convs, total = chat_service.list_conversations(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    formatted = [
        ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=None
        )
        for c in convs
    ]
    return ConversationListResponse(conversations=formatted, total=total)


@router.get("/history/{conversation_id}", response_model=ConversationResponse)
@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full message history and citations for a specific conversation."""
    conv = chat_service.get_conversation(db=db, conversation_id=conversation_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return chat_service.format_conversation_response(conv)


@router.delete("/history/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages."""
    success = chat_service.delete_conversation(db=db, conversation_id=conversation_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return {"message": "Conversation deleted successfully.", "conversation_id": conversation_id}
