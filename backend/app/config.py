"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Recruiter Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql://recruiter:password@localhost:5432/recruiter_db"

    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # S3
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "us-east-1"

    # Bedrock
    BEDROCK_MODEL_ID: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_EMBEDDINGS_MODEL: str = "amazon.titan-embed-text-v2:0"
    BEDROCK_REGION: str = "us-east-1"

    # JWT
    JWT_SECRET: str = "your-super-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "txt"]

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
