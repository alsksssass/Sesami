from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from common.router_registry import FeatureRouter
from common.database import db_manager

# v1 features를 import하여 FeatureRouter에 자동 등록
import features.v1  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트"""
    # 시작
    print("🚀 Starting application...")
    db_manager.create_all_tables()
    print("✅ Database tables created/verified")
    yield
    # 종료
    
    print("👋 Shutting down application...")

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
        f"{settings.FRONTEND_URL}:5173",          # http://localhost:3000
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

    # 전체 상태 판단
    all_healthy = db_healthy 

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "database": "connected" if db_healthy else "disconnected",
        }
    }


@app.get("/routes")
async def list_routes():
    """등록된 모든 라우트 정보 (개발/디버깅용)"""
    return {
        "total": len(FeatureRouter.get_registered_routes()),
        "routes": FeatureRouter.get_registered_routes()
    }
