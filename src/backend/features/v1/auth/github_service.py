"""
GitHub OAuth 인증 서비스
"""
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from config import settings
from common.exceptions import UnauthorizedException, BadRequestException
from common.encryption import TokenEncryption
from .models import User


class GitHubOAuthService:
    """GitHub OAuth 2.0 인증 처리"""

    GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_API = "https://api.github.com/user"

    def __init__(self, db: Session):
        self.db = db

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        GitHub OAuth 인증 URL 생성

        Args:
            state: CSRF 방지용 상태 값 (선택사항)

        Returns:
            GitHub 로그인 페이지 URL
        """
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "read:user user:email repo",  # 필요한 권한: 사용자 정보 + 레포지토리 접근
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.GITHUB_AUTHORIZE_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> str:
        """
        Authorization code를 Access token으로 교환

        Args:
            code: GitHub에서 받은 authorization code

        Returns:
            GitHub access token

        Raises:
            BadRequestException: 토큰 교환 실패
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
            )

            if response.status_code != 200:
                raise BadRequestException("Failed to exchange code for token")

            data = response.json()

            if "error" in data:
                raise BadRequestException(f"GitHub OAuth error: {data.get('error_description', 'Unknown error')}")

            access_token = data.get("access_token")
            if not access_token:
                raise BadRequestException("No access token received from GitHub")

            return access_token

    async def get_github_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        GitHub Access token으로 사용자 정보 가져오기

        Args:
            access_token: GitHub access token

        Returns:
            GitHub 사용자 정보 딕셔너리

        Raises:
            UnauthorizedException: 잘못된 토큰
        """
        async with httpx.AsyncClient() as client:
            # 사용자 기본 정보
            response = await client.get(
                self.GITHUB_USER_API,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

            if response.status_code != 200:
                raise UnauthorizedException("Invalid GitHub access token")

            user_data = response.json()

            # 이메일 정보 (별도 API)
            email_response = await client.get(
                f"{self.GITHUB_USER_API}/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

            if email_response.status_code == 200:
                emails = email_response.json()
                # primary 이메일 찾기
                primary_email = next(
                    (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                    None
                )
                if primary_email:
                    user_data["email"] = primary_email

            return user_data

    def create_or_update_user(self, github_data: Dict[str, Any], access_token: str) -> User:
        """
        GitHub 사용자 정보로 DB에 사용자 생성 또는 업데이트

        Args:
            github_data: GitHub API에서 받은 사용자 정보
            access_token: GitHub access token

        Returns:
            User 모델 인스턴스
        """
        github_id = str(github_data["id"])

        # 기존 사용자 조회
        user = self.db.query(User).filter(User.github_id == github_id).first()

        # Access token 암호화
        encrypted_token = TokenEncryption.encrypt(access_token)

        if user:
            # 기존 사용자 업데이트
            user.username = github_data["login"]
            user.email = github_data.get("email")
            user.avatar_url = github_data.get("avatar_url")
            user.access_token = encrypted_token
        else:
            # 새 사용자 생성
            user = User(
                github_id=github_id,
                username=github_data["login"],
                email=github_data.get("email"),
                avatar_url=github_data.get("avatar_url"),
                access_token=encrypted_token,
            )
            self.db.add(user)

        self.db.commit()
        self.db.refresh(user)

        return user

    async def authenticate_with_github(self, code: str) -> User:
        """
        GitHub OAuth 전체 플로우 처리

        Args:
            code: GitHub authorization code

        Returns:
            인증된 User 객체

        Raises:
            BadRequestException, UnauthorizedException: 인증 실패
        """
        # 1. Code를 Access token으로 교환
        access_token = await self.exchange_code_for_token(code)

        # 2. Access token으로 사용자 정보 가져오기
        github_user_info = await self.get_github_user_info(access_token)

        # 3. DB에 사용자 생성/업데이트
        user = self.create_or_update_user(github_user_info, access_token)

        return user
