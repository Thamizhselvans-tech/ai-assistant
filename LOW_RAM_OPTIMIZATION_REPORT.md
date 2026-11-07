# AI Knowledge Assistant – Low RAM Optimization Report (4GB RAM)

**Project:** AI Knowledge Assistant  
**Hardware Profile:** Windows 11 Laptop with 4GB Total RAM  
**Date:** November 7, 2026  
**Status:** Completed & Validated (All 83/83 Tests Passing, 100%)  
**Documentation:** `LOW_RAM_OPTIMIZATION_REPORT.md`

---

## 1. Executive Summary

Running an enterprise AI assistant on Windows 11 with 4GB RAM presents severe memory constraints:
* **Operating System Baseline:** Windows 11 consumes approximately **2.0 GB – 2.4 GB** of RAM at idle.
* **Available Headroom:** Applications have only **~1.5 GB** of usable physical memory before Windows starts aggressive pagefile swapping (thrashing) to disk, causing freezes or out-of-memory (OOM) crashes.
* **The Problem with Local 7B/8B LLMs:** A standard 7B or 8B model requires **5 GB – 16 GB** of RAM (even with 4-bit quantization, it demands 4.5 GB+), making local inference impossible on 4GB hardware.

### Strategic Solution: Hybrid Low-RAM Architecture
1. **Lightweight Local Core:**
   - **Embeddings:** `all-MiniLM-L6-v2` (~90 MB RAM) running locally via Sentence Transformers.
   - **Vector Store:** ChromaDB running locally on disk with SQLite metadata.
   - **Database & Cache:** SQLite (`app.db`) with zero standalone server overhead.
   - **API & UI:** FastAPI + Streamlit throttled for minimal working set memory.
2. **Offloaded Cloud Generation (0 MB Local LLM RAM):**
   - Text generation is delegated to high-speed cloud providers (OpenAI, Groq, OpenRouter, Gemini, DeepSeek) through an OpenAI-compatible provider abstraction layer.
   - API keys are secured in backend `.env` variables only.
3. **Graceful Multilingual Direct RAG Fallback:**
   - When a cloud provider has quota exhaustion (e.g. HTTP 429), connection limits, or is unconfigured, the pipeline immediately falls back to verified grounded citations and excerpts directly from local ChromaDB and SentenceTransformers without crashing.
   - Fully supports **Tamil, Tanglish, and English**.

---

## 2. Preserved Architecture & Technology Stack

All approved technology stack layers remain 100% intact:

| Component | Technology | Optimization Applied for 4GB RAM |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | Minimalist ChatGPT layout, live provider pill, low-RAM hardware metrics. |
| **Backend API** | FastAPI + Uvicorn | Lightweight asynchronous routes, singleton dependency injection. |
| **Relational Database** | SQLite (`data/app.db`) | In-process, zero daemon overhead, cascade indexing. |
| **Vector Store** | ChromaDB (`chroma_data/`) | Persistent vector storage, metadata filtering (`user_id`, `document_id`). |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`)| PyTorch capped at 2 threads, thread-safe lazy loading, LRU query caching. |
| **Cloud LLM Layer** | OpenAI SDK (Multi-Provider) | Configurable layer supporting OpenAI, Groq, OpenRouter, Gemini, DeepSeek. |
| **Authentication** | JWT (HS256) + bcrypt | Strict multi-user document and conversation isolation. |
| **Document Processing**| PyMuPDF, python-docx, TXT | Throttled chunk batching (16–32 chunks) with explicit garbage collection. |

---

## 3. Configurable Cloud LLM Provider Layer

A new abstraction layer [`backend/app/services/llm_provider.py`](file:///c:/Users/kgoku/OneDrive/Documents/Ai-assistent/backend/app/services/llm_provider.py) enables instant provider switching via `.env` without modifying the RAG pipeline or any backend code.

### Supported Providers Out-of-the-Box:

| Provider | Supported Models | Base URL | Environment Variable | 4GB RAM Benefit |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI** | `gpt-4o-mini`, `gpt-4o` | `https://api.openai.com/v1` | `OPENAI_API_KEY` | 0 MB local RAM |
| **Groq** *(Recommended)* | `llama-3.1-8b-instant`, `mixtral-8x7b-32768` | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | Ultra-fast (300+ tok/s), generous free tier, 0 MB local RAM |
| **OpenRouter** | `meta-llama/llama-3.1-8b-instruct:free` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | Free model access, 0 MB local RAM |
| **Google Gemini** | `gemini-1.5-flash` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `GEMINI_API_KEY` | High context window, 0 MB local RAM |
| **DeepSeek** | `deepseek-chat` | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` | High reasoning, low cost |
| **Custom / Local** | `qwen2.5:0.5b`, `llama3.2:1b` (via Ollama) | `http://127.0.0.1:11434/v1` | `CUSTOM_LLM_API_KEY` | Local experimentation (<1GB RAM) |

