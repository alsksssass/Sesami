# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sesami**는 GitHub 기여도 분석 플랫폼으로, **Graph-RAG 기반 코드 지식 그래프**를 활용하여 개발자의 정량적·정성적 기여도를 심층 분석합니다.

**핵심 기능 (v2 업그레이드)**:
- GitHub OAuth 인증으로 Private Repository 접근
- `git blame` 기반 자동 기여도 분석
- **Graph-RAG**: 코드 지식 그래프(Neo4j) + 시맨틱 검색으로 교차 파일 아키텍처 인사이트 도출
- **시맨틱 코드 검색**: OpenSearch/Qdrant 기반 임베딩 검색으로 자연어 쿼리 지원
- 기술 스택 분석 및 시계열 트렌드 추적

**v2 주요 변경사항**:
- **지식 그래프**: Tree-sitter 파서로 AST 추출 → Neo4j에 코드 구조(파일, 함수, 클래스, 호출 관계) 저장
- **시맨틱 인덱스**: AWS Bedrock/OpenAI 임베딩 → OpenSearch Serverless에 벡터 저장
- **멀티 에이전트 오케스트레이션**: Step Functions(L1 컨트롤러 + L2 팬아웃 Map) + AWS Batch(L3 툴 러너)
- **관측성**: CloudWatch + X-Ray/OpenTelemetry 기반 분산 추적

**3-Tier 비동기 아키텍처**:
- **Frontend**: React 19 + Vite + Tailwind CSS + TypeScript
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy 2.0
- **Worker**: Celery (로컬) → AWS Batch (프로덕션)
- **Queue**: Redis (로컬) → Amazon SQS (프로덕션)
- **Graph Store**: Neo4j AuraDB (또는 Neptune Serverless v2)
- **Vector Store**: Amazon OpenSearch Serverless (또는 Qdrant)
- **Shared Storage**: EFS (클론 저장소, JSONL), S3 (임베딩 캐시)

**핵심 설계 패턴**: `TaskService` 추상화로 로컬↔AWS 환경 전환 시 비즈니스 로직 수정 없이 마이그레이션 가능

**제품 KPI (v2)**:
- 인사이트 깊이: 2GB 미만 저장소 90%를 90초 이내 분석
- 에이전트 신뢰도: L2/L3 작업 실패율 5% 이하
- 비용 효율성: 분석 1건당 2달러 이하

---

## Development Commands

### 로컬 환경 시작
```bash
# Docker Compose로 전체 시스템 실행
docker-compose up --build
docker-compose up -d --build  # 백그라운드 실행

# Graph-RAG 개발 환경 (v2)
make graph-dev  # Neo4j + OpenSearch 로컬 컨테이너 포함

# 로그 확인
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f worker
```

### 서비스 접속
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **PostgreSQL**: `psql postgresql://sesami_user:sesami_password_2025@localhost:5432/sesami_db`
- **Redis**: `redis-cli -h localhost -p 6379`
- **Neo4j Browser** (로컬): http://localhost:7474
- **OpenSearch Dashboards** (로컬): http://localhost:5601

### 컨테이너 셸 접속
```bash
docker-compose exec backend bash
docker-compose exec frontend sh
docker-compose exec worker bash
docker-compose exec db psql -U sesami_user sesami_db
docker-compose exec neo4j cypher-shell -u neo4j -p password
```

### 데이터베이스 마이그레이션
```bash
# Backend 컨테이너 내부에서 실행
docker-compose exec backend bash

# 마이그레이션 생성 (graph_snapshot 테이블 포함)
alembic revision --autogenerate -m "migration description"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1

# 현재 상태 확인
alembic current
```

### Worker 모니터링
```bash
# 활성 작업 확인
docker-compose exec worker celery -A celery_app inspect active

# Worker 상태
docker-compose exec worker celery -A celery_app status

# Redis 큐 깊이 확인
docker-compose exec queue redis-cli LLEN celery
```

### 그래프 작업 (v2)
```bash
# Neo4j 데이터 임포트 (초기 적재)
docker-compose exec neo4j neo4j-admin database import \
  --nodes=/import/graph_nodes.jsonl \
  --relationships=/import/graph_edges.jsonl

# 그래프 스냅샷 확인
docker-compose exec backend python -c "
from common.database import SessionLocal
db = SessionLocal()
snapshots = db.execute('SELECT * FROM graph_snapshot').fetchall()
print(snapshots)
"
```

### 테스트 실행
```bash
# Backend 테스트
docker-compose exec backend pytest
docker-compose exec backend pytest tests/test_auth.py -v
docker-compose exec backend pytest tests/test_graph_loader.py -v  # v2 추가

# Frontend 테스트
docker-compose exec frontend npm test
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run build

# 통합 스모크 테스트
make ci
```

