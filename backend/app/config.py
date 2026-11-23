from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://dataco:dataco@localhost:5433/dataco"
    model_dir: Path = BACKEND_DIR / "model"
    cors_origins: list[str] = ["http://localhost:5180", "http://127.0.0.1:5180"]
    max_upload_mb: int = 200

    # Criterio de calidad definido en la fase 1 de CRISP-ML(Q)
    min_accuracy: float = 0.70
    min_f1: float = 0.70
    min_roc_auc: float = 0.80


settings = Settings()
