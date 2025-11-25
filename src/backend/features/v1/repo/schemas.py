from enum import Enum
from pydantic import BaseModel, HttpUrl, conint
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from features.v1.repo.models import AnalysisStatus


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
    repos: List[Dict[str, str]] # name - url 쌍


class LanguageStackInfo(BaseModel):
    """언어 사용 정보"""
    level: int
    stack: Dict[str, str]
    strength: List[str]
    weakness: List[str]


class RepositoryUserAnalysisResult(BaseModel):
    """레포지토리에서의 유저 활동 분석 결과"""
    contribution: float
    language: Dict[str, LanguageStackInfo]
    role: Dict[str, int]

    
class RepositoryAnalysisResult(BaseModel):
    """레포지토리 분석 결과"""
    markdown: str
    security_score: float
    stack: List[str]
    user: RepositoryUserAnalysisResult


class RepositoryAnalysisResponse(BaseModel):
    """레포지토리 분석 상태"""
    name: str
    url: str
    result: Optional[RepositoryAnalysisResult] = None
    state: AnalysisStatus
    error_log: Optional[str] = None
    
    class Config:
        from_attributes = True


class RepositoryAnalysisMVPResponse(BaseModel):
    name: str
    url: str
    result: Optional[dict[str, Any]] = None
    state: AnalysisStatus
    error_log: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    """레포지토리 분석 결과 리스트 응답"""
    repositories: List[RepositoryAnalysisMVPResponse]
