# 구현 계획서

## 🎯 전체 구현 로드맵

```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│  Phase 1    │  Phase 2    │  Phase 3    │  Phase 4    │  Phase 5    │
│  기초 구축  │  핵심 기능  │  고도화     │  AWS 준비   │  프로덕션   │
│  (2주)      │  (3주)      │  (2주)      │  (3주)      │  (2주)      │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

**전체 기간**: 12주 (약 3개월)

---

## 📅 Phase 1: 기초 인프라 구축 (Week 1-2)

### 목표
✅ 로컬 개발 환경 완성
✅ 기본 API 엔드포인트 구현
✅ 데이터베이스 스키마 확정
✅ Frontend 기본 레이아웃

### 작업 항목

#### Week 1
**Backend**
- [ ] Database 모델 완성
  - `User`, `Repository`, `AnalysisJob`, `AnalysisResult` 테이블
  - SQLAlchemy relationships 정의
  - Alembic 마이그레이션 생성
- [ ] 인증 API 완성
  - GitHub OAuth 콜백 처리
  - JWT 토큰 발급/갱신
  - User CRUD 엔드포인트
- [ ] 기본 예외 처리 및 미들웨어
  - CORS 설정
  - Request ID 추적
  - Error handling middleware

**Frontend**
- [ ] 라우팅 구조 설정
  - React Router 설정
  - Protected routes
  - 레이아웃 컴포넌트
- [ ] 인증 UI
  - 로그인 페이지
  - GitHub OAuth 버튼
  - 콜백 처리

**DevOps**
- [ ] Docker Compose 최종 검증
  - 모든 서비스 헬스체크
  - Volume 영속성 확인
  - 환경변수 정리
- [ ] .gitignore 정리
  - .env 파일 제외
  - node_modules, __pycache__ 제외

#### Week 2
**Backend**
- [ ] 분석 작업 API 기본 구조
  - `POST /api/v1/analysis/start` - 분석 시작
  - `GET /api/v1/analysis/{job_id}` - 상태 조회
  - `GET /api/v1/analysis/history` - 히스토리 조회
- [ ] TaskService 추상화 검증
  - LocalTaskService 테스트
  - 의존성 주입 확인
- [ ] Logging 설정
  - Structured logging (JSON)
  - Request/Response 로그

**Frontend**
- [ ] Dashboard 기본 레이아웃
  - 네비게이션 바
  - 사이드바 (메뉴)
  - 컨텐츠 영역
- [ ] API 서비스 클라이언트
  - Axios 설정
  - 인터셉터 (토큰 추가)
  - 에러 핸들링

**문서화**
- [ ] API 문서 정리 (FastAPI 자동 생성 + 추가 설명)
- [ ] 로컬 개발 가이드 업데이트
- [ ] 환경변수 문서화

---

## 📅 Phase 2: 핵심 분석 기능 구현 (Week 3-5)

### 목표
✅ Worker 분석 로직 100% 완성
✅ Frontend 분석 페이지 구현
✅ 실시간 상태 업데이트

### 작업 항목

#### Week 3
**Worker**
- [ ] GitAnalyzer 클래스 완성
  - `clone_repository()` - Private 저장소 지원
  - `analyze_blame()` - 사용자 기여도 계산
  - `analyze_tech_stack()` - 언어/프레임워크 감지
  - `cleanup()` - 임시 파일 삭제
- [ ] Celery Task 구현
  - `analyze_repository_task()`
  - 진행 상태 업데이트 (PENDING → PROCESSING → COMPLETED)
  - 에러 핸들링 및 재시도 로직
- [ ] 대용량 레포지토리 처리
  - 타임아웃 설정 (30분)
  - 메모리 최적화
  - 증분 blame (파일별 처리)

**Backend**
- [ ] Worker 작업 제출 로직
  - GitHub API를 통한 레포지토리 검증
  - 중복 작업 방지
  - 작업 큐 제출
- [ ] 실시간 상태 API
  - WebSocket 또는 Server-Sent Events (선택)
  - Polling 엔드포인트 최적화

#### Week 4
**Worker**
- [ ] 시계열 분석 로직
  - 커밋 히스토리 기반 기간별 분석
  - 주별/월별 기술 스택 변화
  - 데이터 집계 및 최적화
- [ ] 결과 저장 로직
  - JSON 직렬화
  - 데이터베이스 저장
  - 인덱싱 최적화

**Frontend**
- [ ] 새로운 분석 페이지
  - 레포지토리 URL 입력
  - GitHub 레포지토리 목록 (API 연동)
  - 분석 시작 버튼
- [ ] 분석 진행 상태 페이지
  - 프로그레스 바
  - 상태 메시지 표시
  - 실시간 업데이트 (Polling)

#### Week 5
**Frontend**
- [ ] 분석 결과 페이지
  - 기여도 차트 (Chart.js or Recharts)
  - 기술 스택 시각화
  - 시계열 그래프
- [ ] 분석 히스토리 페이지
  - 과거 분석 목록
  - 재분석 기능
  - 삭제 기능

**Testing**
- [ ] Backend 단위 테스트
  - pytest 설정
  - API 엔드포인트 테스트
  - TaskService 테스트
- [ ] Worker 단위 테스트
  - GitAnalyzer 메서드 테스트
  - Mock GitHub API
- [ ] E2E 테스트
  - Frontend → Backend → Worker 전체 흐름

---

## 📅 Phase 3: 고도화 및 개선 (Week 6-7)

### 목표
✅ 사용자 경험 개선
✅ 성능 최적화
✅ 에러 처리 강화

### 작업 항목

#### Week 6
**기능 추가**
- [ ] 레포지토리 즐겨찾기
  - 자주 분석하는 레포지토리 저장
  - 원클릭 재분석
- [ ] 알림 시스템
  - 분석 완료 시 이메일 (선택)
  - 브라우저 알림 (Web Push)
- [ ] 분석 캐싱
  - 동일 레포지토리 + 동일 커밋 = 재사용
  - 캐시 만료 정책 (7일)

**성능 최적화**
- [ ] API 응답 속도 개선
  - Database 쿼리 최적화
  - Eager loading (N+1 문제 해결)
  - 인덱스 추가
- [ ] Frontend 번들 크기 감소
  - Code splitting
  - Lazy loading
  - Tree shaking
- [ ] Worker 병렬 처리
  - 파일별 병렬 blame 분석
  - 멀티프로세싱 활용

#### Week 7
**보안 강화**
- [ ] Rate Limiting
  - API 요청 제한 (사용자당 10req/min)
  - Celery 작업 제한 (사용자당 5 동시 작업)
- [ ] Input Validation
  - 레포지토리 URL 검증
  - SQL Injection 방지
  - XSS 방지
- [ ] 감사 로그
  - 사용자 행동 로깅
  - 분석 작업 히스토리

**UI/UX 개선**
- [ ] 반응형 디자인 완성
  - 모바일 레이아웃
  - 태블릿 최적화
- [ ] 로딩 상태 개선
  - Skeleton UI
  - 진행률 표시
- [ ] 에러 메시지 개선
  - 사용자 친화적 메시지
  - 해결 방법 제시

---

## 📅 Phase 4: AWS 마이그레이션 준비 (Week 8-10)

### 목표
✅ AWS 인프라 구축
✅ Worker 코드 AWS Batch 변환
✅ CI/CD 파이프라인

### 작업 항목

#### Week 8
**AWS 인프라 (IaC)**
- [ ] Terraform 설정
  - VPC, Subnet, Security Groups
  - RDS (PostgreSQL)
  - ECR (Container Registry)
- [ ] Secrets Manager 설정
  - GitHub OAuth 크레덴셜
  - DB 암호
  - JWT Secret
  - 암호화 키

**Worker 변환**
- [ ] AWS Batch용 코드 작성
  - `run_analysis.py` 작성
  - SQS 메시지 파싱
  - Secrets Manager 통합
- [ ] Dockerfile.aws 작성
  - AWS CLI 설치
  - boto3 추가
  - Entry Point 변경

#### Week 9
**AWS 인프라 (계속)**
- [ ] ECS Cluster 구성
  - Fargate Task Definition
  - ECS Service 설정
  - Auto Scaling 정책
- [ ] Application Load Balancer
  - HTTPS 설정 (ACM)
  - Target Group 연결
  - Health Check
- [ ] AWS Batch 구성
  - Compute Environment (Spot)
  - Job Queue
  - Job Definition

**Backend 변환**
- [ ] AwsTaskService 구현
  - SQS 메시지 전송
  - 환경변수 기반 전환
- [ ] Secrets Manager 통합
  - boto3 클라이언트
  - 토큰 복호화

#### Week 10
**SQS + EventBridge 연동**
- [ ] SQS Queue 생성
  - Standard Queue
  - DLQ (Dead Letter Queue)
- [ ] EventBridge Pipe 설정
  - SQS → Batch 트리거
  - Job Parameter 전달

**CI/CD 파이프라인**
- [ ] GitHub Actions 워크플로우
  - Docker 이미지 빌드
  - ECR 푸시
  - ECS 배포 트리거
- [ ] 배포 스크립트
  - Blue-Green 배포 (선택)
  - Rollback 절차

---

## 📅 Phase 5: 프로덕션 배포 및 검증 (Week 11-12)

### 목표
✅ AWS 프로덕션 배포
✅ 모니터링 및 알람 설정
✅ 부하 테스트

### 작업 항목

#### Week 11
**배포**
- [ ] 데이터베이스 마이그레이션
  - 로컬 → RDS 데이터 이관
  - 스키마 검증
- [ ] Docker 이미지 배포
  - Backend → ECR → ECS
  - Worker → ECR → Batch
- [ ] DNS 설정
  - Route53 도메인 연결
  - CloudFront (선택)

**모니터링**
- [ ] CloudWatch 설정
  - 로그 그룹 생성
  - 메트릭 필터
  - 대시보드
- [ ] CloudWatch Alarms
  - 높은 에러율 (>5%)
  - 긴 응답 시간 (>1s)
  - 큐 깊이 증가 (>100)
- [ ] SNS 알림
  - 이메일 알림
  - Slack 통합 (선택)

#### Week 12
**테스트 및 검증**
- [ ] 기능 테스트
  - 전체 사용자 플로우
  - 에지 케이스 검증
- [ ] 부하 테스트
  - 동시 사용자 100명
  - API 처리량 측정
  - Worker 스케일링 검증
- [ ] 보안 스캔
  - ECR 이미지 스캔
  - OWASP Top 10 체크
  - 취약점 패치

**문서화 및 인수인계**
- [ ] 운영 가이드
  - 배포 절차
  - 모니터링 방법
  - 트러블슈팅
- [ ] API 문서 최종 검토
- [ ] 사용자 가이드

---

## 🎯 우선순위 매트릭스

### 높음 (Must Have)
1. ✅ Worker 분석 로직 (git blame, tech stack)
2. ✅ 인증 시스템 (GitHub OAuth + JWT)
3. ✅ 기본 API 엔드포인트
4. ✅ Frontend 주요 페이지 (Dashboard, 분석 결과)
5. ✅ AWS Batch 마이그레이션

### 중간 (Should Have)
1. 🔨 시계열 분석
2. 🔨 실시간 상태 업데이트 (WebSocket)
3. 🔨 알림 시스템
4. 🔨 레포지토리 즐겨찾기
5. 🔨 CI/CD 파이프라인

### 낮음 (Nice to Have)
1. 💡 코드 품질 분석 (SonarQube 통합)
1. 💡 LLM 기반 정성 평가
3. 💡 팀 협업 기능
4. 💡 리포트 PDF 내보내기
5. 💡 다국어 지원

---

## 📊 진행 상황 추적

### Milestone 체크리스트

**Milestone 1: 로컬 환경 완성** (Week 2 종료)
- [ ] Docker Compose로 모든 서비스 실행 가능
- [ ] GitHub OAuth 로그인 성공
- [ ] 기본 API 엔드포인트 작동
- [ ] Frontend 기본 레이아웃 완성

**Milestone 2: 핵심 기능 구현** (Week 5 종료)
- [ ] Worker 분석 로직 100% 완성
- [ ] 분석 작업 전체 플로우 작동
- [ ] 결과 페이지 시각화 완성
- [ ] E2E 테스트 통과

**Milestone 3: 고도화 완료** (Week 7 종료)
- [ ] 성능 최적화 완료 (API <500ms)
- [ ] 보안 강화 완료 (Rate Limiting, Validation)
- [ ] 반응형 디자인 완성

**Milestone 4: AWS 준비 완료** (Week 10 종료)
- [ ] Terraform 인프라 구축 완료
- [ ] Worker AWS Batch 변환 완료
- [ ] CI/CD 파이프라인 구축

**Milestone 5: 프로덕션 배포** (Week 12 종료)
- [ ] AWS 프로덕션 환경 배포 완료
- [ ] 모니터링 및 알람 설정 완료
- [ ] 부하 테스트 통과 (100 동시 사용자)
- [ ] 운영 문서 완성

---

## 🛠️ 개발 환경 설정

### 필수 도구
```bash
# 로컬 개발
brew install docker docker-compose
brew install postgresql
brew install redis

