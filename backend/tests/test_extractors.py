"""Tests for document extractors: PDF, DOCX, and TXT."""

import os
import tempfile
import pytest
import docx
try:
    import pymupdf as fitz
except ImportError:
    import fitz

from backend.app.rag.extractors import DocumentExtractor, normalize_text


def test_normalize_text():
    raw = "Hello   world!\r\n\r\n\r\nThis is a   test.\n\n\n\nFinal line."
    clean = normalize_text(raw)
    assert "Hello world!" in clean
    assert "This is a test." in clean
    assert "\n\n\n" not in clean


def test_extract_txt():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Line 1: Knowledge management.\n\nLine 2: Semantic retrieval.")
        f_path = f.name

    try:
        doc = DocumentExtractor.extract(f_path, original_filename="notes.txt")
        assert doc.filename == "notes.txt"
        assert doc.file_type == "txt"
        assert doc.total_pages == 1
        assert "Knowledge management." in doc.full_text
        assert "Semantic retrieval." in doc.full_text
    finally:
        if os.path.exists(f_path):
            os.unlink(f_path)


def test_extract_txt_empty():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("   \n\n   ")
        f_path = f.name

    try:
        doc = DocumentExtractor.extract(f_path, original_filename="empty.txt")
        assert doc.warning_message is not None
        assert doc.full_text == ""
    finally:
        if os.path.exists(f_path):
            os.unlink(f_path)


def test_extract_docx():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f_path = f.name

    try:
        doc_obj = docx.Document()
        doc_obj.add_heading("Architecture Overview", level=1)
        doc_obj.add_paragraph("This application uses FastAPI for backend and Streamlit for frontend.")
        
        # Add table
        table = doc_obj.add_table(rows=2, cols=2)
        table.rows[0].cells[0].text = "Component"
        table.rows[0].cells[1].text = "Technology"
        table.rows[1].cells[0].text = "Vector DB"
        table.rows[1].cells[1].text = "ChromaDB"
        doc_obj.save(f_path)

        extracted = DocumentExtractor.extract(f_path, original_filename="tech_spec.docx")
        assert extracted.file_type == "docx"
        assert "Architecture Overview" in extracted.full_text
        assert "FastAPI" in extracted.full_text
        assert "Vector DB | ChromaDB" in extracted.full_text
    finally:
        if os.path.exists(f_path):
            os.unlink(f_path)


def test_extract_pdf_multipage():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f_path = f.name

    try:
        # Create a genuine 2-page PDF with PyMuPDF
        pdf_doc = fitz.open()
        p1 = pdf_doc.new_page()
        p1.insert_text((50, 72), "Chapter 1: Introduction to Retrieval-Augmented Generation.")
        
        p2 = pdf_doc.new_page()
        p2.insert_text((50, 72), "Chapter 2: Vector embeddings and similarity search using ChromaDB.")
        pdf_doc.save(f_path)
        pdf_doc.close()

        extracted = DocumentExtractor.extract(f_path, original_filename="rag_guide.pdf")
        assert extracted.file_type == "pdf"
        assert extracted.total_pages == 2
        assert len(extracted.pages) == 2
        assert extracted.pages[0].page_number == 1
        assert "Chapter 1: Introduction" in extracted.pages[0].text
        assert extracted.pages[1].page_number == 2
        assert "Chapter 2: Vector embeddings" in extracted.pages[1].text
        assert not extracted.is_scanned
    finally:
        if os.path.exists(f_path):
            os.unlink(f_path)


def test_extract_pdf_scanned_detection():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f_path = f.name

    try:
        # Create a PDF page with no text (simulating image-only or scanned)
        pdf_doc = fitz.open()
        _ = pdf_doc.new_page()
        pdf_doc.save(f_path)
        pdf_doc.close()

        extracted = DocumentExtractor.extract(f_path, original_filename="scanned.pdf")
        assert extracted.is_scanned is True
        assert "Scanned or image-only" in extracted.warning_message
    finally:
        if os.path.exists(f_path):
            os.unlink(f_path)


def test_validate_unsupported_extension():
    with pytest.raises(ValueError) as exc:
        DocumentExtractor.validate_file("document.exe", max_size_bytes=1000)
    assert "Unsupported file format" in str(exc.value)


def test_validate_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        DocumentExtractor.validate_file("does_not_exist.pdf", max_size_bytes=1000)
