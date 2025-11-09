# 로컬 개발 환경 구축 가이드

## 🎯 목표

로컬 Docker Compose 환경에서 전체 시스템을 실행하여:
- ✅ 핵심 분석 로직 100% 완성
- ✅ API 기능 검증
- ✅ Frontend-Backend 통합 테스트
- ✅ AWS 마이그레이션 준비

---

## 📋 사전 요구사항

### 필수 소프트웨어
```bash
# 버전 확인
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
node --version            # Node.js 18+
python --version          # Python 3.12+
git --version             # Git 2.30+
```

### GitHub OAuth 앱 설정
1. GitHub Settings → Developer settings → OAuth Apps → New OAuth App
2. 설정:
   - **Application name**: `Sesami Local Dev`
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/auth/callback`
3. 생성 후 **Client ID**와 **Client Secret** 저장

---

## 🚀 빠른 시작

### 1. 프로젝트 클론
```bash
cd ~/goinfre
git clone <repository-url> Sesami
cd Sesami
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성 (이미 존재할 수 있음)
cat > .env << 'EOF'
# Database
POSTGRES_USER=sesami_user
POSTGRES_PASSWORD=sesami_password_2025
POSTGRES_DB=sesami_db
DB_PORT=5432
DATABASE_URL=postgresql://sesami_user:sesami_password_2025@db:5432/sesami_db

# Redis
REDIS_HOST=queue
REDIS_PORT=6379
REDIS_EXTERNAL_PORT=6379
QUEUE_BROKER_URL=redis://queue:6379/0

# Application Ports
FRONTEND_PORT=3000
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# GitHub OAuth (⚠️ 실제 값으로 교체 필요)
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback

# JWT Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-256-bit-minimum
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption
ENCRYPTION_KEY=your-fernet-encryption-key-base64-encoded-here

# Task Service (로컬 환경)
TASK_SERVICE_IMPL=LOCAL

# Worker
CELERY_BROKER_URL=redis://queue:6379/0
CELERY_RESULT_BACKEND=redis://queue:6379/0

# Logging
LOG_LEVEL=INFO
EOF
```

### 3. 암호화 키 생성
```bash
# Python으로 Fernet 키 생성
python3 << 'EOF'
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f"ENCRYPTION_KEY={key.decode()}")
EOF

# 출력된 키를 .env 파일의 ENCRYPTION_KEY에 복사
```

### 4. 전체 시스템 실행
```bash
# Docker Compose로 모든 서비스 시작
docker-compose up --build

# 또는 백그라운드 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

### 5. 접속 확인
```bash
# Frontend
open http://localhost:3000

# Backend API 문서
open http://localhost:8000/docs

# PostgreSQL (외부 클라이언트)
psql postgresql://sesami_user:sesami_password_2025@localhost:5432/sesami_db

# Redis (redis-cli)
redis-cli -h localhost -p 6379
```

---

## 🏗️ 서비스별 상세 설명

### Frontend (React + Vite)

**Docker 설정** (`docker/frontend/Dockerfile`):
```dockerfile
FROM node:20-alpine

WORKDIR /app

# 의존성 설치 최적화
COPY src/frontend/package*.json ./
RUN npm ci

# 소스 코드 복사
COPY src/frontend/ ./

# 개발 서버 실행
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**주요 파일**:
- `src/frontend/src/App.tsx` - 라우팅 및 레이아웃
- `src/frontend/src/contexts/AuthContext.tsx` - 인증 상태 관리
- `src/frontend/src/pages/` - 페이지 컴포넌트
- `src/frontend/src/services/` - API 클라이언트

**로컬 개발**:
```bash
# Frontend 컨테이너 쉘 접속
docker-compose exec frontend sh

# 의존성 추가
npm install <package-name>

