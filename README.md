# Sesami - GitHub Contribution Analyzer

Sesami는 GitHub 저장소와 개발자의 활동을 분석해 **정량/정성 기여 지표**와 **Graph-RAG 기반 인사이트**를 제공하는 플랫폼을 목표로 합니다. 최신 아키텍처 방향은 [`CLAUDE.md`](./CLAUDE.md)에 정리되어 있으며, 본 문서는 현재 레포지토리 상태와 구축 계획을 한눈에 파악할 수 있도록 정리합니다.

## 현재 구현 현황 요약

| 영역 | 현재 레포지토리 상태 | 최신 아키텍처 방향 (`CLAUDE.md`) |
| --- | --- | --- |
| 프론트엔드 | React 19 + Vite + Tailwind 기반 UI, OAuth 흐름/분석 뷰 등 주요 페이지 골격 존재 | 동일 스택 유지, Graph-RAG 결과 시각화 및 분석 리포트 UX 고도화 |
| 백엔드 | 코드 미구현 (`src/backend` 비어 있음) | FastAPI + PostgreSQL + SQLAlchemy 2.0, TaskService 추상화, Graph/Vector 파이프라인 API |
| 워커 | 코드 미구현 (`src/worker` 비어 있음) | 로컬: Celery + Redis, 프로덕션: AWS Batch + Step Functions + SQS |
| 데이터 계층 | Docker Compose로 PostgreSQL/Redis 컨테이너 스켈레톤만 정의 | PostgreSQL + Neo4j + OpenSearch, 그래프 스냅샷/시맨틱 인덱스 파이프라인 |
| 인프라/운영 | Docker/Makefile 스켈레톤 존재 | AWS 기반 관측성(X-Ray, CloudWatch), 시크릿/배포 전략 정립 |

👉 전체 아키텍처와 목표 기능의 세부 사항은 [`CLAUDE.md`](./CLAUDE.md)를 참고하세요.

## 디렉터리 구조

```
Sesami/
├── docker/                 # Docker 빌드 컨텍스트 (backend/worker 이미지는 추후 구현 필요)
├── docker-compose.yml      # 로컬 멀티 서비스 구성 (현 단계에선 backend/worker 컨테이너 실행 불가)
├── docs/                   # 설계 문서, 작업 계획 등
├── src/
│   ├── frontend/           # React/Vite 애플리케이션 (현재 유일한 실제 구현 영역)
│   ├── backend/            # FastAPI 서비스 자리 (현재 .gitkeep만 존재)
│   └── worker/             # 분석 워커 자리 (현재 .gitkeep만 존재)
├── Makefile                # Docker Compose 헬퍼 명령
├── CLAUDE.md               # 최신 아키텍처/운영 가이드
└── README.md               # 현재 문서
```

## 개발 환경 준비

### 1. 프론트엔드 단독 실행 (임시)

백엔드/워커 구현 전까지는 프론트엔드만 로컬에서 확인할 수 있습니다.

```bash
cd src/frontend
npm install
npm run dev
```

> `.env`의 `VITE_BACKEND_URL`은 아직 구현되지 않은 API 엔드포인트를 가리킵니다. 프론트엔드 API 호출은 네트워크 에러가 발생할 수 있으며, 목 데이터/Mocking이 필요합니다.

### 2. Docker Compose 스켈레톤

전체 스택 실행용 명령은 이미 마련되어 있으나, 백엔드/워커 이미지 빌드에 필요한 코드와 `requirements.txt` 등이 아직 없습니다. 코드가 준비된 이후에는 아래 명령으로 통합 환경을 띄울 수 있습니다.

```bash
make dev          # docker-compose up
make dev-d        # 백그라운드 실행
make stop / down  # 컨테이너 종료
make logs         # 통합 로그 스트림 확인
```

> `docker/backend/Dockerfile`, `docker/worker/Dockerfile` 등은 추후 FastAPI/Celery 애플리케이션 코드와 의존성을 추가해야 정상 빌드됩니다.

## 테스트 & 품질

- 프론트엔드: `npm run lint`, `npm test`, `npm run build`
- 백엔드/워커: 아직 테스트 코드 없음. `CLAUDE.md`에서는 `pytest` 기반 백엔드 테스트, 통합 스모크(`make ci`)를 목표로 합니다.

## 목표 아키텍처 하이라이트

`CLAUDE.md`에서 정의된 주요 아키텍처 방향은 다음과 같습니다.

- **TaskService 추상화**: 로컬(Celery)과 프로덕션(AWS Batch) 환경 간 작업 큐 구현을 스위치할 수 있는 인터페이스.
- **Graph-RAG 파이프라인**: Tree-sitter 기반 AST 추출 → Neo4j 적재 → OpenSearch 시맨틱 인덱싱.
- **관측성 및 운영 가드레일**: CloudWatch/X-Ray, Secrets Manager, 테스트/마이그레이션 절차 등.

이러한 요소들은 현재 코드베이스에는 구현되어 있지 않으며, 향후 작업 계획(`docs/WORK_PLAN.md`)에 따라 점진적으로 반영될 예정입니다.

## 다음 단계

- [`docs/WORK_PLAN.md`](./docs/WORK_PLAN.md)에 최신 아키텍처 대비 누락된 구현 목록과 우선순위를 정리했습니다.
- 우선 백엔드/워커 코드 스캐폴딩과 TaskService 인터페이스 정의부터 진행하고, 이후 그래프/시맨틱 파이프라인과 AWS 인프라 요소를 순차적으로 도입하는 것이 권장됩니다.

---

문의나 논의가 필요하면 이슈/PR에 `architecture`, `backend`, `worker`, `graph-rag` 레이블을 사용해 주세요.
