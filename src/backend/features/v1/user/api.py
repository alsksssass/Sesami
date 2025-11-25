from fastapi import Depends, Response, Query, status, Header, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import or_, Integer, Float

from uuid import UUID
from math import ceil
from typing import List

from config import settings
from common.exceptions import BadRequestException, NotFoundException, UnauthorizedException
from common.router_registry import FeatureRouter
from common.dependencies import get_current_user, get_db
from features.v1.auth.models import User
from features.v1.repo.models import Analysis, AnalysisState
from .schemas import (
    UserAnalysisResponse,
    UserAnalysisSearchRequest,
    UserAnalysisSearchResponse,
    UserAnalysisMVPResponse,
    UserAnalysisResult
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
    db: Session = Depends(get_db)
):
    """유저 종합 분석 결과 조회"""
    analysis = db.query(Analysis).filter(Analysis.user_id == user.id).first()
    if analysis is None:
        raise NotFoundException('User analysis result does not exist')
    return {
        'result': analysis.result.get('markdown', ''),
        'status': analysis.status
    }

@search_router.get("", response_model=UserAnalysisSearchResponse)
async def search_user_analysis(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(5, ge=1, le=100, description="페이지 크기"),
    dev_type: List[str] = Query(default=[], description="개발 타입 필터"),
    db: Session = Depends(get_db)
):
    """유저 검색 결과 조회"""

    
    # Analysis와 User를 조인
    query = db.query(Analysis, User).join(User, Analysis.user_id == User.id)
    
    # 분석 완료된 것만 필터링
    query = query.filter(Analysis.status == AnalysisState.DONE)
    
    # dev_type 필터링 (role의 키가 dev_type에 포함되는 경우)
    if dev_type:
        # PostgreSQL JSON 연산자 사용: result->'role' ? 'dev_type'
        conditions = []
        for dt in dev_type:
            condition = (
                (Analysis.result.op('->')('role').op('->')(dt).isnot(None)) &
                (Analysis.result.op('->')('role').op('->>')(dt).cast(Float) != 0)
            )
            conditions.append(condition)
        query = query.filter(or_(*conditions))
    
    # level 순으로 정렬 (result->level->level 기준 내림차순)
    query = query.order_by(
        Analysis.result.op('->')('level').op('->>')('level').cast(Integer).desc(),
        Analysis.result.op('->')('level').op('->>')('experience').cast(Integer).desc()
    )
    
    # 전체 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * size
    results = query.offset(offset).limit(size).all()
    
    # 응답 데이터 구성
    items = []
    for order, (analysis, user) in enumerate(results, start=offset + 1):
        result_data = analysis.result or {}
        level_data = result_data.get('level', {})
        
        items.append({
            "order": order,
            "nickname": user.nickname,
            "level": level_data.get('level', 0),
            "exp": level_data.get('experience', 0),
            "stack": result_data.get('tech_stack', []),
            "dev_type": [k for k, v in result_data.get('role', {}).items() if v != 0]
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": ceil(total / size) if total > 0 else 0
    }