# 빌드 확인
npm run build
```

---

### Backend (FastAPI)

**Docker 설정** (`docker/backend/Dockerfile`):
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY src/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY src/backend/ ./

# 개발 서버 (hot reload)
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**주요 디렉토리 구조**:
```
src/backend/
├── main.py                    # FastAPI 애플리케이션 진입점
├── config.py                  # 설정 관리 (pydantic-settings)
├── common/                    # 공통 유틸리티
│   ├── database.py           # SQLAlchemy 세션 관리
│   ├── dependencies.py       # FastAPI 의존성 주입
│   ├── encryption.py         # Fernet 암호화
│   ├── exceptions.py         # 커스텀 예외
│   └── task_service/         # TaskService 추상화
│       ├── base.py           # ITaskService 인터페이스
│       └── local_service.py  # LocalTaskService (Celery)
├── features/
│   └── v1/
│       ├── auth/             # 인증 모듈
│       │   ├── api.py        # 라우터
│       │   ├── models.py     # SQLAlchemy 모델
│       │   ├── schemas.py    # Pydantic 스키마
│       │   ├── github_service.py
│       │   └── jwt_service.py
│       └── github_analysis/  # 분석 모듈
│           ├── api.py
│           ├── models.py
│           ├── schemas.py
│           └── services/
│               ├── analysis_service.py
│               └── github_api_service.py
```

**로컬 개발**:
```bash
# Backend 컨테이너 쉘 접속
docker-compose exec backend bash

# 의존성 추가
pip install <package-name>
# requirements.txt 업데이트
pip freeze > requirements.txt

# 데이터베이스 마이그레이션
alembic revision --autogenerate -m "migration message"
alembic upgrade head

# 대화형 Python (DB 쿼리 테스트)
python
>>> from common.database import SessionLocal
>>> db = SessionLocal()
>>> # 쿼리 실행
```

---

### Worker (Celery)

**Docker 설정** (`docker/worker/Dockerfile`):
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Git 필수 (레포지토리 클론)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY src/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY src/worker/ ./

# Celery Worker 실행
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
```

**주요 파일**:
```
src/worker/
├── celery_app.py             # Celery 앱 초기화
├── tasks.py                  # Celery 태스크 정의
├── database.py               # SQLAlchemy (Worker용)
└── analysis/
    ├── __init__.py
    └── git_analyzer.py       # Git 분석 로직 (⚠️ 구현 필요)
```

**핵심 구현 필요: `git_analyzer.py`**

```python
# src/worker/analysis/git_analyzer.py

import os
import tempfile
import subprocess
from typing import Dict, List
from git import Repo
from collections import defaultdict

class GitAnalyzer:
    """Git 저장소 분석 엔진"""

    def __init__(self, repo_url: str, access_token: str):
        self.repo_url = repo_url
        self.access_token = access_token
        self.temp_dir = None
        self.repo = None

    def clone_repository(self) -> str:
        """Private 저장소 클론 (Access Token 사용)"""
        self.temp_dir = tempfile.mkdtemp(prefix='sesami_analysis_')

        # https://oauth2:TOKEN@github.com/user/repo.git 형식
        auth_url = self.repo_url.replace(
            'https://',
            f'https://oauth2:{self.access_token}@'
        )

        self.repo = Repo.clone_from(auth_url, self.temp_dir)
        return self.temp_dir

    def analyze_blame(self, user_email: str) -> Dict[str, float]:
        """git blame으로 사용자 기여도 분석"""
        if not self.repo:
            raise ValueError("Repository not cloned")

        user_lines = 0
        total_lines = 0

        # 모든 추적된 파일 순회
        for item in self.repo.tree().traverse():
            if item.type == 'blob':  # 파일만
                file_path = item.path

                try:
                    # git blame 실행
                    blame = self.repo.git.blame(
                        '--line-porcelain',
                        'HEAD',
                        '--',
                        file_path
                    )

                    for line in blame.split('\n'):
                        if line.startswith('author-mail'):
                            email = line.split('<')[1].split('>')[0]
                            total_lines += 1
                            if email == user_email:
                                user_lines += 1

                except Exception as e:
                    # 바이너리 파일 등 blame 불가능한 파일 스킵
                    continue

        contribution_rate = (user_lines / total_lines * 100) if total_lines > 0 else 0

        return {
            'user_lines': user_lines,
            'total_lines': total_lines,
            'contribution_percentage': round(contribution_rate, 2)
        }

    def analyze_tech_stack(self) -> Dict[str, any]:
        """파일 확장자 및 프레임워크 분석"""
        if not self.repo:
            raise ValueError("Repository not cloned")

        extensions = defaultdict(int)
        frameworks = set()

        for item in self.repo.tree().traverse():
            if item.type == 'blob':
                # 확장자 카운트
                _, ext = os.path.splitext(item.path)
                if ext:
                    extensions[ext] += 1

                # 프레임워크 감지 파일
                filename = os.path.basename(item.path)
                if filename == 'package.json':
                    frameworks.add('Node.js/npm')
                elif filename == 'requirements.txt':
                    frameworks.add('Python')
                elif filename == 'pom.xml':
                    frameworks.add('Java/Maven')
                elif filename == 'Dockerfile':
                    frameworks.add('Docker')

        return {
            'languages': dict(extensions),
            'frameworks': list(frameworks)
        }

    def cleanup(self):
        """임시 디렉토리 삭제"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            subprocess.run(['rm', '-rf', self.temp_dir])
```

