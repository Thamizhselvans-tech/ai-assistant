# AI Knowledge Assistant – Docker Deployment & Containerization Report

**Target Docker Hub Account**: `thamizhprabha`  
**Frontend Image**: `thamizhprabha/ai-knowledge-frontend:latest`  
**Backend Image**: `thamizhprabha/ai-knowledge-backend:latest`  
**Docker Hub Profile**: [https://hub.docker.com/repositories/thamizhprabha](https://hub.docker.com/repositories/thamizhprabha)  
**Date**: November 9, 2026  
**Status**: Containerization & Configuration Complete – Verification Passed (132/132 tests)

---

## 1. Project Structure Inspected

A complete inspection of the project architecture and codebase was conducted prior to generating container configurations:

```
Ai-assistent/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI routers (auth, documents, chat, health, admin)
│   │   ├── core/
│   │   │   └── config.py         # Pydantic Settings (dynamic PORT, DATA_DIR, providers)
│   │   ├── database/             # SQLite SQLAlchemy engine, models, session
│   │   ├── models/               # ORM entities (User, Document, ChatSession, Message)
│   │   ├── rag/                  # RAG pipeline, retriever, embeddings, vector_store
│   │   ├── schemas/              # Pydantic DTOs for request/response validation
│   │   ├── services/             # LLM provider, multilingual detector, auth service
│   │   └── main.py               # Actual FastAPI application entry point
│   ├── tests/                    # 132 comprehensive Pytest test cases
│   ├── requirements.txt          # Dedicated backend dependency manifest
│   ├── .dockerignore             # Context exclusions for backend image
│   └── Dockerfile                # Dedicated FastAPI multi-stage production Dockerfile
├── frontend/
│   ├── assets/                   # Static assets, branding logos, icons
│   ├── components/               # Modular UI components
│   │   ├── chat_composer/        # Custom Streamlit component (HTML/JS + Python)
│   │   ├── admin_ui.py           # Admin panel & system telemetry
│   │   ├── auth_ui.py            # Authentication & session controls
│   │   ├── chat_ui.py            # Chat interface & real-time streaming
│   │   ├── citation_viewer.py    # Source citation expanders
│   │   ├── dashboard_ui.py       # Metrics & analytics view
│   │   ├── doc_ui.py             # Document library view
│   │   ├── sidebar.py            # Obsidian Emerald navigation sidebar
│   │   └── upload_component.py   # Multi-file drag-and-drop upload
│   ├── styles/
│   │   └── custom.css            # Dark Obsidian & Emerald Green design system
│   ├── app.py                    # Actual Streamlit application entry point
│   ├── auth.py                   # Client session state & JWT auth guards
│   ├── api_client.py             # Centralized HTTP client to FastAPI backend
│   ├── config.py                 # URL resolution, theme definitions
│   ├── requirements.txt          # Dedicated frontend dependency manifest
│   ├── .dockerignore             # Context exclusions for frontend image
│   └── Dockerfile                # Dedicated Streamlit multi-stage production Dockerfile
├── chroma_data/                  # Runtime ChromaDB vector store persistence directory
├── data/                         # Runtime SQLite database (app.db) and document uploads
├── docker-compose.yml            # Multi-service composition (frontend + backend)
├── .dockerignore                 # Root Docker ignore exclusions
├── .env.example                  # Environment configuration template with safe placeholders
├── requirements-backend.txt      # Root backend dependencies reference
└── requirements-frontend.txt     # Root frontend dependencies reference
```

### Key Components Identified:
1. **Actual Streamlit Entrypoint**: `frontend/app.py` (executed via `streamlit run frontend/app.py`).
2. **Actual FastAPI Entrypoint**: `backend/app/main.py` (`app = FastAPI(...)`, exposed as `backend.app.main:app`).
3. **Database & Storage Directories**:
   - SQLite Database: Anchored to `/app/data/app.db` (configurable via `DATABASE_URL` and `DATA_DIR`).
   - ChromaDB Vector Store: Anchored to `/app/chroma_data` (configurable via `CHROMA_PERSIST_DIRECTORY`).
   - Document Uploads: Anchored to `/app/data/uploads` (configurable via `UPLOAD_DIR`).
4. **Custom Streamlit Components**:
   - `frontend/components/chat_composer`: First-party bi-directional Streamlit component (`index.html` + `__init__.py`) supporting inline document attachment without triggering submission, Web Speech API microphone speech recognition for Tamil and English, dynamic multiline message textarea with character counter, and send button.
   - `frontend/styles/custom.css`: Emerald Dark theme styling injected at runtime.
5. **Multilingual Detection**:
   - Automatic Tamil, English, and Tanglish detection managed by `backend/app/services/language_detector.py` and `language_service.py`.

---

## 2. Dockerfiles Created

### A. Frontend Dockerfile (`frontend/Dockerfile`)
- **Base Image**: `python:3.12-slim` (Multi-stage build).
- **Security**: Runs under dedicated least-privilege non-root user `appuser` (UID 1000).
- **Network**: Binds Streamlit to `0.0.0.0`.
- **Dynamic Port**: Supports `PORT` environment variable with default fallback to `8080`.
- **Telemetry**: Disabled via `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` and `STREAMLIT_SERVER_HEADLESS=true`.
- **Healthcheck**: Validates `curl -f http://localhost:${PORT:-8080}/_stcore/health`.
- **Packaging**: Includes all required frontend assets, styles, and the custom `chat_composer` component.

### B. Backend Dockerfile (`backend/Dockerfile`)
- **Base Image**: `python:3.12-slim` (Multi-stage build).
- **Security**: Runs under dedicated least-privilege non-root user `appuser` (UID 1000).
- **Runtime**: Runs FastAPI via `uvicorn backend.app.main:app` with 2 worker processes.
- **Network**: Binds Uvicorn to `0.0.0.0`.
- **Dynamic Port**: Fully supports `PORT` environment variable with default fallback to `8080`.
- **Storage Initialization**: Creates `/app/data/uploads`, `/app/chroma_data`, and `/home/appuser/.cache` with proper permissions.
- **Healthcheck**: Validates `curl -f http://localhost:${PORT:-8080}/health`.

---

## 3. Docker Ignore Configuration

Created strict `.dockerignore` files at:
- `backend/.dockerignore`
- `frontend/.dockerignore`
- `.dockerignore` (project root)

**Excluded Items**:
- Environment files: `.env`, `.env.*`, `secrets.toml`, `.streamlit/secrets.toml`
- Cloud credentials: `*service-account*.json`, `*firebase*.json`, `*-adminsdk-*.json`
- Virtual environments: `.venv/`, `venv/`, `env/`
- Bytecode & cache: `__pycache__/`, `*.py[cod]`, `.pytest_cache/`
- Runtime storage: `data/`, `chroma_data/`, `*.db`, `*.sqlite`, `*.sqlite3`, `uploads/`
- Temporary & log files: `*.log`, `logs/`, `*.tmp`, `*.swp`
- Version control: `.git/`, `.gitignore`

---

## 4. Docker Compose Configuration (`docker-compose.yml`)

The multi-container composition orchestrates frontend and backend services:

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: thamizhprabha/ai-knowledge-backend:latest
    container_name: ai_knowledge_backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - API_PORT=8000
      - API_HOST=0.0.0.0
      - APP_ENV=production
      - DEBUG=False
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-insecure_dev_secret_key_change_in_production_32chars}
      - JWT_ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=1440
      - REFRESH_TOKEN_EXPIRE_DAYS=7
      - DATA_DIR=/app/data
      - DATABASE_URL=sqlite:////app/data/app.db
      - CHROMA_PERSIST_DIRECTORY=/app/chroma_data
      - CHROMA_COLLECTION_NAME=ai_knowledge_assistant
      - UPLOAD_DIR=/app/data/uploads
      - MAX_UPLOAD_SIZE_MB=15
      - EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
      - LOW_RAM_MODE=True
      - EMBEDDING_BATCH_SIZE=16
      - TORCH_NUM_THREADS=2
      - AI_PROVIDER=${AI_PROVIDER:-gemini}
      - LLM_PROVIDER=${LLM_PROVIDER:-gemini}
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      - GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.5-flash-lite}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://api.openai.com/v1}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
      - GROQ_API_KEY=${GROQ_API_KEY:-}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
      - CORS_ORIGINS=${CORS_ORIGINS:-*}
    volumes:
      - rag_sqlite_data:/app/data
      - rag_chroma_data:/app/chroma_data
      - rag_model_cache:/home/appuser/.cache
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - rag_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: thamizhprabha/ai-knowledge-frontend:latest
    container_name: ai_knowledge_frontend
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - PORT=8501
      - BACKEND_API_URL=http://backend:8000
      - API_BASE_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - rag_network

