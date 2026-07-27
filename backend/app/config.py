from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / "env" / ".env"
load_dotenv(ENV_FILE)


def env_value(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI标准化病人临床思维训练平台"
    environment: str = env_value("FASTAPI_ENV", env_value("ENVIRONMENT", "development"))
    backend_host: str = env_value("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(env_value("BACKEND_PORT", "8000"))
    frontend_origin: str = env_value("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
    openai_model: str = env_value("OPENAI_MODEL", "gpt-4.1")
    rag_provider: str = env_value("RAG_PROVIDER", "local")
    chroma_db_path: str = env_value("CHROMA_DB_PATH", "./storage/chroma")
    milvus_host: str = env_value("MILVUS_HOST", "127.0.0.1")
    milvus_port: str = env_value("MILVUS_PORT", "19530")
    tts_provider: str = env_value("TTS_PROVIDER", "placeholder")

    @property
    def milvus_uri(self) -> str:
        return env_value("MILVUS_URI", f"http://{self.milvus_host}:{self.milvus_port}")


settings = Settings()
