# v1 설계 문서 아카이브

## 📦 보관 이유

이 디렉토리는 Sesami 프로젝트의 **v1 설계 문서**를 보관하고 있습니다.

**아카이브 날짜**: 2025년 11월 9일
**이유**: v2 설계로 전환 완료 (Graph-RAG, Neo4j, 시맨틱 검색 등 주요 아키텍처 변경)

---

## 📚 보관된 문서

| 파일명 | 설명 | 크기 |
|--------|------|------|
| `00_OVERVIEW.md` | v1 프로젝트 개요 및 목표 | 7.6 KB |
| `01_SYSTEM_ARCHITECTURE.md` | v1 3계층 아키텍처 설계 | 35 KB |
| `02_LOCAL_DEVELOPMENT.md` | v1 로컬 개발 환경 가이드 | 14.4 KB |
| `03_AWS_MIGRATION.md` | v1 AWS 마이그레이션 전략 | 26.9 KB |
| `06_IMPLEMENTATION_PLAN.md` | v1 구현 계획 (12주 로드맵) | 12.7 KB |
| `README.md` | v1 설계 문서 인덱스 | 5.4 KB |

**총 크기**: 약 101.5 KB

---

## 🔄 v1 vs v2 주요 차이점

### v1 아키텍처 (이 문서들)
- ✅ 기본 3계층 구조 (Frontend, Backend, Worker)
- ✅ Git Blame 기반 기여도 분석
- ✅ Celery 비동기 작업 처리
- ✅ PostgreSQL + Redis 기본 스택
- ✅ AWS Batch 마이그레이션 계획

### v2 아키텍처 (현재 활성)
- 🚀 **Graph-RAG**: Neo4j 지식 그래프 기반 코드 분석
- 🚀 **시맨틱 검색**: AWS Bedrock Titan 임베딩 + Amazon OpenSearch
- 🚀 **Multi-Agent Orchestration**: L0/L1/L2/L3 계층형 에이전트
- 🚀 **Tree-sitter 파싱**: 다국어 AST 추출
- 🚀 **Step Functions 워크플로우**: 대규모 병렬 처리
- 🚀 **고급 분석 도구**: SonarQube, Semgrep, CodeQL, TruffleHog 통합

**상세 내용**: [`../v2/PROJECT_PLAN_V2.md`](../v2/PROJECT_PLAN_V2.md) 참조

---

## 🎯 이 문서를 언제 참조해야 하나요?

1. **설계 진화 과정 이해**: v1에서 v2로의 아키텍처 변경 근거 파악
2. **역사적 컨텍스트**: 초기 기술 선정 배경 및 의사결정 과정 추적
3. **레거시 코드 분석**: v1 시절에 작성된 코드의 원래 설계 의도 확인
4. **마이그레이션 검증**: v2 전환 시 누락된 v1 기능 체크

---

## ⚠️ 중요 안내

- ❌ **이 문서들은 더 이상 활성 설계 문서가 아닙니다**
- ❌ **구현 시 이 문서들을 참조하지 마세요**
- ✅ **모든 새로운 작업은 [`../v2/PROJECT_PLAN_V2.md`](../v2/PROJECT_PLAN_V2.md)를 따르세요**

---

## 📖 현재 활성 문서

프로젝트 개발은 다음 문서들을 참조하세요:

- **공식 설계 문서**: [`../v2/PROJECT_PLAN_V2.md`](../v2/PROJECT_PLAN_V2.md)
- **변경 사항 요약**: [`../v2/README.md`](../v2/README.md)
- **AI 컨텍스트**: [`/CLAUDE.md`](../../../../CLAUDE.md)
- **프로젝트 README**: [`/README.md`](../../../../README.md)

---

**아카이브 담당자**: Claude Code
**마지막 업데이트**: 2025-11-09