**로컬 테스트**:
```bash
# Worker 로그 실시간 확인
docker-compose logs -f worker

# Celery 작업 큐 상태
docker-compose exec worker celery -A celery_app inspect active

# 수동 작업 트리거 (Python shell)
docker-compose exec backend python
>>> from common.task_service.local_service import LocalTaskService
>>> svc = LocalTaskService()
>>> svc.submit_analysis_job(user_id="test", repo_url="https://github.com/user/repo")
```

---

## 🧪 개발 워크플로우

### 1. 새로운 기능 개발
```bash
# 1. Feature 브랜치 생성
git checkout -b feature/new-analysis-metric

# 2. 코드 작성
# Backend: src/backend/features/v1/...
# Frontend: src/frontend/src/...
# Worker: src/worker/analysis/...

# 3. 로컬 테스트
docker-compose up -d
# 브라우저에서 테스트

# 4. 로그 확인
docker-compose logs -f backend
docker-compose logs -f worker

# 5. 커밋 및 푸시
git add .
git commit -m "feat: add new analysis metric"
git push origin feature/new-analysis-metric
```

### 2. 데이터베이스 스키마 변경
```bash
# 1. SQLAlchemy 모델 수정
# src/backend/features/v1/*/models.py

# 2. 마이그레이션 생성
docker-compose exec backend alembic revision --autogenerate -m "add analysis_results table"

# 3. 마이그레이션 적용
docker-compose exec backend alembic upgrade head

# 4. 롤백 (필요시)
docker-compose exec backend alembic downgrade -1
```

### 3. API 엔드포인트 추가
```python
# src/backend/features/v1/github_analysis/api.py

from fastapi import APIRouter, Depends
from common.dependencies import get_current_user
from .schemas import AnalysisRequest, AnalysisResponse
from .services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    current_user = Depends(get_current_user),
    service: AnalysisService = Depends()
):
    """새로운 분석 작업 시작"""
    result = await service.create_analysis_job(
        user_id=current_user.id,
        repo_url=request.repo_url
    )
    return result
```

### 4. 문제 해결

**컨테이너 재시작**:
```bash
# 특정 서비스만 재시작
docker-compose restart backend

# 전체 재시작
docker-compose restart

# 캐시 무효화 후 재빌드
docker-compose down
docker-compose up --build --force-recreate
```

**데이터베이스 초기화**:
```bash
# ⚠️ 모든 데이터 삭제 주의
docker-compose down -v
docker-compose up -d
```

**포트 충돌 해결**:
```bash
# 포트 사용 프로세스 확인
lsof -i :3000
lsof -i :8000
lsof -i :5432

# 프로세스 종료
kill -9 <PID>
```

---

## 📝 개발 체크리스트

### Backend 개발
- [ ] API 엔드포인트 구현
- [ ] Pydantic 스키마 정의
- [ ] SQLAlchemy 모델 생성
- [ ] 비즈니스 로직 서비스 계층 구현
- [ ] 의존성 주입 설정
- [ ] 예외 처리 및 에러 핸들링
- [ ] API 문서 (FastAPI 자동 생성)
- [ ] 단위 테스트 (pytest)

### Frontend 개발
- [ ] 페이지 컴포넌트 생성
- [ ] API 서비스 클라이언트
- [ ] 상태 관리 (Context API)
- [ ] 라우팅 설정
- [ ] UI/UX 디자인 (Tailwind CSS)
- [ ] 에러 핸들링 및 로딩 상태
- [ ] 반응형 디자인
- [ ] 타입 안정성 (TypeScript)

### Worker 개발
- [ ] Celery 태스크 정의
- [ ] Git 분석 로직 구현
- [ ] 진행 상태 업데이트
- [ ] 에러 핸들링 및 재시도
- [ ] 결과 데이터베이스 저장
- [ ] 로깅 및 모니터링
- [ ] 성능 최적화 (대용량 레포지토리)

---

**다음 문서**: [03_AWS_MIGRATION.md](./03_AWS_MIGRATION.md) - AWS 프로덕션 환경 마이그레이션
