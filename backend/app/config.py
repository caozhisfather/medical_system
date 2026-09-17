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
    openai_api_key: str = env_value("OPENAI_API_KEY", "")
    openai_base_url: str = env_value("OPENAI_BASE_URL", "https://api.openai.com")
    rag_provider: str = env_value("RAG_PROVIDER", "local")
    chroma_db_path: str = env_value("CHROMA_DB_PATH", "./storage/chroma")
    milvus_host: str = env_value("MILVUS_HOST", "127.0.0.1")
    milvus_port: str = env_value("MILVUS_PORT", "19530")
    tts_provider: str = env_value("TTS_PROVIDER", "placeholder")
    digital_human_mode: str = env_value("DIGITAL_HUMAN_MODE", "mock")
    liveact_service_url: str = env_value("LIVEACT_SERVICE_URL", "http://127.0.0.1:8090")
    embedding_model: str = env_value("EMBEDDING_MODEL", "text-embedding-v3")
    embedding_api_key: str = env_value("EMBEDDING_API_KEY", env_value("DASHSCOPE_API_KEY", env_value("QWEN_API_KEY", "")))
    embedding_base_url: str = env_value("EMBEDDING_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode")
    embedding_timeout: float = float(env_value("EMBEDDING_TIMEOUT", "30"))
    vision_model: str = env_value("QWEN_VISION_MODEL", "qwen-vl-max")
    vision_api_key: str = env_value("QWEN_VISION_API_KEY", env_value("EMBEDDING_API_KEY", env_value("DASHSCOPE_API_KEY", "")))
    vision_base_url: str = env_value("QWEN_VISION_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    vision_timeout: float = float(env_value("QWEN_VISION_TIMEOUT", "60"))
    liveact_request_timeout: float = float(env_value("LIVEACT_REQUEST_TIMEOUT", "3.0"))
    liveact_avatar_id: str = env_value("LIVEACT_AVATAR_ID", "standardized_patient_001")
    liveact_voice: str = env_value("TTS_VOICE", "zh_female_warm")
    sparkos_app_id: str = env_value("LLM_APPID", "")
    sparkos_api_key: str = env_value("LLM_APIKEY", "")
    sparkos_api_secret: str = env_value("LLM_APISECRET", "")
    sparkos_ws_url: str = env_value("LLM_WS_URL", "wss://sparkos.xfyun.cn/v1/openapi/chat")
    sparkos_scene: str = env_value("LLM_SCENE", "sos_app")
    rag_url: str = env_value("RAG_URL", "")
    rag_api_password: str = env_value("RAG_APIPWD", "")
    auth_database_path: str = env_value("AUTH_DATABASE_PATH", str(ROOT_DIR / "data" / "auth.sqlite3"))
    skill_database_path: str = env_value("SKILL_DATABASE_PATH", str(ROOT_DIR / "data" / "skills.sqlite3"))
    mail_host: str = env_value("MAIL_HOST", "smtp.163.com")
    mail_port: int = int(env_value("MAIL_PORT", "465"))
    mail_username: str = env_value("MAIL_USERNAME", "")
    mail_password: str = env_value("MAIL_PASSWORD", "")
    mail_from_name: str = env_value("MAIL_FROM_NAME", "临思智训")
    public_frontend_url: str = env_value("PUBLIC_FRONTEND_URL", env_value("FRONTEND_ORIGIN", "http://127.0.0.1:5173"))

    @property
    def milvus_uri(self) -> str:
        return env_value("MILVUS_URI", f"http://{self.milvus_host}:{self.milvus_port}")


settings = Settings()
