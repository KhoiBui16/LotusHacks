"""
Settings riêng cho AI agent workflow.

File này tách khỏi `app.core.settings` để:
1. Giữ nguyên config/runtime hiện có của `main`
2. Cho phép agent workflow có thêm cấu hình LLM/RAG riêng
3. Đảm bảo script chạy trực tiếp từ `backend/` vẫn đọc đúng `backend/.env`
"""
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


_PLACEHOLDER_MARKERS = (
    "YOUR_CLUSTER",
    "YOUR-CLUSTER",
    "YOUR_API_KEY",
    "YOUR_ZILLIZ",
    "example.invalid",
)


def _load_env_files() -> None:
    """Load `backend/.env` nếu tồn tại, nhưng không override env đã có sẵn."""
    backend_dir = Path(__file__).resolve().parents[2]
    backend_env = backend_dir / ".env"
    if backend_env.exists():
        load_dotenv(backend_env, override=False)


def _is_placeholder(value: str) -> bool:
    """Kiểm tra env value còn là placeholder/template hay không."""
    if not value:
        return False
    return any(marker in value for marker in _PLACEHOLDER_MARKERS)


def _normalise_zilliz_uri(raw_uri: str, milvus_host: str, milvus_port: str) -> str:
    """
    Chuẩn hóa endpoint để `MilvusClient` dùng ổn định.

    Hỗ trợ cả:
    - `ZILLIZ_URI=https://...:19534`
    - `MILVUS_HOST=https://...:19534/` + `MILVUS_PORT=19534`
    """
    candidate = raw_uri.strip()
    if not candidate or _is_placeholder(candidate):
        candidate = milvus_host.strip()

    candidate = candidate.rstrip("/")
    if not candidate:
        return ""

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    netloc = parsed.netloc or parsed.path
    if milvus_port and parsed.port is None and netloc:
        candidate = f"{parsed.scheme}://{netloc}:{milvus_port}"

    return candidate.rstrip("/")


_load_env_files()


class AgentSettings:
    """Tập hợp settings dùng cho LLM + RAG của workflow agent."""

    def __init__(self) -> None:
        # LLM
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
        self.QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
        self.QWEN_BASE_URL: str = os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.HF_TOKEN: str = os.getenv("HF_TOKEN", "")

        # Agent runtime
        self.AGENT_LLM_MODEL: str = os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini")
        self.FALLBACK_LLM_MODEL: str = os.getenv("FALLBACK_LLM_MODEL", "qwen-plus")
        self.AGENT_LLM_TEMPERATURE: float = float(os.getenv("AGENT_LLM_TEMPERATURE", "0"))

        # RAG / Zilliz
        self.MILVUS_HOST: str = os.getenv("MILVUS_HOST", "")
        self.MILVUS_PORT: str = os.getenv("MILVUS_PORT", "")
        self.ZILLIZ_URI: str = _normalise_zilliz_uri(
            os.getenv("ZILLIZ_URI", ""),
            self.MILVUS_HOST,
            self.MILVUS_PORT,
        )
        self.ZILLIZ_TOKEN: str = os.getenv("ZILLIZ_TOKEN", "")
        self.ZILLIZ_COLLECTION_NAME: str = os.getenv(
            "ZILLIZ_COLLECTION_NAME",
            "insurance_policies",
        )
        self.ZILLIZ_EMBED_MODEL: str = os.getenv(
            "ZILLIZ_EMBED_MODEL",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        )
        self.ZILLIZ_EMBED_DIM: int = int(os.getenv("ZILLIZ_EMBED_DIM", "768"))
        self.ZILLIZ_TIMEOUT_SEC: int = int(os.getenv("ZILLIZ_TIMEOUT_SEC", "15"))
        self.TRIAGE_RAG_K: int = int(os.getenv("TRIAGE_RAG_K", "5"))
        self.COVERAGE_RAG_K: int = int(os.getenv("COVERAGE_RAG_K", "5"))

        # Shared app settings reused by agent/docs/tests
        self.MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "lotushacks")
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "10080"))
        self.ALLOWED_ORIGINS: list[str] = [
            value.strip()
            for value in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:3000,http://localhost:5173",
            ).split(",")
            if value.strip()
        ]


agent_settings = AgentSettings()
