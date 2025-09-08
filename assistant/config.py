"""
python app.py                          # uses defaults
POSTGRES_USER=superuser python app.py  # overrides from env
"""
from __future__ import annotations

import os
# import inspect
# import pytz  # requires: pip install pytz
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import logging
# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, computed_field


class Settings(BaseModel):
    """
    Examples
    --------
    s = Settings()

    print(s.dict())  # model_dump
    # {'POSTGRES_DB': 'llm_rag', 'POSTGRES_HOST': 'localhost', ...}
    """
    class Config:
        env_file = ".env"      # optional
        env_file_encoding = "utf-8"
        case_sensitive = True

    def local_or_docker_service(url="", service=None):
        if os.path.exists('/.dockerenv') and service:
            return url.replace("localhost", service)
        elif service:
            return url.replace(service, "localhost")
        else:
            return url

    # General
    DATA_PATH: str = Field(default=os.getenv("DATA_PATH", "Data/documents-with-ids.json"))
    DATA_URL: str = Field(default="https://huggingface.co/datasets/bitext/Bitext-media-llm-chatbot-training-dataset/resolve/main/bitext-media-llm-chatbot-training-dataset.csv")

    RUN_TIMEZONE_CHECK: str = os.getenv("RUN_TIMEZONE_CHECK", "0")
    TZ_INFO: str = Field(default=os.getenv("TZ", "Europe/Istanbul"))
    TZ_UTC: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field  # recomputed each time it's accessed
    @property
    def TZ_LOCAL(self) -> datetime:
        return datetime.now(ZoneInfo(self.TZ_INFO))

    # Postgres
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "llm_rag")
    POSTGRES_HOST: str = local_or_docker_service(os.getenv("POSTGRES_HOST", "localhost"), "postgres")  # "localhost" or "postgres"
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = Field(default=os.getenv("POSTGRES_PASSWORD", "admin"), repr=False, description="secret")  # not print
    POSTGRES_TABLE: str = os.getenv("POSTGRES_TABLE", "conversations")
    POSTGRES_TABLE1: str = os.getenv("POSTGRES_TABLE1", "feedback")

    # Grafana
    GRAFANA_ADMIN_USER: str = os.getenv("GRAFANA_ADMIN_USER", "admin")
    GRAFANA_ADMIN_PASSWORD: str = Field(default=os.getenv("GRAFANA_ADMIN_PASSWORD", "admin"), repr=False)
    GRAFANA_SECRET_KEY: str = Field(default=os.getenv("GRAFANA_SECRET_KEY", "SECRET_KEY"), repr=False)

    # OpenAI
    OPENAI_API_KEY: str | None = Field(default=os.getenv("OPENAI_API_KEY", "sk-..."), repr=False)
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL_EMBED: str = os.getenv("OPENAI_MODEL_EMBED", "text-embedding-3-small")
    OPENAI_MODEL_CHAT: str = os.getenv("OPENAI_MODEL_CHAT", "gpt-4o-mini")

    # Huggingface
    HF_TOKEN: str | None = Field(default=os.getenv("HF_TOKEN", "hf-..."), repr=False)
    HF_API_KEY: str | None = Field(default=os.getenv("HF_TOKEN", "hf-..."), repr=False)
    HF_BASE_URL: str = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1")  # for openai chat model
    HF_MODEL_EMBED: str = os.getenv("HF_MODEL_EMBED", "nomic-ai/nomic-embed-text-v1.5")
    HF_MODEL_CHAT: str = os.getenv("HF_MODEL_CHAT", "openai/gpt-oss-120b")

    # Ollama
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "ollama")  # dummy key
    OLLAMA_BASE_URL: str = local_or_docker_service(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), "ollama")  # "localhost" or "ollama"
    OLLAMA_MODEL_EMBED: str = os.getenv("OLLAMA_MODEL_EMBED", "nomic-embed-text")
    OLLAMA_MODEL_CHAT: str = os.getenv("OLLAMA_MODEL_CHAT", "phi3")

    # Provider selection
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "OLLAMA")  #.lower()  ## OPENAI or OLLAMA or HF
    API_KEY: str | None = Field(default=os.getenv(f"{LLM_PROVIDER}_API_KEY", OLLAMA_API_KEY), repr=False)
    BASE_URL: str = local_or_docker_service(os.getenv(f"{LLM_PROVIDER}_BASE_URL", OLLAMA_BASE_URL), "ollama")
    MODEL_EMBED: str = os.getenv(f"{LLM_PROVIDER}_MODEL_EMBED", OLLAMA_MODEL_EMBED)
    MODEL_CHAT: str = os.getenv(f"{LLM_PROVIDER}_MODEL_CHAT", OLLAMA_MODEL_CHAT)

    # Scraper
    TIMEOUT_PDF_REQUEST: int = int(os.getenv("TIMEOUT_PDF_REQUEST", 60))
    SE_SLOWMO_MS: int = int(os.getenv("SE_SLOWMO_MS", 200))
    DEFAULT_MAX_PAGES: int = int(os.getenv("DEFAULT_MAX_PAGES", 1))

    # Chunking
    CHUNK_MAX_TOKENS: int = int(os.getenv("CHUNK_MAX_TOKENS", 512))
    CHUNK_OVERLAP_TOKENS: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", 64))

    # Features
    ENABLE_FAISS: bool = os.getenv("ENABLE_FAISS", "false").lower() == "true"


# ✅ Instance
SETTINGS = Settings()

# ✅ Database config dict
DB_CONFIG = {
    "database": SETTINGS.POSTGRES_DB,  # or "dbname"
    "host": SETTINGS.POSTGRES_HOST,
    "port": SETTINGS.POSTGRES_PORT,
    "user": SETTINGS.POSTGRES_USER,
    "password": SETTINGS.POSTGRES_PASSWORD,
}
