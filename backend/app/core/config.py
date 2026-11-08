"""Application configuration settings using Pydantic Settings."""

import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "AI Knowledge Assistant"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PORT: Optional[int] = None  # Support Render / Cloud dynamic $PORT

    # Storage Paths & Mount Points
    DATA_DIR: str = "./data"  # Set to /var/data for Render Persistent Disk

    # Security & JWT
    JWT_SECRET_KEY: str = "insecure_dev_secret_key_change_in_production_32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    CHROMA_COLLECTION_NAME: str = "ai_knowledge_assistant"

    # Embedding Model & Optimization
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    LOW_RAM_MODE: bool = True
    EMBEDDING_BATCH_SIZE: int = 16
    TORCH_NUM_THREADS: int = 2

    # LLM Provider Configuration (Low-RAM Architecture: Offloads generation to cloud)
    # Supported providers: 'gemini', 'openai', 'groq', 'openrouter', 'deepseek', 'custom'
    AI_PROVIDER: str = "gemini"
    LLM_PROVIDER: str = "gemini"

    # Google Gemini (Official Google GenAI SDK & Free-Tier Model)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # OpenAI (Optional / Fallback Provider)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.1

    # Groq (Ultra-fast, generous tier, lightweight cloud inference)
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # OpenRouter (Aggregator with free and open-source models)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"


    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Custom / Local (e.g. Ollama for lightweight quantized experimentation)
    CUSTOM_LLM_API_KEY: str = ""
    CUSTOM_LLM_BASE_URL: str = "http://127.0.0.1:11434/v1"
    CUSTOM_LLM_MODEL: str = "qwen2.5:0.5b"

    # Firebase Cloud Storage & Project Integration (ai-agent-7fab4)
    FIREBASE_PROJECT_ID: str = "ai-agent-7fab4"
    FIREBASE_STORAGE_BUCKET: str = "ai-agent-7fab4.firebasestorage.app"
    FIREBASE_AUTH_DOMAIN: str = "ai-agent-7fab4.firebaseapp.com"

    # Document & RAG Pipeline
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 15
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_RETRIEVAL: int = 4
    SIMILARITY_THRESHOLD: float = 0.20

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @model_validator(mode="after")
    def post_process_settings(self) -> "Settings":
        # Check PORT environment variable (standard on Render and cloud hosts)
        port_env = os.environ.get("PORT")
        if port_env:
            try:
                self.API_PORT = int(port_env)
            except ValueError:
                pass
        elif self.PORT:
            self.API_PORT = self.PORT

        # Support persistent data directory mount (e.g. Render Persistent Disk: DATA_DIR=/var/data)
        data_dir_env = os.environ.get("DATA_DIR")
        if data_dir_env:
            self.DATA_DIR = data_dir_env.rstrip("/\\")
            # If storage paths weren't explicitly overridden in environment, anchor them to DATA_DIR
            if "DATABASE_URL" not in os.environ:
                self.DATABASE_URL = f"sqlite:///{self.DATA_DIR}/app.db"
            if "CHROMA_PERSIST_DIRECTORY" not in os.environ:
                self.CHROMA_PERSIST_DIRECTORY = f"{self.DATA_DIR}/chroma_data"
            if "UPLOAD_DIR" not in os.environ:
                self.UPLOAD_DIR = f"{self.DATA_DIR}/uploads"

        # Security check for production JWT secret
        if self.APP_ENV == "production" and "insecure_dev_secret" in self.JWT_SECRET_KEY:
            import logging
            logging.getLogger("backend.app.core.config").warning(
                "SECURITY WARNING: Default insecure JWT_SECRET_KEY detected in production environment! "
                "Please set a strong cryptographically generated JWT_SECRET_KEY in your deployment environment variables."
            )

        return self

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create storage directories if they do not exist."""
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)
        db_path = self.DATABASE_URL.replace("sqlite:///", "")
        if "/" in db_path or "\\" in db_path:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
