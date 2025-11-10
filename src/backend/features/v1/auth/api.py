from fastapi import Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.router_registry import FeatureRouter
from common.dependencies import get_current_user
from .schemas import (
    UserResponse,
    TokenResponse,
    GitHubCallbackRequest,
    GitHubLoginResponse
)
from .github_service import GitHubOAuthService
from .jwt_service import JWTService
from .models import User

router = FeatureRouter(
    name="auth",
    version="v1",
    description="Authentication & Authorization"
)


@router.get("/github/login", response_model=GitHubLoginResponse)
async def github_login(db: Session = Depends(get_db)):
    """
    GitHub OAuth 로그인 URL 생성

    프론트엔드에서 이 URL로 리다이렉트하면 GitHub 로그인 페이지로 이동합니다.
    """
    github_service = GitHubOAuthService(db)
    authorization_url = github_service.get_authorization_url()
    return GitHubLoginResponse(authorization_url=authorization_url)


@router.post("/github/callback", response_model=TokenResponse)
async def github_callback(request: GitHubCallbackRequest, db: Session = Depends(get_db)):
    """
    GitHub OAuth 콜백 처리

    GitHub에서 리다이렉트된 후 authorization code를 받아
    사용자 인증 및 JWT 토큰을 발급합니다.
    """
    github_service = GitHubOAuthService(db)

    # GitHub OAuth 인증 처리
    user = await github_service.authenticate_with_github(request.code)

    # JWT 토큰 생성
    access_token = JWTService.create_user_token(user.id)

    # 응답
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회

    JWT 토큰을 통해 인증된 사용자 정보를 반환합니다.
    Header: Authorization: Bearer <token>
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout():
    """
    로그아웃 (클라이언트에서 토큰 삭제)

    서버는 stateless이므로 클라이언트에서 토큰을 삭제하면 됩니다.
    향후 토큰 블랙리스트 기능 추가 가능.
    """
    return {"message": "Successfully logged out"}
