from typing import List
from common.exceptions import BadRequestException, UnauthorizedException
from fastapi import Depends, Response, Query, status, Header, APIRouter
from uuid import UUID
from sqlalchemy.orm import Session
from config import settings

from common.router_registry import FeatureRouter
from common.dependencies import get_current_user, get_db
from features.v1.auth.models import User
from .schemas import (
    UserAnalysisResponse,
    UserAnalysisSearchRequest,
    UserAnalysisSearchResponse,
    UserAnalysisMVPResponse,
)

router = FeatureRouter(
    name="user",
    version="v1",
    description="User Analysis"
)

search_router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search User Analysis"]
)

@router.get("/analyze", response_model=UserAnalysisMVPResponse)
async def get_user_analysis(
    user: User = Depends(get_current_user),
):
    """유저 종합 분석 결과 조회"""
    # TODO: 종합 분석 db에서 불러오기
    return {
        "result": """# 유저 종합 분석 결과

## 기술 스택

### Python
- 레벨: 5
- 경험치: 120
- 기술 스택: fastapi, pydantic, sqlalchemy, celery

## 코드 품질
- Clean Code 점수: 0.75

## 역할 분포
- backend: 80%
- frontend: 20%"""
    }

@search_router.get("", response_model=UserAnalysisSearchResponse)
async def search_user_analysis(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(5, ge=1, le=100, description="페이지 크기"),
    dev_type: List[str] = Query(default=[], description="개발 타입 필터"),
):
    """유저 검색 결과 조회"""
    # TODO: 유저 검색 결과 조회
    return {
        "items": [
            {
                "order": 1,
                "nickname": "Park Jinyoung",
                "level": 4,
                "exp": 39,
                "stack": ["python", "fastapi", "sqlalchemy"],
                "dev_type": ["backend", "data_science"]
            },
            {
                "order": 2,
                "nickname": "Park Hyemin",
                "level": 3,
                "exp": 28,
                "stack": ["javascript", "react", "node.js"],
                "dev_type": ["frontend", "ai"]
            }
        ],
        "total": 2,
        "page": 1,
        "size": 2,
        "pages": 1
    }