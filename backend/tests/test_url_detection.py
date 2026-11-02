"""Regression test suite for URL detection, warning badges, and conversational guidance."""

import io
import pytest
from unittest.mock import MagicMock
from fastapi import UploadFile

from backend.app.rag.document_loader import DocumentLoader, LoadedDocument
from backend.app.services.document_service import DocumentService, DocumentStatus
from backend.app.rag.pipeline import RAGPipeline
from backend.app.rag.chunker import DocumentChunk
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.vector_store import VectorStore
import backend.app.rag.vector_store as vs_module
from backend.app.models.user import User


def test_url_only_txt_detection_and_warning(db_session, user_a, tmp_path):
    """Test 1: Upload a TXT file containing only one URL."""
    url_content = b"https://share.gemini.google/7uj7hnsQGxyE\n"
    upload_file = UploadFile(
        file=io.BytesIO(url_content),
        filename="gemini_link.txt",
        headers={"content-type": "text/plain"}
    )

    doc_service = DocumentService()
    doc = doc_service.process_upload(db=db_session, user_id=user_a.id, file=upload_file)

    # Verify detected as warning with message
    assert doc.status == DocumentStatus.WARNING
    assert doc.status_message is not None
    assert "contains only a web link" in doc.status_message
    assert doc.chunk_count == 1

    # Verify query does not produce fabricated answers
    pipeline = RAGPipeline()
    answer, citations, is_grounded = pipeline.answer_question(
        question="Summarize the key objectives and main findings.",
        user_id=user_a.id,
        document_ids=[doc.id]
    )

    assert is_grounded is False
    assert len(citations) == 0
    assert "cannot find the answer" in answer.lower()
    assert "appears to contain only a web link" in answer


def test_actual_text_txt_upload_and_qa(db_session, user_a, tmp_path):
    """Test 2: Upload a TXT file containing actual text."""
    story_content = (
        b"Chapter 1: The Quantum Observatory.\n"
        b"Dr. Eleanor Vance discovered an anomalous gravitational wave signature near Jupiter.\n"
        b"The primary objective of the mission was to verify whether primordial black holes exist.\n"
        b"The main finding confirmed a miniature singularity with a mass equivalent to Mount Everest."
    )
    upload_file = UploadFile(
        file=io.BytesIO(story_content),
        filename="quantum_story.txt",
        headers={"content-type": "text/plain"}
    )

    doc_service = DocumentService()
    doc = doc_service.process_upload(db=db_session, user_id=user_a.id, file=upload_file)

    # Verify extraction and chunking
    assert doc.status == DocumentStatus.COMPLETED
    assert doc.chunk_count >= 1
    assert doc.status_message == "Document successfully indexed."

    # Mock LLM generation for grounded response
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "The main finding confirmed a miniature singularity with a mass equivalent to Mount Everest."
    mock_res = MagicMock()
    mock_res.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_res

    pipeline = RAGPipeline(openai_client=mock_client)
    answer, citations, is_grounded = pipeline.answer_question(
        question="What was the main finding of the mission?",
        user_id=user_a.id
    )

    assert is_grounded is True
    assert len(citations) >= 1
    assert citations[0].filename == "quantum_story.txt"
    assert "miniature singularity" in answer


def test_mixed_text_and_urls_txt_upload(db_session, user_a, tmp_path):
    """Test 3: Upload a TXT file containing both normal text and URLs."""
    mixed_content = (
        b"Title: Modern Astrophysics References\n\n"
        b"The James Webb Space Telescope observes the universe in infrared wavelengths.\n"
        b"It was launched on December 25, 2021 from Kourou, French Guiana.\n"
        b"Official NASA Mission portal: https://www.nasa.gov/mission_pages/webb/main/index.html\n"
        b"ESA Deep Space Archive: https://www.esa.int/Science_Exploration/Space_Science/Webb\n"
        b"Conclusion: Infrared observations allow astronomers to peer through cosmic dust clouds."
    )
    upload_file = UploadFile(
        file=io.BytesIO(mixed_content),
        filename="jwst_research.txt",
        headers={"content-type": "text/plain"}
    )

    doc_service = DocumentService()
    doc = doc_service.process_upload(db=db_session, user_id=user_a.id, file=upload_file)

    # Verify that URLs do NOT cause document rejection
    assert doc.status == DocumentStatus.COMPLETED
    assert doc.chunk_count >= 1
    assert "successfully indexed" in doc.status_message

    # Test question answering based on normal text
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "The James Webb Space Telescope was launched on December 25, 2021 from Kourou, French Guiana."
    mock_res = MagicMock()
    mock_res.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_res

    pipeline = RAGPipeline(openai_client=mock_client)
    answer, citations, is_grounded = pipeline.answer_question(
        question="When was the James Webb Space Telescope launched?",
        user_id=user_a.id
    )

    assert is_grounded is True
    assert len(citations) >= 1
    assert citations[0].filename == "jwst_research.txt"
    assert "December 25, 2021" in answer


