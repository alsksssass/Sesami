# Sesami 프로젝트 전체 설계 개요

## 📋 문서 구조

이 설계 문서는 다음과 같이 구성되어 있습니다:

1. **[00_OVERVIEW.md](./00_OVERVIEW.md)** (현재 문서) - 전체 개요
2. **[01_SYSTEM_ARCHITECTURE.md](./01_SYSTEM_ARCHITECTURE.md)** - 시스템 아키텍처
3. **[02_LOCAL_DEVELOPMENT.md](./02_LOCAL_DEVELOPMENT.md)** - 로컬 개발 환경
4. **[03_AWS_MIGRATION.md](./03_AWS_MIGRATION.md)** - AWS 마이그레이션 계획
5. **[04_API_SPECIFICATION.md](./04_API_SPECIFICATION.md)** - API 명세
6. **[05_DATABASE_SCHEMA.md](./05_DATABASE_SCHEMA.md)** - 데이터베이스 스키마
7. **[06_IMPLEMENTATION_PLAN.md](./06_IMPLEMENTATION_PLAN.md)** - 구현 계획

---

## 🎯 프로젝트 목표

**Sesami**는 GitHub 기여도 분석 플랫폼으로, 다음 기능을 제공합니다:

### 핵심 기능
1. **GitHub OAuth 인증**: 사용자의 Private Repository 접근 권한 확보
2. **자동 기여도 분석**: `git blame` 기반 정량적 기여도 측정
3. **기술 스택 분석**: 사용 언어, 프레임워크, 기술 트렌드 시각화
4. **시계열 분석**: 기간별 기술 스택 변화 추이
5. **코드 품질 분석**: 정적 분석 도구 통합 (선택적)

---

## 🏗️ 핵심 아키텍처 원칙

### 1. 비동기 작업 처리 (Asynchronous Job Processing)

```
┌─────────┐    요청    ┌─────────┐    작업    ┌────────┐
│ 사용자  │ ────────> │ API 서버 │ ────────> │  큐    │
└─────────┘           └─────────┘           └────────┘
                           ↑                      ↓
                           │                  ┌────────┐
                           └──────  결과  ─── │ Worker │
                                              └────────┘
```

**장점**:
- 즉각적인 사용자 응답 (UX 향상)
- 무거운 작업(git clone, blame)을 백그라운드 처리
- 수평 확장 가능 (Worker 추가)

### 2. 추상화 기반 설계 (Abstraction-Based Design)

```python
# 환경에 관계없이 동일한 인터페이스
ITaskService
    ├── LocalTaskService  (Redis + Celery)
    └── AwsTaskService    (SQS + AWS Batch)
```

**목적**: 로컬 개발과 AWS 프로덕션 환경 간 최소한의 코드 수정

---

## 📊 현재 프로젝트 상태

### 구현된 기능 ✅
- Docker Compose 기반 멀티 서비스 환경
- Frontend (React + Vite + Tailwind CSS)
- Backend API (FastAPI)
- Worker 분석 엔진 (Celery)
- PostgreSQL 데이터베이스
- Redis 작업 큐
- GitHub OAuth 인증 플로우
- JWT 기반 인증 시스템
- 기본 암호화 유틸리티
- 의존성 주입 패턴 적용
- 작업 추상화 레이어 (TaskService)

### 미구현 / 개선 필요 🔨
- Worker 핵심 분석 로직 완성
- AWS Batch 마이그레이션 준비
- API 엔드포인트 확장
- 프론트엔드 UI 컴포넌트
- 테스트 코드
- 모니터링 및 로깅
- CI/CD 파이프라인

---

## 🛠️ 기술 스택

### Frontend
- **React 19.1**: UI 프레임워크
- **Vite 7.1**: 빌드 도구
- **Tailwind CSS 4.1**: 스타일링
- **React Router 7.9**: 라우팅
- **TypeScript 5.9**: 타입 안정성

### Backend
- **FastAPI 0.115**: 비동기 웹 프레임워크
- **SQLAlchemy 2.0**: ORM
- **Alembic 1.14**: DB 마이그레이션
- **Pydantic 2.10**: 데이터 검증
- **Python-Jose**: JWT 토큰 처리
- **Passlib**: 비밀번호 해싱

### Worker
- **Celery 5.4**: 분산 작업 큐
- **GitPython 3.1**: Git 작업 자동화
- **Redis 5.2**: 작업 브로커

