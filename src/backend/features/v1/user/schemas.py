from enum import Enum
from pydantic import BaseModel, HttpUrl, conint
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from features.v1.repo.models import AnalysisState


class LanguageInfo(BaseModel):
    """언어별 상세 정보"""
    stack: List[str]
    level: int
    exp: int


class UserAnalysisResult(BaseModel):
    """유저 종합 분석 결과"""
    python: LanguageInfo
    clean_code: float
    role: Dict[str, int] # 역할에 맞는 기술스택 보유 퍼센트
    markdown: str
    
    class Config:
        # 동적 필드 허용 (언어별 정보: "python", "javascript" 등)
        extra = "allow"


class UserAnalysisResponse(BaseModel):
    """유저 종합 분석 결과 응답"""
    result: UserAnalysisResult


class UserAnalysisMVPResponse(BaseModel):
    result: str # markdown 형식
    status: AnalysisState


class DevType(str, Enum):
    """개발 타입"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULLSTACK = "fullstack"
    AI = "ai"
    DATA_SCIENCE = "data_science"


class UserAnalysisSearchRequest(BaseModel):
    """유저 검색 요청"""
    dev_type: List[DevType]


class UserSearchItem(BaseModel):
    """검색 결과 유저 정보"""
    order: int  # 순위
    nickname: str
    level: int
    exp: int
    stack: List[str]
    dev_type: List[str]


class UserAnalysisSearchResponse(BaseModel):
    """유저 검색 결과 (페이지네이션)"""
    items: List[UserSearchItem]
    total: int
    page: int
    size: int
    pages: int
