# Step-by-Step Implementation Plan: AI Knowledge Assistant 2.0

**Project:** AI Knowledge Assistant  
**Objective:** Incorporate reference RAG advancements (Hybrid Retrieval, Conversational Follow-up Resolution, Context Deduplication, LangChain Text Splitting) into the existing secure full-stack architecture.  

---

## 1. Execution Principles

1. **Non-Destructive Upgrade:** Preserve working features in the existing workspace (FastAPI routes, SQLite session management, JWT auth, Streamlit dashboard).
2. **Fixed Technology Stack:** Strictly adhere to Python, Streamlit, FastAPI, OpenAI API, Sentence Transformers, ChromaDB, PyMuPDF, python-docx, LangChain, SQLite, SQLAlchemy, JWT Authentication, and Pytest.
3. **Approval Before Code Changes:** Complete architectural blueprints first, review with stakeholder, and begin coding only upon explicit confirmation.

---

## 2. Phased Implementation Roadmap

### Phase 1: Environment & Dependency Alignment
- Verify `langchain`, `langchain-community`, `langchain-core`, and `rank-bm25` in virtual environment.
- Ensure all package versions in `requirements.txt` remain compatible without dependency conflicts.
- **Verification:** Run `uv pip check` and test imports.

### Phase 2: Enhanced Ingestion & Chunking (`backend/app/rag/`)
- Upgrade `DocumentExtractor` (`extractors.py`):
  - Enhance PyMuPDF (`fitz`) parsing to extract tables and format tabular cells with markdown pipes (`|`).
  - Add text-cleaning regexes from reference engine (ligatures, publication artifacts, whitespace).
- Upgrade `TextChunker` (`chunker.py`):
  - Integrate LangChain's `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`.
  - Embed source prefix into chunk body: `[Source: {filename}, Page {page_number}] {chunk_text}` to boost citation accuracy.
- **Verification:** Run extractor unit tests on sample PDF with tables and TXT files.

### Phase 3: Hybrid Retrieval Engine (`backend/app/rag/`)
- Implement `HybridRetriever` (`backend/app/rag/hybrid_retriever.py`):
  - ChromaDB dense vector retriever filtered by `user_id` and document IDs.
  - In-memory `BM25Retriever` initialized from user's active chunks.
  - Merge via `EnsembleRetriever` with dynamic weighting (30% Vector / 70% BM25 for keyword-heavy queries; 70% Vector / 30% BM25 for semantic queries).
  - Add `_dedupe_docs` to remove overlapping chunks from context.
- Implement conversational query expansion:
  - Add `_resolve_followup_query` to handle follow-up queries like *"tell me more"* or *"expand on that"*.
  - Add `_expand_query` to expand year/date ranges.
- **Verification:** Run retrieval test comparing dense-only vs. hybrid recall on short queries (e.g. *"what is pdf"*).

### Phase 4: Backend Integration & Streaming Support (`backend/app/`)
- Update `rag_pipeline.py`:
  - Connect hybrid retriever to OpenAI completion generator.
  - Implement streaming generator (`query_stream`) yielding SSE chunks.
- Add `/api/chat/ask/stream` endpoint in `backend/app/api/chat.py` for real-time token streaming.
- Add `/api/admin/metrics` endpoint providing chunk statistics, collection counts, and health diagnostics.
- Ensure all endpoints maintain strict JWT validation and user isolation.
- **Verification:** Execute `backend/tests/` and verify 200 OK on both standard and streaming endpoints.

### Phase 5: Streamlit Frontend Modernization (`frontend/`)
- Upgrade `chat_ui.py`:
  - Support real-time streaming answer generation via `st.write_stream`.
  - Display hybrid search badge (indicating both dense semantic and BM25 keyword matches).
  - Expandable source citation cards with verbatim excerpts and page badges.
- Upgrade `dashboard_ui.py`:
  - Real-time chunk statistics (total chunks, average length, indexed documents, active memory).
- Ensure seamless conversation resume and delete operations.
- **Verification:** Launch Streamlit and perform upload, search, and streaming chat in browser.

### Phase 6: Automated Testing & Verification
- Expand test suite in `backend/tests/`:
  - `test_hybrid_retrieval.py`: Test BM25 exact keyword match and dense vector ensemble.
  - `test_query_expansion.py`: Test follow-up query rewriting.
  - `test_streaming.py`: Test SSE streaming endpoint with mocked LLM.
- Run complete test suite:
  ```powershell
  .venv\Scripts\python -m pytest backend/tests -v
  ```
- Verify 100% test pass rate.

### Phase 7: Deployment & Documentation
- Update `Dockerfile` and `docker-compose.yml` to reflect any new environment settings.
- Update `README.md` and Windows batch launch scripts.
- Commit all changes cleanly to Git with clean working tree.

---

## 3. Order of Implementation Checklist

- [ ] **Step 1:** Confirm user approval to begin implementation.
- [ ] **Step 2:** Install `langchain`, `langchain-community`, `rank-bm25` into `.venv`.
- [ ] **Step 3:** Implement table parsing & ligature cleaning in `backend/app/rag/extractors.py`.
- [ ] **Step 4:** Implement LangChain chunker with source tags in `backend/app/rag/chunker.py`.
- [ ] **Step 5:** Implement Hybrid Retriever (ChromaDB + BM25) and Query Expansion in `backend/app/rag/`.
- [ ] **Step 6:** Update `RAGPipeline` and add streaming endpoint to FastAPI router.
- [ ] **Step 7:** Update Streamlit frontend for streaming responses and chunk diagnostics.
- [ ] **Step 8:** Execute full pytest suite and verify 100% test pass rate.
- [ ] **Step 9:** Commit cleanly to Git and provide final launch instructions.