volumes:
  rag_sqlite_data:
    name: rag_sqlite_data
  rag_chroma_data:
    name: rag_chroma_data
  rag_model_cache:
    name: rag_model_cache

networks:
  rag_network:
    driver: bridge
```

---

## 5. Local Testing & Verification Results

The entire Pytest test suite was executed against the project codebase:

```bash
python -m pytest backend/tests
```

**Results**:
- **132 passed / 132 tests (100% pass rate)**
- **Verification categories**:
  - `test_auth.py` (10 passed): User registration, duplicate detection, password hashing, JWT issue & validation.
  - `test_chat_history.py` (3 passed): Session isolation, message history pagination, multi-turn tracking.
  - `test_chunker.py` (3 passed): Recursive text splitting, token preservation, chunk overlap.
  - `test_composer_full_suite.py` (15 passed): Chat composer UI controls, multi-language speech, attachment handling.
  - `test_composer_upload.py` (9 passed): Document attachment upload pipeline via multipart form.
  - `test_deployment_preparation.py` (15 passed): FastAPI lifespan, `/health` and `/api/health` endpoints, dynamic `PORT`, persistent disk mount anchoring, CORS wildcard and regex matching.
  - `test_documents.py` (6 passed): Document upload, duplicate detection, deletion, metadata retrieval.
  - `test_e2e.py` (2 passed): Complete end-to-end user query and citation pipeline.
  - `test_extractors.py` (8 passed): PDF (PyMuPDF), DOCX (python-docx), and plain TXT extraction.
  - `test_frontend_integration.py` (6 passed): Dynamic backend URL resolution via env & `st.secrets`, API client error recovery.
  - `test_gemini_provider.py` (8 passed): Google GenAI SDK integration, prompt formatting, model fallback.
  - `test_low_ram_optimization.py` (7 passed): RAM budgeting, single-threaded PyTorch execution, batch processing.
  - `test_multilingual_detection.py` (11 passed): Automatic Tamil (தமிழ்), English, and Tanglish detection and prompt routing.
  - `test_persistence_lifecycle.py` (1 passed): Database and ChromaDB persistence verification across restarts.
  - `test_phase2_rag.py` (11 passed): ChromaDB similarity search, threshold filtering, citation building.
  - `test_phase3_api.py` (9 passed): REST API contracts, authentication headers, schema validation.
  - `test_rag_pipeline.py` (2 passed): Grounded answer generation and fallback answers.
  - `test_url_detection.py` (5 passed): URL and web reference extraction.
  - `test_vector_store.py` (1 passed): Vector collection management and index stability.

---

## 6. Build Commands

To build the images locally:

```bash
# Build Frontend Image
docker build -t thamizhprabha/ai-knowledge-frontend:latest ./frontend

