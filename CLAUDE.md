# CLAUDE.md - Sesami v4.0 (PDD v4.0)

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Project Overview

**Sesami**는 GitHub 기여도 분석을 넘어선 **Enterprise HR Tech 플랫폼**입니다.

**v4.0의 핵심 변화** (PDD v4.0 기반):
- **이전 (v2)**: 단일 Worker 파이프라인 (Git → Graph → Vector)
- **현재 (v4.0)**: **3-Tier 멀티 에이전트 오케스트레이션** (L1 → L2 → L3)

### 핵심 컨셉

**"컨텍스트(Context)를 이해하는 HR Tech"**

1. **L3-Tools** (저비용, CPU, 100% 실행)
   - Pylint, SonarQube, Semgrep, TruffleHog, DORA
   - **역할**: 객관적 사실 수집

2. **L3-Agents** (고비용, LLM, 10% 선별 실행)
   - Proficiency Agent, Architecture Agent, Collaboration Agent
   - **역할**: Graph-RAG + Vector-RAG를 도구로 사용하여 **심층 추론**

3. **L1-Finalize** (최종 LLM)
   - **역할**: 모든 데이터를 종합하여 **다차원 역량 리포트** 생성

---

## 🏛️ Architecture v4.0

### 3-Tier 오케스트레이션

```
┌─────────────────────────────────────────────────────┐
│ L0: Frontend (React)                                │
│  - GitHub OAuth 인증                                 │
│  - POST /api/v1/analysis/start                      │
└────┬────────────────────────────────────────────────┘
     │
     ↓ SQS 메시지 (256KB)
┌─────────────────────────────────────────────────────┐
│ L1: Backend API + Main Orchestrator (FastAPI)      │
│  1. Pre-flight Check (비용 예측, 방어벽)             │
│  2. L3-Builder 실행 (Graph/Vector DB 구축)          │
│  3. L2 Fan-out (N개 Sub Step Functions)             │
│  4. Wait for All L2                                  │
│  5. L1-Finalize (Graph-RAG + 최종 LLM)              │
│  6. RDS 저장                                         │
└────┬────────────────────────────────────────────────┘
     │
     ↓ N개 병렬
┌─────────────────────────────────────────────────────┐
│ L2: Sub Orchestrator (파일 그룹별)                  │
│  1. L3-Tool Fan-out (100% 실행)                     │
│     ├─ pylint_tool (Graviton + Spot)                │
│     ├─ sonarqube_tool                                │
│     └─ semgrep_tool                                  │
│  2. Wait for Tools                                   │
│  3. Filter (CPU: 복잡도 > 10 && 라인 > 100)         │
│  4. L3-Agent Fan-out (선별된 10%만)                 │
│     ├─ proficiency_agent (LLM)                       │
│     │   - Neo4j (Graph-RAG)                          │
│     │   - OpenSearch (Vector-RAG)                    │
│     │   - Bedrock Claude 3.5 Sonnet                  │
│     └─ architecture_agent (LLM)                      │
│  5. Wait for Agents                                  │
│  6. Reduce (EFS: l2_summary_{group_id}.json)        │
└────┬────────────────────────────────────────────────┘
     │
     ↓ 수천~수만 개 병렬
┌─────────────────────────────────────────────────────┐
│ L3: Batch Jobs (AWS Batch or Celery)               │
│                                                      │
│ L3-Tool (저비용, CPU, 100%)                         │
│  - 입력: {"file": "main.py", "tool": "pylint"}      │
│  - 출력: EFS l3_tool_pylint_main.py.json            │
│                                                      │
│ L3-Agent (고비용, LLM, 10%)                         │
│  - 입력: {"file": "auth.py", "agent": "proficiency"}│
│  - 도구: Neo4j, OpenSearch, Bedrock                 │
│  - 출력: EFS l3_agent_proficiency_auth.py.json      │
└─────────────────────────────────────────────────────┘
```

---

## 📂 Directory Structure v4.0

