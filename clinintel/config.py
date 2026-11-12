from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("CLINTEL_ENV", "development")
    api_key: str = os.getenv("CLINTEL_API_KEY", "")
    database_url: str = os.getenv("CLINTEL_DATABASE_URL", "")
    data_mode: str = os.getenv("CLINTEL_DATA_MODE", "synthetic")
    model_path: Path = Path(os.getenv("CLINTEL_MODEL_PATH", ROOT / "artifacts/readmission-demo.joblib"))
    audit_path: Path = Path(os.getenv("CLINTEL_AUDIT_PATH", ROOT / "artifacts/audit.jsonl"))
    allowed_origins: tuple[str, ...] = tuple(filter(None, os.getenv("CLINTEL_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")))


settings = Settings()
