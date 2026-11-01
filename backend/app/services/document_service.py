"""Document management service handling storage, extraction, chunking, and vector indexing."""

import os
import re
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.document import Document
from backend.app.rag.document_loader import DocumentLoader, LoadedDocument
from backend.app.rag.text_splitter import DocumentTextSplitter, DocumentChunk
from backend.app.rag.embeddings import embedding_service
import backend.app.rag.vector_store as vs_module

logger = logging.getLogger(__name__)


class DocumentStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    WARNING = "warning"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal or unsafe characters."""
    base_name = os.path.basename(filename)
    # Remove non-alphanumeric except . _ -
    clean = re.sub(r"[^\w\.\-]", "_", base_name)
    return clean or "document"


class DocumentService:
    """Orchestrates document uploads, extraction, chunking, vector indexing, and deletion."""

    def __init__(self):
        self.splitter = DocumentTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        # Backwards compatibility alias
        self.chunker = self.splitter

    def get_user_documents(self, db: Session, user_id: int) -> List[Document]:
        """List all documents owned by user."""
        return db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all()

    def get_document_by_id(self, db: Session, document_id: str, user_id: int) -> Optional[Document]:
        """Get single document ensuring ownership."""
        return db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()

    def process_upload(self, db: Session, user_id: int, file: UploadFile) -> Document:
        """Validate, store, extract, chunk, embed, and index an uploaded document."""
        original_name = file.filename or "uploaded_file"
        safe_name = sanitize_filename(original_name)
        ext = Path(safe_name).suffix.lower()

        if ext not in DocumentLoader.SUPPORTED_EXTENSIONS:
            supported_str = ", ".join(sorted(DocumentLoader.SUPPORTED_EXTENSIONS))
            raise ValueError(f"Unsupported file extension '{ext}'. Supported: {supported_str}")

        # Create user-specific upload directory
        user_upload_dir = Path(settings.UPLOAD_DIR) / str(user_id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        doc_id = str(uuid.uuid4())
        stored_filename = f"{doc_id}_{safe_name}"
        destination_path = user_upload_dir / stored_filename

        # Stream write with size limit checking
        total_size = 0
        max_bytes = settings.max_upload_size_bytes

        try:
            with open(destination_path, "wb") as out_file:
                while chunk := file.file.read(1024 * 64):
                    total_size += len(chunk)
                    if total_size > max_bytes:
                        out_file.close()
                        if destination_path.exists():
                            destination_path.unlink()
                        raise ValueError(f"File exceeds maximum size limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")
                    out_file.write(chunk)

            if total_size == 0:
                if destination_path.exists():
                    destination_path.unlink()
                raise ValueError("The uploaded file is empty (0 bytes).")

        except Exception as e:
            if destination_path.exists():
                destination_path.unlink()
            raise e

        # Create database record in 'processing' status
        doc_record = Document(
            id=doc_id,
            user_id=user_id,
            filename=safe_name,
            original_filename=original_name,
            file_type=ext.lstrip("."),
            file_size_bytes=total_size,
            file_path=str(destination_path),
            status=DocumentStatus.PROCESSING,
            page_count=0,
            chunk_count=0
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        try:
            # Step 1: Extract text and metadata using DocumentLoader
            extracted: LoadedDocument = DocumentLoader.load(str(destination_path), original_filename=original_name)
            doc_record.page_count = extracted.total_pages

            if extracted.is_scanned:
                doc_record.status = DocumentStatus.WARNING
                doc_record.status_message = (
                    extracted.warning_message
                    or "Scanned or image-only PDF detected. Optical Character Recognition (OCR) is not yet supported."
                )
                db.commit()
                db.refresh(doc_record)
                return doc_record

            # Step 2: Chunk the extracted text
            chunks: List[DocumentChunk] = self.splitter.split_document(
                document=extracted,
                document_id=doc_id,
                user_id=user_id
            )
            if not chunks:
                doc_record.status = DocumentStatus.WARNING
                doc_record.status_message = (
                    extracted.warning_message
                    or "No readable text content extracted from document."
                )
                db.commit()
                db.refresh(doc_record)
                return doc_record

            # Step 3: Embed chunks
            chunk_texts = [c.text for c in chunks]
            embeddings = embedding_service.embed_documents(chunk_texts)

            # Step 4: Index into ChromaDB
            vs_module.vector_store.add_chunks(chunks, embeddings)

            doc_record.chunk_count = len(chunks)
            doc_record.status = DocumentStatus.COMPLETED
            doc_record.status_message = "Document successfully indexed."
            db.commit()
            db.refresh(doc_record)
            return doc_record

        except Exception as ex:
            logger.error(f"Error indexing document {doc_id}: {str(ex)}")
            doc_record.status = DocumentStatus.FAILED
            doc_record.status_message = f"Indexing failed: {str(ex)}"
            db.commit()
            db.refresh(doc_record)
            raise ex

    def delete_document(self, db: Session, document_id: str, user_id: int) -> bool:
        """Delete document file, vector DB records, and database row."""
        doc = self.get_document_by_id(db, document_id, user_id)
        if not doc:
            return False

        # 1. Remove vector records from ChromaDB
        try:
            vs_module.vector_store.delete_document_chunks(document_id=document_id, user_id=user_id)
        except Exception as e:
            logger.warning(f"Error removing vector chunks for doc {document_id}: {e}")

        # 2. Remove physical file
        try:
            path = Path(doc.file_path)
            if path.exists():
                path.unlink()
        except Exception as e:
            logger.warning(f"Error removing physical file for doc {document_id}: {e}")

        # 3. Remove from database
        db.delete(doc)
        db.commit()
        return True


document_service = DocumentService()
