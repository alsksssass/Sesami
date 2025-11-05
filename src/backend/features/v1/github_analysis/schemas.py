from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


# Repository Schemas
class RepositoryOwner(BaseModel):
    """레포지토리 소유자 정보"""
    login: str
    id: int
    avatar_url: str
    html_url: str


class RepositoryResponse(BaseModel):
    """GitHub 레포지토리 응답"""
    id: int  # GitHub repo ID
    name: str
    full_name: str
    owner: RepositoryOwner
    html_url: str
    description: Optional[str] = None
    private: bool
    fork: bool
    language: Optional[str] = None
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    default_branch: str
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    size: int
    has_issues: bool
    has_projects: bool
    has_wiki: bool


class RepositoryListResponse(BaseModel):
    """레포지토리 목록 응답"""
    total_count: int
    repositories: List[RepositoryResponse]


# Analysis Schemas
class AnalysisRequest(BaseModel):
    """분석 요청"""
    repo_url: str
    target_user: str  # 분석 대상 GitHub 사용자명
    branch: Optional[str] = "main"  # 분석 대상 브랜치


class AnalysisResponse(BaseModel):
    """분석 요청 응답"""
    analysis_id: UUID
    task_id: str
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    """분석 상태 응답"""
    analysis_id: UUID
    repo_url: str
    target_user: str
    branch: str
    status: str
    task_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ContributionResult(BaseModel):
    """기여도 분석 결과"""
    total_lines: int
    added_lines: int
    deleted_lines: int
    commits: int
    files_changed: int


class AnalysisResultResponse(BaseModel):
    """분석 결과 응답"""
    analysis_id: UUID
    repo_url: str
    target_user: str
    branch: str
    status: str
    results: Optional[ContributionResult] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
