from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from common.database import get_db
from common.exceptions import UnauthorizedException

# OAuth2 Bearer 스킴
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자 가져오기

    JWT 토큰을 검증하고 해당 사용자를 반환합니다.

    Args:
        credentials: HTTP Bearer 토큰
        db: 데이터베이스 세션

    Returns:
        User: 인증된 사용자 객체

    Raises:
        UnauthorizedException: 토큰이 유효하지 않거나 사용자가 존재하지 않음
    """
    # 순환 import 방지를 위해 함수 내부에서 import
    from features.v1.auth.jwt_service import JWTService
    from features.v1.auth.models import User

    # JWT 토큰에서 사용자 ID 추출
    token = credentials.credentials
    user_id = JWTService.get_user_id_from_token(token)

    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("User not found")

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """
    선택적 인증 (토큰이 없어도 통과)

    Args:
        credentials: HTTP Bearer 토큰 (선택사항)
        db: 데이터베이스 세션

    Returns:
        User | None: 인증된 사용자 또는 None
    """
    if credentials is None:
        return None

    try:
        return get_current_user(credentials, db)
    except Exception:
        return None


def require_admin(current_user=Depends(get_current_user)):
    """
    관리자 권한 필요

    Args:
        current_user: 현재 사용자

    Raises:
        HTTPException: 관리자 권한이 없음

    TODO: User 모델에 is_admin 필드 추가 후 구현
    """
    # TODO: 관리자 권한 검증 로직 추가
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required"
    #     )
    pass