def test_pdf_and_docx_upload_unaffected(db_session, user_a, tmp_path):
    """Test 4: Verify existing PDF and DOCX uploads remain unaffected."""
    # 4.1 Test PDF
    import pymupdf as fitz
    pdf_doc = fitz.open()
    page1 = pdf_doc.new_page()
    page1.insert_text((50, 50), "PDF Section 1: Atmospheric Chemistry and Ozone Depletion.")
    page2 = pdf_doc.new_page()
    page2.insert_text((50, 50), "PDF Section 2: Montreal Protocol environmental recovery metrics.")
    pdf_bytes = pdf_doc.write()
    pdf_doc.close()

    upload_pdf = UploadFile(
        file=io.BytesIO(pdf_bytes),
        filename="ozone_report.pdf",
        headers={"content-type": "application/pdf"}
    )
    doc_service = DocumentService()
    pdf_record = doc_service.process_upload(db=db_session, user_id=user_a.id, file=upload_pdf)

    assert pdf_record.status == DocumentStatus.COMPLETED
    assert pdf_record.page_count == 2
    assert pdf_record.chunk_count >= 2

    # 4.2 Test DOCX
    import docx
    word_doc = docx.Document()
    word_doc.add_heading("Geological Survey", level=1)
    word_doc.add_paragraph("Tectonic plate movements in the Pacific Ring of Fire.")
    table = word_doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Region"
    table.cell(0, 1).text = "Magnitude"
    table.cell(1, 0).text = "Kanto"
    table.cell(1, 1).text = "7.2"

    docx_buf = io.BytesIO()
    word_doc.save(docx_buf)
    docx_bytes = docx_buf.getvalue()

    upload_docx = UploadFile(
        file=io.BytesIO(docx_bytes),
        filename="geology_survey.docx",
        headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    )
    docx_record = doc_service.process_upload(db=db_session, user_id=user_a.id, file=upload_docx)

    assert docx_record.status == DocumentStatus.COMPLETED
    assert docx_record.chunk_count >= 1
    assert "successfully indexed" in docx_record.status_message


def test_pipeline_guidance_for_unrelated_queries(tmp_path):
    """Test 5: Verify new pipeline guidance for queries with no relevant retrieval results."""
    vs = VectorStore(persist_dir=str(tmp_path / "url_chroma"), collection_name="test_url_guidance")
    
    # Add a chunk that contains only a URL
    url_chunk = DocumentChunk(
        id="url_c1",
        document_id="doc_url",
        user_id=42,
        filename="link.txt",
        page_number=1,
        chunk_index=0,
        text="https://share.gemini.google/7uj7hnsQGxyE",
        metadata={"document_id": "doc_url", "user_id": 42, "filename": "link.txt", "page_number": 1, "chunk_index": 0}
    )
    vs.add_chunks([url_chunk], embedding_service.embed_documents([url_chunk.text]))

    orig_vs = vs_module.vector_store
    vs_module.vector_store = vs

    try:
        pipeline = RAGPipeline()
        answer, citations, is_grounded = pipeline.answer_question(
            question="What are the financial results for Q3?",
            user_id=42
        )

        assert is_grounded is False
        assert len(citations) == 0
        assert "cannot find the answer" in answer.lower()
        # Ensure the contextual guidance note is included
        assert "appears to contain only a web link" in answer
        assert "does not browse external websites" in answer
    finally:
        vs_module.vector_store = orig_vs