# Build Backend Image
docker build -t thamizhprabha/ai-knowledge-backend:latest ./backend
```

To run both services locally with Docker Compose:

```bash
docker compose up --build
```

**Access Endpoints**:
- Frontend UI: [http://localhost:8501](http://localhost:8501)
- Backend OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Backend Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 7. Push to Docker Hub Instructions

### A. Prerequisites on Docker Hub
Ensure the following repositories are created in your Docker Hub account:
1. `thamizhprabha/ai-knowledge-frontend`
2. `thamizhprabha/ai-knowledge-backend`

*If they do not exist yet:*
1. Navigate to [https://hub.docker.com/repository/create](https://hub.docker.com/repository/create).
2. Set **Namespace** to `thamizhprabha`.
3. Set **Repository Name** to `ai-knowledge-frontend` (select Public or Private). Click **Create**.
4. Repeat for `ai-knowledge-backend`.

### B. Authenticate with Docker Hub
In your terminal, log in securely:

```bash
docker login
```
*(Enter your Docker Hub username `thamizhprabha` and Personal Access Token or password when prompted by Docker CLI).*

### C. Push Images
Once authenticated:

```bash
# Push Frontend Image
docker push thamizhprabha/ai-knowledge-frontend:latest

# Push Backend Image
docker push thamizhprabha/ai-knowledge-backend:latest
```

### D. Verify Pushed Images
Verify locally:
```bash
docker images | grep thamizhprabha
```

View on Docker Hub:
- Frontend: [https://hub.docker.com/r/thamizhprabha/ai-knowledge-frontend](https://hub.docker.com/r/thamizhprabha/ai-knowledge-frontend)
- Backend: [https://hub.docker.com/r/thamizhprabha/ai-knowledge-backend](https://hub.docker.com/r/thamizhprabha/ai-knowledge-backend)

---

## 8. Environment Variables Guide

Copy `.env.example` to `.env` or set these in your cloud container platform (e.g., Render, Railway, Cloud Run):

| Variable | Recommended / Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8080` (or `8000` / `8501`) | Listening container port |
| `APP_ENV` | `production` | Runtime mode (`production` disables dev banners) |
| `DEBUG` | `False` | Disables debug stack traces in production |
| `JWT_SECRET_KEY` | *Cryptographic 32+ hex string* | Secret key for JWT signing |
| `DATABASE_URL` | `sqlite:////app/data/app.db` | SQLite database file location |
| `CHROMA_PERSIST_DIRECTORY` | `/app/chroma_data` | Persistent ChromaDB storage |
| `UPLOAD_DIR` | `/app/data/uploads` | Document upload directory |
| `AI_PROVIDER` | `gemini` | Primary LLM provider (`gemini`, `openai`, `groq`) |
| `GEMINI_API_KEY` | *Your Gemini API Key* | API key for Google Gemini |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Gemini model variant |
| `OPENAI_API_KEY` | *Your OpenAI Key (optional)* | API key for OpenAI fallback |
| `BACKEND_API_URL` | `http://backend:8000` | Backend URL used by frontend |

---

## 9. Deployment Limitations & Architectural Notes

1. **Volume Persistence**:
   - Both SQLite (`/app/data`) and ChromaDB (`/app/chroma_data`) store persistent state on disk.
   - When deploying to production cloud platforms (e.g. Render, Railway, AWS ECS), ensure persistent disk volumes are mounted to `/app/data` and `/app/chroma_data` to preserve user accounts, documents, and vector embeddings across container restarts.
2. **Embedding Model Memory Footprint**:
   - The backend runs `sentence-transformers/all-MiniLM-L6-v2` locally inside the container (~90MB model size, ~250MB RAM footprint).
   - `LOW_RAM_MODE=True` and `TORCH_NUM_THREADS=2` ensure it operates comfortably within standard 512MB–1GB container RAM limits.
3. **Independent Scalability**:
   - The frontend and backend images are decoupled. The frontend container can be scaled horizontally or hosted separately (e.g., Streamlit Community Cloud) by pointing `BACKEND_API_URL` to the backend public URL.
