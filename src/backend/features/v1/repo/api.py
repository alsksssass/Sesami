from typing import List
import uuid
from common.exceptions import BadRequestException, UnauthorizedException, NotFoundException
from fastapi import Depends, Response, Query, status, Header
from uuid import UUID
from sqlalchemy.orm import Session
from config import settings
import json

from common.router_registry import FeatureRouter
from common.dependencies import get_current_user, get_db
from features.v1.auth.models import User
from .schemas import (
    AnalysisRequest,
    AnalysisResultResponse,
    RepositoryListResponse,
    RepositoryAnalysisMVPResponse
)
from .models import AnalysisStatus, Analysis, RepositoryAnalysis
from features.v1.github_analysis.dependencies import get_github_api_service
from features.v1.github_analysis.services import GitHubAPIService
from .services import AnalysisService, get_analysis_service

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
    analysis_service: AnalysisService = Depends(get_analysis_service),
    github_service: GitHubAPIService = Depends(get_github_api_service),
    db: Session = Depends(get_db)
):
    """
    레포지토리 분석 시작

    Args:
        request: 분석할 레포지토리 리스트

    Returns:
        None
    """
    locked_user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .with_for_update()
        .first()
    )
    repo_len = len(request.repos)
    if locked_user.repo_count != 0:
        raise BadRequestException("Repository analysis request is already used")
    
    if repo_len == 0:
        raise BadRequestException("repo_urls must not be empty")
    
    locked_user.repo_count += repo_len
    
    # 1. github token 확인
    try:
        await github_service.verify_github_token()
    except Exception:
        raise UnauthorizedException()
        
    # 2. DB에 row 저장
    repo_urls = [list(repo_dict.values())[0] for repo_dict in request.repos]
    analysis = Analysis(user_id=current_user.id,
                        repository_url=json.dumps(repo_urls),
                        status=AnalysisStatus.PROCESSING,
                        main_task_uuid=uuid.uuid4()
                        )
    db.add(analysis)
    
    repo_analysis_ids = []
    for repo_dict in request.repos:
        repo_name, repo_url = list(repo_dict.items())[0]
        repo_analysis = RepositoryAnalysis(
            user_id=current_user.id,
            repository_name=repo_name,
            repository_url=repo_url,
            status=AnalysisStatus.PROCESSING,
            main_task_uuid=analysis.main_task_uuid,
            task_uuid=uuid.uuid4()
        )
        db.add(repo_analysis)
        repo_analysis_ids.append(repo_analysis.task_uuid)
    db.commit()
    # 3. job 요청
    analysis_service.request_analysis(current_user.id, current_user.username, repo_urls, analysis.main_task_uuid, repo_analysis_ids)
    return


@router.get("/analyze", response_model=AnalysisResultResponse)
async def get_analysis_result(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """분석 결과 조회"""
    repos = db.query(RepositoryAnalysis).filter(
                RepositoryAnalysis.user_id == user.id
            ).all()
    if not repos:
        raise NotFoundException('Repository analysis result does not exist')
    return {
        "repositories": [RepositoryAnalysisMVPResponse(
                name=repo.repository_name,
                url=repo.repository_url,
                state=repo.status,
                error_log=repo.error_message,
                result=repo.result if repo.result else None
            ) for repo in repos]
    }
