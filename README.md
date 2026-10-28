# 🧠 AI Knowledge Assistant – Full-Stack RAG Application

An enterprise-grade, production-minded **Retrieval-Augmented Generation (RAG)** application. It empowers users to upload private documents (PDF, DOCX, TXT), perform semantic similarity search against local vector embeddings, ask questions in natural language, and receive factually grounded answers with source citations and page-level references.

---

## 🏛️ Architecture Overview

The system is architected as an isolated multi-tenant system with strict data separation between users:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Streamlit Frontend                            │
│  (Auth UI, Document Library, Modern Chat Bubbles, Citations, Metrics)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JWT Bearer Token)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                              │
│ ┌───────────────────────────┬───────────────────────────┬────────────┐ │
│ │  Authentication & Users   │    Document Ingestion     │  Chat & QA │ │
│ │  (JWT, bcrypt, isolation) │  (PyMuPDF, docx, chunker) │  (RAG Flow)│ │
│ └─────────────┬─────────────┴─────────────┬─────────────┴─────┬──────┘ │
└───────────────┼───────────────────────────┼───────────────────┼────────┘
                ▼                           ▼                   ▼
    ┌───────────────────────┐   ┌───────────────────────┐   ┌────────────┐
    │  SQLite (SQLAlchemy)  │   │  SentenceTransformers │   │ OpenAI LLM │
    │ Users, Docs, History  │   │   (all-MiniLM-L6-v2)  │   │  API / Mock│
    └───────────────────────┘   └───────────┬───────────┘   └────────────┘
                                            ▼
                                ┌───────────────────────┐
                                │ ChromaDB Vector Store │
                                │  (Cosine Persistence) │
                                └───────────────────────┘
```

---

## 🚀 Key Features

### 1. Secure Authentication & User Isolation
- User registration and login with **bcrypt** password hashing.
- Stateless **JWT (HMAC-SHA256)** token authentication with configurable expiry.
- Strict multi-tenant isolation: every database query and vector retrieval operation is filtered by `user_id`. Users can never access or delete another user's documents or conversations.

### 2. Multi-Format Document Ingestion & Extraction
- **PDF Extraction:** Uses **PyMuPDF (`fitz`)** preserving exact physical page numbers.
- **DOCX Extraction:** Uses **`python-docx`** extracting text from paragraphs and structured tables.
- **TXT Extraction:** Native Python text handling supporting multiple character encodings (UTF-8, Latin-1, CP1252).
- **Scanned PDF Detection:** Heuristic engine detects image-only or scanned PDFs without readable text and provides clear warnings.
- **Validation:** Enforces configurable file size limits (default 15 MB), MIME types, and path traversal prevention.

### 3. Smart Chunking & Persistent Vector Storage
- Configurable sliding-window text chunker (default chunk size: 800 chars, overlap: 150 chars).
- Preserves rich metadata: `document_id`, `user_id`, `filename`, `page_number`, and `chunk_index`.
- Dense vector embeddings generated locally via **Sentence Transformers (`all-MiniLM-L6-v2`)**.
- Stored in persistent **ChromaDB** collections with cosine distance metric (`hnsw:space: cosine`).
- Deleting a document removes the database record, physical storage, and all associated vector embeddings.

### 4. Grounded RAG Question-Answering Pipeline
- **Strict Grounding:** The prompt instructs the LLM to answer *strictly* and *exclusively* based on the retrieved context chunks.
- **No Hallucinations:** When no relevant chunks meet the similarity threshold or documents lack evidence, the system explicitly states: *"I cannot find the answer to this question in the uploaded documents."*
- **Prompt Injection Defense:** Document excerpts are bounded inside `<context>` XML blocks and treated as untrusted reference data.
- **Source Citations:** Every answer includes the source filename, page number, similarity match percentage, and expandable text excerpts.
- **Unconfigured Mode Graceful Fallback:** If `OPENAI_API_KEY` is not provided, the pipeline executes full vector retrieval and outputs top document excerpts with citations.

### 5. Polished Modern Streamlit UI
- High-end SaaS dashboard aesthetic: soft-neutral palette (`#F8FAFC`), dark charcoal typography (`#0F172A`), and blue accent (`#2563EB`).
- User and Assistant message bubbles.
- Document management panel with processing status badges (`Ready`, `Warning`, `Failed`).
- Suggested starter questions upon document upload.
- Full conversation history persistence: reopen, continue, or delete prior chats.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Streamlit 1.66+ | Modern interactive web UI |
| **Backend API** | FastAPI 0.162+ | High-performance asynchronous REST API |
| **Server** | Uvicorn | ASGI web server |
| **Embeddings** | Sentence Transformers | Local dense vector embeddings (`all-MiniLM-L6-v2`) |
| **Vector DB** | ChromaDB 1.5+ | Persistent local vector database |
| **PDF Parser** | PyMuPDF (fitz) | High-speed PDF text and page extraction |
| **DOCX Parser** | python-docx | Word document text extraction |
| **Metadata DB** | SQLite + SQLAlchemy 2.0 | User accounts, document metadata, chat history |
| **Security** | PyJWT, bcrypt | JWT generation, verification, password hashing |
| **Validation** | Pydantic v2 & Pydantic-Settings | Request/response schemas & configuration |
| **Testing** | Pytest 9.2+, FastAPI TestClient | Comprehensive automated testing suite (35 tests) |
| **Deployment** | Docker & Docker Compose | Multi-container production deployment |

