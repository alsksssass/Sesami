# Sesami v2 Alignment Work Plan

본 문서는 현재 레포지토리 상태를 [`CLAUDE.md`](../CLAUDE.md)에 정의된 최신 아키텍처/운영 지침과 비교하여, 필요한 구현 과제를 단계별로 정리한 작업 계획서입니다.

## 0. 현황 요약

- **프론트엔드**: React/Vite 기반 주요 화면(로그인, 저장소 선택, 분석 상태/결과 등) 골격 구현. API 연동은 아직 실제 백엔드가 없어 실패할 가능성이 큼.
- **백엔드**: FastAPI 애플리케이션 및 의존성 미구현. `docker/backend/Dockerfile`이 `requirements.txt`를 기대하지만 파일이 없음.
- **워커**: Celery/분석 로직 미구현, Dockerfile만 존재.
- **데이터 계층**: PostgreSQL/Redis 컨테이너 정의는 있으나 Neo4j/OpenSearch 등 Graph-RAG 컴포넌트 미구성.
- **운영 툴링**: 마이그레이션, 테스트, 관측성, 시크릿 전략 미정.

이하 단계는 `CLAUDE.md`의 우선 순위를 기준으로, 레포지토리를 실사용 가능한 상태로 수렴시키기 위한 순차 작업을 제안합니다.

## 1. 백엔드 & 공통 모듈 베이스라인

1. FastAPI 프로젝트 스캐폴딩
   - `src/backend/app/main.py`, 라우터 구조, 설정 모듈 구성
   - Pydantic v2, SQLAlchemy 2.0 스타일 채택 (`CLAUDE.md` 요구)
2. 데이터베이스 스키마 초기화
   - `analysis`, `analysis_task`, `graph_snapshot` 등 핵심 테이블 모델/마이그레이션 정의
   - Alembic 설정 및 `alembic.ini`, `env.py` 구성
3. TaskService 추상화 도입
   - `src/backend/common/task_service/base.py`에 `ITaskService` 인터페이스 정의
   - 로컬 기본 구현(`LocalTaskService`)은 Celery 호출을 목킹하도록 stub 작성
4. API 엔드포인트 1차 구현
   - `/api/v1/analysis/start`, `/status/{id}`, `/result/{id}` 등 프론트엔드에서 호출하는 최소 경로
   - Swagger/OpenAPI 문서 자동 노출 (`/docs`)
5. Docker/Makefile 보정
   - `src/backend/requirements.txt` 추가 및 Dockerfile 빌드 검증

**산출물**: 기본 백엔드 서버 기동 및 프론트엔드에서 API 호출 시 200/404 등 정상 응답.

## 2. 워커 & 큐 처리 파이프라인

1. Celery 앱 초기화
   - `src/worker/celery_app.py` 및 작업 큐 설정 (`Redis` 브로커)
   - `LocalTaskService.enqueue_analysis`가 Celery 태스크를 호출하도록 연결
2. 분석 태스크 스텁 작성
   - `analysis.logic.run_full_analysis` 등 워커 모듈에서 실제 분석 로직을 호출하도록 구조화
   - 현재는 Git 데이터 접근/Graph 연동이 없어, mock 분석 결과를 저장하도록 임시 구현
3. 결과 저장/조회 연동
   - 워커가 완료 후 `analysis`/`analysis_result` 테이블을 업데이트하고 백엔드 API가 이를 반환
4. 테스트 체계
   - Celery 태스크 단위 테스트 및 FastAPI 엔드포인트 통합 테스트 (`pytest` + `httpx` + `pytest-asyncio`)

**산출물**: 로컬 Docker Compose 실행 시 프론트엔드 → 백엔드 → 워커 흐름이 mock 데이터 기준으로 end-to-end 동작.

## 3. Graph-RAG 파이프라인 구축

1. 코드 파싱 단계
   - Tree-sitter 기반 파서 래퍼 구현, 분석 대상 저장소를 로컬 디렉터리에 클론
   - 그래프 노드/엣지 JSONL 생성 (`/mnt/efs/{analysis_id}/graph_nodes.jsonl` 등)
2. Neo4j 적재 레이어
   - 초기 bulk import 및 증분 로더(`graph_loader.py`) 구현
   - Docker Compose에 Neo4j 서비스 추가, 관련 환경 변수/볼륨 구성
3. 시맨틱 인덱스
   - 텍스트 청킹, 임베딩 생성(Bedrock/OpenAI), OpenSearch/Qdrant 적재 로직 구현
   - 재사용을 위한 S3 캐싱 전략 인터페이스 정의 (로컬에서는 로컬 파일 시스템 사용)
4. API 확장
   - Graph-RAG 기반 질의 API, 분석 리포트 생성 엔드포인트 추가
   - 프론트엔드와의 연동 스펙 정의 및 문서화

**산출물**: Graph 및 시맨틱 인덱스를 생성/조회할 수 있는 백엔드/워커 기능, 관련 테스트 및 운영 가이드.

## 4. AWS 프로덕션 경로 & 관측성

1. TaskService AWS 구현체
   - `AwsBatchTaskService` 작성: SQS 메시지 생성, Step Functions/Bacth 연동 모듈화
   - 인프라 IaC 초안(Terraform/CloudFormation) 작성 혹은 수동 절차 문서화
2. 시크릿/구성 관리
   - `.env` 템플릿 정리, AWS Secrets Manager/SSM Parameter Store 활용 가이드
3. 관측성 체계
   - 구조화 로그(JSON) 설정, OpenTelemetry 트레이싱 훅, Prometheus/CloudWatch 메트릭 수집 포인트 정의
4. 운영 가이드
   - 배포 파이프라인(CI/CD) 요구사항, 롤백 전략, 데이터 마이그레이션 가이드 (`docs/design/v2/PROJECT_PLAN_V2.md` 연계)

**산출물**: 프로덕션 배포 시 필요한 AWS 연동 코드와 운영 문서.

## 5. 프론트엔드 고도화

1. Graph-RAG 결과 시각화 컴포넌트 설계
2. 분석 진행/실패 상태에 대한 실시간 갱신(UI 폴링 또는 WebSocket)
3. 사용자 온보딩, 접근 제어, 보고서 내보내기(예: PDF)
4. E2E 테스트(Cypress/Playwright) 및 접근성 점검

**산출물**: 백엔드 기능과 동기화된 UX, 테스트 커버리지 확대.

## 6. 문서 & 지식 정리

1. README/CLAUDE.md/디자인 문서 동기화 프로세스 확립
2. 개발자 온보딩 가이드 (`docs/GETTING_STARTED.md`) 작성
3. API 레퍼런스 자동 생성/게시 방법 정의
4. 장애 대응/트러블슈팅 런북 작성

---

### 진행 우선순위 제안

1. **백엔드/워커 베이스라인 구축 (섹션 1-2)** — 프론트엔드와의 최소 기능 연동 확보
2. **Graph-RAG 파이프라인 (섹션 3)** — 제품 핵심 가치 창출
3. **AWS 연동 및 관측성 (섹션 4)** — 프로덕션 신뢰성 확보
4. **프론트엔드/문서 고도화 (섹션 5-6)** — 사용자 경험 및 운영 효율 개선

각 단계 완료 후에는 `CLAUDE.md`와 본 계획서를 재검토하여 다음 작업 범위를 조정하세요.
