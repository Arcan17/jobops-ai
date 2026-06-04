"""Application settings loaded from environment (pydantic-settings).

No secret is ever hardcoded; every value is overridable via environment / .env.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- General ---
    app_name: str = "JobOps AI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://jobops:jobops@localhost:5432/jobops"
    )

    # --- Auth (single seeded user) ---
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    seed_user_email: str = "me@example.com"
    seed_user_password: str = "change-me"

    # --- Providers (LLM / embeddings) ---
    llm_provider: str = "mock"  # mock | anthropic | openai
    embedding_provider: str = "mock"  # mock | openai
    embedding_dim: int = 384
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # --- Matching ---
    match_top_k: int = 5

    # --- Scoring weights (must sum to 100) ---
    weight_stack: float = 30.0
    weight_seniority: float = 20.0
    weight_modality_location: float = 15.0
    weight_projects: float = 15.0
    weight_salary: float = 10.0
    weight_risk: float = 10.0

    # --- Recommendation thresholds (on the 1-10 score) ---
    recommend_apply_min: float = 7.0
    recommend_quick_min: float = 5.0

    # --- HTTP ---
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