### 환경 정리
```bash
# 컨테이너 중지
docker-compose down

# 컨테이너 + 볼륨 삭제 (⚠️ DB + Graph 데이터 삭제)
docker-compose down -v

# 캐시 무효화 재빌드
docker-compose build --no-cache
docker-compose up --build --force-recreate
```

---

## Architecture Deep Dive

### 1. TaskService 추상화 패턴 (핵심)

**목적**: 로컬 개발(Celery)과 AWS 프로덕션(SQS+Batch) 환경에서 동일한 비즈니스 로직 사용

**위치**: `src/backend/common/task_service/`

**구조**:
```
task_service/
├── base.py              # ITaskService 인터페이스 정의
├── local_service.py     # LocalTaskService (Celery + Redis)
└── aws_batch_service.py # AwsBatchTaskService (SQS + AWS Batch) - 🔨 Phase 1 구현 예정
```

**핵심 인터페이스**:
```python
class ITaskService(ABC):
    @abstractmethod
    async def enqueue_analysis(
        self,
        analysis_id: UUID,
        repo_url: str,
        target_user: str
    ) -> str:
        """분석 작업을 큐에 추가"""
        pass
```

**환경 전환 로직**:
- 환경변수 `TASK_SERVICE_IMPL` 값에 따라 구현체 선택
- `"LOCAL"` → `LocalTaskService` (Celery)
- `"AWS_BATCH"` → `AwsBatchTaskService` (SQS + Step Functions)

**사용 예시**:
```python
# Backend API에서
from common.dependencies import get_task_service

@router.post("/analysis/start")
async def start_analysis(
    task_service: ITaskService = Depends(get_task_service)
):
    job_id = await task_service.enqueue_analysis(...)
    return {"job_id": job_id}
```

### 2. Graph-RAG 아키텍처 (v2 핵심)

**지식 그래프 스키마** (Neo4j):

| 노드 타입 | 필수 속성 | 관계 |
|----------|----------|------|
| `Developer` | `id`, `login`, `email` | `COMMITTED_BY` |
| `Repository` | `id`, `name`, `visibility`, `default_branch` | `CONTAINS` |
| `Commit` | `hash`, `timestamp`, `message` | `COMMITTED_BY`, `MODIFIED` |
| `File` | `path`, `language`, `loc` | `CONTAINS` → `Class`, `Function` |
| `Class` | `name`, `file_path` | `INHERITS_FROM`, `IMPLEMENTS` |
| `Function` | `name`, `signature`, `file_path` | `CALLS` |
| `Module` | `name`, `type` | `IMPORTS` |

**그래프 구축 파이프라인**:
```
1. 파싱 (Tree-sitter)
   ↓
2. AST 추출 → JSONL 생성
   (/mnt/efs/{analysis_id}/graph_nodes.jsonl, graph_edges.jsonl)
   ↓
3. 적재 (Neo4j)
   - 초기: neo4j-admin database import
   - 증분: graph_loader.py (Cypher UNWIND)
   ↓
4. 버전 관리
   - graph_snapshot_id → PostgreSQL 저장
```

**시맨틱 인덱스 파이프라인**:
```
1. 청킹 (기본 200토큰, 오버랩 50)
   ↓
2. 임베딩 생성
   - AWS Bedrock (Titan Text Embeddings)
   - 또는 OpenAI (text-embedding-3-large)
   ↓
3. 벡터 저장
   - Amazon OpenSearch Serverless
   - 메타데이터: 그래프 노드 ID 참조
   ↓
4. 캐싱 (S3)
   - 커밋 해시 기반 재사용
```

**Graph-RAG 쿼리 흐름**:
```
사용자 쿼리 (자연어)
   ↓
1. 그래프 컨텍스트 수집 (Neo4j Cypher)
   - 소유권, 결합도, 호출 관계
   ↓
2. 시맨틱 검색 (OpenSearch)
   - 유사 코드 블록 검색
   ↓
3. 컨텍스트 결합 → LLM (Claude/GPT-4o)
   - 최종 인사이트 생성
```

### 3. 멀티 에이전트 워크플로 (v2)

**L0 (프론트엔드)**:
- React 대시보드 → `/api/v1/analysis/start` 호출
- 저장소 메타데이터 + 필터 전송

**L1 (백엔드 FastAPI)**:
- GitHub OAuth 스코프 검증
- 캐시 조회 (graph_snapshot 테이블)
- 작업 페이로드 → SQS 전송
- `analysis_id` 기록

