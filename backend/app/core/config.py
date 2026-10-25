"""Settings loaded exclusively from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration shared by ingestion and future API services."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://fashion:fashion@localhost:5432/fashion"
    data_dir: Path = Path("data")
    clip_model: str = "ViT-B-32"
    clip_pretrained: str = "laion2b_s34b_b79k"
    embedding_batch_size: int = 32
    request_timeout_seconds: float = 20.0


@lru_cache
def get_settings() -> Settings:
    """Return the singleton settings object."""

    return Settings()
