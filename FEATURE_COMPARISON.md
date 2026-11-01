# Feature Comparison Matrix

**Project:** AI Knowledge Assistant vs. Reference Implementation  
**Technology Stack:** Python, FastAPI, Streamlit, ChromaDB, Sentence Transformers, PyMuPDF, python-docx, LangChain, SQLite, SQLAlchemy, JWT, Pytest  

---

## 1. Architectural & Functional Comparison

| Capability | Proposal Requirement | Reference Implementation | Current AI Knowledge Assistant | Target Upgraded System |
|---|---|---|---|---|
| **Frontend Framework** | Streamlit (Python) | React / Vite SPA (`App.jsx`) | Streamlit 1.66+ Multi-Tab SaaS Dashboard | Streamlit 1.66+ with Enhanced Hybrid Controls |
| **Backend Framework** | FastAPI (REST + Docs) | FastAPI | FastAPI (Modular routers, CORS, DI) | FastAPI with Streaming + Hybrid Endpoints |
| **Authentication & Security** | JWT (HMAC-SHA256) + bcrypt | ❌ None (completely public) | ✅ Full JWT + bcrypt, user route protection | ✅ Full JWT + bcrypt + Admin role auditing |
| **Multi-Tenancy & Isolation** | Strict user-level data isolation | ❌ None (single global user) | ✅ Complete SQLite & ChromaDB `user_id` filtering | ✅ Multi-tenant dense + scoped BM25 isolation |
| **Supported File Formats** | PDF, DOCX, TXT | PDF, TXT only | PDF, DOCX, TXT | PDF (PyMuPDF + tables), DOCX, TXT |
| **PDF Extraction Engine** | PyMuPDF (`fitz`) page-level | `pdfplumber` (tables) | PyMuPDF (`fitz`) with page-level mapping | PyMuPDF (`fitz`) with structured table parsing |
| **Scanned PDF Detection** | Heuristic character density | ❌ Basic empty text check | ✅ Page density heuristic (< 15 chars/page) | ✅ Page density heuristic + warning badge |
| **Chunking Strategy** | Configurable sliding window | LangChain `RecursiveCharacterTextSplitter` | Custom sliding window chunker (800/150) | LangChain `RecursiveCharacterTextSplitter` with Source Tagging |
| **Embedding Generation** | Sentence Transformers (`all-MiniLM-L6-v2`) | `HuggingFaceEmbeddings(all-MiniLM-L6-v2)` | Local `SentenceTransformer` singleton | Local `SentenceTransformer` / LangChain HuggingFace |
| **Vector Database** | Persistent ChromaDB | FAISS local directory | Persistent ChromaDB with Cosine Distance | Persistent ChromaDB with Cosine Distance |
| **Hybrid Search (Vector + BM25)** | High retrieval recall | ✅ `EnsembleRetriever` (FAISS + BM25) | Dense ChromaDB search only | ✅ ChromaDB dense + Scoped BM25 Hybrid Retriever |
| **Query Expansion / Follow-ups** | Conversational continuity | ✅ Regex follow-up + date expansion | Raw query passed to vector search | ✅ Follow-up turn resolution + query expansion |
| **Database Persistence** | SQLite (SQLAlchemy ORM) | ❌ In-memory deque (lost on restart) | ✅ SQLite (`users`, `documents`, `conversations`, `messages`) | ✅ SQLite with extended metadata & citation logs |
| **Document Deletion** | Atomic file + DB + vector delete | ❌ Deletes file only; vectors remain in FAISS | ✅ Deletes file, SQLite row, and ChromaDB vectors | ✅ Deletes file, SQLite row, ChromaDB vectors, and BM25 index |
| **Admin & Health Monitoring** | Diagnostics & statistics | Ad-hoc `/debug/chunks` | ✅ `GET /api/health` (DB, ChromaDB status) | ✅ `/api/health` + Chunk Metrics Dashboard |
| **Automated Testing** | Pytest unit, integration, mock LLM | ❌ Manual scripts (`test_query.py`) | ✅ 35 passing automated tests (100% pass) | ✅ 40+ automated tests covering hybrid RAG & streaming |
| **Containerization** | Docker & Docker Compose | ❌ None (`render.yaml` only) | ✅ `Dockerfile` + `docker-compose.yml` | ✅ Production multi-container Compose setup |

---

## 2. Gap Analysis Summary

### High-Priority Gaps Solved by Reference Repo:
1. **Short-query & Keyword Recall:** Pure dense vector search with a similarity threshold of 0.35 rejected queries like *"what is pdf"* or specific rare names like *"Melia"*. Incorporating BM25 via LangChain `EnsembleRetriever` solves this issue.
2. **Context Deduplication:** When multiple chunks overlap significantly, passing duplicate sentences wastes LLM context window tokens. A deduplication step ensures maximum information density.
3. **Conversational Follow-up Resolution:** Users asking follow-up questions like *"Tell me more"* or *"Can you elaborate?"* fail in stateless vector retrieval. Resolving the query using conversational memory before retrieval maintains topic coherence.

### Critical Gaps in Reference Repo Fixed by Our Architecture:
1. **Zero Security:** The reference repo exposed open endpoints allowing anyone to read or delete all files. Our architecture provides full JWT authentication and bcrypt hashing.
2. **Lack of Multi-Tenancy:** The reference repo could only serve one user. Our architecture segregates all uploads, vectors, and chat history by `user_id`.
3. **Vector Store Invalidation on Delete:** FAISS in the reference repo leaves orphaned vectors when a file is deleted. Our ChromaDB vector store purges all chunks by document ID.
4. **Missing DOCX & PyMuPDF:** Our architecture natively supports Word documents and ultra-fast PyMuPDF processing.
