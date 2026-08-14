from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


INSECURE_DEFAULT_SECRET_KEYS = [
    "production-secret-key-change-me-in-prod",
    "your-super-secret-key-change-in-production",
    "secret",
    "secretkey",
    "change-me",
    "password",
    "1234567890",
]


class Settings(BaseSettings):
    PROJECT_NAME: str = "FlowPilot AI API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-for-local-testing-only-1234567890"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "flowpilot_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "sqlite+aiosqlite:///./flowpilot.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Production LLM Gateway Configuration
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_TIMEOUT: float = 30.0
    LLM_MAX_RETRIES: int = 3
    LLM_FALLBACK_ENABLED: bool = False
    LLM_FALLBACK_PROVIDER: Optional[str] = "ollama"
    LLM_FALLBACK_MODEL: Optional[str] = "llama3"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env_mode = (self.ENVIRONMENT or "development").lower().strip()
        if env_mode in ["production", "prod"]:
            secret = (self.SECRET_KEY or "").strip()
            if not secret or secret in INSECURE_DEFAULT_SECRET_KEYS or len(secret) < 32:
                raise ValueError("Production configuration error: Insecure or default SECRET_KEY configured.")
        return self


settings = Settings()
