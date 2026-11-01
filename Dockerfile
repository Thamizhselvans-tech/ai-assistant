# ==============================================================================
# Multi-Stage Production Dockerfile for AI Knowledge Assistant
# Supports: Backend (FastAPI) and Frontend (Streamlit)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Dependencies
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean packaging
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Production Base
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS production-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

# Install curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user for least-privilege security
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Prepare persistent storage directories
RUN mkdir -p /app/data/uploads /app/chroma_data /home/appuser/.cache && \
    chown -R appuser:appgroup /app /home/appuser/.cache

# Copy source code with appropriate permissions
COPY --chown=appuser:appgroup backend/ /app/backend/
COPY --chown=appuser:appgroup frontend/ /app/frontend/
COPY --chown=appuser:appgroup .env.example /app/.env.example

USER appuser

# ------------------------------------------------------------------------------
# Stage 3: Backend Image
# ------------------------------------------------------------------------------
FROM production-base AS backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ------------------------------------------------------------------------------
# Stage 4: Frontend Image
# ------------------------------------------------------------------------------
FROM production-base AS frontend

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true"]
