# Sesami 설계 문서

## 🎯 현재 활성 버전: v2

Sesami 프로젝트는 **Graph-RAG 기반 코드 분석 플랫폼**입니다.

---

## 📘 공식 설계 문서 (v2)

### 주요 문서
| 문서 | 설명 | 크기 |
|------|------|------|
| [**PROJECT_PLAN_V2.md**](v2/PROJECT_PLAN_V2.md) | 🔥 **메인 설계 문서** - Graph-RAG, Neo4j, 시맨틱 검색, Multi-Agent 아키텍처 | 상세 |
| [**v2/README.md**](v2/README.md) | v1 → v2 변경 사항 요약 및 Gap Analysis | 요약 |

### v2 핵심 아키텍처

#### 1. **Graph-RAG 아키텍처**
- **Neo4j 지식 그래프**: 코드 구조를 그래프로 모델링
  - 노드: Developer, Repository, Commit, File, Class, Function, Module
  - 관계: COMMITTED_BY, MODIFIED, CONTAINS, CALLS, IMPORTS, INHERITS_FROM
- **Tree-sitter 파싱**: 다국어 AST 추출 (Python, JavaScript, TypeScript, Java 등)

#### 2. **시맨틱 코드 검색**
- **AWS Bedrock Titan 임베딩**: UniXcoder 기반 코드 임베딩
- **Amazon OpenSearch Serverless**: 벡터 검색 인프라
- **자연어 쿼리**: "데이터베이스 연결을 처리하는 코드" 검색 가능

#### 3. **Multi-Agent Orchestration**
```
L0 (Frontend) → L1 (Backend API)
                    ↓
            L2 (Step Functions Orchestrator)
                    ↓
            L3-Tool (정적 분석: Pylint, SonarQube, Semgrep, CodeQL)
            L3-Agent (LLM 분석: AWS Bedrock Claude)
```

#### 4. **고급 분석 도구 통합**
- **SonarQube**: 기술 부채(SQALE), 보안 취약점, 코드 스멜
- **Semgrep**: 커스텀 보안 규칙, PII/GDPR 탐지
- **CodeQL**: 고급 데이터 흐름 및 보안 분석
- **TruffleHog**: 비밀 정보(Secret) 누출 감지
- **Radon**: Python 코드 복잡도 (Cyclomatic Complexity)

#### 5. **5차원 역량 평가 모델**
```python
class DeveloperProficiencyPayload:
    technical_skills: Dict[str, float]        # 언어별 숙련도
    architectural_awareness: float            # SOLID 원칙, 모듈 결합도
    security_consciousness: float             # 취약점 커밋 비율
    testing_discipline: float                 # 테스트 커버리지, 품질
    documentation_quality: float              # 주석 비율, Docstring 품질
    privacy_compliance_score: float           # GDPR/PII 준수
    overall_level: Literal["Junior", "Mid", "Senior", "Lead"]
```

#### 6. **AWS 인프라**
- **Step Functions**: L2 Orchestrator (Map 상태로 병렬 처리)
- **AWS Batch**: L3 작업 실행 (Spot 인스턴스 + Graviton ARM64)
- **EFS**: 리포지토리 저장 (Elastic Throughput 모드)
- **Neo4j AuraDB**: 관리형 그래프 DB
- **DynamoDB**: 멱등성 테이블, 분석 메타데이터
- **X-Ray**: 분산 추적 (Distributed Tracing)

---

## 📦 문서 구조

```
docs/design/
├── README.md (이 파일)
├── v2/                          ← 현재 활성 버전
│   ├── PROJECT_PLAN_V2.md       ← 메인 설계 문서
│   └── README.md                ← v2 변경 사항 요약
└── archive/
    └── v1/                      ← 아카이브 (참조용)
        ├── ARCHIVED_README.md
        ├── 00_OVERVIEW.md
        ├── 01_SYSTEM_ARCHITECTURE.md
        ├── 02_LOCAL_DEVELOPMENT.md
        ├── 03_AWS_MIGRATION.md
        ├── 06_IMPLEMENTATION_PLAN.md
        └── README.md
```

---

## 🚀 빠른 시작

### 로컬 개발
```bash
# 환경 변수 설정
cp .env.example .env

# Docker Compose로 전체 스택 실행
make up

# Neo4j 브라우저 접속
open http://localhost:7474
# ID: neo4j, PW: neo4j_password

# OpenSearch 대시보드
open http://localhost:5601
```

### v2 핵심 명령어
```bash
# Graph-RAG 분석 실행
make graph-dev

# Neo4j 쿼리 실행
make neo4j-query QUERY="MATCH (d:Developer)-[:COMMITTED_BY]->(c:Commit) RETURN d, c LIMIT 10"

# OpenSearch 인덱스 확인
make opensearch-indices

# 시맨틱 검색 테스트
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication logic", "k": 5}'
```

---

## 📖 관련 문서

- **AI 컨텍스트**: [`/CLAUDE.md`](../../CLAUDE.md) - Claude Code를 위한 프로젝트 가이드 (v2 반영됨)
- **프로젝트 README**: [`/README.md`](../../README.md) - 전체 프로젝트 개요
- **Makefile**: [`/Makefile`](../../Makefile) - 개발 명령어 모음

---

## 🔄 마이그레이션 이력

| 버전 | 날짜 | 주요 변경 사항 |
|------|------|----------------|
| **v2** | 2025-11-09 | Graph-RAG, Neo4j, 시맨틱 검색, Multi-Agent 도입 |
| v1 | 2025-11-05 | 초기 3계층 아키텍처, Git Blame 분석, AWS Batch 계획 |

---

## ⚠️ 중요 안내

- ✅ **모든 개발은 v2 설계 문서를 따릅니다**
- ✅ **v1 문서는 `archive/v1/`에서 참조용으로만 사용**
- ✅ **CLAUDE.md는 v2 내용이 반영되어 있습니다**

---

**최종 업데이트**: 2025-11-09
**담당**: Claude Code