**L2 (Step Functions Map)**:
- `files_to_process`를 최대 동시성 100으로 팬아웃
- 각 Batch Job에 추적 컨텍스트 주입
- 실패 허용율 5%

**L3 (Worker/Batch Job)**:
```python
# worker/run_analysis.py
def main():
    # 1. SQS 메시지 파싱
    job_data = json.loads(os.environ['SQS_MESSAGE_BODY'])

    # 2. EFS/S3에서 저장소 스냅샷 가져오기
    repo_path = fetch_from_efs(job_data['analysis_id'])

    # 3. 그래프 슬라이스 생성/재활용
    graph_loader.load_or_reuse(job_data['commit_hash'])

    # 4. 시맨틱 쿼리 실행
    semantic_results = semantic_search.query(job_data['query'])

    # 5. PostgreSQL + Neo4j로 결과 전송
    save_results(job_data['analysis_id'], semantic_results)

    # 6. 헬스 프로브 → CloudWatch
    report_metrics()

    # 7. 성공 시 SQS 메시지 삭제, 실패 시 DLQ
```

**재시도 로직**:
- 최대 2회 자동 재시도
- 실패 시 DLQ에 격리
- CloudWatch Alarm 트리거

### 4. Feature-Based 모듈 구조

**자동 등록 패턴**: 각 Feature는 독립적으로 라우터를 등록

**디렉토리 구조**:
```
src/backend/features/v1/
├── auth/                # 인증 모듈
│   ├── api.py           # APIRouter 정의
│   ├── models.py        # SQLAlchemy ORM
│   ├── schemas.py       # Pydantic 스키마
│   ├── github_service.py
│   └── jwt_service.py
├── github_analysis/     # 분석 모듈
│   ├── api.py
│   ├── models.py
│   ├── schemas.py
│   └── services/
│       ├── analysis_service.py
│       └── github_api_service.py
└── webhooks/            # Webhook 모듈
    ├── api.py
    ├── models.py
    └── schemas.py
```

**새로운 Feature 추가 방법**:
1. `features/v1/{feature_name}/` 디렉토리 생성
2. `api.py`에 `router = APIRouter(prefix="/api/v1/{name}", tags=["{name}"])` 작성
3. `features/v1/__init__.py`에서 import하면 자동 등록됨

### 5. 의존성 주입 (Dependency Injection)

**FastAPI Depends()로 DB 세션, 인증, 서비스 주입**

**DB 세션 관리**:
```python
from common.dependencies import get_db
from sqlalchemy.orm import Session

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
# 세션 자동 commit/rollback/close
```

**현재 사용자 인증**:
```python
from common.dependencies import get_current_user

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
# JWT 토큰 검증 후 User 객체 반환
```

**TaskService 주입**:
```python
from common.dependencies import get_task_service

@router.post("/analysis")
async def create_analysis(
    task_service: ITaskService = Depends(get_task_service)
):
    # 환경에 따라 LocalTaskService 또는 AwsBatchTaskService 주입됨
    pass
```

### 6. Worker 분석 로직 (v2 업데이트)

**현재 상태**: 기본 git blame 로직 외에 **Graph-RAG 파이프라인 구현 필요**

**필요 구현**:

#### 6.1 `src/worker/analysis/git_analyzer.py` (기본)
```python
class GitAnalyzer:
    def clone_repository(self) -> str:
        """GitHub 토큰으로 Private 저장소 클론"""
        # https://oauth2:TOKEN@github.com/user/repo.git 형식 사용
        pass

    def analyze_blame(self, user_email: str) -> Dict[str, float]:
        """git blame으로 사용자 기여도 계산"""
        # 모든 파일 순회하며 git blame --line-porcelain 실행
        # user_lines / total_lines 계산
        pass

    def analyze_tech_stack(self) -> Dict[str, any]:
        """파일 확장자 및 프레임워크 감지"""
        # .py, .js, .ts 등 확장자 카운트
        # package.json, requirements.txt 등 프레임워크 파일 감지
        pass

    def cleanup(self):
        """임시 클론 디렉토리 삭제"""
        pass
```

