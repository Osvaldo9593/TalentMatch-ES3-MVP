from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TalentMatch API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # CORS Settings
    FRONTEND_URL: str | None = None
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    def get_cors_origins(self) -> List[str]:
        origins = list(self.BACKEND_CORS_ORIGINS)
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins

    # Database Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "talentmatch_db"
    DATABASE_URL: str | None = None

    # Storage and CV Settings
    CV_STORAGE_PATH: str = "storage/cvs"
    MAX_CV_FILE_SIZE_MB: int = 10

    # OpenRouter API (AI Integration)
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "openrouter/free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_TIMEOUT_SECONDS: float = 30.0

    # Authentication
    JWT_SECRET_KEY: str = "change-this-development-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    SEED_ADMIN_EMAIL: str = "admin@guinezingenieria.cl"
    SEED_ADMIN_PASSWORD: str = "change-me-admin"
    SEED_RECRUITER_EMAIL: str = "recruiter@guinezingenieria.cl"
    SEED_RECRUITER_PASSWORD: str = "change-me-recruiter"

    # AI Evaluation Settings
    MAX_CV_TEXT_LENGTH: int = 8000
    EVALUATION_SCORE_RECOMMENDED_THRESHOLD: int = 80
    EVALUATION_SCORE_REVIEW_THRESHOLD: int = 60

    @property
    def max_cv_file_size_bytes(self) -> int:
        return self.MAX_CV_FILE_SIZE_MB * 1024 * 1024

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
