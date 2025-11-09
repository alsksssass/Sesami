# Sesami Project Plan v2 (Graph-RAG 버전)

## 1. 격차 분석 및 문서 목적
`docs/design/`(v1)은 초기 PDD를 거의 그대로 반영했으나 `projectreadme.md`에서 제시된 업그레이드(그래프-RAG, 시맨틱 인덱싱, AWS Batch 오케스트레이션, 관측성)를 반영하지 못했습니다. 본 v2 계획서는 다음 내용을 보완합니다.
- L3 에이전트가 의존하는 **Graph-RAG + 시맨틱 검색** 아키텍처를 정식으로 정의합니다.
- AWS Batch·Step Functions·분산 팬아웃 제어가 포함된 **다단 오케스트레이션 파이프라인(L0↔L3)**을 명시합니다.
- 그래프 적재, 임베딩, 안정성 작업을 12주 일정에 맞춰 재배치한 **전달 로드맵**을 제공합니다.
- 시크릿, IaC, CI/CD 등 암묵적이던 **운영 가드레일**을 목록화합니다.

## 2. 제품 목표 및 KPI
1. **인사이트 깊이**: 2GB 미만 저장소의 90%에 대해 90초 이내에 교차 파일 아키텍처 시그널(소유권, 결합도, 리스크)을 도출.
2. **에이전트 신뢰도**: 자동 재시도와 헬스 프로브를 통해 L2/L3 작업 실패율을 5% 이하로 유지.
3. **비용 효율성**: 그래프 캐시와 선택적 시맨틱 검색을 결합해 전체 분석 1건당 비용을 2달러 이하로 유지.

## 3. 시스템 아키텍처 개요
### 3.1 로컬 런타임(`docker-compose.yml`)
- 서비스: `frontend`(React/Vite), `backend`(FastAPI), `worker`(Celery), `db`(PostgreSQL), `queue`(Redis).
- 진입 커맨드: `Makefile`의 `make dev`, `make fresh` 등을 사용하며 기능 개발 시 기본 경로로 삼습니다.

### 3.2 클라우드 런타임(AWS 타깃)
- **API 계층**: ECS Fargate에서 구동되는 FastAPI 컨테이너, ALB 뒤에 배치하며 시크릿은 AWS Secrets Manager에서 주입.
- **비동기 계층**: SQS(ingest/retry)가 AWS Batch 컴퓨팅 환경으로 메시지를 전달하고 `worker/run_analysis.py`를 실행.
- **그래프 + 벡터 저장소**
  - **Neo4j AuraDB**: 코드 지식 그래프를 호스팅하며 Cypher+GDS 활용이 용이. IAM 통합이 더 중요하면 Neptune Serverless v2를 백업안으로 유지.
  - **Amazon OpenSearch Serverless**(또는 자체 운영 Qdrant): 시맨틱 코드 검색용 임베딩을 저장.
- **공유 스토리지**: EFS는 클론된 저장소와 중간 JSONL 산출물을, S3는 패키징 아티팩트 및 캐시된 임베딩을 저장.
- **오케스트레이션**: Step Functions 3계층 상태 머신(L1 글로벌 컨트롤러, L2 분산 Map, L3 툴 러너) 최대 동시성 100, 허용 실패율 5%.

### 3.3 에이전트 워크플로
1. **L0(프론트엔드)**: React 대시보드가 저장소 메타데이터와 필터를 담아 `/api/v1/analysis/start` 호출.
2. **L1(백엔드 FastAPI)**: GitHub OAuth 스코프 검증, 캐시 조회, 작업 페이로드를 SQS에 적재, `analysis_id` 기록.
3. **L2(Step Functions Map)**: `files_to_process`를 팬아웃하며 동시성을 조절하고 각 Batch 작업에 추적 컨텍스트를 주입.
4. **L3(Worker/Batch Job)**:
   - `worker/run_analysis.py`가 `SQS_MESSAGE_BODY`를 읽고 EFS/S3에서 저장소 스냅샷을 가져와 그래프 슬라이스를 생성/재활용, 시맨틱 쿼리를 실행, PostgreSQL + Neo4j로 결과를 전송.
   - 헬스 프로브가 CloudWatch로 지표를 전송하며 실패 시 최대 2회 자동 재시도 후 DLQ에 격리.

## 4. Graph-RAG & 시맨틱 검색 설계도
### 4.1 지식 그래프 스키마
| 노드 | 필수 속성 | 비고 |
| --- | --- | --- |
| `Developer` | `id`, `login`, `email` | GitHub API에서 파생 |
| `Repository` | `id`, `name`, `visibility`, `default_branch` | 프로젝트 메타데이터 연결 |
| `Commit` | `hash`, `timestamp`, `message` | `COMMITTED_BY`, `MODIFIED`로 연결 |
| `File` | `path`, `language`, `loc` | `Class`/`Function` 포함 |
| `Class` | `name`, `file_path` | `INHERITS_FROM` 추가 |
| `Function` | `name`, `signature`, `file_path` | `CALLS` 추가 |
| `Module` | `name`, `type` | import/패키지 정보 |

엣지: `COMMITTED_BY`, `MODIFIED`, `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS_FROM`, `IMPLEMENTS`.

### 4.2 그래프 구축 파이프라인
1. **파싱**: 워커 이미지에 Tree-sitter 파서를 포함(`pip install tree-sitter tree-sitter-python …`). 파일이 일부 깨져도 CST를 생성.
2. **추출**: `tree_sitter_languages.get_language(lang)`과 tree-sitter-graph 쿼리를 사용해 노드/엣지를 산출.
3. **스테이징**: `/mnt/efs/{analysis_id}/graph_nodes.jsonl`, `.../graph_edges.jsonl` 경로에 JSONL로 저장.
4. **적재**: 초기 적재는 Neo4j `neo4j-admin database import`, 증분 적재는 `src/worker/analysis/graph_loader.py`(구현 예정)에서 Cypher `UNWIND` 실행.
5. **버전 관리**: 각 적재에 `graph_snapshot_id`를 부여해 PostgreSQL에 저장, 재현성을 확보.

