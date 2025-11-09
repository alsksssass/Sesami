# Sesami 프로젝트 설계 문서

## 📚 문서 개요

이 디렉토리는 Sesami 프로젝트의 전체 시스템 설계 및 구현 계획을 포함합니다.

---

## 📖 문서 목록

### 1. [전체 개요 (00_OVERVIEW.md)](./00_OVERVIEW.md)
**목적**: 프로젝트 전체 구조 이해
- 프로젝트 목표 및 핵심 기능
- 아키텍처 원칙 (비동기 처리, 추상화)
- 현재 구현 상태
- 기술 스택 전체 개요

**대상**: 새로운 팀원, 프로젝트 이해관계자

---

### 2. [시스템 아키텍처 (01_SYSTEM_ARCHITECTURE.md)](./01_SYSTEM_ARCHITECTURE.md)
**목적**: 시스템의 세부 구조 파악
- 3-Tier 아키텍처 설계
- 비동기 작업 흐름 (Frontend → Backend → Queue → Worker)
- 컴포넌트 간 통신 프로토콜
- 보안 아키텍처 (인증, 암호화, IAM)
- 확장성 및 모니터링 전략

**대상**: 백엔드 개발자, 아키텍트, DevOps 엔지니어

---

### 3. [로컬 개발 환경 (02_LOCAL_DEVELOPMENT.md)](./02_LOCAL_DEVELOPMENT.md)
**목적**: 로컬에서 개발 환경 구축 및 실행
- Docker Compose 기반 멀티 서비스 실행
- 환경변수 설정 가이드
- 서비스별 상세 설명 (Frontend, Backend, Worker)
- Worker 핵심 로직 구현 예제 (GitAnalyzer)
- 개발 워크플로우 및 문제 해결
- 개발 체크리스트

**대상**: 전체 개발자 (필수 읽기)

---

### 4. [AWS 마이그레이션 (03_AWS_MIGRATION.md)](./03_AWS_MIGRATION.md)
**목적**: 로컬 → AWS 프로덕션 환경 전환
- 컴포넌트별 AWS 서비스 매핑
- AWS 아키텍처 전체 설계
- **핵심**: Worker Celery → AWS Batch 변환
- Terraform 인프라 코드 예제
- IAM Roles 설계
- 배포 프로세스 및 비용 최적화

**대상**: 백엔드 개발자, DevOps 엔지니어, 아키텍트

---

### 5. [구현 계획 (06_IMPLEMENTATION_PLAN.md)](./06_IMPLEMENTATION_PLAN.md)
**목적**: 단계별 구현 일정 및 우선순위
- 12주 로드맵 (5 Phases)
- Phase별 상세 작업 항목
- Milestone 체크리스트
- 우선순위 매트릭스 (Must/Should/Nice to Have)
- 리스크 관리
- 일일/주간 체크리스트

**대상**: 프로젝트 매니저, 전체 개발자

---

## 🚀 빠른 시작 가이드

### 새로운 팀원이라면?
```
1. 00_OVERVIEW.md 읽기 (프로젝트 이해)
2. 02_LOCAL_DEVELOPMENT.md 읽기 (로컬 환경 구축)
3. 실제로 docker-compose up 실행해보기
4. 06_IMPLEMENTATION_PLAN.md 확인 (현재 진행 상황)
```

### Backend 개발자라면?
```
1. 01_SYSTEM_ARCHITECTURE.md 읽기
2. 02_LOCAL_DEVELOPMENT.md의 Backend 섹션 집중
3. Worker 로직 구현 시작
4. 03_AWS_MIGRATION.md 숙지 (추후 마이그레이션 대비)
```

### Frontend 개발자라면?
```
1. 00_OVERVIEW.md 읽기 (API 흐름 이해)
2. 02_LOCAL_DEVELOPMENT.md의 Frontend 섹션 집중
3. API 명세 확인 (FastAPI Swagger: http://localhost:8000/docs)
```

### DevOps 엔지니어라면?
```
1. 01_SYSTEM_ARCHITECTURE.md 읽기
2. 03_AWS_MIGRATION.md 집중 (Terraform, IAM, ECS, Batch)
3. CI/CD 파이프라인 설계
```

---

## 📁 프로젝트 구조 참고

```
Sesami/
├── docs/
│   └── design/                 # 📍 현재 위치
│       ├── README.md          # 이 파일
│       ├── 00_OVERVIEW.md
│       ├── 01_SYSTEM_ARCHITECTURE.md
│       ├── 02_LOCAL_DEVELOPMENT.md
│       ├── 03_AWS_MIGRATION.md
│       └── 06_IMPLEMENTATION_PLAN.md
│
├── docker/                     # Docker 설정 파일
├── src/
│   ├── frontend/              # React 앱
│   ├── backend/               # FastAPI 앱
│   └── worker/                # Celery Worker
├── docker-compose.yml
└── .env                       # 환경변수 (git ignored)
```

---

## 🔄 문서 업데이트 정책

### 언제 업데이트하나?
1. **아키텍처 변경 시**: 새로운 서비스 추가, 데이터 흐름 변경
2. **새로운 기능 구현 후**: API 엔드포인트 추가, 데이터베이스 스키마 변경
3. **AWS 인프라 변경 시**: Terraform 코드 업데이트, 새로운 AWS 서비스 도입
4. **Milestone 달성 시**: 구현 계획서의 체크리스트 업데이트

### 어떻게 업데이트하나?
1. 해당 문서 수정
2. 변경 내역을 PR에 명시
3. 팀 리뷰 후 머지

---

## 📝 추가 예정 문서

- [ ] **04_API_SPECIFICATION.md** - 상세 API 명세
- [ ] **05_DATABASE_SCHEMA.md** - ERD 및 테이블 상세
- [ ] **07_TESTING_STRATEGY.md** - 테스트 전략 및 커버리지
- [ ] **08_TROUBLESHOOTING.md** - 일반적인 문제 해결

---

## 💡 문서 작성 원칙

1. **명확성**: 기술적 배경이 다른 팀원도 이해 가능하도록
2. **실용성**: 실제 구현 시 참고할 수 있는 코드 예제 포함
3. **최신성**: 프로젝트 진행에 따라 지속적으로 업데이트
4. **구조화**: 섹션을 명확히 구분하여 필요한 정보를 빠르게 찾을 수 있도록

---

## 🤝 기여 방법

문서 개선 제안이 있다면:
1. 이슈 생성: `docs: [문서명] 개선 제안`
2. PR 생성: 수정 사항과 함께 변경 이유 명시
3. 팀 리뷰 요청

---

## 📞 문의

문서 관련 질문이나 피드백은:
- GitHub Issues
- 팀 슬랙 채널
- 주간 리뷰 미팅

---

**마지막 업데이트**: 2025년 11월 9일
**작성자**: Claude Code (SuperClaude Framework)
