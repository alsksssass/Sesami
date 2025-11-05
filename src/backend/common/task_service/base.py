from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID


class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class ITaskService(ABC):
    """Task Queue 서비스 인터페이스

    로컬 환경(Redis + Celery)과 AWS 환경(SQS + Batch)을 추상화하는 인터페이스
    """

    @abstractmethod
    async def enqueue_analysis(
        self,
        analysis_id: UUID,
        repo_url: str,
        target_user: str,
        branch: Optional[str] = None
    ) -> str:
        """분석 작업을 큐에 추가

        Args:
            analysis_id: 분석 작업 ID (DB에 저장된 Analysis 레코드의 ID)
            repo_url: 분석할 GitHub 저장소 URL
            target_user: 기여도를 분석할 GitHub 사용자명
            branch: 분석할 브랜치 (기본값: main/master)

        Returns:
            task_id: 작업 추적용 ID (Celery task_id 또는 AWS Batch job_id)
        """
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """작업 상태 조회

        Args:
            task_id: 작업 ID

        Returns:
            TaskStatus: 작업 상태
        """
        pass

    @abstractmethod
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 결과 조회

        Args:
            task_id: 작업 ID

        Returns:
            작업 결과 딕셔너리 또는 None (작업 미완료 시)
        """
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소

        Args:
            task_id: 작업 ID

        Returns:
            취소 성공 여부
        """
        pass
