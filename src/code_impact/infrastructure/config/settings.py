"""Application configuration via pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "code-impact-predictor"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Security
    secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: PostgresDsn
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis / Celery
    redis_url: RedisDsn
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_commits: str = "commits"
    qdrant_collection_issues: str = "issues"
    qdrant_collection_docs: str = "docs"

    # LLM (explanation only)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: Literal["openai", "anthropic", "local"] = "openai"
    llm_backend: Literal["mock", "openai", "anthropic"] = "mock"
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 2048

    # ML
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_backend: Literal["mock", "sentence_transformer"] = "sentence_transformer"
    gnn_backend: Literal["mock", "pytorch"] = "mock"
    gnn_model_path: str = "/app/models/gnn/latest.pt"
    risk_model_path: str = "/app/models/risk/latest.pt"
    model_storage_path: str = "/data/models"
    inference_device: str = "cpu"
    ensemble_gnn_weight: float = 0.5
    ensemble_classical_weight: float = 0.3
    ensemble_historical_weight: float = 0.2

    # Git
    git_storage_path: str = "/data/repos"
    graph_storage_path: str = "/data/graphs"
    max_repo_size_mb: int = 500

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Monitoring
    prometheus_enabled: bool = True
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def database_url_str(self) -> str:
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
