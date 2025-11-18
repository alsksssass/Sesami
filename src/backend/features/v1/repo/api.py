from typing import List
from common.exceptions import BadRequestException, UnauthorizedException
from fastapi import Depends, Response, Query, status, Header
from uuid import UUID
from sqlalchemy.orm import Session
from config import settings

from common.router_registry import FeatureRouter
from common.dependencies import get_current_user, get_db
from features.v1.auth.models import User
from .schemas import (
    AnalysisRequest,
    AnalysisResultResponse,
    RepositoryListResponse
)
from .models import AnalysisStatus
from features.v1.github_analysis.dependencies import get_github_api_service
from features.v1.github_analysis.services import GitHubAPIService

router = FeatureRouter(
    name="repo",
    version="v1",
    description="GitHub Repository"
)


@router.get("/list", response_model=RepositoryListResponse)
async def get_current_user_repositories(
    github_service: GitHubAPIService = Depends(get_github_api_service),
    languages: List[str] = Query(
        default=["python"],
        description="조회할 언어. 예: ?languages=python&languages=go"
    ),
):
    """
    현재 로그인한 유저의 특정 언어 레포지토리 조회
    
    Arguments:
        languages: 조회하고자 하는 언어(레포지토리의 주 언어) 리스트

    Returns:
        RepositoryListResponse: 레포지토리 정보를 담고 있는 리스트
    """
    repos = await github_service.get_all_repositories()
    filtered_repos = list(filter(lambda v: (v["language"] or "").lower() in languages, repos))

    return RepositoryListResponse(
        total_count=len(filtered_repos),
        repositories=filtered_repos
    )


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    # analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    레포지토리 분석 시작

    Args:
        request: 분석할 레포지토리 리스트

    Returns:
        None
    """
    repo_len = len(request.repo_urls)
    if current_user.repo_count != 0:
        raise BadRequestException("Repository analysis request is already used")
    
    if repo_len == 0:
        raise BadRequestException("repo_urls must not be empty")
    
    current_user.repo_count += repo_len
    
    # TODO: 레포지토리 분석 시작
    # await analysis_service.start_analysis(request, current_user.id)
    return


@router.get("/analyze", response_model=AnalysisResultResponse)
async def get_analysis_result(
    user: User = Depends(get_current_user),
    # analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """분석 결과 조회"""
    # TODO: analysis_service에서 조회하도록 수정
    # repos = await analysis_service.get_results_by_user(user.id)
    return {
        "repositories": [
            {
                "name": "sesami",
                "url": "https://github.com/acme/sesami",
                "state": AnalysisStatus.DONE,
                "result": {
                    "markdown": "## Summary\n- Great project\n- Stable release",
                    "security_score": 0.3,  # 0~1 부동소수
                    "stack": ["python", "fastapi", "postgresql"],
                    "user": {
                        "contribution": 30.0,  # % 기준이면 0~100 float
                        "language": {
                            "python": {
                                "level": 5,
                                "stack": {"fastapi": "상", "pydantic": "중"},
                                "strength": ["async I/O", "type hints"],
                                "weakness": ["test coverage"]
                            }
                        },
                        "role": {"backend": 10}
                    }
                }
            },
            {
                "name": "another-repo",
                "url": "https://github.com/acme/another-repo",
                "state": AnalysisStatus.PROCESSING,
                "result": None,
                "error_log": None
            }
        ]
    }


@router.post("/result")
async def complete_repository_analysis(
    repo_analysis_id: UUID,
    x_batch_secret: str = Header(),
    # analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Repository 분석 Batch 작업 완료 콜백
    
    Batch 컨테이너가 Repository 분석 완료 후 호출한다. DB에 분석 완료된 JSON을 읽어와서 저장

    Args:
        repo_analysis_id (UUID): Repository 분석 id
        x_batch_secret (str, optional): Batch 컨테이너의 시크릿 키
    """
    # TODO: S3에서 uuid로 저장된 json 가져와서 db에 저장
    return