# AWS CLI
brew install awscli
aws configure  # Access Key 설정

# Terraform
brew install terraform

# Python 개발
brew install python@3.12
pip install virtualenv

# Node.js 개발
brew install node@20
```

### VS Code 확장
- Python
- Pylance
- ESLint
- Prettier
- Docker
- GitLens
- Thunder Client (API 테스트)

---

## 📝 일일 체크리스트

### 개발 시작 시
- [ ] `git pull origin main` (최신 코드 가져오기)
- [ ] `docker-compose up -d` (로컬 환경 시작)
- [ ] 브라우저에서 접속 확인
- [ ] 당일 작업 항목 확인

### 개발 종료 시
- [ ] 변경 사항 커밋 및 푸시
- [ ] PR 생성 (feature 브랜치)
- [ ] `docker-compose down` (선택)
- [ ] 내일 작업 계획 정리

---

## 🚨 리스크 관리

### 높은 리스크
| 리스크 | 영향 | 확률 | 완화 전략 |
|-------|------|------|-----------|
| Worker 성능 문제 (대용량 레포) | 높음 | 중간 | 타임아웃 설정, 증분 처리, AWS Batch 스케일링 |
| AWS 비용 초과 | 높음 | 중간 | Spot Instances, 비용 알람, 예산 설정 |
| GitHub API Rate Limit | 중간 | 높음 | 캐싱, Token Pool, 재시도 로직 |

### 중간 리스크
| 리스크 | 영향 | 확률 | 완화 전략 |
|-------|------|------|-----------|
| 데이터베이스 마이그레이션 실패 | 중간 | 낮음 | 백업, Dry-run, 점진적 마이그레이션 |
| CI/CD 파이프라인 문제 | 낮음 | 중간 | 수동 배포 절차 준비, 롤백 계획 |

---

## 📞 팀 커뮤니케이션

### 주간 리뷰
- **매주 금요일 17:00**
- 완료 항목 확인
- 다음 주 계획 수립
- 블로커 논의

### 일일 스탠드업 (선택)
- **매일 10:00 (15분)**
- 어제 한 일
- 오늘 할 일
- 블로커

---

**완료**: 이제 모든 설계 문서가 작성되었습니다. 각 문서를 참고하여 단계적으로 구현을 진행하세요.
