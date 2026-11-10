# 🧠 AI Knowledge Assistant – Full-Stack RAG Application

[![Docker Hub Backend](https://img.shields.io/badge/Docker%20Hub-Backend%20Image-blue?logo=docker)](https://hub.docker.com/r/thamizhprabha/ai-knowledge-backend)
[![Docker Hub Frontend](https://img.shields.io/badge/Docker%20Hub-Frontend%20Image-blue?logo=docker)](https://hub.docker.com/r/thamizhprabha/ai-knowledge-frontend)
[![Tests](https://img.shields.io/badge/Tests-132%2F132%20Passed%20(100%25)-success)](https://github.com/Thamizhselvans-tech/ai-assistant)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)

An enterprise-grade, production-minded **Retrieval-Augmented Generation (RAG)** application. It empowers users to upload documents (PDF, DOCX, TXT), perform semantic similarity search against local vector embeddings, ask questions in natural language, and receive factually grounded answers with source citations and page-level references.

### 🐳 Published Official Docker Images
- **Backend Image**: [`thamizhprabha/ai-knowledge-backend:latest`](https://hub.docker.com/r/thamizhprabha/ai-knowledge-backend)
- **Frontend Image**: [`thamizhprabha/ai-knowledge-frontend:latest`](https://hub.docker.com/r/thamizhprabha/ai-knowledge-frontend)
- **Docker Hub Profile**: [hub.docker.com/repositories/thamizhprabha](https://hub.docker.com/repositories/thamizhprabha)

---

## 🏛️ System Architecture

```
                         ┌─────────────────────────────┐
                         │   Client (Browser / API)    │
                         └──────────────┬──────────────┘
                                        │ HTTPS (Port 443) / HTTP (Port 80)
                                        ▼
                         ┌─────────────────────────────┐
                         │   Reverse Proxy (Nginx /    │
                         │   Caddy with TLS & WSS)     │
                         └──────┬───────────────┬──────┘
                                │               │
          Streamlit WebSockets  │               │ REST API / Auth / Uploads
          & Static UI (8501)    ▼               ▼
                   ┌─────────────────┐    ┌─────────────────┐
                   │    Frontend     │    │     Backend     │
                   │ (Streamlit App) │───>│ (FastAPI & RAG) │
                   └─────────────────┘    └────────┬────────┘
                                                   │
                                                   ▼
                         ┌───────────────────────────────────────────┐
                         │             Persistent Stores             │
                         │ ├─ rag_sqlite_data: Users, Chats, Docs   │
                         │ ├─ rag_chroma_data: ChromaDB Vectors      │
                         │ └─ rag_model_cache: Embedding Model Cache │
                         └───────────────────────────────────────────┘
```

---

## 🚀 Key Features

### 1. Secure Authentication & Role-Based Access Control
- User registration and login with **bcrypt** password hashing.
- Dual-token stateless authentication: short-lived **JWT access tokens** (30 min) and long-lived **refresh tokens** (7 days).
- **Role-Based Access Control (RBAC)**: Support for regular `user` and `admin` roles.
- Dedicated admin portal (`/api/admin/*` and `pages/5_Admin.py`) for system health audits, user listing, and system-wide document inspection.
- Multi-tenant isolation: every database query and ChromaDB retrieval query is strictly scoped by `user_id`.

### 2. Multi-Format Document Ingestion & Extraction
- **PDF Extraction:** Uses **PyMuPDF (`fitz`)** preserving exact physical page numbers.
- **DOCX Extraction:** Uses **`python-docx`** extracting text from paragraphs and structured tables.
- **TXT Extraction:** Native Python text handling supporting multiple character encodings (UTF-8, Latin-1, CP1252).
- **Scanned PDF Detection:** Heuristic engine detects image-only or scanned PDFs without readable text and provides actionable warnings.
- **Validation:** Strict MIME validation, extension whitelisting, and configurable file size limits (default 15 MB).

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

### 5. Multi-Page Streamlit Frontend
- High-end SaaS dashboard aesthetic: soft-neutral palette (`#F8FAFC`), dark charcoal typography (`#0F172A`), and blue accent (`#2563EB`).
- Multi-page navigation:
  - `1_Dashboard.py`: Live stats (total documents, chunks, conversations), quick actions, and recent activity.
  - `2_Documents.py`: File uploader dropzone, multi-format card browser, chunk count, and deletion.
  - `3_AI_Chat.py`: Modern conversational chat interface with citations and similarity scores.
  - `4_Chat_History.py`: Historical thread browser to resume or purge past conversations.
  - `5_Admin.py`: Administrative diagnostics, registered user overview, and system health status.
  - `6_Settings.py`: Model parameter inspector and session configuration.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Streamlit 1.42+ | Multi-page modern interactive web UI |
| **Backend API** | FastAPI 0.115+ | High-performance asynchronous REST API |
| **Server** | Uvicorn | ASGI web server |
| **Embeddings** | Sentence Transformers | Local dense vector embeddings (`all-MiniLM-L6-v2`) |
| **Vector DB** | ChromaDB 0.6+ | Persistent local vector database |
| **PDF Parser** | PyMuPDF (fitz) | High-speed PDF text and page extraction |
| **DOCX Parser** | python-docx | Word document and table text extraction |
| **Metadata DB** | SQLite + SQLAlchemy 2.0 | User accounts, document metadata, chat history |
| **Security** | PyJWT, Passlib, bcrypt | Dual JWT generation, verification, password hashing |
| **Validation** | Pydantic v2 & Pydantic-Settings | Request/response schemas & configuration |
| **Testing** | Pytest 9.2+, FastAPI TestClient | Comprehensive automated testing suite (62 tests) |
| **Deployment** | Docker & Docker Compose | Multi-stage production containerization |
| **Reverse Proxy** | Nginx / Caddy | TLS/SSL termination & WebSocket upgrades |

---

## 📁 Project Structure

```
ai-knowledge-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── admin.py             # Administrative audit endpoints (/api/admin)
│   │   │   ├── auth.py              # Authentication endpoints (/api/auth)
│   │   │   ├── documents.py         # Document management endpoints (/api/documents)
│   │   │   ├── chat.py              # Chat & RAG QA endpoints (/api/chat)
│   │   │   ├── health.py            # Health diagnostics (/api/health)
│   │   │   └── deps.py              # JWT, user, admin & DB dependency injection
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings
│   │   │   ├── security.py          # Bcrypt hashing & PyJWT token handling
│   │   │   └── exceptions.py        # Custom HTTP exceptions
│   │   ├── database/
│   │   │   ├── base.py              # SQLAlchemy Base
│   │   │   └── session.py           # Engine, sessionmaker, SQLite PRAGMA
│   │   ├── models/
│   │   │   ├── user.py              # User SQL table (role, admin flag)
│   │   │   ├── document.py          # Document metadata SQL table
│   │   │   └── chat.py              # Conversation, Message & Citation SQL tables
│   │   ├── rag/
│   │   │   ├── extractors.py        # PDF, DOCX, TXT extraction & validation
│   │   │   ├── document_loader.py   # Page-level loader & scanner detection
│   │   │   ├── chunker.py           # Overlapping chunking engine
│   │   │   ├── text_splitter.py     # Recursive text splitter adapter
│   │   │   ├── embeddings.py        # Sentence Transformers singleton
│   │   │   ├── vector_store.py      # ChromaDB persistence & filtered search
│   │   │   ├── retriever.py         # Semantic retriever with score thresholding
│   │   │   ├── prompts.py           # System prompts & injection defense
│   │   │   └── pipeline.py          # End-to-end grounded RAG QA pipeline
│   │   ├── schemas/
│   │   │   ├── auth.py              # Pydantic auth schemas
│   │   │   ├── document.py          # Pydantic document schemas
│   │   │   └── chat.py              # Pydantic chat & citation schemas
│   │   ├── services/
│   │   │   ├── auth_service.py      # User authentication & token management
│   │   │   ├── document_service.py  # Document storage & pipeline orchestration
│   │   │   └── chat_service.py      # Chat history, RAG generation & citations
│   │   └── main.py                  # FastAPI app initialization, routes & CORS
│   └── tests/
│       ├── conftest.py              # In-memory DB, temp Chroma, mocks
│       ├── test_auth.py             # Registration, login, JWT validation
│       ├── test_documents.py        # Uploads, deletion, cross-user isolation
│       ├── test_extractors.py       # PDF, DOCX, TXT, scanned detection
│       ├── test_chunker.py          # Overlapping chunks & metadata
│       ├── test_vector_store.py     # Chroma search & user isolation
│       ├── test_rag_pipeline.py     # Grounded QA & insufficient evidence
│       ├── test_chat_history.py     # Conversations & message persistence
│       ├── test_phase2_rag.py       # Comprehensive RAG pipeline tests
│       ├── test_phase3_api.py       # Refresh tokens, admin endpoints, pagination
│       ├── test_frontend_integration.py # Streamlit config & client mocks
│       ├── test_persistence_lifecycle.py # Cold restart persistence tests
│       └── test_e2e.py              # Full end-to-end integration lifecycle
├── frontend/
│   ├── app.py                       # Streamlit entrypoint & router
│   ├── config.py                    # Constants, styling, API URLs
│   ├── auth.py                      # Session state authentication controller
│   ├── api_client.py                # Typed HTTP client for FastAPI backend
│   ├── components/
│   │   ├── header.py                # Top navbar & user status
│   │   ├── sidebar.py               # Sidebar navigation & quick actions
│   │   ├── metrics_cards.py         # Dashboard KPI metric cards
│   │   ├── document_card.py         # Document card component & actions
│   │   ├── chat_message.py          # Chat bubbles (user & assistant)
│   │   ├── citation_viewer.py       # Expandable citation references
│   │   ├── upload_component.py      # Drag-and-drop file uploader
│   │   └── loading.py               # Spinners & loading placeholders
│   ├── pages/
│   │   ├── 1_Dashboard.py           # Dashboard overview page
│   │   ├── 2_Documents.py           # Document library & upload page
│   │   ├── 3_AI_Chat.py             # Active conversational RAG chat
│   │   ├── 4_Chat_History.py        # Conversation threads browser
│   │   ├── 5_Admin.py               # Admin diagnostics & system status
│   │   └── 6_Settings.py            # User settings & configuration
│   └── styles/
│       └── custom.css               # Clean SaaS design stylesheet
├── deploy/
│   ├── nginx/nginx.conf             # Production Nginx config (TLS + WebSockets)
│   ├── caddy/Caddyfile              # Production Caddyfile (Automatic TLS)
│   └── systemd/                     # Systemd service units (Backend & Frontend)
├── Dockerfile                       # Multi-stage production container build
├── docker-compose.yml               # Production Compose stack with persistent volumes
├── .dockerignore                    # Build optimization exclusions
├── .env.example                     # Development environment template
├── .env.production                  # Production environment template
├── PRODUCTION_DEPLOYMENT.md         # Full deployment and reverse proxy guide
├── BACKUP_RECOVERY.md               # Backup, volume snapshot & disaster recovery runbook
├── PHASE_1_REPORT.md                # Phase 1 verification report
├── PHASE_2_REPORT.md                # Phase 2 verification report
├── PHASE_3_REPORT.md                # Phase 3 verification report
├── PHASE_4_REPORT.md                # Phase 4 verification report
├── PHASE_5_REPORT.md                # Phase 5 verification report
├── pytest.ini                       # Pytest configuration
├── requirements.txt                 # Pinned dependencies
├── run_backend.bat                  # Windows batch runner for backend
├── run_frontend.bat                 # Windows batch runner for frontend
└── start.py                         # Unified runner for concurrent execution
```

---

## ⚙️ Installation & Quickstart

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-knowledge-assistant.git
cd ai-knowledge-assistant
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate
# Activate on Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env     # Linux / macOS
copy .env.example .env   # Windows
```

---

## 🏃 Running the Application

### Option A: Pre-built Docker Hub Images (Zero-Setup / Recommended)
Pull and run the pre-built, production-ready images directly from Docker Hub without building locally:

```bash
# Pull images directly
docker pull thamizhprabha/ai-knowledge-backend:latest
docker pull thamizhprabha/ai-knowledge-frontend:latest

# Run with docker compose
docker compose up -d
```
- Web Application: `http://localhost:8501`
- Backend API Docs: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

#### 📦 One-Click Windows Distribution Scripts
If running on Windows with Docker Desktop installed:
- **`start.bat`**: Detects Docker daemon, verifies `.env`, pulls latest images, boots services, and opens the browser.
- **`stop.bat`**: Gracefully stops all containers while preserving SQLite and ChromaDB vector volumes.
- **`restart.bat`**: Seamlessly restarts frontend and backend services.
- **`backup.bat`**: Creates timestamped local backups of SQLite database and vector embeddings.
- **`AI-Knowledge-Assistant-Installer.zip`**: Portable standalone ZIP containing all runner scripts and configuration templates for zero-code distribution to end users.

### Option B: Unified Concurrent Runner (Local Python Dev)
Runs both the FastAPI backend (`:8000`) and Streamlit frontend (`:8501`) together:
```bash
python start.py
```

### Option C: Build from Source with Docker Compose
```bash
# 1. Setup production environment
cp .env.production .env

# 2. Build and launch containers
docker compose up -d --build
```
- Detailed production guide: [PRODUCTION_DEPLOYMENT.md](file:///C:/Users/kgoku/OneDrive/Documents/Ai-assistent/PRODUCTION_DEPLOYMENT.md)

---

## 🧪 Automated Testing

The project is backed by **132 comprehensive automated tests** with 100% pass rate:

```bash
.venv\Scripts\python -m pytest backend/tests -v
```

### Test Coverage Highlights:
- **Authentication (`test_auth.py`)**: 10 tests passing (Registration, Bcrypt password verification, duplicate checking, JWT token rotation, protected routes).
- **RAG Document Extraction (`test_extractors.py`, `test_phase2_rag.py`)**: Multi-page PDF text extraction with exact page numbers, scanned PDF heuristic detection, DOCX paragraphs and tables, UTF-8/Latin-1 TXT encodings.
- **Chunking & Embeddings (`test_chunker.py`, `test_phase2_rag.py`)**: Overlapping chunk validation, token preservation, Sentence Transformers 384-dimensional vectors.
- **Vector Search & Persistence (`test_vector_store.py`, `test_persistence_lifecycle.py`)**: ChromaDB persistent storage, multi-tenant user isolation, cold restart survival test.
- **FastAPI Endpoints (`test_phase3_api.py`, `test_deployment_preparation.py`)**: Refresh token flows, dynamic PORT binding, CORS validation, document lifecycles, chat query pagination.
- **Gemini & Multi-Provider LLM (`test_gemini_provider.py`)**: Google GenAI integration, fallback grounding, strict citation schema validation.
- **Multilingual Support (`test_multilingual_detection.py`)**: Automatic language identification and handling for English, Tamil, and Tanglish.
- **Composer & Voice UI (`test_composer_full_suite.py`, `test_composer_upload.py`)**: Streamlit chat input composer, attachment uploads, browser speech recognition.
- **Low-RAM Architecture (`test_low_ram_optimization.py`)**: Single-threaded PyTorch, batch-size limiting, optimized memory footprint for 4GB RAM targets.
- **End-to-End Pipeline (`test_e2e.py`)**: Full document upload ➔ embedding ➔ question asking ➔ citation extraction lifecycle.

---

## 📡 API Reference

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### Authentication
- `POST /api/auth/register`: Create a new user account.
- `POST /api/auth/login`: Authenticate and obtain JWT access and refresh tokens.
- `POST /api/auth/refresh`: Refresh expired access token using refresh token.
- `GET /api/auth/me`: Get current authenticated user profile.

### Document Management
- `POST /api/documents/upload`: Upload PDF, DOCX, or TXT file. Validates, chunks, embeds, and indexes into ChromaDB.
- `GET /api/documents`: List all documents belonging to current user.
- `GET /api/documents/{document_id}`: Retrieve metadata for a specific document.
- `DELETE /api/documents/{document_id}`: Delete document, source file, and all associated ChromaDB vector embeddings.

### Chat & Grounded QA
- `POST /api/chat/ask`: Submit query for grounded AI answer generation with citations.
- `GET /api/chat/history`: List conversations for current user with pagination.
- `GET /api/chat/history/{conversation_id}`: Retrieve message history and source citations.
- `DELETE /api/chat/history/{conversation_id}`: Delete conversation thread.

### Administration & Diagnostics
- `GET /api/admin/users`: List all registered users (Admin only).
- `GET /api/admin/documents`: List system-wide documents across all users (Admin only).
- `GET /api/admin/health`: Detailed system diagnostics and database statistics (Admin only).
- `GET /api/health`: Public system health check.

---

## 🔒 Production Security & Disaster Recovery

- **Zero Hardcoded Secrets**: Secrets loaded via environment variables; high-entropy tokens generated using `secrets.token_hex(32)`.
- **Atomic Database Backups**: Live online SQLite backup via `sqlite3 .backup` without locking issues.
- **Disaster Recovery**: Step-by-step restoration procedures for SQLite and ChromaDB detailed in [BACKUP_RECOVERY.md](file:///C:/Users/kgoku/OneDrive/Documents/Ai-assistent/BACKUP_RECOVERY.md).
- **Reverse Proxy Protection**: Production Nginx configuration with rate-limiting, SSL termination, and WebSocket upgrade support in [deploy/nginx/nginx.conf](file:///C:/Users/kgoku/OneDrive/Documents/Ai-assistent/deploy/nginx/nginx.conf).

---

## 📄 License
MIT License. Free for enterprise and personal development.