```
Sesami/
├── docs/
│   └── design/v2/
│       ├── PROJECT_PLAN_V2.md        # 기존 v2 계획 (보존용)
│       ├── ARCHITECTURE_V4.md        # 🆕 v4.0 아키텍처 상세
│       └── PDD_V4.md                 # 사용자 제공 PDD 문서
│
├── src/
│   ├── frontend/                     # L0: React UI
│   │
│   ├── backend/                      # L1: FastAPI + Main Orchestrator
│   │   ├── features/v1/
│   │   │   ├── auth/                 # GitHub OAuth
│   │   │   ├── github_analysis/      # POST /analysis/start
│   │   │   └── insights/             # 🆕 GET /insights (최종 리포트 조회)
│   │   ├── common/
│   │   │   ├── dependencies.py       # ✅ 의존성 주입 (환경별 동적)
│   │   │   ├── graph_service.py      # IGraphService (Neo4j)
│   │   │   ├── vector_service.py     # IVectorService (OpenSearch)
│   │   │   └── task_service/
│   │   │       ├── base.py           # ITaskService 인터페이스
│   │   │       ├── local_service.py  # Celery (로컬)
│   │   │       └── aws_batch_service.py # Step Functions (AWS)
│   │   └── orchestrator/             # 🆕 L1 Main Orchestrator
│   │       ├── __init__.py
│   │       ├── main_state_machine.py # L1 Step Functions 로직
│   │       ├── preflight_check.py    # 비용 예측
│   │       └── finalize_agent.py     # L1-Finalize (최종 LLM)
│   │
│   ├── worker/                       # L3: Batch Jobs
│   │   ├── l3_tools/                 # 🆕 L3-Tools (저비용 분석)
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # IL3Tool 인터페이스
│   │   │   ├── pylint_tool.py        # ✅ 구현 완료
│   │   │   ├── sonarqube_tool.py     # 구현 필요
│   │   │   ├── semgrep_tool.py       # 구현 필요
│   │   │   ├── trufflehog_tool.py    # 구현 필요
│   │   │   └── dora_calculator.py    # 구현 필요
│   │   │
│   │   ├── l3_builders/              # 🆕 L3-Builders (Graph/Vector 구축)
│   │   │   ├── __init__.py
│   │   │   ├── graph_builder.py      # Neo4j 그래프 구축 (Tree-sitter)
│   │   │   └── vector_builder.py     # OpenSearch 벡터 인덱스
│   │   │
│   │   ├── l3_agents/                # 🆕 L3-Agents (LLM 기반 분석)
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py         # ✅ IL3Agent 인터페이스
│   │   │   ├── proficiency_agent.py  # ✅ 구현 완료 (Graph+Vector+LLM)
│   │   │   ├── architecture_agent.py # 구현 필요
│   │   │   └── collaboration_agent.py # 구현 필요
│   │   │
│   │   ├── l2_logic/                 # 🆕 L2 Filter + Reducer
│   │   │   ├── __init__.py
│   │   │   ├── filter.py             # ✅ CPU 기반 필터링
│   │   │   └── reducer.py            # ✅ 중간 집계 (EFS 저장)
│   │   │
│   │   ├── analysis/                 # 기존 분석 로직 (재사용)
│   │   │   ├── git_analyzer.py       # Git clone, blame
│   │   │   ├── graph_loader.py       # (→ l3_builders/graph_builder.py로 이동 예정)
│   │   │   └── semantic_search.py    # (→ l3_builders/vector_builder.py로 이동 예정)
│   │   │
│   │   ├── tasks.py                  # 수정 필요: L3 Entry Point
│   │   ├── celery_app.py             # Celery 설정
│   │   └── database.py               # DB 세션
│   │
│   └── shared/                       # 공유 모델 및 스키마
│       ├── models.py                 # Analysis, AnalysisStatus
│       ├── graph_models.py           # GraphSnapshot, VectorIndex
│       └── schemas/                  # 🆕 JSON Schema (Event Envelope)
│           ├── __init__.py
│           ├── event_envelope.py     # ✅ 표준 봉투 구조
│           ├── l3_tool_output.py     # L3-Tool 출력 스키마
│           ├── l3_agent_output.py    # L3-Agent 출력 스키마
│           └── l2_summary.py         # L2 요약본 스키마
│
├── docker-compose.yml                # 수정 필요: L3 컨테이너 추가
├── .env                              # 수정 필요: L3 환경변수
├── Makefile                          # 수정 필요: 새 명령어 추가
└── CLAUDE.md                         # 🔄 현재 문서
```

