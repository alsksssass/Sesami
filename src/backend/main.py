from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from common.router_registry import FeatureRouter
from common.database import db_manager
from common.dependencies import get_graph_service, get_vector_service

# v1 features를 import하여 FeatureRouter에 자동 등록
import features.v1  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트"""
    # 시작
    print("🚀 Starting application...")
    db_manager.create_all_tables()
    print("✅ Database tables created/verified")

    # Graph-RAG 서비스 초기화 확인
    try:
        graph_service = get_graph_service()
        vector_service = get_vector_service()
        print("✅ Graph-RAG services initialized")
    except Exception as e:
        print(f"⚠️  Graph-RAG services initialization warning: {e}")

    yield

    # 종료
    print("👋 Shutting down application...")

    # Graph-RAG 서비스 연결 종료
    try:
        graph_service = get_graph_service()
        vector_service = get_vector_service()
        await graph_service.close()
        await vector_service.close()
        print("✅ Graph-RAG services closed")
    except Exception as e:
        print(f"⚠️  Graph-RAG services cleanup warning: {e}")


app = FastAPI(
    title="GitHub Contribution Analyzer",
    description="API for analyzing GitHub repository contributions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (개발 환경용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,          # http://localhost:3000
        "http://localhost:5173",        # Vite 기본 포트
        "http://localhost:5174",        # Vite 대체 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 자동 등록
FeatureRouter.register_all(app)


@app.get("/")
async def root():
    return {"message": "GitHub Contribution Analyzer API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """헬스체크 - PostgreSQL, Neo4j, OpenSearch 연결 상태 확인"""
    # PostgreSQL 상태 확인
    db_healthy = db_manager.health_check()

    # Neo4j 상태 확인
    neo4j_healthy = False
    try:
        graph_service = get_graph_service()
        neo4j_healthy = await graph_service.check_health()
    except Exception as e:
        print(f"Neo4j health check failed: {e}")

    # OpenSearch 상태 확인
    opensearch_healthy = False
    try:
        vector_service = get_vector_service()
        opensearch_healthy = await vector_service.check_health()
    except Exception as e:
        print(f"OpenSearch health check failed: {e}")

    # 전체 상태 판단
    all_healthy = db_healthy and neo4j_healthy and opensearch_healthy

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "database": "connected" if db_healthy else "disconnected",
            "neo4j": "connected" if neo4j_healthy else "disconnected",
            "opensearch": "connected" if opensearch_healthy else "disconnected"
        }
    }


@app.get("/routes")
async def list_routes():
    """등록된 모든 라우트 정보 (개발/디버깅용)"""
    return {
        "total": len(FeatureRouter.get_registered_routes()),
        "routes": FeatureRouter.get_registered_routes()
    }
