


# 🚀 Sesami v4.0 – **AI 기반 개발자 실력 검증 플랫폼**


<div align="center">

### **“LLM Multi-Agent로 개발자의 ‘진짜 실력’을 증명한다”**

**이제 AI가 직접 개발자의 코드를 ‘함수 단위’까지 파고들어 분석합니다.**

[➡️ 구현 사이트](https://sesami.crimecat.org/)
[➡️ GitHub Repo](https://github.com/alsksssass/Sesami)
[➡️ 시연 영상](https://www.youtube.com/watch?v=Ar82IGwsPqY)

</div>

---

# 🎯 1. 문제 정의 (Problem Statement)

현행 개발자 채용 프로세스는 심각한 문제를 가지고 있습니다.

### ❗ 1) 포트폴리오 기반 평가의 신뢰 부족

* GitHub 레포 대부분이 **팀 프로젝트**
* "이 사람이 실제로 작성한 코드인가?" 확인 불가

### ❗ 2) 레포/파일 단위 요약은 피상적

* 단순 요약 AI 도구는 **기여도도, 코드 품질도 측정 못함**

### ❗ 3) 기업은 빠르고 정확한 검증을 원함

* 인사팀은 기술을 모르고, 개발팀은 시간이 없음

---

# 💡 2. 솔루션 (What We Built)

우리는 **LLM 기반 Multi-Agent 오케스트레이션**으로
개발자의 GitHub 전체를 **함수(Function) 단위**까지 자동으로 분석하는 플랫폼을 만들었습니다.

## ✨ Sesami v4.0의 핵심 기능

### 🧬 1) **Commit Level Authorship Verification**

Git 로그 + Diff + Metadata → **작성자 코드만 자동 추출**

### 🧩 2) **Function-Level Deep Code Analysis**

파일이 아닌 **AST(Tree-sitter) 기반 함수 단위 분석**

### 🕸️ 3) **Graph-RAG + Vector-RAG 하이브리드 구조**

* Neo4j 코드/커밋 그래프
* ChromaDB 벡터 임베딩
  → **코드 의미 + 구조적 맥락**까지 이해

### 🤖 4) **17개 전문 LLM 에이전트로 품질/보안/성능 분석**

* Quality
* Security
* Performance
* Architecture
  각 영역 전문 AI가 병렬로 분석

### 📊 5) **실시간 리포트**

React 기반 UI로 보기 쉽게 제공
→ HR팀도 기술 없이 검증 가능

---

# 🏗️ 3. 전체 아키텍처 (Architecture)

<div align="center">

```
React → FastAPI → AWS Batch → Deep Agent (LangGraph)
                         ↓
               Neo4j / ChromaDB / S3
```

</div>

### Deep Agent는 이렇게 작동합니다:

```
Setup → Static Analysis → Commit Analysis → RAG → Eval → Report
       (병렬)                 (그래프)           (LLM)
```

각 분석은 **LangGraph 기반 17개 Multi-Agent**가 비동기 병렬 수행.

→ **파일 수 200+, 커밋 500+ 레포지토리도 2~5분 내 분석**

---

# 🤯 4. 우리의 기술 난제 해결 (Technical Challenges Solved)

### ✔ Git commit authorship 정밀 식별

PyDriller로 commit traversal → Neo4j 그래프 구축 → 작성자 = 확실하게 식별

### ✔ 함수 단위 파싱

Tree-sitter로 파이썬·JS·TS 코드 분석 → Cyclomatic complexity까지 측정

### ✔ Hybrid RAG

* Vector RAG: 의미 기반 코드 유사도
* Graph RAG: 구조 기반 컨텍스트
  → AI가 단순 요약이 아닌 **정확한 판단** 수행

### ✔ Multi-Agent 병렬 처리

LangGraph 기반

* Level 1: Static / Commit / RAG 분석
* Level 2: Commit Evaluator 병렬 수백 개
* Level 3: 보안/품질/성능/아키텍처 전문가 에이전트
  → 전체 파이프라인 처리 시간 **극적으로 단축**

---

## 🧪 5. 사용 방법

### 🔹 지원자

* ### Step 1. **GitHub 계정 연동** (OAuth 로그인)
  ![Image](https://github.com/user-attachments/assets/43befa0f-2fc2-4090-b6a2-0502ac59e56a)
  
* ### Step 2. **평가받을 레포지토리 선택** 및 분석 요청
  ![Image](https://github.com/user-attachments/assets/38c89857-bcc3-4ea2-965f-74e4e2566209)
  
* ### Step 3. **AI 분석 시작** 및 지원 완료
  ![Image](https://github.com/user-attachments/assets/da139f78-80c6-4802-864f-85bb11f2a261)
  
* ### Step 4. **개인 역량 리포트**를 통해 자신의 코드 분석 결과 열람 가능
  ![Image](https://github.com/user-attachments/assets/44daeff8-ceed-484f-893e-13b7aacf699e)

---

### 🔹 채용 담당자

* ### Step 1. 기업별 **맞춤형 평가 기준 등록**
  ![Image](https://github.com/user-attachments/assets/10bcc48b-b6a8-43bd-a36f-e4f049fdaa44)

* ### Step 2. **역량 순위별 대시보드**에서 지원자 직무 및 상세 리포트 한눈에 파악
  ![Image](https://github.com/user-attachments/assets/682a234c-acf2-40a2-9532-2279fd37e80a)

---

# 📦 6. 프로젝트 구조 (정리본)

```
Sesami/
├── deepagent/            # Deep Agent AI 엔진
│   ├── agents/           # 17개 LLM Agent
│   ├── core/             # LangGraph Orchestrator
│   ├── shared/           # Neo4j/ChromaDB 도구
│   └── main.py           # CLI 실행
│
├── src/
│   ├── frontend/         # React + Vite UI
│   ├── backend/          # FastAPI API
│   └── shared/           # 공통 Schema/Model
│
├── docker/               # Docker 배포 구성
└── docker-compose.yml
```

---

# 🚀 7. 빠른 실행 (Quick Start)

## 개발 환경 실행

```bash
make dev
```

## Deep Agent 단독 실행

```bash
python deepagent/main.py --git-url https://github.com/user/repo
```

---

# 📊 8. 결과 출력 예시 (Sample Output)

### ✔ 코드 품질 진단

* 함수 복잡도
* 구조적 개선 포인트
* 잠재적 버그
* 테스트 커버리지 부족 영역

### ✔ 개발자 스킬 프로파일

AI가 정리한 “개발자 스킬·역량·패턴”

### ✔ 아키텍처 관점 분석

MVC 패턴 적용 여부
DB 연동 구조
비동기 처리 방식
메모리/성능 이슈 등

### ✔ 증거 기반 리포트

모든 판단에는 commit hash + code block이 증거로 포함됨

---

# 🔥 9. 왜 해커톤에서 우승할 프로젝트인가? (Why This Project Wins)

### 1) **HR-Tech + AI + GraphDB + Multi-Agent**

현재 가장 뜨거운 기술 4개가 유기적으로 결합된 솔루션.

### 2) **명확한 문제 해결 → 기업 니즈 직결**

실제 인사팀/CTO가 직면한 문제를 정확히 해결.

### 3) **확실한 기술력 차별화**

* AST 파싱
* Commit Authorship
* LangGraph
* RAG Hybrid
* AWS Batch 병렬 처리
  이 정도 기술 조합은 해커톤에서 극소수 팀만 구현 가능.

### 4) **시연이 강력함**

레포지토리 선택 → 분석 → 상세 리포트가 뜨는 과정 자체가 “와!”가 나옴.

### 5) **이미 실서비스 수준 완성도**

Demo URL + FastAPI + React + Docker 구성까지 완비.

---

# 🌱 10. 향후 확장성 (Future Work)

* 다국어 코드 분석(LangChain Tools)
* Go / Rust / Java / C++ 확장
* GitLab / Bitbucket 지원
* AI 인터뷰 솔루션 연동
* 기업용 관리자 페이지 (채용 파이프라인 자동화)
* 인재 매칭 추천 엔진 (개발자 ↔ 기업 매칭)

---

# 👥 11. 팀 소개

| 이름             | 역할                    | GitHub                                                         |
| -------------- | --------------------- | -------------------------------------------------------------- |
| **alsksssass** | 인프라·백엔드·Deep Agent 총괄 | [https://github.com/alsksssass](https://github.com/alsksssass) |
| **smj53**      | 백엔드·Deep Agent 개발      | [https://github.com/smj53](https://github.com/smj53)           |
| **somilee**    | 프론트엔드 개발              | [https://github.com/somilee](https://github.com/somilee)       |

---

<div align="center">

# ❤️ Sesami v4.0

### “AI가 개발자의 실력을 진짜로 이해하도록 만들다.”

👉 Demo: [https://sesami.crimecat.org](https://sesami.crimecat.org)
👉 Repo: [https://github.com/alsksssass/Sesami](https://github.com/alsksssass/Sesami)

</div>

--