---

## 🔑 Core Design Patterns

### 1. Event Envelope (동적 확장)

**문제**: L3 작업자가 10개에서 50개로 늘어날 때 L1/L2 코드 수정?

**해결**: 표준 JSON 봉투 구조

```python
# 모든 L3 작업자는 이 형식으로 결과를 EFS에 저장
{
  "tool_name": "PYLINT_TOOL",
  "tool_type": "L3_TOOL",
  "file_path": "src/backend/main.py",
  "execution_time_ms": 1234,
  "payload": {
    "score": 9.5,
    "errors": [],
    "warnings": ["Line too long"]
  },
  "metadata": {
    "worker_id": "batch-job-12345",
    "timestamp": "2025-01-10T12:34:56Z"
  }
}
```

**L2 Reducer**는 `tool_name`을 Key로 동적 집계:
```python
summary = {}
for envelope in results:
    tool = envelope['tool_name']
    if tool not in summary:
        summary[tool] = []
    summary[tool].append(envelope['payload'])
```

**결과**: L3에 `PROFICIENCY_AGENT` 추가 → L1/L2 코드 수정 없음 ✅

---

### 2. Dependency Injection (환경별 동적 전환)

**문제**: 로컬(Celery) vs AWS(Batch) 환경 전환 시 코드 수정?

**해결**: `dependencies.py`의 의존성 주입

```python
# src/backend/common/dependencies.py
def get_task_service() -> ITaskService:
    if settings.TASK_SERVICE_IMPL == "AWS_BATCH":
        return AwsBatchTaskService()  # Step Functions
    else:
        return LocalTaskService()     # Celery

def get_graph_service() -> IGraphService:
    return LocalGraphService(neo4j_uri=settings.NEO4J_URI)

def get_vector_service() -> IVectorService:
    return LocalVectorService(opensearch_endpoint=settings.OPENSEARCH_ENDPOINT)
```

**사용**:
```python
# Backend API
@router.post("/analysis/start")
async def start_analysis(
    task_service: ITaskService = Depends(get_task_service),
    graph_service: IGraphService = Depends(get_graph_service)
):
    job_id = await task_service.enqueue_analysis(...)
    return {"job_id": job_id}

# Worker
def run_l3_agent(file_path: str):
    graph_service = get_graph_service()
    vector_service = get_vector_service()

    agent = ProficiencyAgent(
        graph_service=graph_service,
        vector_service=vector_service,
        llm_client=bedrock_client
    )
    result = agent.execute(file_path)
```

**결과**: `.env`의 `TASK_SERVICE_IMPL=AWS_BATCH`만 변경 → 전체 AWS 전환 ✅

---

### 3. L2 Filter (비용 최적화)

**문제**: 모든 파일에 LLM 호출하면 비용 폭발

**해결**: CPU 기반 필터링 (L3-Tool 결과 활용)

```python
# src/worker/l2_logic/filter.py
class L2Filter:
    def filter_significant_files(self, tool_results):
        significant_files = set()

        for tool_result in tool_results:
            # Pylint: 낮은 점수
            if tool_result['tool_name'] == 'PYLINT_TOOL':
                if tool_result['payload']['score'] < 8.0:
                    significant_files.add(tool_result['file_path'])

            # Semgrep: 보안 이슈 존재
            elif tool_result['tool_name'] == 'SEMGREP_TOOL':
                if len(tool_result['payload']['findings']) > 0:
                    significant_files.add(tool_result['file_path'])

        return list(significant_files)
```

**결과**: 500 files → L3-Tool 100% (저비용) → Filter → 50 files (10%) → L3-Agent (고비용) ✅

---

### 4. Graph-RAG + Vector-RAG (PDD v4.0 핵심)

**문제**: LLM이 코드의 "구조적 중요도"와 "의미적 효율성"을 어떻게 판단?

**해결**: L3-Agent가 Neo4j + OpenSearch를 **도구**로 사용

