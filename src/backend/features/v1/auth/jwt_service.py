"""
JWT 토큰 생성 및 검증 서비스
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from jose import JWTError, jwt

from config import settings
from common.exceptions import UnauthorizedException


class JWTService:
    """JWT 토큰 관리"""

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        JWT Access Token 생성

        Args:
            data: 토큰에 포함할 데이터 (예: {"sub": user_id})
            expires_delta: 만료 시간 (기본값: 설정 파일의 값 사용)

        Returns:
            JWT 토큰 문자열
        """
        to_encode = data.copy()

        # 만료 시간 설정
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "iat": now})

        # JWT 인코딩
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        JWT 토큰 검증 및 페이로드 추출

        Args:
            token: JWT 토큰 문자열

        Returns:
            토큰 페이로드 딕셔너리

        Raises:
            UnauthorizedException: 토큰 검증 실패
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise UnauthorizedException(f"Invalid token: {str(e)}")

    @staticmethod
    def get_user_id_from_token(token: str) -> UUID:
        """
        JWT 토큰에서 사용자 ID 추출

        Args:
            token: JWT 토큰 문자열

        Returns:
            사용자 UUID

        Raises:
            UnauthorizedException: 토큰 검증 실패 또는 user_id 없음
        """
        payload = JWTService.verify_token(token)

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Token missing user identifier")

        try:
            return UUID(user_id)
        except (ValueError, AttributeError):
            raise UnauthorizedException("Invalid user identifier in token")

    @staticmethod
    def create_user_token(user_id: UUID, **extra_claims) -> str:
        """
        사용자 ID로 JWT 토큰 생성 (편의 메서드)

        Args:
            user_id: 사용자 UUID
            **extra_claims: 추가로 토큰에 포함할 데이터

        Returns:
            JWT 토큰 문자열
        """
        token_data = {"sub": str(user_id), **extra_claims}
        return JWTService.create_access_token(token_data)
