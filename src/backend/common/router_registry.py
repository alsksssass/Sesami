from fastapi import APIRouter, FastAPI
from typing import List, Optional


class FeatureRouter(APIRouter):
    """
    메타데이터 기반 자동 등록 라우터

    Usage:
        router = FeatureRouter(
            name="auth",
            version="v1",
            description="Authentication and authorization"
        )
    """
    _registry: List['FeatureRouter'] = []

    def __init__(
        self,
        name: str,
        version: str = "v1",
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Args:
            name: Feature 이름 (URL path에 사용)
            version: API 버전 (v1, v2 등)
            description: Feature 설명
            **kwargs: APIRouter의 다른 인자들
        """
        super().__init__(**kwargs)
        self.feature_name = name
        self.version = version
        self.description = description or f"{name.replace('_', ' ').title()} API"

        # 레지스트리에 자동 등록
        self._registry.append(self)

    @classmethod
    def register_all(cls, app: FastAPI):
        """
        등록된 모든 FeatureRouter를 FastAPI 앱에 자동으로 추가

        Args:
            app: FastAPI 애플리케이션 인스턴스
        """
        from features.v1.user.api import search_router, public_router
        app.include_router(search_router)
        app.include_router(public_router)
        
        for router in cls._registry:
            app.include_router(
                router,
                prefix=f"/api/{router.version}/{router.feature_name}",
                tags=[router.description]
            )
            print(f"✅ Registered: /api/{router.version}/{router.feature_name} - {router.description}")

    @classmethod
    def get_registered_routes(cls) -> List[dict]:
        """등록된 모든 라우트 정보 반환 (디버깅용)"""
        return [
            {
                "name": router.feature_name,
                "version": router.version,
                "path": f"/api/{router.version}/{router.feature_name}",
                "description": router.description
            }
            for router in cls._registry
        ]

    @classmethod
    def clear_registry(cls):
        """레지스트리 초기화 (테스트용)"""
        cls._registry.clear()