#### 6.2 `src/worker/analysis/graph_loader.py` (v2 신규)
```python
class GraphLoader:
    """Neo4j 그래프 적재 및 버전 관리"""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def parse_with_tree_sitter(self, file_path: str, language: str) -> Dict:
        """Tree-sitter로 AST 파싱"""
        # tree-sitter-python, tree-sitter-javascript 등 사용
        # 노드(Class, Function) + 엣지(CALLS, IMPORTS) 추출
        pass

    def stage_to_jsonl(self, nodes: List, edges: List, analysis_id: str):
        """EFS에 JSONL 스테이징"""
        # /mnt/efs/{analysis_id}/graph_nodes.jsonl
        # /mnt/efs/{analysis_id}/graph_edges.jsonl
        pass

    def bulk_load_to_neo4j(self, analysis_id: str):
        """Neo4j 대량 적재 (Cypher UNWIND)"""
        # UNWIND $nodes AS node CREATE (n:File {path: node.path, ...})
        # UNWIND $edges AS edge MATCH (a), (b) CREATE (a)-[:CALLS]->(b)
        pass

    def create_snapshot(self, commit_hash: str, analysis_id: str) -> str:
        """PostgreSQL에 graph_snapshot 레코드 생성"""
        # graph_snapshot_id 반환
        pass

    def reuse_snapshot(self, commit_hash: str) -> Optional[str]:
        """기존 스냅샷 재사용 가능 여부 확인"""
        # 커밋 해시 기반 캐시 조회
        pass
```

#### 6.3 `src/worker/analysis/semantic_search.py` (v2 신규)
```python
class SemanticSearch:
    """시맨틱 코드 검색 (OpenSearch/Qdrant)"""

    def __init__(self, opensearch_endpoint: str, bedrock_client):
        self.opensearch = OpenSearch([opensearch_endpoint])
        self.bedrock = bedrock_client

    def chunk_code(self, file_content: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
        """코드 청킹"""
        # 함수 단위 또는 토큰 단위 청킹
        pass

    def generate_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
        """AWS Bedrock 임베딩 생성"""
        # bedrock.invoke_model("amazon.titan-embed-text-v1")
        pass

    def index_to_opensearch(self, embeddings: List, metadata: List[Dict]):
        """OpenSearch에 벡터 인덱싱"""
        # 메타데이터: graph_node_id, file_path, chunk_text
        pass

    def query(self, natural_language_query: str, k: int = 5) -> List[Dict]:
        """자연어 쿼리로 유사 코드 검색"""
        query_embedding = self.generate_embeddings([natural_language_query])[0]
        results = self.opensearch.search(
            index="code_embeddings",
            body={"query": {"knn": {"vector": query_embedding, "k": k}}}
        )
        return results
```

**상세 구현 가이드**: `docs/design/v2/PROJECT_PLAN_V2.md` 참조

### 7. 인증 및 보안

**GitHub OAuth 2.0 + JWT 인증 플로우**:
```
1. 사용자 "GitHub 로그인" 클릭
   ↓
2. Frontend → Backend GET /api/v1/auth/github
   ↓
3. Backend → GitHub OAuth 페이지로 리디렉션
   ↓
4. GitHub에서 사용자 권한 승인
   ↓
5. GitHub → Backend Callback (code 포함)
   ↓
6. Backend: code → access_token 교환
   ↓
7. Backend: GitHub API로 사용자 정보 조회
   ↓
8. Backend: access_token 암호화 저장 (Fernet)
   ↓
9. Backend: JWT 토큰 생성 (15분 유효)
   ↓
10. Frontend: JWT 저장 및 API 요청 시 Header 포함
```

**암호화**:
- GitHub Access Token: Fernet 암호화 후 DB 저장
- 암호화 키: `.env`의 `ENCRYPTION_KEY` (생성: `Fernet.generate_key()`)

**JWT 설정**:
- Access Token: 15분 만료
- Refresh Token: 7일 만료
- Algorithm: HS256

---

## 환경 변수 설정

### 필수 `.env` 변수

**데이터베이스**:
```bash
POSTGRES_USER=sesami_user
POSTGRES_PASSWORD=sesami_password_2025
POSTGRES_DB=sesami_db
DATABASE_URL=postgresql://sesami_user:sesami_password_2025@db:5432/sesami_db
```

**Queue (Redis)**:
```bash
REDIS_HOST=queue
REDIS_PORT=6379
QUEUE_BROKER_URL=redis://queue:6379/0
CELERY_BROKER_URL=redis://queue:6379/0
CELERY_RESULT_BACKEND=redis://queue:6379/0
```

**Graph Store (Neo4j)** - v2 추가:
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

**Vector Store (OpenSearch)** - v2 추가:
```bash
OPENSEARCH_ENDPOINT=https://opensearch:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=your_opensearch_password
```

**AWS Bedrock (임베딩)** - v2 추가:
```bash
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.titan-embed-text-v1
```

**GitHub OAuth**:
```bash
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback
```

**보안**:
```bash
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Fernet 암호화 키 생성
ENCRYPTION_KEY=your-fernet-encryption-key-base64
```

**애플리케이션**:
```bash
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
TASK_SERVICE_IMPL=LOCAL  # 또는 AWS_BATCH
```

