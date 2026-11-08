"""Comprehensive test suite for Automatic Multilingual Language Detection and Same-Language RAG Responses.

Covers all 11 required scenarios:
1. Tamil script input
2. English input
3. Tanglish input
4. Mixed Tamil-English technical questions
5. Tamil follow-up questions
6. English language switching
7. Tamil PDF summarization
8. English PDF summarization
9. RAG citations
10. Irrelevant questions
11. Missing provider configuration
"""

import io
import pytest
from unittest.mock import MagicMock, patch

from backend.app.core.config import settings
from backend.app.services.language_detector import LanguageDetector, language_detector
from backend.app.services.language_service import language_service
from backend.app.rag.prompts import (
    build_multilingual_system_prompt,
    build_multilingual_rag_prompt,
    INSUFFICIENT_EVIDENCE_MAP,
)
from backend.app.rag.pipeline import RAGPipeline, rag_pipeline
from backend.app.schemas.chat import SourceCitation


def create_sample_pdf(text: str) -> io.BytesIO:
    """Helper to generate a minimal in-memory PDF for test uploads."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = io.BytesIO(doc.tobytes())
    doc.close()
    return pdf_bytes


# =========================================================================
# Scenario 1: Tamil Script Input
# =========================================================================
def test_tamil_script_input():
    """Verify accurate detection of Tamil Unicode script and prompt generation."""
    # Pure Tamil questions
    q1 = "இந்த ஆவணத்தில் உள்ள முக்கிய குறிப்புகள் என்ன?"
    q2 = "வணக்கம், நீங்கள் யார்?"
    q3 = "செயற்கை நுண்ணறிவு எவ்வாறு செயல்படுகிறது?"

    assert language_detector.detect_language(q1) == LanguageDetector.LANG_TAMIL
    assert language_detector.detect_language(q2) == LanguageDetector.LANG_TAMIL
    assert language_detector.detect_language(q3) == LanguageDetector.LANG_TAMIL

    # Check system prompt includes Tamil instruction
    sys_prompt = build_multilingual_system_prompt(LanguageDetector.LANG_TAMIL)
    assert "Tamil - தமிழ்" in sys_prompt
    assert "understandable Tamil" in sys_prompt


# =========================================================================
# Scenario 2: English Input
# =========================================================================
def test_english_input():
    """Verify accurate detection of English queries."""
    q1 = "What are the primary objectives of this document?"
    q2 = "Explain machine learning."
    q3 = "Summarize the key architectural decisions."

    assert language_detector.detect_language(q1) == LanguageDetector.LANG_ENGLISH
    assert language_detector.detect_language(q2) == LanguageDetector.LANG_ENGLISH
    assert language_detector.detect_language(q3) == LanguageDetector.LANG_ENGLISH

    sys_prompt = build_multilingual_system_prompt(LanguageDetector.LANG_ENGLISH)
    assert "English" in sys_prompt


# =========================================================================
# Scenario 3: Tanglish Input
# =========================================================================
def test_tanglish_input():
    """Verify Tanglish recognition using phonetic patterns, suffixes, and n-grams."""
    q1 = "Machine learning na enna?"
    q2 = "indha doc epdi work aaguthu sollunga"
    q3 = "Romba nalla irukku"
    q4 = "Brief-ah sollu bro"
    q5 = "Adhoda types enna?"

    assert language_detector.detect_language(q1) == LanguageDetector.LANG_TANGLISH
    assert language_detector.detect_language(q2) == LanguageDetector.LANG_TANGLISH
    assert language_detector.detect_language(q3) == LanguageDetector.LANG_TANGLISH
    assert language_detector.detect_language(q4) == LanguageDetector.LANG_TANGLISH
    assert language_detector.detect_language(q5) == LanguageDetector.LANG_TANGLISH

    sys_prompt = build_multilingual_system_prompt(LanguageDetector.LANG_TANGLISH)
    assert "Tanglish / Tamil" in sys_prompt
    assert "friendly conversational Tanglish" in sys_prompt


# =========================================================================
# Scenario 4: Mixed Tamil-English Technical Questions
# =========================================================================
def test_mixed_tamil_english_technical_questions():
    """Verify mixed technical queries preserve technical terms while identifying base language."""
    # Mixed Tamil Script with English technical keywords
    q_ta_tech1 = "Deep Learning-ல் Convolutional Neural Network எவ்வாறு செயல்படுகிறது?"
    q_ta_tech2 = "Python FastAPI-ல் RAG pipeline-ஐ உருவாக்குவது எப்படி?"
    assert language_detector.detect_language(q_ta_tech1) == LanguageDetector.LANG_TAMIL
    assert language_detector.detect_language(q_ta_tech2) == LanguageDetector.LANG_TAMIL

    # Mixed Tanglish with English technical terms
    q_tg_tech1 = "Supervised learning matrum unsupervised learning ku ulla difference enna?"
    q_tg_tech2 = "Gradient descent epdi converge aagum nu sollu"
    assert language_detector.detect_language(q_tg_tech1) == LanguageDetector.LANG_TANGLISH
    assert language_detector.detect_language(q_tg_tech2) == LanguageDetector.LANG_TANGLISH


# =========================================================================
# Scenario 5: Tamil Follow-up Questions (Conversation Context Continuity)
# =========================================================================
def test_tamil_follow_up_questions():
    """Verify follow-up questions inherit and preserve conversation language context."""
    detector = LanguageDetector()

    # Turn 1: Tanglish introductory query
    t1 = "Machine Learning na enna?"
    l1 = detector.detect_language(t1)
    assert l1 == "tanglish"

    # Turn 2: Short Tanglish follow-up with specific verb 'kudu'
    t2 = "Example kudu."
    l2 = detector.detect_language(t2, context_language=l1)
    assert l2 == "tanglish"

    # Turn 3: Short ambiguous follow-up (<= 3 words, e.g. "Example?") inherits context
    t3 = "Example?"
    l3 = detector.detect_language(t3, context_language=l2)
    assert l3 == "tanglish"

    # Turn 4: Tamil script follow-up
    t4 = "மேலும் விவரங்களை விளக்குக."
    l4 = detector.detect_language(t4, context_language="ta")
    assert l4 == "ta"

    # Turn 5: Short neutral continuation in Tamil context
    t5 = "அடுத்தது என்ன?"
    l5 = detector.detect_language(t5, context_language=l4)
    assert l5 == "ta"


# =========================================================================
# Scenario 6: English Language Switching
# =========================================================================
def test_english_language_switching():
    """Verify explicit language switches take priority over prior conversation context."""
    detector = LanguageDetector()

    # Prior message was in Tanglish
    prior_context = "tanglish"

    # User explicitly instructs to switch to English
    switch_en1 = "Now explain in English."
    switch_en2 = "Can you explain in English please?"
    switch_en3 = "Switch to English"

    assert detector.detect_language(switch_en1, context_language=prior_context) == "en"
    assert detector.detect_language(switch_en2, context_language=prior_context) == "en"
    assert detector.detect_language(switch_en3, context_language=prior_context) == "en"

    # Full English sentence with standard grammar breaks previous context
    full_en = "What are the computational trade-offs of this approach?"
    assert detector.detect_language(full_en, context_language=prior_context) == "en"

    # Switching back to Tamil
    switch_ta1 = "Tamil-la sollu"
    switch_ta2 = "Explain in Tamil"
    assert detector.detect_language(switch_ta1, context_language="en") in ["ta", "tanglish"]
    assert detector.detect_language(switch_ta2, context_language="en") in ["ta", "tanglish"]


# =========================================================================
# Scenario 7: Tamil PDF Summarization (End-to-End RAG)
# =========================================================================
def test_tamil_pdf_summarization(client, headers_a):
    """Verify end-to-end PDF summarization when asked in Tamil."""
    pdf_text = (
        "Project Phoenix Executive Summary.\n"
        "Key Objective: Modernize banking infrastructure with low-latency APIs.\n"
        "Main Finding: Microservices reduced operational overhead by 42 percent."
    )
    pdf_bytes = create_sample_pdf(pdf_text)
    files = {"file": ("phoenix_project.pdf", pdf_bytes, "application/pdf")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    tamil_prompt = "இந்த PDF-ஐ சுருக்கமாக விளக்கவும்."
    assert language_detector.detect_language(tamil_prompt) == "ta"

    mock_tamil_answer = (
        "பீனிக்ஸ் திட்டத்தின் முக்கிய நோக்கம் குறைந்த தாமதமுடைய API-களுடன் "
        "வங்கி உள்கட்டமைப்பை நவீனமயமாக்குவதாகும். இதன் மூலம் செயல்பாட்டுச் செலவு 42% குறைக்கப்பட்டுள்ளது."
    )

    with patch("backend.app.services.llm_provider.llm_provider_service.generate_completion") as mock_gen:
        mock_gen.return_value = (mock_tamil_answer, None, None)
        res = client.post("/api/chat/ask", headers=headers_a, json={
            "question": tamil_prompt,
            "document_ids": [doc_id]
        })

    assert res.status_code == 200
    data = res.json()
    assert data["grounded"] is True
    assert data["language"] == "ta"
    assert "42%" in data["answer"] or "42" in data["answer"]
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["filename"] == "phoenix_project.pdf"


# =========================================================================
# Scenario 8: English PDF Summarization (End-to-End RAG)
# =========================================================================
def test_english_pdf_summarization(client, headers_a):
    """Verify end-to-end PDF summarization when asked in English."""
    pdf_text = (
        "Quantum Computing Roadmap.\n"
        "Objective: Build a 1000-qubit fault-tolerant quantum processor by 2028.\n"
        "Milestone: Surface code error correction demonstrated with 99.9% fidelity."
    )
    pdf_bytes = create_sample_pdf(pdf_text)
    files = {"file": ("quantum_roadmap.pdf", pdf_bytes, "application/pdf")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    en_prompt = "Summarize the key findings from this PDF."
    assert language_detector.detect_language(en_prompt) == "en"

    mock_en_answer = "The roadmap aims to achieve a 1000-qubit fault-tolerant quantum processor with 99.9% fidelity by 2028."

    with patch("backend.app.services.llm_provider.llm_provider_service.generate_completion") as mock_gen:
        mock_gen.return_value = (mock_en_answer, None, None)
        res = client.post("/api/chat/ask", headers=headers_a, json={
            "question": en_prompt,
            "document_ids": [doc_id]
        })

    assert res.status_code == 200
    data = res.json()
    assert data["grounded"] is True
    assert data["language"] == "en"
    assert "1000-qubit" in data["answer"]
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["filename"] == "quantum_roadmap.pdf"


# =========================================================================
# Scenario 9: RAG Citations Preservation
# =========================================================================
def test_rag_citations_preservation(client, headers_a):
    """Verify that document filenames and page numbers remain unmodified in citations."""
    pdf_text = "கணினி டெலிமெட்ரி அறிக்கை: CPU core வெப்பநிலை 48 டிகிரி செல்சியஸில் சீராக உள்ளது. Telemetry data confirmed."
    pdf_bytes = create_sample_pdf(pdf_text)
    files = {"file": ("Telemetry_Diagnostics_V2.pdf", pdf_bytes, "application/pdf")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Ask in Tamil
    with patch("backend.app.services.llm_provider.llm_provider_service.generate_completion") as mock_gen:
        mock_gen.return_value = ("CPU வெப்பநிலை 48 டிகிரி செல்சியஸில் சீராக உள்ளது.", None, None)
        res = client.post("/api/chat/ask", headers=headers_a, json={
            "question": "CPU வெப்பநிலை என்ன?",
            "document_ids": [doc_id],
            "similarity_threshold": 0.15
        })

    assert res.status_code == 200
    data = res.json()
    assert len(data["sources"]) >= 1
    citation = data["sources"][0]
    # Critical: Do not translate or modify source filename
    assert citation["filename"] == "Telemetry_Diagnostics_V2.pdf"
    assert citation["page_number"] == 1
    assert "48" in citation["excerpt"]


# =========================================================================
# Scenario 10: Irrelevant Questions
# =========================================================================
def test_irrelevant_questions_multilingual():
    """Verify ungrounded/irrelevant questions receive localized 'insufficient evidence' notices."""
    pipeline = RAGPipeline()

    # Tamil Irrelevant Question (user 999 has no documents)
    ans_ta, cits_ta, grounded_ta = pipeline.answer_question(
        question="இந்த ஆவணத்தில் சந்திராயன் மிஷன் பற்றி என்ன உள்ளது?",
        user_id=999
    )
    assert grounded_ta is False
    assert len(cits_ta) == 0
    assert "பதிவேற்றப்பட்ட ஆவணங்களில்" in ans_ta

    # Tanglish Irrelevant Question
    ans_tg, cits_tg, grounded_tg = pipeline.answer_question(
        question="Indha doc-la Chandrayaan pathi irukka?",
        user_id=999
    )
    assert grounded_tg is False
    assert len(cits_tg) == 0
    assert "Upload panna documents-la" in ans_tg

    # English Irrelevant Question
    ans_en, cits_en, grounded_en = pipeline.answer_question(
        question="Does this document mention Apollo 11 lunar landings?",
        user_id=999
    )
    assert grounded_en is False
    assert len(cits_en) == 0
    assert "cannot find the answer" in ans_en.lower()


# =========================================================================
# Scenario 11: Missing Provider Configuration (Graceful Multilingual Fallback)
# =========================================================================
def test_missing_provider_configuration_multilingual_fallback(client, headers_a):
    """Verify that when cloud LLM is unconfigured, grounded fallback notice is in user's language."""
    content = "The database cluster maintains 3 read replicas across Availability Zone 1."
    files = {"file": ("cluster_config.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    upload_res = client.post("/api/documents/upload", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Simulate LLM Provider returning 'unconfigured' error code
    with patch("backend.app.services.llm_provider.llm_provider_service.generate_completion") as mock_gen:
        mock_gen.return_value = (None, "unconfigured", "No API key configured.")

        # Tamil query asking for summary
        res_ta = client.post("/api/chat/ask", headers=headers_a, json={
            "question": "இந்த கிளஸ்டர் உள்ளமைவை சுருக்கமாக கூறவும்.",
            "document_ids": [doc_id]
        })
        assert res_ta.status_code == 200
        ans_ta = res_ta.json()["answer"]
        assert "கிளவுட் AI" in ans_ta
        assert "cluster_config.txt" in ans_ta
        assert "3 read replicas" in ans_ta

        # English query asking for summary
        res_en = client.post("/api/chat/ask", headers=headers_a, json={
            "question": "Summarize how many read replicas are in the cluster.",
            "document_ids": [doc_id]
        })
        assert res_en.status_code == 200
        ans_en = res_en.json()["answer"]
        assert "Cloud AI" in ans_en
        assert "cluster_config.txt" in ans_en
        assert "3 read replicas" in ans_en
