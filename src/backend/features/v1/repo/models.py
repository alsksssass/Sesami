from common.database import Base
from sqlalchemy import Column, String, DateTime, JSON, UUID, ForeignKey, Enum
import uuid
import enum
import datetime
from datetime import timezone


class AnalysisStatus(str, enum.Enum):
    """분석 작업 상태"""
    PROCESSING = "progress"
    DONE = "done"
    ERROR = "error"    


def utc_now():
    """UTC aware datetime factory for SQLAlchemy default"""
    return datetime.now(timezone.utc)

# 각 레포지토리별 분석 결과를 저장하는 테이블
class RepositoryAnalysis(Base):
    __tablename__ = "repository_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    repository_url = Column(String, index=True)
    result = Column(JSON, nullable=True) # RepositoryAnalysisResult 형태의 JSON

    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PROCESSING)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

# 모든 분석이 끝난 후 종합 분석 결과를 저장하는 테이블
class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    repository_url = Column(String, index=True)
    # target_user = Column(String, nullable=False) # 분석 대상 GitHub 사용자명 -> username
    result = Column(JSON, nullable=True) # UserAnalysisResult 형태의 JSON

    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PROCESSING)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
