# ==============================================================================
# Backend Dockerfile for AI Knowledge Assistant (FastAPI)
# Target Architecture: Python 3.12 Slim Multi-Stage Build (CPU Optimized)
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

# Create virtual environment for clean layer isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Pre-install lightweight CPU-only PyTorch (~150MB instead of ~3.5GB NVIDIA CUDA wheels)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    APP_ENV=production \
    PORT=8080 \
    API_HOST=0.0.0.0 \
    DATA_DIR=/app/data \
    DATABASE_URL="sqlite:////app/data/app.db" \
    CHROMA_PERSIST_DIRECTORY=/app/chroma_data \
    UPLOAD_DIR=/app/data/uploads

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create least-privilege non-root user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Prepare runtime storage directories and adjust ownership
RUN mkdir -p /app/data/uploads /app/chroma_data /home/appuser/.cache && \
    chown -R appuser:appgroup /app /home/appuser/.cache

# Copy backend source code into /app/backend
COPY --chown=appuser:appgroup . /app/backend/

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || curl -f http://localhost:${PORT:-8080}/api/health || exit 1

# Launch FastAPI using Uvicorn, binding to 0.0.0.0 and supporting dynamic $PORT with 8080 default
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2"]