### Infrastructure (로컬)
- **PostgreSQL**: 메인 데이터베이스
- **Redis**: 작업 큐 브로커
- **Docker Compose**: 오케스트레이션

### Infrastructure (AWS 계획)
- **Amazon ECS on Fargate**: API 서버
- **AWS Batch**: Worker 실행
- **Amazon SQS**: 작업 큐
- **Amazon RDS (PostgreSQL)**: 데이터베이스
- **AWS Secrets Manager**: 보안 정보 관리
- **Amazon ECR**: 컨테이너 레지스트리

---

## 📁 프로젝트 구조

```
Sesami/
├── docs/
│   └── design/               # 설계 문서 (이 폴더)
│       ├── 00_OVERVIEW.md
│       ├── 01_SYSTEM_ARCHITECTURE.md
│       ├── 02_LOCAL_DEVELOPMENT.md
│       ├── 03_AWS_MIGRATION.md
│       ├── 04_API_SPECIFICATION.md
│       ├── 05_DATABASE_SCHEMA.md
│       └── 06_IMPLEMENTATION_PLAN.md
│
├── docker/                   # Docker 설정
│   ├── frontend/
│   ├── backend/
│   ├── worker/
│   ├── db/
│   └── queue/
│
├── src/
│   ├── frontend/            # React 애플리케이션
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── contexts/
│   │   │   ├── hooks/
│   │   │   ├── pages/
│   │   │   └── services/
│   │   └── package.json
│   │
│   ├── backend/             # FastAPI 애플리케이션
│   │   ├── common/          # 공통 유틸리티
│   │   │   ├── database.py
│   │   │   ├── dependencies.py
│   │   │   ├── encryption.py
│   │   │   ├── exceptions.py
│   │   │   └── task_service/
│   │   ├── features/        # 기능별 모듈
│   │   │   └── v1/
│   │   │       ├── auth/
│   │   │       ├── github_analysis/
│   │   │       └── webhooks/
│   │   ├── config.py
│   │   └── main.py
│   │
│   └── worker/              # Celery Worker
│       ├── analysis/
│       │   └── git_analyzer.py
│       ├── celery_app.py
│       ├── database.py
│       └── tasks.py
│
├── docker-compose.yml
├── .env
└── README.md
```

---

## 🔄 개발 프로세스

### Phase 1: 로컬 개발 완성 (현재)
1. ✅ 기본 인프라 구축
2. 🔨 Worker 분석 로직 구현
3. 🔨 API 엔드포인트 확장
4. 🔨 Frontend UI 완성
5. 🔨 테스트 작성

### Phase 2: AWS 마이그레이션 준비
1. TaskService 추상화 검증
2. AWS 인프라 설계
3. Docker 이미지 최적화
4. 보안 정책 수립

### Phase 3: AWS 배포
1. ECR 이미지 푸시
2. RDS 마이그레이션
3. ECS/Batch 설정
4. 모니터링 구성

---

## 🔐 보안 고려사항

### 로컬 환경
- `.env` 파일로 민감 정보 관리
- `.gitignore`에 보안 파일 등록
- JWT 토큰 기반 인증

### AWS 환경
- **AWS Secrets Manager**: GitHub 토큰, DB 암호 저장
- **IAM Roles**: 최소 권한 원칙
- **VPC/Security Groups**: 네트워크 격리
- **암호화**: 전송 및 저장 데이터 암호화

---

## 📈 확장성 계획

### 수평 확장
- **API 서버**: ECS 서비스 Auto Scaling
- **Worker**: AWS Batch Compute Environment 스케일링
- **Database**: RDS Read Replica

### 성능 최적화
- **캐싱**: Redis 캐시 레이어
- **비동기 처리**: asyncio 활용
- **배치 처리**: 대량 분석 작업 최적화

---

## 📚 참고 문서

- [GitHub 분석기 PDD v4.0](../projectreadme.md)
- [Docker Compose 설정](../../docker-compose.yml)
- [기존 마이그레이션 문서](../../MIGRATION_GUIDE.md)
- [CORS 수정 가이드](../../CORS_FIX.md)

---

**다음 문서**: [01_SYSTEM_ARCHITECTURE.md](./01_SYSTEM_ARCHITECTURE.md) - 시스템 아키텍처 상세 설계
