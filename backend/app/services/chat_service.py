"""Chat service handling conversation persistence, message history, and RAG execution."""

import json
import uuid
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.chat import Conversation, ChatMessage
from backend.app.rag.pipeline import rag_pipeline
from backend.app.schemas.chat import (
    ChatAskRequest,
    ChatAskResponse,
    SourceCitation,
    ChatMessageResponse,
    ConversationResponse
)

logger = logging.getLogger(__name__)


class ChatService:
    """Manages conversations, message logging, and RAG question answering."""

    def list_conversations(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Conversation], int]:
        """Retrieve paginated conversations for the user, ordered by most recently updated."""
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        total = query.count()
        convs = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
        return convs, total

    def get_conversation(self, db: Session, conversation_id: str, user_id: int) -> Optional[Conversation]:
        """Retrieve a specific conversation ensuring ownership."""
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

    def delete_conversation(self, db: Session, conversation_id: str, user_id: int) -> bool:
        """Delete conversation and all its messages."""
        conv = self.get_conversation(db, conversation_id, user_id)
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True

    def ask(self, db: Session, user_id: int, req: ChatAskRequest) -> ChatAskResponse:
        """Execute RAG QA pipeline and persist the interaction."""
        # 1. Resolve or create conversation with ownership enforcement
        conversation: Optional[Conversation] = None
        if req.conversation_id:
            conversation = self.get_conversation(db, req.conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found or access denied.")

        if not conversation:
            clean_title = (req.question[:40] + "...") if len(req.question) > 40 else req.question
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=clean_title
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 2. Persist user question
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=req.question,
            sources_json=None
        )
        db.add(user_msg)
        db.commit()

        # 3. Call RAG Pipeline
        answer, citations, is_grounded = rag_pipeline.answer_question(
            question=req.question,
            user_id=user_id,
            document_ids=req.document_ids,
            top_k=req.top_k
        )

        # 4. Persist assistant response and citations
        sources_dict_list = [c.model_dump() for c in citations]
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            sources_json=json.dumps(sources_dict_list)
        )
        db.add(assistant_msg)

        # Update conversation timestamp
        conversation.title = conversation.title
        db.commit()
        db.refresh(assistant_msg)

        return ChatAskResponse(
            answer=answer,
            conversation_id=conversation.id,
            message_id=assistant_msg.id,
            sources=citations,
            citations=citations,
            grounded=is_grounded
        )

    @staticmethod
    def format_message_response(msg: ChatMessage) -> ChatMessageResponse:
        sources: List[SourceCitation] = []
        if msg.sources_json:
            try:
                raw_sources = json.loads(msg.sources_json)
                sources = [SourceCitation(**item) for item in raw_sources]
            except Exception:
                sources = []

        return ChatMessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            sources=sources,
            citations=sources,
            created_at=msg.created_at
        )

    def format_conversation_response(self, conv: Conversation) -> ConversationResponse:
        messages = [self.format_message_response(m) for m in conv.messages]
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=messages
        )


chat_service = ChatService()
