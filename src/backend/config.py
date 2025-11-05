from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis/Queue
    QUEUE_BROKER_URL: str

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Token Encryption
    ENCRYPTION_KEY: str

    # Task Service
    TASK_SERVICE_TYPE: str = "local"  # "local" or "aws"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