---

## 📁 Project Structure

```
ai-knowledge-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # Authentication endpoints (/api/auth)
│   │   │   ├── documents.py     # Document management endpoints (/api/documents)
│   │   │   ├── chat.py          # Chat & RAG endpoints (/api/chat)
│   │   │   ├── health.py        # Health diagnostics (/api/health)
│   │   │   └── deps.py          # JWT & DB dependency injection
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic BaseSettings
│   │   │   ├── security.py      # bcrypt hashing & PyJWT tokens
│   │   │   └── exceptions.py    # Custom HTTP exceptions
│   │   ├── database/
│   │   │   ├── base.py          # SQLAlchemy Base
│   │   │   └── session.py       # Engine, sessionmaker, SQLite PRAGMA
│   │   ├── models/
│   │   │   ├── user.py          # User SQL table
│   │   │   ├── document.py      # Document metadata SQL table
│   │   │   └── chat.py          # Conversation & ChatMessage SQL tables
│   │   ├── rag/
│   │   │   ├── extractors.py    # PDF, DOCX, TXT extraction & validation
│   │   │   ├── chunker.py       # Overlapping chunking engine
│   │   │   ├── embeddings.py    # Sentence Transformers singleton
│   │   │   ├── vector_store.py  # ChromaDB persistence & filtered search
│   │   │   └── pipeline.py      # End-to-end RAG QA pipeline
│   │   ├── schemas/
│   │   │   ├── auth.py          # Pydantic auth schemas
│   │   │   ├── document.py      # Pydantic document schemas
│   │   │   └── chat.py          # Pydantic chat & citation schemas
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   └── chat_service.py
│   │   └── main.py              # FastAPI app initialization & CORS
│   └── tests/
│       ├── conftest.py          # In-memory DB, temp Chroma, mocks
│       ├── test_auth.py         # Registration, login, JWT validation
│       ├── test_documents.py    # Uploads, deletion, cross-user isolation
│       ├── test_extractors.py   # PDF, DOCX, TXT, scanned detection
│       ├── test_chunker.py      # Overlapping chunks & metadata
│       ├── test_vector_store.py # Chroma search & user isolation
│       ├── test_rag_pipeline.py # Grounded QA & insufficient evidence
│       ├── test_chat_history.py # Conversations & message persistence
│       └── test_e2e.py          # End-to-end lifecycle verification
├── frontend/
│   ├── app.py                   # Streamlit entrypoint
│   ├── components/
│   │   ├── auth_ui.py           # Login & Registration cards
│   │   ├── chat_ui.py           # Message bubbles & expandable citations
│   │   ├── doc_ui.py            # Upload dropzone & document library
│   │   ├── dashboard_ui.py      # Metrics cards & system status
│   │   ├── history_ui.py        # Conversation browser & resume
│   │   ├── settings_ui.py       # Configuration inspector
│   │   └── sidebar.py           # Brand header, profile badge, nav
│   └── services/
│       └── api_client.py        # HTTP client for FastAPI backend
├── data/                        # Local file uploads and SQLite DB (git-ignored)
├── chroma_data/                 # Local persistent vector store (git-ignored)
├── .env.example                 # Sample configuration template
├── .gitignore                   # Ignore runtime data, caches, secrets
├── Dockerfile                   # Multi-stage container build
├── docker-compose.yml           # Backend + Frontend compose specification
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Python dependencies
├── run_backend.bat              # Windows batch runner for backend
├── run_frontend.bat             # Windows batch runner for frontend
├── start.py                     # Unified concurrent runner
└── README.md                    # Comprehensive documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-knowledge-assistant.git
cd ai-knowledge-assistant
```

