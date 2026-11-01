"""Persistence Lifecycle Test Suite: Verifying SQLite and ChromaDB data survive container restarts."""

import os
import shutil
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.base import Base
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.chat import Conversation, ChatMessage
from backend.app.rag.vector_store import VectorStore
from backend.app.rag.text_splitter import DocumentChunk
from backend.app.rag.embeddings import embedding_service
from backend.app.core.security import hash_password


def test_sqlite_and_chromadb_persistence_across_restarts():
    """Simulates a container restart by tearing down connections and re-opening the persistent files."""
    temp_dir = tempfile.mkdtemp(prefix="persistence_test_")
    db_file = os.path.join(temp_dir, "test_app.db")
    db_url = f"sqlite:///{db_file}"
    chroma_dir = os.path.join(temp_dir, "chroma_data")
    os.makedirs(chroma_dir, exist_ok=True)

    try:
        # =====================================================================
        # Phase A: Initial Ingestion & State Creation (Simulating Running Container)
        # =====================================================================
        engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine1)
        Session1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
        db1 = Session1()

        # 1. Create User
        user = User(
            id=1,
            email="persistent_user@example.com",
            username="persistent_alice",
            hashed_password=hash_password("Password123!"),
            is_active=True,
            is_admin=True,
            role="admin"
        )
        db1.add(user)
        db1.commit()

        # 2. Create Document Record
        doc = Document(
            id="doc_persistent_01",
            user_id=1,
            filename="enterprise_policy.pdf",
            original_filename="enterprise_policy.pdf",
            file_type="pdf",
            file_size_bytes=45000,
            file_path=os.path.join(temp_dir, "enterprise_policy.pdf"),
            status="completed",
            page_count=3,
            chunk_count=2
        )
        db1.add(doc)
        db1.commit()

        # 3. Create Conversation & Messages
        conv = Conversation(
            id="conv_persistent_01",
            user_id=1,
            title="Policy Inquiry"
        )
        db1.add(conv)
        db1.commit()

        msg = ChatMessage(
            id="msg_persistent_01",
            conversation_id="conv_persistent_01",
            role="assistant",
            content="Enterprise data retention policy specifies 7 years.",
            sources_json='[{"document_id": "doc_persistent_01", "filename": "enterprise_policy.pdf", "page_number": 2, "chunk_index": 0, "excerpt": "Data retention is 7 years.", "score": 0.92}]'
        )
        db1.add(msg)
        db1.commit()
        db1.close()
        engine1.dispose()

        # 4. Insert Vector Embeddings into Persistent ChromaDB
        vs1 = VectorStore(persist_dir=chroma_dir, collection_name="persistent_knowledge")
        chunks = [
            DocumentChunk(
                id="doc_persistent_01_0",
                document_id="doc_persistent_01",
                user_id=1,
                filename="enterprise_policy.pdf",
                file_type="pdf",
                page_number=2,
                chunk_index=0,
                text="The enterprise data retention policy mandates a minimum retention period of 7 years for financial records.",
                metadata={"document_id": "doc_persistent_01", "user_id": 1, "filename": "enterprise_policy.pdf", "page_number": 2}
            ),
            DocumentChunk(
                id="doc_persistent_01_1",
                document_id="doc_persistent_01",
                user_id=1,
                filename="enterprise_policy.pdf",
                file_type="pdf",
                page_number=3,
                chunk_index=1,
                text="Disaster recovery failover must occur within an RTO of under 15 minutes.",
                metadata={"document_id": "doc_persistent_01", "user_id": 1, "filename": "enterprise_policy.pdf", "page_number": 3}
            )
        ]
        embeddings = embedding_service.embed_documents([c.text for c in chunks])
        vs1.add_chunks(chunks, embeddings)
        assert vs1.count() == 2

        # =====================================================================
        # Phase B: Container Termination / Cold Restart
        # Deliberately delete client instances and memory references
        # =====================================================================
        del vs1
        del engine1

        # =====================================================================
        # Phase C: Post-Restart Verification (Connecting to Persisted Files)
        # =====================================================================
        engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
        Session2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
        db2 = Session2()

        # Verify User survived
        persisted_user = db2.query(User).filter(User.id == 1).first()
        assert persisted_user is not None
        assert persisted_user.username == "persistent_alice"
        assert persisted_user.email == "persistent_user@example.com"
        assert persisted_user.is_admin is True

        # Verify Document survived
        persisted_doc = db2.query(Document).filter(Document.id == "doc_persistent_01").first()
        assert persisted_doc is not None
        assert persisted_doc.filename == "enterprise_policy.pdf"
        assert persisted_doc.chunk_count == 2
        assert persisted_doc.status == "completed"

        # Verify Conversation and Citation Message survived
        persisted_conv = db2.query(Conversation).filter(Conversation.id == "conv_persistent_01").first()
        assert persisted_conv is not None
        assert len(persisted_conv.messages) == 1
        assert "7 years" in persisted_conv.messages[0].content
        assert "enterprise_policy.pdf" in persisted_conv.messages[0].sources_json

        db2.close()
        engine2.dispose()

        # Verify ChromaDB Vectors survived cold restart
        vs2 = VectorStore(persist_dir=chroma_dir, collection_name="persistent_knowledge")
        assert vs2.count() == 2
        assert vs2.document_exists("doc_persistent_01", user_id=1) is True

        # Run Semantic Search against persisted index
        q_vec = embedding_service.embed_query("How many years is data retention?")
        search_results = vs2.search(query_embedding=q_vec, user_id=1, top_k=2)
        assert len(search_results) >= 1
        assert search_results[0].document_id == "doc_persistent_01"
        assert search_results[0].page_number == 2
        assert "7 years" in search_results[0].text

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
