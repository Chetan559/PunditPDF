from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── LLM APIs ──────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str
    GROQ_API_KEY: str
    MISTRAL_API_KEY: str

    # ── Hugging Face ──────────────────────────────────────────────────────────
    HUGGINGFACE_API_KEY: str = ""

    # ── Vector Store ──────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # ── File Storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    SECRET_KEY: str = "changeme-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # ── RAG ───────────────────────────────────────────────────────────────────
    MAX_CHAT_HISTORY: int = 20
    TOP_K_RETRIEVAL: int = 5
    MAX_CITATIONS: int = 4

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()