**Shared Storage (AWS)** - v2 추가:
```bash
EFS_MOUNT_PATH=/mnt/efs
S3_EMBEDDING_CACHE_BUCKET=sesami-embeddings-cache
```

### 암호화 키 생성
```bash
python3 << 'EOF'
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f"ENCRYPTION_KEY={key.decode()}")
EOF
```

---

## AWS 마이그레이션 전략

**상세 문서**: `docs/design/v2/PROJECT_PLAN_V2.md`

### 컴포넌트 매핑 (v2 업데이트)

| 로컬 환경 | AWS 서비스 | 변경 사항 |
|----------|----------|----------|
| Frontend (React) | CloudFront + S3 | `npm run build` → S3 업로드 |
| Backend (FastAPI) | ECS on Fargate | Docker 이미지 → ECR → ECS |
| Worker (Celery) | AWS Batch + Step Functions | `run_analysis.py` 작성, L1/L2/L3 오케스트레이션 |
| PostgreSQL | Amazon RDS | `pg_dump` → RDS 복원 |
| Redis | Amazon SQS | TaskService 구현체 교체 |
| Neo4j (로컬) | Neo4j AuraDB | 또는 Neptune Serverless v2 |
| OpenSearch (로컬) | OpenSearch Serverless | 벡터 인덱스 마이그레이션 |
| .env | Secrets Manager | 환경변수 → Secrets 이관 |
| - | EFS | 클론 저장소, JSONL 스테이징 |
| - | S3 | 임베딩 캐시, 아티팩트 |

### AWS Step Functions 오케스트레이션 (v2)

**L1 (글로벌 컨트롤러)**:
```json
{
  "Comment": "Sesami Analysis Orchestration",
  "StartAt": "ValidateInput",
  "States": {
    "ValidateInput": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:ValidateAnalysisRequest",
      "Next": "CheckCache"
    },
    "CheckCache": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:CheckGraphSnapshot",
      "Next": "FanOutFiles"
    },
    "FanOutFiles": {
      "Type": "Map",
      "ItemsPath": "$.files_to_process",
      "MaxConcurrency": 100,
      "Iterator": {
        "StartAt": "SubmitBatchJob",
        "States": {
          "SubmitBatchJob": {
            "Type": "Task",
            "Resource": "arn:aws:states:::batch:submitJob.sync",
            "Parameters": {
              "JobDefinition": "sesami-worker",
              "JobQueue": "sesami-job-queue",
              "ContainerOverrides": {
                "Environment": [
                  {"Name": "FILE_PATH", "Value.$": "$.file_path"},
                  {"Name": "ANALYSIS_ID", "Value.$": "$.analysis_id"}
                ]
              }
            },
            "Retry": [
              {
                "ErrorEquals": ["States.TaskFailed"],
                "MaxAttempts": 2,
                "BackoffRate": 2
              }
            ],
            "Catch": [
              {
                "ErrorEquals": ["States.ALL"],
                "ResultPath": "$.error",
                "Next": "LogToDLQ"
              }
            ],
            "End": true
          },
          "LogToDLQ": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:SendToDLQ",
            "End": true
          }
        }
      },
      "Next": "AggregateResults"
    },
    "AggregateResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:AggregateGraphResults",
      "End": true
    }
  }
}
```

### 핵심 변경 사항

**1. AwsBatchTaskService 구현** (Phase 1):
```python
# src/backend/common/task_service/aws_batch_service.py
import boto3
import json

class AwsBatchTaskService(ITaskService):
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.sfn = boto3.client('stepfunctions')
        self.queue_url = os.environ['SQS_QUEUE_URL']
        self.state_machine_arn = os.environ['STEP_FUNCTIONS_ARN']

    async def enqueue_analysis(self, analysis_id, repo_url, target_user):
        # Step Functions 실행 시작
        response = self.sfn.start_execution(
            stateMachineArn=self.state_machine_arn,
            input=json.dumps({
                'analysis_id': str(analysis_id),
                'repo_url': repo_url,
                'target_user': target_user
            })
        )
        return response['executionArn']
```