```python
# src/worker/l3_agents/proficiency_agent.py
class ProficiencyAgent(IL3Agent):
    def analyze(self, file_path, context):
        # 1️⃣ Graph-RAG: 구조적 수준 분석
        graph_insights = self._analyze_structural_level(file_path)
        # Neo4j Cypher: 의존성 복잡도, 아키텍처 계층 분석

        # 2️⃣ Vector-RAG: 의미적 효율성 분석
        vector_insights = self._analyze_semantic_efficiency(file_path)
        # OpenSearch k-NN: 유사 코드 패턴, 알고리즘 효율성 비교

        # 3️⃣ LLM: 최종 판단
        llm_assessment = self.invoke_llm(
            prompt=f"""
            구조적 분석: {graph_insights}
            의미적 분석: {vector_insights}
            정적 분석: {context['PYLINT_TOOL']}

            위 정보를 바탕으로 개발자의 숙련도를 평가하세요.
            """
        )

        return {
            "level": llm_assessment["level"],
            "confidence": llm_assessment["confidence"],
            "reasoning": llm_assessment["reasoning"]
        }
```

**결과**: LLM이 단순 코드 읽기가 아닌 **컨텍스트 기반 추론** ✅

---

## 🚀 Development Commands

### 로컬 환경 시작

```bash
# Docker Compose로 전체 시스템 실행
docker-compose up --build

# L3 컨테이너 포함 (Tools, Builders, Agents)
docker-compose up -d --build backend worker l3-tools l3-agents neo4j opensearch
```

### 서비스 접속
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **OpenSearch**: https://localhost:9200

### L3 작업자 테스트

```bash
# L3-Tool 테스트 (Pylint)
docker-compose exec l3-tools python -m l3_tools.pylint_tool /path/to/file.py

# L3-Agent 테스트 (Proficiency)
docker-compose exec l3-agents python -m l3_agents.proficiency_agent /path/to/file.py

# L2 Filter 테스트
docker-compose exec worker python -m l2_logic.filter

# L2 Reducer 테스트
docker-compose exec worker python -m l2_logic.reducer
```

---

## 🔧 Environment Variables v4.0

### 새로 추가된 환경변수

```bash
# L3 실행 모드
L3_EXECUTION_MODE=LOCAL  # LOCAL | AWS_BATCH

# L3-Tools 설정
PYLINT_ENABLED=true
SONARQUBE_URL=http://sonarqube:9000
SONARQUBE_TOKEN=your_token
SEMGREP_RULES=p/security-audit,p/owasp-top-ten
TRUFFLEHOG_ENABLED=true

# L3-Agents 설정
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
AGENT_EXECUTION_THRESHOLD=0.10  # 10%만 실행

# L2 Filter 임계값
L2_FILTER_MIN_COMPLEXITY=10
L2_FILTER_MIN_LINES=100
L2_FILTER_MAX_QUALITY_SCORE=8.0

# EFS 공유 스토리지
EFS_MOUNT_PATH=/mnt/efs
EFS_RESULTS_DIR=/mnt/efs/results

# 비용 제어
MAX_BUDGET_PER_ANALYSIS=100.00  # USD
PREFLIGHT_CHECK_ENABLED=true

# Graph/Vector DB (기존)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
OPENSEARCH_ENDPOINT=https://opensearch:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=your_password
```

---

## 📝 Implementation Roadmap

### ✅ Phase 1: 기반 구축 (완료)
- ✅ 디렉토리 구조 생성 (`l3_tools`, `l3_builders`, `l3_agents`, `l2_logic`)
- ✅ Event Envelope 스키마 정의 (`shared/schemas/event_envelope.py`)
- ✅ L3-Tools 베이스 인터페이스 + Pylint 구현
- ✅ L3-Agents 베이스 인터페이스 + Proficiency Agent 구현
- ✅ L2 Filter + Reducer 구현

### ⏳ Phase 2: L3 작업자 완성 (진행 중)
- ⏳ SonarQube Tool 구현
- ⏳ Semgrep Tool 구현
- ⏳ TruffleHog Tool 구현
- ⏳ DORA Calculator 구현
- ⏳ Graph Builder 구현 (기존 `graph_loader.py` 이동)
- ⏳ Vector Builder 구현 (기존 `semantic_search.py` 이동)
- ⏳ Architecture Agent 구현
- ⏳ Collaboration Agent 구현

