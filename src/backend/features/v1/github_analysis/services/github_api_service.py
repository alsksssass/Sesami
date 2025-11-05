"""
GitHub API 통합 서비스
사용자의 레포지토리 및 GitHub 데이터 조회
"""
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from common.encryption import TokenEncryption
from common.exceptions import UnauthorizedException, BadRequestException
from features.v1.auth.models import User


class GitHubAPIService:
    """
    GitHub REST API 통합 서비스

    사용자의 액세스 토큰을 사용하여 GitHub API 호출
    """

    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self, user: User):
        """
        Args:
            user: 인증된 User 객체 (암호화된 access_token 포함)
        """
        self.user = user
        # 암호화된 토큰 복호화
        if not user.access_token:
            raise UnauthorizedException("User has no GitHub access token")
        self.access_token = TokenEncryption.decrypt(user.access_token)

    def _get_headers(self) -> Dict[str, str]:
        """GitHub API 요청 헤더 생성"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def get_repositories(
        self,
        visibility: str = "all",
        affiliation: str = "owner,collaborator,organization_member",
        sort: str = "updated",
        per_page: int = 100,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        현재 사용자의 레포지토리 목록 가져오기

        Args:
            visibility: all | public | private (기본: all)
            affiliation: owner,collaborator,organization_member (기본: 전체)
            sort: created | updated | pushed | full_name (기본: updated)
            per_page: 페이지당 결과 수 (1-100, 기본: 100)
            page: 페이지 번호 (기본: 1)

        Returns:
            레포지토리 목록

        Raises:
            UnauthorizedException: 토큰이 유효하지 않음
            BadRequestException: API 요청 실패
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/user/repos",
                headers=self._get_headers(),
                params={
                    "visibility": visibility,
                    "affiliation": affiliation,
                    "sort": sort,
                    "per_page": per_page,
                    "page": page
                },
                timeout=30.0
            )

            if response.status_code == 401:
                raise UnauthorizedException("Invalid or expired GitHub token")

            if response.status_code != 200:
                raise BadRequestException(f"GitHub API error: {response.status_code}")

            return response.json()

    async def get_all_repositories(
        self,
        visibility: str = "all",
        affiliation: str = "owner,collaborator,organization_member"
    ) -> List[Dict[str, Any]]:
        """
        사용자의 모든 레포지토리 가져오기 (페이지네이션 자동 처리)

        Args:
            visibility: all | public | private
            affiliation: owner,collaborator,organization_member

        Returns:
            모든 레포지토리 목록
        """
        all_repos = []
        page = 1

        while True:
            repos = await self.get_repositories(
                visibility=visibility,
                affiliation=affiliation,
                per_page=100,
                page=page
            )

            if not repos:
                break

            all_repos.extend(repos)

            # 100개 미만이면 마지막 페이지
            if len(repos) < 100:
                break

            page += 1

        return all_repos

    async def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        특정 레포지토리 상세 정보 가져오기

        Args:
            owner: 레포지토리 소유자
            repo: 레포지토리 이름

        Returns:
            레포지토리 상세 정보
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}",
                headers=self._get_headers(),
                timeout=30.0
            )

            if response.status_code == 404:
                raise BadRequestException("Repository not found")

            if response.status_code != 200:
                raise BadRequestException(f"GitHub API error: {response.status_code}")

            return response.json()

    async def get_rate_limit(self) -> Dict[str, Any]:
        """
        GitHub API Rate Limit 조회

        Returns:
            Rate limit 정보
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/rate_limit",
                headers=self._get_headers(),
                timeout=10.0
            )

            return response.json()
