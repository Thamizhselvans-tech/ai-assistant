# Production Deployment Guide: AI Knowledge Assistant

This guide provides end-to-end instructions for deploying the **AI Knowledge Assistant** (FastAPI backend, Streamlit frontend, SQLite metadata database, and ChromaDB vector store) in production environments.

---

## 1. System Architecture Overview

```
                         ┌─────────────────────────────┐
                         │   Client (Browser / API)    │
                         └──────────────┬──────────────┘
                                        │ HTTPS (Port 443) / HTTP (Port 80)
                                        ▼
                         ┌─────────────────────────────┐
                         │   Reverse Proxy (Nginx /    │
                         │   Caddy with Let's Encrypt) │
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
                                        ┌─────────────────────┐
                                        │  Persistent Volumes │
                                        │ ├─ rag_sqlite_data  │
                                        │ ├─ rag_chroma_data  │
                                        │ └─ rag_model_cache  │
                                        └─────────────────────┘
```

- **Reverse Proxy**: Terminates TLS/SSL, handles WebSocket upgrades for Streamlit, enforces rate limits and max upload sizes (20MB).
- **Backend Container (`ai-knowledge-backend`)**: Python 3.12-slim executing Uvicorn with FastAPI, LangChain, PyMuPDF, python-docx, and ChromaDB. Runs as unprivileged user `appuser` (UID 1000).
- **Frontend Container (`ai-knowledge-frontend`)**: Python 3.12-slim running Streamlit UI, communicating internally with the backend via Docker network DNS (`http://backend:8000`).
- **Data Persistence**: Named Docker volumes ensure databases, vector embeddings, and cached ML models persist across restarts.

---

## 2. Host Requirements & Prerequisites

- **OS**: Ubuntu 22.04+ LTS, Debian 12+, RHEL 9+, or Windows Server with WSL2/Docker Desktop.
- **Hardware Minimums**:
  - CPU: 2 vCPUs (4 vCPUs recommended for batch document chunking & embeddings)
  - RAM: 4 GB minimum (8 GB recommended for local SentenceTransformers model inference)
  - Storage: 20 GB free SSD storage
- **Installed Software**:
  - [Docker Engine](https://docs.docker.com/engine/install/) (v24.0+)
  - [Docker Compose](https://docs.docker.com/compose/install/) (v2.20+)
  - Optional: Nginx or Caddy (if hosting reverse proxy on bare metal host)

---

## 3. Environment Setup & Secrets Generation

### Step 3.1: Generate Cryptographically Secure Secrets
Never use default development keys in production. Generate distinct high-entropy secrets for JWT authentication:

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate REFRESH_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3.2: Configure `.env.production`
Copy the production environment template and fill in your generated values:

```bash
cp .env.production .env
```

Ensure the following variables are configured:
```dotenv
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Paste generated 64-character hex strings
SECRET_KEY=paste_generated_secret_key_here
REFRESH_SECRET_KEY=paste_generated_refresh_key_here

# OpenAI API Key (or local LLM endpoint)
OPENAI_API_KEY=sk-proj-your-production-openai-key

# Production Frontend and Backend URLs
BACKEND_API_URL=http://backend:8000
FRONTEND_URL=https://rag.yourdomain.com
CORS_ORIGINS=["https://rag.yourdomain.com", "http://localhost:8501"]

# Storage Paths inside Containers
DATABASE_URL=sqlite:////app/data/app.db
CHROMA_PERSIST_DIRECTORY=/app/chroma_data
UPLOAD_DIR=/app/data/uploads

# Hugging Face Model Cache
HF_HOME=/home/appuser/.cache/huggingface
```

---

## 4. Docker Deployment

### Step 4.1: Build and Launch Containers
From the repository root directory:

```bash
# 1. Build optimized multi-stage images
docker compose build --no-cache

# 2. Launch containers in detached mode
docker compose up -d
```

### Step 4.2: Verify Container Health
Check the container status and health check results:

```bash
docker compose ps
```

Expected output:
```text
NAME                    IMAGE                         STATUS                    PORTS
ai-knowledge-backend    ai-knowledge-assistant:backend    Up (healthy) 127.0.0.1:8000->8000/tcp
ai-knowledge-frontend   ai-knowledge-assistant:frontend   Up (healthy) 127.0.0.1:8501->8501/tcp
```

### Step 4.3: Validate API and Frontend Endpoints
```bash
# Test backend health check
curl -f http://127.0.0.1:8000/api/health

# Test frontend HTTP status
curl -I http://127.0.0.1:8501/_stcore/health
```

---

## 5. Reverse Proxy & SSL/TLS Configuration

### Option A: Nginx with Let's Encrypt / Certbot (Recommended)

1. Copy the provided production Nginx configuration:
   ```bash
   sudo cp deploy/nginx/nginx.conf /etc/nginx/conf.d/ai_knowledge_assistant.conf
   ```
2. Edit `/etc/nginx/conf.d/ai_knowledge_assistant.conf` and update `server_name` with your actual domain (`rag.yourdomain.com`).
3. Obtain free SSL certificates using Certbot:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d rag.yourdomain.com
   ```
4. Test and reload Nginx:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

*Key Nginx Directives Included in `deploy/nginx/nginx.conf`:*
- `client_max_body_size 20M;` — Supports large multi-page PDF/DOCX uploads.
- `proxy_http_version 1.1;` with `Upgrade` and `Connection` headers — Ensures Streamlit WebSocket (`/_stcore/stream`) sessions do not disconnect.
- Rate limiting zones (`auth_limit` and `api_limit`) protecting auth endpoints against brute force attacks.

### Option B: Caddy (Automatic HTTPS)

1. Copy the Caddyfile:
   ```bash
   sudo cp deploy/caddy/Caddyfile /etc/caddy/Caddyfile
   ```
2. Replace `rag.yourdomain.com` with your domain.
3. Reload Caddy:
   ```bash
   sudo systemctl reload caddy
   ```

---

## 6. Bare Metal / Linux Systemd Deployment (Alternative to Docker)

If deploying directly onto a Linux VM without Docker:

1. Create a dedicated system user:
   ```bash
   sudo useradd -r -s /bin/false -d /opt/ai-knowledge-assistant appuser
   ```
2. Clone repository to `/opt/ai-knowledge-assistant` and set ownership:
   ```bash
   sudo chown -R appuser:appuser /opt/ai-knowledge-assistant
   ```
3. Create virtual environment and install dependencies:
   ```bash
   sudo -u appuser python3 -m venv /opt/ai-knowledge-assistant/.venv
   sudo -u appuser /opt/ai-knowledge-assistant/.venv/bin/pip install --upgrade pip
   sudo -u appuser /opt/ai-knowledge-assistant/.venv/bin/pip install -r requirements.txt
   ```
4. Install systemd services:
   ```bash
   sudo cp deploy/systemd/ai-knowledge-backend.service /etc/systemd/system/
   sudo cp deploy/systemd/ai-knowledge-frontend.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now ai-knowledge-backend ai-knowledge-frontend
   ```

---

## 7. Firewall & Security Hardening

Configure `ufw` to expose only public web ports:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```
*Never expose internal backend port 8000 or raw frontend port 8501 directly to the public internet.*

---

## 8. Operational Maintenance & Logs

- **Follow real-time backend logs**:
  ```bash
  docker compose logs -f backend
  ```
- **Follow real-time frontend logs**:
  ```bash
  docker compose logs -f frontend
  ```
- **Restart services gracefully**:
  ```bash
  docker compose restart
  ```
- **Graceful shutdown**:
  ```bash
  docker compose down
  ```