**2. AWS Batch Worker Entry Point** (Phase 3):
```python
# src/worker/run_analysis.py
import os
import json
import boto3
from analysis.git_analyzer import GitAnalyzer
from analysis.graph_loader import GraphLoader
from analysis.semantic_search import SemanticSearch

def main():
    # SQS 메시지에서 작업 정보 파싱
    job_data = json.loads(os.environ['SQS_MESSAGE_BODY'])

    # Secrets Manager에서 GitHub 토큰 가져오기
    secrets = boto3.client('secretsmanager')
    secret = secrets.get_secret_value(SecretId='github-token')
    access_token = json.loads(secret['SecretString'])['token']

    # EFS에서 저장소 스냅샷 가져오기
    efs_path = f"/mnt/efs/{job_data['analysis_id']}"

    # GraphLoader로 그래프 구축
    graph_loader = GraphLoader(
        neo4j_uri=os.environ['NEO4J_URI'],
        neo4j_user=os.environ['NEO4J_USER'],
        neo4j_password=os.environ['NEO4J_PASSWORD']
    )

    # 커밋 해시 기반 캐시 확인
    snapshot_id = graph_loader.reuse_snapshot(job_data['commit_hash'])
    if not snapshot_id:
        # 새로운 그래프 빌드
        nodes, edges = graph_loader.parse_with_tree_sitter(efs_path)
        graph_loader.stage_to_jsonl(nodes, edges, job_data['analysis_id'])
        graph_loader.bulk_load_to_neo4j(job_data['analysis_id'])
        snapshot_id = graph_loader.create_snapshot(job_data['commit_hash'], job_data['analysis_id'])

    # SemanticSearch로 임베딩 생성 및 인덱싱
    semantic = SemanticSearch(
        opensearch_endpoint=os.environ['OPENSEARCH_ENDPOINT'],
        bedrock_client=boto3.client('bedrock-runtime')
    )
    chunks = semantic.chunk_code(file_content)
    embeddings = semantic.generate_embeddings(chunks)
    semantic.index_to_opensearch(embeddings, metadata)

    # 결과 저장
    save_results(job_data['analysis_id'], snapshot_id)

    # CloudWatch 메트릭 전송
    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='Sesami/Worker',
        MetricData=[
            {'MetricName': 'GraphBuildTime', 'Value': elapsed_time, 'Unit': 'Seconds'},
            {'MetricName': 'EmbeddingCount', 'Value': len(embeddings), 'Unit': 'Count'}
        ]
    )

    # SQS 메시지 삭제
    sqs = boto3.client('sqs')
    sqs.delete_message(
        QueueUrl=os.environ['SQS_QUEUE_URL'],
        ReceiptHandle=os.environ['SQS_RECEIPT_HANDLE']
    )

if __name__ == '__main__':
    main()
```

**3. IaC (AWS CDK)** - Phase 3:
```typescript
// infra/cdk/stacks/sesami-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as batch from 'aws-cdk-lib/aws-batch';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as efs from 'aws-cdk-lib/aws-efs';

export class SesamiStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // EFS for shared storage
    const fileSystem = new efs.FileSystem(this, 'SesamiEFS', {
      vpc: vpc,
      encrypted: true
    });

    // Batch Compute Environment
    const computeEnv = new batch.ComputeEnvironment(this, 'SesamiComputeEnv', {
      computeResources: {
        type: batch.ComputeResourceType.SPOT,
        maxvCpus: 256,
        instanceTypes: [new ec2.InstanceType('c5.xlarge')],
        vpc: vpc
      }
    });

    // Batch Job Definition
    const jobDef = new batch.JobDefinition(this, 'SesamiWorkerJob', {
      container: {
        image: ecs.ContainerImage.fromRegistry('sesami/worker:latest'),
        vcpus: 4,
        memoryLimitMiB: 8192,
        mountPoints: [{
          containerPath: '/mnt/efs',
          sourceVolume: 'efs'
        }],
        environment: {
          NEO4J_URI: neo4jSecret.secretValueFromJson('uri').toString(),
          OPENSEARCH_ENDPOINT: opensearchDomain.domainEndpoint
        }
      }
    });

    // Step Functions State Machine
    const orchestrator = new sfn.StateMachine(this, 'SesamiOrchestrator', {
      definition: l1ControllerChain,
      timeout: cdk.Duration.minutes(30)
    });
  }
}
```

---

## 코드 구조 및 규칙

