"""Application configuration using Pydantic settings"""

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App settings
    app_name: str = Field("Folium", validation_alias="APP_NAME")
    DEBUG: bool = False
    version: str = Field("1.0.0", validation_alias="VERSION")

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://localhost:3000",
        "http://frontend:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = ""

    # JWT Authentication
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Multi-Cloud Storage Configuration
    STORAGE_PROVIDER: str = "minio"  # 'aws', 'azure', 'minio'
    STORAGE_BUCKET: str = "folium-dev"
    STORAGE_REGION: str = "us-east-2"
    STORAGE_ENDPOINT: str | None = None  # Required for MinIO/Azure (internal Docker)
    STORAGE_PUBLIC_ENDPOINT: str | None = None  # Public-facing endpoint for browser
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_CDN_URL: str | None = None  # Optional CDN URL

    # Azure-specific storage settings
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_ACCOUNT_NAME: str = ""

    # Transcription Service
    TRANSCRIPTION_SERVICE_URL: str = (
        "http://localhost:8001"  # or "http://transcribe:8001" in docker-compose
    )

    # Summarization Service
    SUMMARIZATION_SERVICE_URL: str = (
        "http://localhost:8002"  # or "http://summarize:8002" in docker-compose
    )

    # Temporal
    TEMPORAL_ADDRESS: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    VOICENOTES_WORKFLOW_EXECUTION_TIMEOUT_MINUTES: int = 30
    CHARTREVIEW_INTERNAL_TOKEN: str = ""

    # Legacy settings (deprecated)

    # AWS
    AWS_LAMBDA_ENDPOINT: str = ""
    AWS_REGION: str = "us-east-1"

    # Azure AI
    AZURE_FUNCTIONS_ENDPOINT: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def validate_required_env_settings(self) -> "Settings":
        missing_fields: list[str] = []

        if not self.DATABASE_URL.strip():
            missing_fields.append("DATABASE_URL")

        if not self.JWT_SECRET.strip():
            missing_fields.append("JWT_SECRET")

        if not self.CHARTREVIEW_INTERNAL_TOKEN.strip():
            missing_fields.append("CHARTREVIEW_INTERNAL_TOKEN")

        if self.STORAGE_PROVIDER in {"aws", "minio"}:
            if not self.STORAGE_ACCESS_KEY.strip():
                missing_fields.append("STORAGE_ACCESS_KEY")
            if not self.STORAGE_SECRET_KEY.strip():
                missing_fields.append("STORAGE_SECRET_KEY")

        if self.STORAGE_PROVIDER == "azure" and not (self.AZURE_STORAGE_CONNECTION_STRING.strip()):
            missing_fields.append("AZURE_STORAGE_CONNECTION_STRING")

        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(f"Missing required environment settings: {missing}")

        return self

    class Config:
        env_file = (ROOT_ENV_FILE, BACKEND_ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables (e.g., from .NET Core)


settings: Settings = Settings()
