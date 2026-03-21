from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    llm_provider: str = os.getenv("LLM_PROVIDER", "regex")  # regex | openai

    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "")
    yolo_confidence: float = float(os.getenv("YOLO_CONFIDENCE", "0.25"))

    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))


settings = Settings()
