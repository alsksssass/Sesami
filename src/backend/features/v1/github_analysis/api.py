from fastapi import Depends, Query
from uuid import UUID

from common.router_registry import FeatureRouter
from common.dependencies import get_current_user
from features.v1.auth.models import User
from .schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResultResponse,
    RepositoryResponse,
    RepositoryListResponse
)
from .services import GitHubAPIService, AnalysisService
from .dependencies import get_github_api_service, get_analysis_service

router = FeatureRouter(
    name="analysis",
    version="v1",
    description="GitHub Repository Analysis"
)


@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    GitHub 저장소 분석 시작

    - **repo_url**: 분석할 저장소 URL
    - **target_user**: 기여도를 분석할 GitHub 사용자명
    - **branch**: 분석할 브랜치 (기본값: main)
    """
    return await analysis_service.start_analysis(request, current_user.id)


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """분석 상태 조회"""
    return await analysis_service.get_status(analysis_id)


@router.get("/result/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    analysis_id: UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """분석 결과 조회"""
    return await analysis_service.get_result(analysis_id)


@router.get("/history", response_model=list[AnalysisStatusResponse])
async def get_analysis_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """사용자의 분석 히스토리 조회"""
    return await analysis_service.get_user_history(current_user.id, skip, limit)


# GitHub Repository Endpoints
@router.get("/repos", response_model=RepositoryListResponse)
async def get_user_repositories(
    visibility: str = Query("all", regex="^(all|public|private)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    github_service: GitHubAPIService = Depends(get_github_api_service)
):
    """
    현재 사용자의 GitHub 레포지토리 목록 가져오기

    - **visibility**: all(전체), public(공개만), private(비공개만)
    - **page**: 페이지 번호 (1부터 시작)
    - **per_page**: 페이지당 결과 수 (최대 100)
    """
    repos = await github_service.get_repositories(
        visibility=visibility,
        page=page,
        per_page=per_page
    )

    return RepositoryListResponse(
        total_count=len(repos),
        repositories=repos
    )


@router.get("/repos/all", response_model=RepositoryListResponse)
async def get_all_user_repositories(
    visibility: str = Query("all", regex="^(all|public|private)$"),
    github_service: GitHubAPIService = Depends(get_github_api_service)
):
    """
    현재 사용자의 모든 GitHub 레포지토리 가져오기 (페이지네이션 자동 처리)

    - **visibility**: all(전체), public(공개만), private(비공개만)
    """
    repos = await github_service.get_all_repositories(visibility=visibility)

    return RepositoryListResponse(
        total_count=len(repos),
        repositories=repos
    )


@router.get("/repos/{owner}/{repo}", response_model=RepositoryResponse)
async def get_repository_details(
    owner: str,
    repo: str,
    github_service: GitHubAPIService = Depends(get_github_api_service)
):
    """
    특정 레포지토리 상세 정보 가져오기

    - **owner**: 레포지토리 소유자
    - **repo**: 레포지토리 이름
    """
    repo_data = await github_service.get_repository_details(owner, repo)

    return RepositoryResponse(**repo_data)