### 2. Create and Activate Virtual Environment

Using `uv` (recommended for ultra-fast installs):
```bash
uv venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

Or using standard Python `venv`:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env     # Linux / macOS
copy .env.example .env   # Windows PowerShell / CMD
```

Edit `.env` to configure your settings:
```env
# Security (generate via: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=your-secure-jwt-secret-key-min-32-chars

# OpenAI API Key (optional for testing, required for full generative responses)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Database & Storage
DATABASE_URL=sqlite:///./data/app.db
CHROMA_PERSIST_DIRECTORY=./chroma_data
UPLOAD_DIR=./data/uploads

# Processing Parameters
MAX_UPLOAD_SIZE_MB=15
CHUNK_SIZE=800
CHUNK_OVERLAP=150
TOP_K_RETRIEVAL=4
SIMILARITY_THRESHOLD=0.35
```

---

## 🏃 Running the Application

### Option A: Unified Runner (Single Command)
Runs both the FastAPI backend (port 8000) and Streamlit frontend (port 8501) concurrently:
```bash
python start.py
```

### Option B: Separate Terminals (Manual)

**Terminal 1 — Backend API:**
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Interactive Swagger API documentation available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

**Terminal 2 — Frontend UI:**
```bash
streamlit run frontend/app.py --server.port 8501
```
*Web application available at: [http://127.0.0.1:8501](http://127.0.0.1:8501)*

### Option C: Windows Batch Scripts
- Double-click `run_backend.bat`
- Double-click `run_frontend.bat`

### Option D: Docker Compose
```bash
docker-compose up --build
```
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`

---

## 🧪 Automated Testing

The project includes 35 comprehensive automated tests covering all functional and security aspects.

### Running Tests
```bash
python -m pytest backend/tests -v
```

### Test Results Breakdown
```
backend/tests/test_auth.py::test_register_success PASSED
backend/tests/test_auth.py::test_register_duplicate_email PASSED
backend/tests/test_auth.py::test_register_duplicate_username PASSED
backend/tests/test_auth.py::test_login_success_with_username PASSED
backend/tests/test_auth.py::test_login_success_with_email PASSED
backend/tests/test_auth.py::test_login_invalid_password PASSED
backend/tests/test_auth.py::test_login_nonexistent_user PASSED
backend/tests/test_auth.py::test_protected_route_with_valid_token PASSED
backend/tests/test_auth.py::test_protected_route_without_token PASSED
backend/tests/test_auth.py::test_protected_route_with_invalid_token PASSED
backend/tests/test_chat_history.py::test_ask_creates_conversation_and_messages PASSED
backend/tests/test_chat_history.py::test_cross_user_conversation_isolation PASSED
backend/tests/test_chat_history.py::test_delete_conversation PASSED
backend/tests/test_chunker.py::test_chunker_overlap_validation PASSED
backend/tests/test_chunker.py::test_chunking_short_document PASSED
backend/tests/test_chunker.py::test_chunking_multipage_preserves_page_numbers PASSED
backend/tests/test_documents.py::test_upload_txt_document PASSED
backend/tests/test_documents.py::test_upload_empty_document PASSED
backend/tests/test_documents.py::test_upload_unsupported_extension PASSED
backend/tests/test_documents.py::test_list_and_get_document PASSED
backend/tests/test_documents.py::test_cross_user_document_isolation PASSED
backend/tests/test_documents.py::test_delete_document PASSED
backend/tests/test_e2e.py::test_health_check_endpoint PASSED
backend/tests/test_e2e.py::test_full_rag_lifecycle_e2e PASSED
backend/tests/test_extractors.py::test_normalize_text PASSED
backend/tests/test_extractors.py::test_extract_txt PASSED
backend/tests/test_extractors.py::test_extract_txt_empty PASSED
backend/tests/test_extractors.py::test_extract_docx PASSED
backend/tests/test_extractors.py::test_extract_pdf_multipage PASSED
backend/tests/test_extractors.py::test_extract_pdf_scanned_detection PASSED
backend/tests/test_extractors.py::test_validate_unsupported_extension PASSED
backend/tests/test_extractors.py::test_validate_nonexistent_file PASSED
backend/tests/test_rag_pipeline.py::test_rag_pipeline_with_mocked_llm PASSED
backend/tests/test_rag_pipeline.py::test_rag_pipeline_no_supporting_evidence PASSED
backend/tests/test_vector_store.py::test_vector_store_add_search_and_isolation PASSED

============================= 35 passed in 44s =============================
```

All test cases run deterministically without requiring a paid OpenAI API key using test fixtures and in-memory databases.

---

## 📡 API Endpoints Documentation

### Authentication
- `POST /api/auth/register`: Create a new user account.
  - Body: `{"username": "alex", "email": "alex@example.com", "password": "password123"}`
  - Response: `201 Created` with User object.
- `POST /api/auth/login`: Authenticate and obtain JWT token.
  - Body: `{"username_or_email": "alex", "password": "password123"}`
  - Response: `200 OK` with `{"access_token": "...", "token_type": "bearer", ...}`
- `GET /api/auth/me`: Get current authenticated user profile.

### Document Management
- `POST /api/documents/upload`: Upload file (multipart form data). Validates, chunks, embeds, and indexes into ChromaDB.
- `GET /api/documents`: List all documents belonging to the authenticated user.
- `GET /api/documents/{document_id}`: Retrieve metadata for a specific document.
- `DELETE /api/documents/{document_id}`: Delete document, local file, and ChromaDB vector embeddings.

### Chat & RAG QA
- `POST /api/chat/ask`: Submit question for grounded AI answer generation.
  - Body:
    ```json
    {
      "question": "What is the primary conclusion of the report?",
      "conversation_id": "optional-uuid",
      "document_ids": ["optional-doc-uuid"],
      "top_k": 4
    }
    ```
  - Response:
    ```json
    {
      "answer": "The primary conclusion is ...",
      "conversation_id": "conv-uuid",
      "message_id": "msg-uuid",
      "grounded": true,
      "sources": [
        {
          "document_id": "doc-uuid",
          "filename": "report.pdf",
          "page_number": 3,
          "chunk_index": 2,
          "excerpt": "Based on our experimental findings...",
          "score": 0.8842
        }
      ]
    }
    ```
- `GET /api/chat/history`: List all user conversations.
- `GET /api/chat/history/{conversation_id}`: Retrieve complete message history and citations.
- `DELETE /api/chat/history/{conversation_id}`: Delete a conversation and its messages.

### System Diagnostics
- `GET /api/health`: Health status checking SQLite connectivity, ChromaDB vector store readiness, and configured models.

---

## 🔒 Security Best Practices Implemented

1. **Password Security:** Hashed with bcrypt utilizing 12 rounds of salting. Plaintext passwords are never stored or logged.
2. **Multi-Tenant Isolation:** Every SQL query and ChromaDB retrieval query includes an explicit `user_id` constraint.
3. **Safe File Handling:** Filenames are sanitized, paths are generated using UUID prefixes in user-isolated directories, preventing path traversal attacks (`../`).
4. **Prompt Injection Defense:** User documents are treated as untrusted text. Context is encapsulated inside `<context>` boundaries with explicit instructions to disregard conflicting system directives found within document texts.
5. **No Secret Leaks:** Stack traces and secret keys are stripped from API error responses.
6. **CORS:** Configured explicitly to prevent cross-origin tampering.

---

## ⚖️ Limitations & Roadmap
- **OCR Integration:** Scanned PDFs are accurately detected via heuristic text density checks; integrating Tesseract or Surya OCR is a planned future enhancement.
- **Hybrid Retrieval:** Integrating BM25 keyword search alongside dense embeddings (Reciprocal Rank Fusion) for specialized technical jargon.
- **Reranker:** Cross-encoder reranker (e.g. `bge-reranker-base`) for even sharper top-k selection.

---

## 📄 License
MIT License. Free for enterprise and personal development.
