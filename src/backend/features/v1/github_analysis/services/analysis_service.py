from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from typing import List

from common.exceptions import NotFoundException
from common.task_service import ITaskService
from ..models import Analysis, AnalysisStatus
from ..schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResultResponse,
    ContributionResult
)


class AnalysisService:
    def __init__(self, db: Session, task_service: ITaskService):
        self.db = db
        self.task_service = task_service

    async def start_analysis(
        self,
        request: AnalysisRequest,
        user_id: UUID
    ) -> AnalysisResponse:
        """분석 작업 시작 및 큐에 등록"""
        # 1. DB에 분석 작업 레코드 생성
        analysis = Analysis(
            user_id=user_id,
            repo_url=request.repo_url,
            target_user=request.target_user,
            branch=request.branch,
            status=AnalysisStatus.PENDING
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        # 2. TaskService를 통해 작업 큐에 등록
        task_id = await self.task_service.enqueue_analysis(
            analysis_id=analysis.id,
            repo_url=request.repo_url,
            target_user=request.target_user,
            branch=request.branch
        )

        # 3. task_id 저장
        analysis.task_id = task_id
        self.db.commit()

        return AnalysisResponse(
            analysis_id=analysis.id,
            task_id=task_id,
            status=AnalysisStatus.PENDING.value,
            message="Analysis request has been queued successfully"
        )

    async def get_status(self, analysis_id: UUID) -> AnalysisStatusResponse:
        """분석 작업 상태 조회"""
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise NotFoundException(f"Analysis {analysis_id} not found")

        # TaskService에서 최신 상태 확인
        if analysis.task_id and analysis.status == AnalysisStatus.PENDING:
            task_status = await self.task_service.get_task_status(analysis.task_id)
            # 상태 업데이트
            if task_status.value == "STARTED":
                analysis.status = AnalysisStatus.PROCESSING
                self.db.commit()

        return AnalysisStatusResponse.model_validate(analysis)

    async def get_result(self, analysis_id: UUID) -> AnalysisResultResponse:
        """분석 결과 조회"""
        analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise NotFoundException(f"Analysis {analysis_id} not found")

        # 결과 파싱
        results = None
        if analysis.results:
            results = ContributionResult(**analysis.results)

        return AnalysisResultResponse(
            analysis_id=analysis.id,
            repo_url=analysis.repo_url,
            target_user=analysis.target_user,
            branch=analysis.branch,
            status=analysis.status.value,
            results=results,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message
        )

    async def get_user_history(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[AnalysisStatusResponse]:
        """사용자의 분석 히스토리 조회"""
        analyses = (
            self.db.query(Analysis)
            .filter(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [AnalysisStatusResponse.model_validate(a) for a in analyses]