### 프로젝트 구조 (v2 업데이트)
```
Sesami/
├── docs/
│   └── design/
│       ├── v1/                  # 기록 보존용
│       └── v2/                  # 🎯 최신 계획서 (Graph-RAG)
│           ├── PROJECT_PLAN_V2.md
│           └── README.md
├── infra/
│   └── cdk/                     # AWS CDK IaC (Phase 3 생성)
│       ├── bin/
│       ├── lib/
│       └── stacks/
│           └── sesami-stack.ts
├── src/
│   ├── frontend/                # React + Vite
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── contexts/
│   │   │   ├── hooks/
│   │   │   ├── pages/
│   │   │   │   └── Analysis/   # 그래프 인사이트 UI (v2)
│   │   │   └── services/
│   │   └── package.json
│   ├── backend/                 # FastAPI
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── common/
│   │   │   ├── database.py
│   │   │   ├── dependencies.py
│   │   │   ├── encryption.py
│   │   │   ├── exceptions.py
│   │   │   └── task_service/
│   │   │       ├── base.py
│   │   │       ├── local_service.py
│   │   │       └── aws_batch_service.py  # 🔨 Phase 1
│   │   └── features/v1/
│   │       ├── auth/
│   │       ├── github_analysis/
│   │       │   └── api.py        # /insights 엔드포인트 추가 (v2)
│   │       └── webhooks/
│   └── worker/                  # Celery Worker
│       ├── celery_app.py
│       ├── tasks.py
│       ├── database.py
│       ├── run_analysis.py      # AWS Batch Entry Point (Phase 3)
│       └── analysis/
│           ├── git_analyzer.py
│           ├── graph_loader.py  # 🔨 Phase 2 (Tree-sitter + Neo4j)
│           └── semantic_search.py  # 🔨 Phase 2 (Bedrock + OpenSearch)
├── docker-compose.yml
└── .env
```

### Naming Conventions
- **Python**: `snake_case` (함수/변수), `PascalCase` (클래스)
- **TypeScript**: `camelCase` (함수/변수), `PascalCase` (컴포넌트/타입)
- **파일명**:
  - Python: `snake_case.py`
  - React 컴포넌트: `PascalCase.tsx`
  - 유틸리티: `camelCase.ts`

### Import 순서
```python
# 1. 표준 라이브러리
import os
import json
from typing import Dict, List

# 2. 서드파티 라이브러리
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from neo4j import GraphDatabase  # v2 추가

# 3. 로컬 공통 모듈
from common.database import get_db
from common.exceptions import NotFoundException

# 4. 로컬 Feature 모듈
from .models import User
from .schemas import UserResponse
```

### 에러 처리
```python
# src/backend/common/exceptions.py
from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)

class UnauthorizedException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)

class GraphLoadException(HTTPException):  # v2 추가
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Graph load failed: {detail}")

# 사용 예시
raise NotFoundException(detail="User not found")
raise GraphLoadException(detail="Neo4j connection timeout")
```

---

## 설계 문서 참조

**⭐ v2 우선 참조**: `docs/design/v2/`

| 문서 | 내용 | 버전 |
|-----|------|------|
| `v2/PROJECT_PLAN_V2.md` | **Graph-RAG 종합 계획서** (⭐ 최우선 참조) | v2 |
| `v2/README.md` | v1/v2 차이점 요약 | v2 |
| `v1/00_OVERVIEW.md` | 프로젝트 목표, 기술 스택 (기록용) | v1 |
| `v1/01_SYSTEM_ARCHITECTURE.md` | 기본 3-tier 아키텍처 | v1 |
| `v1/02_LOCAL_DEVELOPMENT.md` | 로컬 환경 구축 | v1 |
| `v1/03_AWS_MIGRATION.md` | AWS 기본 인프라 (v2에서 확장) | v1 |
| `v1/06_IMPLEMENTATION_PLAN.md` | 12주 기본 로드맵 (v2에서 재조정) | v1 |

**참조 우선순위**:
1. **Graph-RAG/시맨틱 검색**: `v2/PROJECT_PLAN_V2.md` (섹션 4)
2. **멀티 에이전트 워크플로**: `v2/PROJECT_PLAN_V2.md` (섹션 3)
3. **12주 로드맵**: `v2/PROJECT_PLAN_V2.md` (섹션 6)
4. **운영 가드레일**: `v2/PROJECT_PLAN_V2.md` (섹션 7)
5. **기본 아키텍처**: `v1/01_SYSTEM_ARCHITECTURE.md`

---

## 현재 구현 상태 (v2 업데이트)

### ✅ 구현 완료
- Docker Compose 멀티 서비스 환경
- FastAPI Backend 구조
- React Frontend 기본 구조
- GitHub OAuth 인증 플로우
- JWT 토큰 시스템
- TaskService 추상화 인터페이스
- LocalTaskService (Celery)
- 데이터베이스 모델 기본 구조

### 🔨 구현 필요 (v2 로드맵)

**Phase 1 (1~2주) - 기반**:
- [ ] `graph_snapshot` 테이블 마이그레이션
- [ ] `AwsBatchTaskService` 구현
- [ ] 로컬 Neo4j + OpenSearch 컨테이너 구성
- [ ] `make graph-dev` 헬퍼 추가