### 4.3 시맨틱 인덱스
1. **청킹**: 저장소 특성에 맞춘 휴리스틱(기본 200토큰, 오버랩 50) 적용, 그래프 노드 ID를 참조 메타데이터로 기록.
2. **임베딩**: 컴플라이언스 요구에 따라 AWS Bedrock(Titan Text Embeddings) 또는 OpenAI `text-embedding-3-large` 사용, 결과는 S3 + OpenSearch에 캐시.
3. **쿼리 흐름**: L3 에이전트가 먼저 코드 그래프 컨텍스트를 수집한 뒤 자연어 프롬프트를 시맨틱 인덱스에 질의하고, 결합된 근거를 LLM(Anthropic Claude 혹은 GPT-4o mini)에 전달해 최종 판단을 생성.

## 5. 모듈 및 책임 구분
| 컴포넌트 | 저장소 경로 | 비고 |
| --- | --- | --- |
| API 계약 | `src/backend/features/v1` | 인증·분석·웹훅. Pydantic 응답이 가능하면 그래프 ID를 포함해야 함. |
| 작업 추상화 | `src/backend/common/task_service` | 기존 `LocalTaskService` 외에 `AwsBatchTaskService` 추가. |
| 워커 코어 | `src/worker/analysis` | `git_analyzer.py`, `graph_loader.py`, `semantic_search.py` 배치. |
| Batch 엔트리포인트 | `worker/run_analysis.py` | 환경 변수를 읽어 그래프+시맨틱 단계를 조율. |
| 프론트엔드 UI | `src/frontend/src/pages/Analysis` | 그래프 클러스터, 시맨틱 매칭, 점수 등 다계층 인사이트 노출. |
| IaC | `infra/cdk`(생성 예정) | Step Functions, Batch, EFS, Neo4j 시크릿, OpenSearch를 관리. |

## 6. 12주 전달 로드맵
### Phase 1 – 기반 (1~2주)
- `graph_snapshot` 테이블용 DB 마이그레이션 확정.
- `AwsBatchTaskService` 구현 및 GitHub OAuth 보강.
- 로컬 Neo4j/OpenSearch 컨테이너 구성, `make graph-dev` 헬퍼 추가.

### Phase 2 – 그래프 & 시맨틱 빌드 (3~5주)
- Tree-sitter 적재 라이브러리와 단위 테스트 완성.
- `graph_loader.py` 대량 적재 + 롤백 로직 구현.
- 청커 + Bedrock 어댑터를 포함한 임베딩 파이프라인 구축 및 스모크 테스트.
- 프론트엔드: 그래프 인사이트 패널, 시맨틱 검색 UI 컴포넌트 추가.

### Phase 3 – 에이전트 워크플로 & AWS 연동 (6~8주)
- AWS CDK로 Step Functions(L1 오케스트레이터, L2 Map) 정의, `infra/cdk/stacks`에 템플릿 저장.
- Batch Job Definition, ECR 이미지, 최소 권한 IAM 역할 패키징(S3/EFS/Secrets).
- CloudWatch 지표/알람(큐 깊이, 그래프 빌드 시간, 실패율) 연결.
- 백엔드: 그래프+시맨틱 결과를 반환하는 `/api/v1/analysis/{id}/insights` API 추가.

### Phase 4 – 안정성 & 비용 (9~10주)
- 커밋 해시 기반 그래프 스냅샷 재사용, 시맨틱 결과 메모이제이션 도입.
- Batch 종료, Neo4j 세션 중단 등 카오스 테스트로 재시도 로직 검증.
- 백엔드/워커에 AWS X-Ray + OpenTelemetry 기반 분산 추적 도입.

### Phase 5 – 출시 준비 (11~12주)
- GitHub 토큰, 정적 시크릿 등 보안 표면 취약점 점검.
- GitHub Actions `deploy.yml`을 OIDC→AWS 롤, 멀티 아키텍처 Docker 빌드, 자동 마이그레이션까지 포함하도록 마무리.
- 파일럿 분석을 수행하고 메트릭·런북을 정리.

## 7. 운영 가드레일
- **시크릿**: GitHub/DB 자격 증명을 이미지에 포함하지 말 것. 로컬 외 환경에서는 Secrets Manager 또는 SSM Parameter Store에서 주입.
- **스키마·계약 변경**: 머지 전 `docs/design/v2/PROJECT_PLAN_V2.md`와 관련 마이그레이션 가이드(`MIGRATION_GUIDE.md`, `UUID_MIGRATION.md`)를 업데이트.
- **테스트**: 최소 기준—백엔드/워커 `pytest`, 프론트엔드 `npm run lint && npm run test`, `make ci`로 통합 스모크 실행.
- **관측성**: Correlation ID가 포함된 JSON 구조 로그를 표준으로 삼고, CloudWatch(및 로컬 Loki)로 전송.

## 8. 다음 액션
1. Phase 1 전달물별 이슈를 생성하고 본 계획서 링크를 첨부.
2. Neo4j/OpenSearch Docker 서비스와 `src/backend/config.py` 내 연결 설정을 구현.
3. 그래프 스키마와 AWS 아키텍처를 확정하기 위한 디자인 리뷰를 이번 주 내로 일정화.

이해관계자 승인을 받으면 v2를 기준 문서로 삼고, v1은 참고용 기록만 유지합니다.
