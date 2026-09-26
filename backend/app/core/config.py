"""
lg2m/backend/app/core/config.py
Configurações da aplicação utilizando pydantic-settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "LG2M — Mentor Agêntico de Estudos"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-akcit-camp-2026"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://lg2m_user:lg2m_password@localhost:5432/lg2m_db"
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_DB_PATH: str = "lg2m_local.db"

    # LLM & Embeddings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=(str(backend_dir / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
