# Technical Repository Analysis: Reference RAG System

**Analyzed Reference Implementation:** Domain-Specific AI Chatbot / AI-RAG Data Pipeline Reference  
**Analysis Date:** November 2026  
**Role:** Senior AI Architect & Python Backend Developer  

---

## 1. Executive Summary

The reference project demonstrates a lightweight, prototype-level RAG pipeline built with FastAPI, LangChain, FAISS, and a React/Vite frontend. It provides several valuable RAG algorithms—most notably **Hybrid Retrieval (dense vector + BM25 keyword matching)** and **conversational follow-up query expansion**. 

However, it is architecturally structured as a **single-user local prototype** lacking enterprise security, multi-tenancy, database persistence, JWT authentication, per-document vector deletion, DOCX ingestion, PyMuPDF parsing, and automated test coverage.

---

## 2. Comprehensive Source File Breakdown

| File Path | Functional Responsibility | Key Strengths | Critical Weaknesses & Gaps |
|---|---|---|---|
| `backend/main.py` | FastAPI application, HTTP routing, file uploads, SSE streaming | Clean SSE streaming `/chat/stream`; simple file upload handling | No authentication, no user isolation, path traversal risk (`UPLOAD_DIR + filename`), in-memory state, non-atomic deletion |
| `backend/rag_engine.py` | Core RAG logic: ingestion, chunking, FAISS + BM25 retrieval, LangChain LLM execution | Hybrid `EnsembleRetriever` (FAISS + BM25); follow-up query resolution; context deduplication | In-memory `deque` chat history; dangerous FAISS deserialization (`allow_dangerous_deserialization=True`); hardcoded weights; no user isolation |
| `backend/view_chunks.py` | CLI debugging utility to inspect chunk length, distribution, and text | Detailed chunk statistics and preview | Standalone utility script, not integrated into an admin UI |
| `backend/test_query.py` & `backend/testxapi.py` | Manual testing scripts querying endpoints | Fast sanity check for local dev | Ad-hoc manual scripts; zero automated `pytest` assertions or mocking |
| `backend/requirements.txt` | Python dependency manifest | Minimal dependency footprint | Lacks pinned versions; uses `faiss-cpu` rather than ChromaDB; lacks SQLAlchemy/JWT |
| `frontend/src/App.jsx` | React Single Page Application | Clean chat UI with streaming support | Not Streamlit; lacks authentication views, user settings, document deletion badges |
| `render.yaml` | Cloud deployment configuration for Render | Basic cloud deployment spec | No Dockerfile, no docker-compose, no containerized multi-service orchestration |

---

## 3. Deep-Dive Pipeline Analysis

### A. Document ETL (Extraction, Transformation, Loading)
1. **Extraction:**
   - Uses `pdfplumber` for PDF files. It extracts text and loops through `page.extract_tables()`, converting 2D tables into ASCII Markdown pipes (`cell | cell`).
   - Uses LangChain's `TextLoader` for plain `.txt` files.
   - **Gap:** Completely lacks DOCX support (`python-docx`) and does not use high-performance PyMuPDF (`fitz`).
2. **Transformation & Cleaning:**
   - Implements regex cleanups in `_clean_text`:
     - Strips publication metadata (`Vol.:(...)`, `1 3`).
     - Fixes common PDF ligature extraction corruption (`/g415` -> `ti`, `/g410` -> `ff`, `/g414` -> `th`).
     - Collapses whitespace and excessive newlines.
   - **Source/Page Prepending:** Directly embeds metadata into chunk text: `[Source: {filename}, Page {page_num}] {chunk_text}`. This helps the LLM cite sources even if the prompt context lacks explicit metadata tagging.
   - **Filtering:** Discards pages `< 100` characters unless all pages would be dropped.
3. **Chunking:**
   - Uses LangChain's `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`.

### B. Embedding Generation & Vector Storage
1. **Embeddings:**
   - Uses `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")` from `langchain_huggingface`.
   - Embeddings are generated on the CPU in batches.
2. **Vector Store:**
   - Uses `FAISS` saved to local directory `faiss_index/`.
   - **Severe Limitation:** FAISS flat indexes do not support granular metadata deletions by document ID. When a user deletes a single file in `main.py`, the physical file is deleted, but the vector chunks remain permanently in the index! The only way the reference repo clears vectors is by wiping the entire `faiss_index` directory.

### C. Retrieval & RAG Pipeline
1. **Hybrid Retrieval (`EnsembleRetriever`):**
   - Combines `FAISS` vector search (semantic similarity, weight 0.3) with `BM25Retriever` (exact keyword frequency, weight 0.7).
   - This directly solves the failure case where users ask keyword-heavy questions (e.g., "what is pdf" or names like "Melia") where dense vector cosine similarity might fall below a strict threshold.
2. **Query Expansion & Conversational Follow-Up Resolution:**
   - Recognizes conversational follow-ups (e.g., *"tell me more"*, *"more details"*, *"can you elaborate"*, *"what about that"*) and automatically prepends the prior user question.
   - Expands numerical year ranges (e.g., *"2016 to 2020"* becomes *"2016 2017 2018 2019 2020"*), ensuring BM25 matches individual year tokens.
3. **Context Deduplication:**
   - `_dedupe_docs` hashes the first 200 characters of retrieved chunks to prevent repetitive context windows.
4. **Generation & Prompting:**
   - Interfaced with OpenAI `gpt-4o-mini` (temperature 0.1, max_tokens 4096).
   - Strict system prompt demanding concise answers grounded in documents and instructing the model to declare when facts are absent.

### D. API & Frontend Architecture
1. **FastAPI Endpoints:**
   - `POST /upload`: Ingests multipart files, saves to disk, triggers ETL.
   - `POST /chat`: Standard blocking QA.
   - `POST /chat/stream`: Server-Sent Events (SSE) streaming tokens.
   - `POST /chat/clear`: In-memory deque reset.
   - `GET /documents`: File listing from disk.
   - `DELETE /documents/{filename}`: File deletion (orphans vectors).
   - `DELETE /documents`: Complete vector store reset.
   - `GET /debug/chunks` & `/debug/chunk-summary`: Internal diagnostic JSON feeds.
2. **Frontend:**
   - Built in React / Tailwind. Not compliant with the required Streamlit multi-page architecture.

---

## 4. Key Takeaways & Recommendations

1. **Adopt Hybrid Search:** Incorporating `BM25Retriever` alongside ChromaDB dense vectors via LangChain's `EnsembleRetriever` will dramatically improve recall for short keyword queries, acronyms, and proper nouns.
2. **Adopt Query Preprocessing:** The follow-up query resolution and date-range expansion are lightweight, effective heuristics that enhance conversational coherence.
3. **Adopt In-Context Source Prepending:** Prepending `[Source: filename, Page X]` directly into chunk text strengthens LLM source grounding and citation generation.
4. **Reject Flawed Patterns:**
   - Do NOT use FAISS (use persistent ChromaDB with user metadata filtering).
   - Do NOT store chat history in a Python `deque` (use SQLite with foreign keys).
   - Do NOT use unauthenticated endpoints (use JWT with bcrypt).
   - Do NOT use React frontend (use Streamlit dashboard).
