from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from common.database import Base


def utc_now():
    """UTC aware datetime factory for SQLAlchemy default"""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    github_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    nickname = Column(String, unique=True, index=True)
    repo_count = Column("repository_request_count", Integer, default=0)
    email = Column(String, unique=True, index=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    access_token = Column(String(500), nullable=True)  # Encrypted GitHub Access Token
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
