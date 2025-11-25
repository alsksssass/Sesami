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
    TASK_SERVICE_IMPL: str = "LOCAL"  # "LOCAL" or "AWS_BATCH"

    # ============================================
    # Neo4j Configuration (Graph Database - v2)
    # ============================================
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # ============================================
    # OpenSearch Configuration (Vector Store - v2)
    # ============================================
    OPENSEARCH_ENDPOINT: str = "https://opensearch:9200"
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: str
    OPENSEARCH_INDEX_NAME: str = "code_embeddings"

    # ============================================
    # AWS Bedrock (Embedding Generation - v2)
    # ============================================
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    BEDROCK_MODEL_ID: str = "amazon.titan-embed-text-v1"
    USE_BEDROCK: bool = False

    # ============================================
    # OpenAI (Bedrock Alternative - Local Dev)
    # ============================================
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ============================================
    # Graph-RAG Settings (v2)
    # ============================================
    GRAPH_SNAPSHOT_CACHE_ENABLED: bool = True
    EMBEDDING_CACHE_ENABLED: bool = True
    CHUNK_SIZE: int = 200
    CHUNK_OVERLAP: int = 50

    JOB_DEFINITION: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
