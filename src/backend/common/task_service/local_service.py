from typing import Optional, Dict, Any
from uuid import UUID
from celery import Celery
from celery.result import AsyncResult

from .base import ITaskService, TaskStatus


class LocalTaskService(ITaskService):
    """로컬 개발 환경용 Task Service (Redis + Celery)"""

    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app

    async def enqueue_analysis(
        self,
        analysis_id: UUID,
        repo_url: str,
        target_user: str,
        branch: Optional[str] = None
    ) -> str:
        """Celery 작업 큐에 분석 요청 추가"""
        # analyze_repository task 호출
        task = self.celery_app.send_task(
            'analyze_repository',
            kwargs={
                "analysis_id": str(analysis_id),
                "repo_url": repo_url,
                "target_user": target_user,
                "branch": branch or "main"
            }
        )
        return task.id

    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Celery 작업 상태 조회"""
        result = AsyncResult(task_id, app=self.celery_app)
        status_map = {
            "PENDING": TaskStatus.PENDING,
            "STARTED": TaskStatus.STARTED,
            "SUCCESS": TaskStatus.SUCCESS,
            "FAILURE": TaskStatus.FAILURE,
            "RETRY": TaskStatus.RETRY,
            "REVOKED": TaskStatus.REVOKED,
        }
        return status_map.get(result.state, TaskStatus.PENDING)

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Celery 작업 결과 조회"""
        result = AsyncResult(task_id, app=self.celery_app)
        if result.ready():
            return result.result
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Celery 작업 취소"""
        result = AsyncResult(task_id, app=self.celery_app)
        result.revoke(terminate=True)
        return True
