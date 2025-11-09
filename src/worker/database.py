"""
워커용 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class AnalysisResult(Base):
    """
    분석 결과 저장 테이블
    """
    __tablename__ = 'analysis_results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    repo_url = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # 분석 요청한 사용자 UUID
    analyzed_user = Column(String, nullable=False)  # 기여자 이메일
    line_count = Column(Integer, default=0)  # 기여한 라인 수

    def __repr__(self):
        return f"<AnalysisResult(repo={self.repo_url}, user={self.analyzed_user}, lines={self.line_count})>"
