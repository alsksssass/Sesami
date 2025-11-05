from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import enum
import uuid

from common.database import Base


def utc_now():
    """UTC aware datetime factory for SQLAlchemy default"""
    return datetime.now(timezone.utc)


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    repo_url = Column(String, nullable=False)
    target_user = Column(String, nullable=False)  # 분석 대상 GitHub 사용자명
    branch = Column(String, default="main")  # 분석 대상 브랜치
    task_id = Column(String, nullable=True)  # Celery task_id 또는 AWS Batch job_id
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    results = Column(JSON, nullable=True)  # 분석 결과 저장
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