**Phase 2 (3~5주) - Graph-RAG**:
- [ ] Tree-sitter 파서 라이브러리 (`graph_loader.py`)
- [ ] Neo4j 대량 적재 + 롤백 로직
- [ ] Bedrock 임베딩 파이프라인 (`semantic_search.py`)
- [ ] 그래프 인사이트 UI 컴포넌트

**Phase 3 (6~8주) - AWS 연동**:
- [ ] AWS CDK - Step Functions (L1/L2)
- [ ] Batch Job Definition + ECR 이미지
- [ ] CloudWatch 메트릭/알람
- [ ] `/api/v1/analysis/{id}/insights` API

**Phase 4 (9~10주) - 안정성**:
- [ ] 그래프 스냅샷 재사용 (커밋 해시 캐싱)
- [ ] 카오스 테스트 + 재시도 검증
- [ ] X-Ray + OpenTelemetry 분산 추적

**Phase 5 (11~12주) - 출시**:
- [ ] 보안 취약점 점검
- [ ] GitHub Actions CI/CD (OIDC)
- [ ] 파일럿 분석 + 메트릭 정리

### 💡 향후 개선 사항
- LLM 기반 정성 평가 (Claude/GPT-4o 통합)
- 실시간 상태 업데이트 (WebSocket)
- 팀 협업 기능
- 리포트 PDF 내보내기

---

## 운영 가드레일 (v2)

### 시크릿 관리
- ⚠️ **절대 금지**: GitHub/DB 자격 증명을 이미지에 포함
- **로컬**: `.env` 파일 (`.gitignore` 필수)
- **AWS**: Secrets Manager 또는 SSM Parameter Store

### 스키마 변경 프로세스
1. `docs/design/v2/PROJECT_PLAN_V2.md` 업데이트
2. Alembic 마이그레이션 생성 및 테스트
3. `MIGRATION_GUIDE.md` 또는 `UUID_MIGRATION.md` 업데이트
4. PR 생성 및 리뷰

### 테스트 최소 기준
- **Backend**: `pytest` (커버리지 80% 이상)
- **Frontend**: `npm run lint && npm run test`
- **통합**: `make ci` 스모크 테스트

### 관측성 표준
- **로그**: JSON 구조 로그 + Correlation ID
- **메트릭**: CloudWatch (AWS) / Prometheus (로컬)
- **추적**: X-Ray + OpenTelemetry
- **알람**: 큐 깊이, 그래프 빌드 시간, 실패율

---

## Troubleshooting

### 포트 충돌
```bash
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :7474  # Neo4j Browser
lsof -i :9200  # OpenSearch
kill -9 <PID>
```

### 데이터베이스 초기화
```bash
# ⚠️ 모든 데이터 삭제 (PostgreSQL + Neo4j + OpenSearch)
docker-compose down -v
docker-compose up --build
```

### Worker가 작업을 처리하지 않음
```bash
# Celery 상태 확인
docker-compose exec worker celery -A celery_app inspect active

# Redis 연결 확인
docker-compose exec queue redis-cli ping

# 큐에 메시지가 있는지 확인
docker-compose exec queue redis-cli LLEN celery
```

### Neo4j 연결 실패 (v2)
```bash
# Neo4j 상태 확인
docker-compose exec neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n);"

# 로그 확인
docker-compose logs neo4j

# 데이터베이스 재시작
docker-compose restart neo4j
```

### OpenSearch 인덱싱 실패 (v2)
```bash
# OpenSearch 상태 확인
curl -X GET "http://localhost:9200/_cluster/health?pretty"

# 인덱스 목록
curl -X GET "http://localhost:9200/_cat/indices?v"

# 특정 인덱스 확인
curl -X GET "http://localhost:9200/code_embeddings/_search?pretty"
```

### 컨테이너 빌드 실패
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache backend
docker-compose build --no-cache worker
docker-compose up --build --force-recreate
```

### 마이그레이션 문제
```bash
# 현재 마이그레이션 상태
docker-compose exec backend alembic current

# 마이그레이션 히스토리
docker-compose exec backend alembic history

# 특정 리비전으로 이동
docker-compose exec backend alembic downgrade <revision>

# graph_snapshot 테이블 확인
docker-compose exec backend python -c "
from common.database import SessionLocal
db = SessionLocal()
result = db.execute('SELECT * FROM graph_snapshot LIMIT 5').fetchall()
print(result)
"
```

### AWS Batch 디버깅 (v2)
```bash
# CloudWatch Logs 확인
aws logs tail /aws/batch/sesami-worker --follow

# Batch Job 상태
aws batch describe-jobs --jobs <job-id>

# Step Functions 실행 기록
aws stepfunctions describe-execution --execution-arn <arn>
```
