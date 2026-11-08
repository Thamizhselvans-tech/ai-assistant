# Production Deployment Guide: AI Knowledge Assistant

This guide walks you through deploying the **AI Knowledge Assistant** to production:
- **Backend API:** FastAPI on [Render](https://render.com)
- **Frontend UI:** Streamlit on [Streamlit Community Cloud](https://share.streamlit.io)
- **Source Code Repository:** [GitHub - Thamizhselvans-tech/ai-assistant](https://github.com/Thamizhselvans-tech/ai-assistant)

---

## Architecture Overview

```
                      ┌─────────────────────────────────────────┐
                      │        Streamlit Community Cloud        │
                      │               (Frontend)                │
                      │         Entrypoint: frontend/app.py     │
                      │         Lightweight (~30s build)        │
                      └────────────────────┬────────────────────┘
                                           │
                                  HTTPS Requests (REST)
                                   + Bearer JWT Tokens
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │              Render.com                 │
                      │            (FastAPI Backend)            │
                      │    uvicorn backend.app.main:app:8000    │
                      ├─────────────────────────────────────────┤
                      │  • JWT Authentication                   │
                      │  • PyMuPDF / python-docx Parsing        │
                      │  • Sentence Transformers Embeddings     │
                      │  • SQLite User & History Database       │
                      │  • ChromaDB Cosine Vector Store         │
                      │  • Google Gemini / OpenAI Cloud LLM     │
                      └────────────────────┬────────────────────┘
                                           │
                                  Mounted Storage
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │         Render Persistent Disk          │
                      │         (or default ./data)             │
                      │     /var/data/app.db (SQLite)           │
                      │     /var/data/chroma_data (ChromaDB)    │
                      │     /var/data/uploads (Raw Files)       │
                      └─────────────────────────────────────────┘
```

---

## Step 1: Push Latest Changes to GitHub

Ensure all deployment preparation files are committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "chore: prepare for Render and Streamlit Cloud production deployment"
git push origin main
```

---

## Step 2: Deploy Backend to Render

### Option A: Using Render Blueprints (`render.yaml`) – Recommended

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **Blueprints** in the top navigation -> Click **New Blueprint Instance**.
3. Connect your GitHub repository: `Thamizhselvans-tech/ai-assistant`.
4. Render will automatically detect [`render.yaml`](./render.yaml).
5. In the environment configuration, enter your **`GEMINI_API_KEY`** (or `OPENAI_API_KEY`).
6. Click **Apply**. Render will build and deploy the backend service automatically.

---

### Option B: Manual Web Service Setup on Render

1. On [Render Dashboard](https://dashboard.render.com), click **New +** -> **Web Service**.
2. Connect your GitHub repository `Thamizhselvans-tech/ai-assistant`.
3. Configure the service settings:

| Field | Setting |
| :--- | :--- |
| **Name** | `ai-knowledge-assistant-backend` |
| **Language** | `Python` |
| **Branch** | `main` |
| **Region** | Oregon (or nearest to your users) |
| **Build Command** | `pip install -r requirements-backend.txt` |
| **Start Command** | `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/health` |

4. Scroll down to **Environment Variables** and add:

| Key | Recommended Value | Notes |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.12.3` | Matches development runtime |
| `APP_ENV` | `production` | Enables production security mode |
| `DEBUG` | `false` | Disables debug stack traces |
| `JWT_SECRET_KEY` | *(Generate a 64-char hex key)* | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `AI_PROVIDER` | `gemini` | Free-tier Google Gemini model |
| `GEMINI_API_KEY` | *(Your Gemini API Key)* | From [Google AI Studio](https://aistudio.google.com) |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite` | Supported free-tier model |
| `CORS_ORIGINS` | `https://*.streamlit.app,http://localhost:8501` | Allows Streamlit Cloud requests |
| `DATA_DIR` | `./data` *(or `/var/data` if disk attached)* | Storage root |

5. *(Optional for Starter Plan)* **Attach a Persistent Disk:**
   - Under the service settings, go to **Disks** -> **Add Disk**.
   - Name: `assistant-data`
   - Mount Path: `/var/data`
   - Size: `1 GB` (or larger)
   - Change environment variable `DATA_DIR` to `/var/data`.

6. Click **Create Web Service**.
7. Wait 2-3 minutes for the build to complete.
8. Once live, test the health endpoint in your browser:
   `https://ai-knowledge-assistant-backend.onrender.com/health`
   Should return: `{"status": "healthy", ...}`.

---

## Step 3: Deploy Frontend to Streamlit Community Cloud

1. Log into [Streamlit Community Cloud](https://share.streamlit.io).
2. Click **Create app** -> **I already have an app**.
3. Configure the repository settings:

| Setting | Value |
| :--- | :--- |
| **Repository** | `Thamizhselvans-tech/ai-assistant` |
| **Branch** | `main` |
| **Main file path** | `frontend/app.py` |
| **App URL** | *Choose a custom subdomain (e.g. `thamizh-ai-assistant`)* |

4. Click **Advanced settings...** -> **Secrets**.
5. Paste your Render backend URL (no trailing slash):

```toml
BACKEND_API_URL = "https://ai-knowledge-assistant-backend.onrender.com"
```

6. Click **Save** -> **Deploy!**.
7. Streamlit Cloud will read `requirements.txt` (only frontend dependencies), installing in ~30 seconds.

---

## Step 4: Verification Checklist

Once both services are deployed:

- [ ] **Backend Health Check:** Open `https://<render-url>/health` - verify status is `"healthy"`.
- [ ] **Swagger Documentation:** Open `https://<render-url>/docs` - verify all API endpoints load.
- [ ] **Frontend Loading:** Open `https://<streamlit-url>.streamlit.app` - verify dark obsidian & emerald UI renders without blank boxes.
- [ ] **Sign In / Account Creation:** Register a user account or sign in with test credentials.
- [ ] **Document Ingestion:** Click `📎 Attach File` in the composer or drag a PDF into the uploader; verify chunks index into ChromaDB.
- [ ] **Multilingual RAG Chat:**
  - Ask in English: `"Explain the main concepts in my document."`
  - Ask in Tamil: `"இந்த ஆவணத்தின் முக்கிய கருத்துக்கள் என்ன?"`
  - Ask in Tanglish: `"Intha document la enna solli irukanga?"`
- [ ] **Data Persistence:** Restart the Render service; verify user accounts, documents, and chat history persist.

---

## Troubleshooting & Tips

### 1. Render Free Tier Cold Starts
On the Render Free tier, web services spin down after 15 minutes of inactivity. The first request after spin-down may take ~45-60 seconds. Our application pre-warms the Sentence Transformers model on startup so that once the server wakes, queries process with zero cold-start delay.

### 2. CORS Errors
If the browser console reports CORS blocked:
- Verify that `CORS_ORIGINS` on Render includes your Streamlit Cloud domain.
- The backend's default regex `https://.*\.streamlit\.app` automatically allows all standard Streamlit subdomains.

### 3. File Size Limits
Render Free tier has a 512MB RAM ceiling. The default upload limit is set to 15MB, and chunking is throttled with batch size 16 to keep memory consumption under 250MB.
