"""
Dependency Injection Container

FastAPI Depends를 사용한 의존성 주입 팩토리 함수들
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.dependencies import get_current_user
from common.task_dependencies import get_task_service
from common.task_service import ITaskService
from features.v1.auth.models import User
from .services import GitHubAPIService, AnalysisService


def get_github_api_service(
    current_user: User = Depends(get_current_user)
) -> GitHubAPIService:
    """
    GitHubAPIService 의존성 주입

    Args:
        current_user: 현재 인증된 사용자

    Returns:
        사용자별 GitHubAPIService 인스턴스

    Usage:
        @router.get("/repos")
        async def get_repos(
            github_service: GitHubAPIService = Depends(get_github_api_service)
        ):
            repos = await github_service.get_repositories()
    """
    return GitHubAPIService(current_user)


def get_analysis_service(
    db: Session = Depends(get_db),
    task_service: ITaskService = Depends(get_task_service)
) -> AnalysisService:
    """
    AnalysisService 의존성 주입

    Args:
        db: 데이터베이스 세션
        task_service: TaskService (로컬/AWS 환경 추상화)

    Returns:
        AnalysisService 인스턴스

    Usage:
        @router.post("/analyze")
        async def start_analysis(
            analysis_service: AnalysisService = Depends(get_analysis_service)
        ):
            result = await analysis_service.start_analysis(...)
    """
    return AnalysisService(db, task_service)
