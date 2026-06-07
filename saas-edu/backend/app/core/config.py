"""
Configuración central de la aplicación.
Usa pydantic-settings para leer variables de entorno.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ===========================================
    # App
    # ===========================================
    APP_NAME: str = "SaasEdu"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # ===========================================
    # Database
    # ===========================================
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_edu"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/saas_edu"

    # ===========================================
    # Redis
    # ===========================================
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ===========================================
    # Security
    # ===========================================
    SECRET_KEY: str = "cambia-esto-en-produccion-minimo-64-caracteres"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ===========================================
    # LLM — Groq
    # ===========================================
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # ===========================================
    # Embeddings
    # ===========================================
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ===========================================
    # ChromaDB
    # ===========================================
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "/data/chroma"

    # ===========================================
    # Documentos
    # ===========================================
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    UPLOAD_DIR: str = "/data/uploads"

    # ===========================================
    # CORS
    # ===========================================
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @property
    def chroma_url(self) -> str:
        """URL completa de ChromaDB."""
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"


# Instancia global de configuración
settings = Settings()