### ⏳ Phase 3: L2 오케스트레이션
- ⏳ L2 Entry Point 구현 (`worker/l2_logic/orchestrator.py`)
- ⏳ L2 Step Functions 정의 (로컬: Celery Chain)
- ⏳ EFS Mock 구현 (로컬: `/tmp/efs`)

### ⏳ Phase 4: L1 오케스트레이션
- ⏳ Pre-flight Check 구현 (`backend/orchestrator/preflight_check.py`)
- ⏳ L1-Finalize Agent 구현 (`backend/orchestrator/finalize_agent.py`)
- ⏳ Main State Machine 구현 (`backend/orchestrator/main_state_machine.py`)

### ⏳ Phase 5: 인프라 통합
- ⏳ docker-compose.yml 재작성 (L3 컨테이너 추가)
- ⏳ AWS CDK 구현 (Step Functions, Batch, EFS, Neo4j, OpenSearch)
- ⏳ CI/CD 파이프라인 (GitHub Actions)

---

## 🔍 Debugging & Monitoring

### L3 작업자 로그 확인

```bash
# L3-Tool 로그
docker-compose logs -f l3-tools

# L3-Agent 로그
docker-compose logs -f l3-agents

# L2 로그
docker-compose exec worker tail -f /var/log/l2_reducer.log

# EFS 결과 확인
docker-compose exec worker ls -lh /mnt/efs/results/
docker-compose exec worker cat /mnt/efs/results/l2_summary_group_0001.json
```

### 비용 추적

```bash
# Pre-flight Check 결과
curl http://localhost:8000/api/v1/analysis/preflight \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo"}'

# 예상 결과:
# {
#   "estimated_cost_usd": 45.50,
#   "files_count": 500,
#   "l3_tools_cost": 5.00,
#   "l3_agents_cost": 40.50,
#   "recommendation": "proceed"
# }
```

---

## 📚 Key Documentation

- **PDD v4.0**: User-provided design document (프로젝트 최우선 참조)
- **ARCHITECTURE_V4.md**: 이 문서의 상세 버전
- **PROJECT_PLAN_V2.md**: 기존 v2 계획 (보존용)
- **shared/schemas/event_envelope.py**: Event Envelope 스키마 정의
- **worker/l3_tools/base.py**: L3-Tool 인터페이스
- **worker/l3_agents/base_agent.py**: L3-Agent 인터페이스

---

## 🚨 Troubleshooting

### Q1: "JSON 파일 (EFS) vs. SQS/Redis" (데이터 전달)

**A**: 둘 다 사용하며, 목적이 다릅니다.

- **SQS/Step Functions**: 작업 시작 명령 (256KB 제한)
- **EFS/S3**: 결과물 저장 (수 MB 크기)

L3는 결과물을 EFS에 쓰고 L2에게 "완료" 신호만 보냅니다 (Map-Reduce 패턴).

### Q2: "LLM 동시성 (1개 vs 1,000개)"

**A**: "1개의 엔드포인트가 1,000개의 병렬 인스턴스로 즉시 확장"됩니다.

L2가 L3-Agent 1,000개를 병렬 실행하면, Bedrock은 AWS 내부 인프라 풀에서 1,000명의 상담원(Inference Instance)을 찾아 1:1로 즉시 배정합니다.

**할당량 주의**: 계정 한도(RPM)를 초과하면 `429 Rate Limit Exceeded` 발생.

---

## 🎓 Learning Resources

### 프로젝트 이해하기
1. `docs/design/v2/PDD_V4.md` 읽기 (사용자 제공, 최우선)
2. `docs/design/v2/ARCHITECTURE_V4.md` 읽기 (상세 설계)
3. `shared/schemas/event_envelope.py` 코드 읽기 (Event Envelope)
4. `worker/l3_agents/proficiency_agent.py` 코드 읽기 (Graph-RAG + Vector-RAG + LLM)

### 핵심 패턴 익히기
1. **Event Envelope**: 동적 확장 패턴
2. **Dependency Injection**: 환경별 동적 전환
3. **L2 Filter**: 비용 최적화
4. **Graph-RAG + Vector-RAG**: LLM 도구 사용

---

**마지막 업데이트**: 2025-01-10 (v4.0)
**문의**: 설계 문서 또는 코드 이해가 어려울 경우 PDD_V4.md 및 ARCHITECTURE_V4.md 참조
