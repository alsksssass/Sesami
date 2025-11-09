"""
GitHub 저장소 분석 Celery 태스크
"""
import os
from uuid import UUID
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Enum
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum

from celery_app import celery_app
from analysis import GitAnalyzer

# DB 설정 (Backend DB와 동일)
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Backend models import (동일한 테이블 사용)
Base = declarative_base()


def utc_now():
    """UTC aware datetime factory for SQLAlchemy default"""
    return datetime.now(timezone.utc)


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    """Backend의 Analysis 모델과 동일"""
    __tablename__ = "analyses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    repo_url = Column(String, nullable=False)
    target_user = Column(String, nullable=False)
    branch = Column(String, default="main")
    task_id = Column(String, nullable=True)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    results = Column(String, nullable=True)  # JSON 결과
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)


@celery_app.task(name="analyze_repository", bind=True)
def analyze_repository(
    self,
    analysis_id: str,
    repo_url: str,
    target_user: str,
    branch: str = "main"
) -> Dict[str, Any]:
    """
    GitHub 저장소의 특정 사용자 기여도를 분석합니다.

    Args:
        self: Celery task 인스턴스 (bind=True)
        analysis_id: 분석 작업 ID (UUID string)
        repo_url: GitHub 저장소 URL
        target_user: 분석 대상 GitHub 사용자명
        branch: 분석 대상 브랜치

    Returns:
        분석 결과 딕셔너리
    """
    print(f"[Task {self.request.id}] Analysis started for {repo_url}")
    db = SessionLocal()
    analyzer = None

    try:
        # 1. DB에서 Analysis 레코드 조회 및 상태 업데이트
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found in database")

        analysis.status = AnalysisStatus.PROCESSING
        db.commit()

        self.update_state(state='PROGRESS', meta={'status': 'Cloning repository...'})

        # 2. GitAnalyzer로 분석 수행
        analyzer = GitAnalyzer()
        repo_path = analyzer.clone_repository(repo_url, branch)

        self.update_state(state='PROGRESS', meta={'status': 'Analyzing contributions...'})

        stats = analyzer.analyze_contributions(repo_path, target_user)

        # 3. 분석 결과를 DB에 저장
        analysis.status = AnalysisStatus.COMPLETED
        analysis.results = {
            "total_lines": stats.total_lines,
            "added_lines": stats.added_lines,
            "deleted_lines": stats.deleted_lines,
            "commits": stats.commits,
            "files_changed": stats.files_changed
        }
        analysis.completed_at = utc_now()
        db.commit()

        print(f"[Task {self.request.id}] Analysis completed successfully")

        return {
            "status": "success",
            "analysis_id": analysis_id,
            "results": analysis.results
        }

    except Exception as e:
        print(f"[Task {self.request.id}] Analysis failed: {e}")

        # 실패 상태 업데이트
        if db:
            try:
                analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
                if analysis:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = str(e)
                    analysis.completed_at = utc_now()
                    db.commit()
            except Exception as db_error:
                print(f"Failed to update error status: {db_error}")
                db.rollback()

        self.update_state(
            state='FAILURE',
            meta={'status': f'Failed: {str(e)}'}
        )

        raise e

    finally:
        # 정리
        if analyzer:
            analyzer.cleanup()
        if db:
            db.close()


@celery_app.task(name="test_task")
def test_task(message: str) -> str:
    """테스트용 간단한 태스크"""
    print(f"Test task received: {message}")
    return f"Processed: {message}"