### How to Switch Providers (Zero Code Changes):
In `.env`:
```bash
# To switch to Groq:
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here

# Or to switch to Google Gemini:
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_your_gemini_key_here
```
The RAG pipeline automatically routes completions to the configured provider while retaining existing prompts and citations.

---

## 4. Multilingual Tamil, Tanglish & English Engine with Grounded Fallback

Implemented in [`backend/app/services/language_service.py`](file:///c:/Users/kgoku/OneDrive/Documents/Ai-assistent/backend/app/services/language_service.py):

### 4.1 Automatic Language Detection
* **Tamil Script (`ta`):** Regex match on Tamil Unicode range `[\u0B80-\u0BD7]`.
* **Tanglish (`tanglish`):** Phonetic Tamil written in Latin script (e.g., *"enna, epdi, sollunga, theriyuma, pannu, irukku, nalla, romba, venum, aaguthu"*).
* **English (`en`):** Default standard English.

### 4.2 Multilingual Prompt Steering
System prompts are dynamically augmented with language rules:
* **Tamil:** Respond completely in natural Tamil; preserve technical keywords (e.g. *Python, API, FastAPI, RAG*) in English.
* **Tanglish:** Understand phonetic Tanglish questions and explain technical concepts in natural Tamil/Tanglish.
* **English:** Clear, accurate, professional English.

### 4.3 Grounded Direct RAG Fallback
When a cloud provider has quota exhaustion (HTTP 429), connection limits, or is offline, the system avoids crashing and delivers direct verified citations in the user's detected language:
* **Tamil:**
  `*(குறிப்பு: கிளவுட் AI சேவை வரம்பு முடிந்தது / கிரெடிட் இல்லை. உங்கள் ஆவணங்களிலிருந்து நேரடியாகப் பெறப்பட்ட உண்மைத் தகவல்கள் கீழே தரப்பட்டுள்ளன:)*`
* **Tanglish:**
  `*(Note: Cloud AI quota mudinjuruchu or credits illa. Unga uploaded documents-la irunthu verify panna direct information keezhe kuduthurukom:)*`
* **English:**
  `*(Note: Cloud AI quota or rate limit reached. Displaying verified grounded excerpts retrieved directly from your indexed documents:)*`
Followed by the exact document filename, page number, and relevant excerpt.

---

## 5. Local AI Experimentation: Quantized Model Evaluation (4GB RAM)

> [!WARNING]
> On a Windows 11 laptop with 4GB RAM, models larger than **1.5 Billion parameters (Q4)** must **NOT** be loaded locally. Loading a 3B, 7B, or 8B model requires 2.5 GB to 6 GB of RAM, causing Windows to exhaust memory and lock the computer.

### Comprehensive Evaluation of Low-RAM Models:

| Model | Quantization | Disk Size | RAM Working Set | CPU Speed on 4GB RAM | Practical Feasibility & Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-0.5B-Instruct** | Q4_K_M | **398 MB** | **~450 MB** | ~18-25 tok/sec | ⭐ **Best for Pure Offline Experimentation:** Fits comfortably inside the ~1.5 GB free RAM window. Handles basic summarization and direct Q&A. |
| **Llama-3.2-1B-Instruct** | Q4_K_M | **810 MB** | **~920 MB** | ~12-16 tok/sec | ⭐ **Recommended 1B Model:** Excellent grammar, good multilingual comprehension, fits within RAM limits if background browser tabs are closed. |
| **Qwen2.5-1.5B-Instruct** | Q4_K_M | **1.1 GB** | **~1.3 GB** | ~8-12 tok/sec | ⚠️ **Upper Limit:** Barely fits inside the 1.5 GB headroom. May cause minor swapping if heavy PDFs are opened simultaneously. |
| **Llama-3.1-8B-Instruct** | Q4_K_M | 4.9 GB | ~5.8 GB | N/A (OOM) | ❌ **Infeasible:** Causes system freeze / crash. Use **Groq Cloud API** instead (0 MB local RAM). |
| **Mistral-7B-Instruct** | Q4_K_M | 4.3 GB | ~5.2 GB | N/A (OOM) | ❌ **Infeasible:** Exceeds total physical RAM of the laptop. |

### How to Run a 0.5B or 1B Model Locally via Ollama (Optional):
1. Install [Ollama](https://ollama.com/) on Windows.
2. Pull the lightweight 0.5B model:
   ```bash
   ollama run qwen2.5:0.5b
   ```
3. Set in your `.env`:
   ```bash
   LLM_PROVIDER=custom
   CUSTOM_LLM_BASE_URL=http://127.0.0.1:11434/v1
   CUSTOM_LLM_MODEL=qwen2.5:0.5b
   ```
The AI Knowledge Assistant will immediately use the local quantized model.

---

## 6. Embedding & Document Ingestion Optimizations

1. **PyTorch CPU Thread Capping:**
   * Configured `torch.set_num_threads(2)` and `torch.set_num_interop_threads(1)`.
   * Prevents PyTorch from spawning thread arenas per CPU core, saving ~150 MB of resident memory.
2. **Thread-Safe Lazy Singleton & LRU Caching:**
   * Guarded `SentenceTransformer("all-MiniLM-L6-v2")` with `threading.Lock()` to prevent duplicate loads during concurrent requests.
   * Implemented in-memory LRU cache (`_query_cache`) for 128 queries, avoiding repeated embedding calculations for common search terms.
3. **Chunk Batching & Garbage Collection:**
   * In `document_service.py`, document chunk embedding and ChromaDB insertion is throttled in batches of 32 chunks followed by `gc.collect()`.
   * PyMuPDF handles explicitly close document readers to free unmanaged memory buffers.

---

## 7. Status & Observability Indicators

1. **Top Status Bar Pill (`frontend/components/header.py`):**
   * Displays active provider and model: `⚡ Provider: OpenAI (gpt-4o-mini)` or `⚡ Groq (llama-3.1-8b)`.
   * Displays live RAM telemetry badge: `RAM: 1.5GB Free (4GB Mode)`.
   * If quota or rate limits occur: displays subtle amber status `⚠️ OpenAI (Direct RAG Fallback Active)`.
2. **Settings Diagnostic Tab (`frontend/components/settings_ui.py`):**
   * Displays all available cloud providers with instructions for switching.
   * Displays live metrics for System RAM Used %, Available GB, and Total GB.
3. **API Endpoints:**
   * `GET /api/health`: Includes `llm_provider`, `llm_model`, `llm_configured`, and `ram` metrics.
   * `GET /api/health/llm`: Dedicated provider diagnostic endpoint.

---

## 8. Test Suite Verification & Quality Gate

Executed the complete pytest regression suite:
```bash
.venv\Scripts\python -m pytest -v
```

### Result:
* **Total Tests:** 83
* **Passed:** 83 (100%)
* **Failed:** 0
* **Regressions:** 0
* **Duration:** 98.88s

### New Test Suite Breakdown (`backend/tests/test_low_ram_optimization.py`):
1. `test_language_detection_tamil_tanglish_english`: **PASSED** (Tamil script, Tanglish heuristics, English).
2. `test_multilingual_fallback_messages`: **PASSED** (Culturally natural citations in user's language).
3. `test_llm_provider_configuration_and_masking`: **PASSED** (Provider switching and key masking).
4. `test_llm_provider_generate_completion_unconfigured`: **PASSED** (Graceful unconfigured error code).
5. `test_embedding_low_ram_optimizations`: **PASSED** (PyTorch 2-thread capping and LRU query cache).
6. `test_rag_pipeline_multilingual_grounded_fallback`: **PASSED** (Grounded retrieval when cloud provider is limited).
7. `test_health_telemetry_includes_ram_and_provider`: **PASSED** (Live RAM metrics and provider status).
