/**
 * API 서비스
 * 백엔드와 통신하는 모든 API 호출을 관리
 */

const API_BASE_URL =
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

/**
 * HTTP 요청 헬퍼
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("access_token");

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // JWT 토큰이 있으면 Authorization 헤더 추가
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Generic HTTP methods
 */
export const get = <T>(endpoint: string): Promise<T> => {
  return request<T>(endpoint, { method: "GET" });
};

export const post = <T>(endpoint: string, data?: any): Promise<T> => {
  return request<T>(endpoint, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  });
};

export const put = <T>(endpoint: string, data?: any): Promise<T> => {
  return request<T>(endpoint, {
    method: "PUT",
    body: data ? JSON.stringify(data) : undefined,
  });
};

export const del = <T>(endpoint: string): Promise<T> => {
  return request<T>(endpoint, { method: "DELETE" });
};

/**
 * API 엔드포인트
 */
export const api = {
  // Generic methods
  get,
  post,
  put,
  delete: del,

  // 인증 관련
  auth: {
    /**
     * GitHub OAuth 로그인 URL 받기
     */
    getGitHubLoginUrl: () =>
      request<{ authorization_url: string }>("/api/v1/auth/github/login"),

    /**
     * GitHub OAuth 콜백 처리
     */
    handleGitHubCallback: (code: string) =>
      request<{
        access_token: string;
        token_type: string;
        user: {
          id: number;
          github_id: string;
          username: string;
          email: string;
          avatar_url: string;
          created_at: string;
        };
      }>("/api/v1/auth/github/callback", {
        method: "POST",
        body: JSON.stringify({ code }),
      }),

    /**
     * 현재 사용자 정보 조회
     */
    getCurrentUser: async () => {
      // Mock 데이터 사용 여부 체크 (VITE_USE_MOCK=false면 실제 API 호출)
      const useMock = import.meta.env.VITE_USE_MOCK !== "false";

      if (useMock) {
        await new Promise((resolve) => setTimeout(resolve, 300)); // 로딩 시뮬레이션

        return {
          id: "550e8400-e29b-41d4-a716-446655440000",
          github_id: "12345678",
          username: "alsksssass",
          nickname: "소민",
          repo_count: 3,
          email: "somin@example.com",
          avatar_url: "https://avatars.githubusercontent.com/u/12345678?v=4",
          created_at: "2024-01-15T10:30:00Z",
        };
      }

      // 프로덕션에서는 실제 API 호출
      return request<{
        id: string;
        github_id: string;
        username: string;
        nickname: string;
        repo_count: number;
        email?: string;
        avatar_url?: string;
        created_at: string;
      }>("/api/v1/auth/me");
    },

    /**
     * 로그아웃
     */
    logout: () =>
      request<{ message: string }>("/api/v1/auth/logout", {
        method: "POST",
      }),
  },

  // 사용자 분석 검색
  search: {
    /**
     * 사용자 분석 검색
     * @param devType - 개발자 타입 필터 (backend, frontend, ai, data)
     * @param page - 페이지 번호
     * @param size - 페이지 크기
     */
    searchUsers: async (params?: {
      dev_type?: "backend" | "frontend" | "ai" | "data";
      page?: number;
      size?: number;
    }) => {
      // Mock 데이터 사용 여부 체크
      const useMock = import.meta.env.VITE_USE_MOCK !== "false";

      if (useMock) {
        await new Promise((resolve) => setTimeout(resolve, 500)); // 로딩 시뮬레이션

        const mockUsers = [
          {
            order: 1,
            nickname: "alsksssass",
            level: 45,
            exp: 18500,
            stack: ["React", "TypeScript", "Node.js", "PostgreSQL"],
            dev_type: ["frontend", "backend"],
          },
          {
            order: 2,
            nickname: "ai_master",
            level: 42,
            exp: 16200,
            stack: ["Python", "TensorFlow", "PyTorch", "Scikit-learn"],
            dev_type: ["ai", "data"],
          },
          {
            order: 3,
            nickname: "backend_dev",
            level: 38,
            exp: 14000,
            stack: ["Java", "Spring Boot", "MySQL", "Redis"],
            dev_type: ["backend"],
          },
          {
            order: 4,
            nickname: "data_scientist",
            level: 40,
            exp: 15800,
            stack: ["Python", "Pandas", "SQL", "Tableau", "Apache Spark"],
            dev_type: ["data"],
          },
          {
            order: 5,
            nickname: "fullstack_ninja",
            level: 50,
            exp: 22000,
            stack: ["Vue.js", "Django", "Docker", "Kubernetes", "AWS"],
            dev_type: ["frontend", "backend", "ai"],
          },
        ];

        // dev_type 필터링
        let filteredUsers = mockUsers;
        if (params?.dev_type) {
          filteredUsers = mockUsers.filter((user) =>
            user.dev_type.includes(params.dev_type!)
          );
        }

        const page = params?.page || 1;
        const size = params?.size || 10;
        const total = filteredUsers.length;
        const pages = Math.ceil(total / size);

        return {
          items: filteredUsers,
          total,
          page,
          size,
          pages,
        };
      }

      // 프로덕션에서는 실제 API 호출
      const queryParams = new URLSearchParams();
      if (params?.dev_type) queryParams.append("dev_type", params.dev_type);
      if (params?.page) queryParams.append("page", params.page.toString());
      if (params?.size) queryParams.append("size", params.size.toString());

      const queryString = queryParams.toString();
      const endpoint = queryString
        ? `/api/v1/search?${queryString}`
        : "/api/v1/search";

      return request<{
        items: Array<{
          order: number;
          nickname: string;
          level: number;
          exp: number;
          stack: string[];
          dev_type: string[];
        }>;
        total: number;
        page: number;
        size: number;
        pages: number;
      }>(endpoint);
    },
  },

  // 분석 관련
  analysis: {
    /**
     * 레포지토리 목록 조회
     */
    getRepositories: () => {
      const useMock = import.meta.env.VITE_USE_MOCK !== "false";

      if (useMock) {
        return Promise.resolve({
          repositories: [
            {
              id: 123456789,
              name: "sesami-frontend",
              full_name: "alsksssass/sesami-frontend",
              owner: {
                login: "alsksssass",
                avatar_url: "https://avatars.githubusercontent.com/u/1?v=4",
                html_url: "https://github.com/alsksssass",
              },
              html_url: "https://github.com/alsksssass/sesami-frontend",
              description: "개발자 역량 분석 플랫폼 프론트엔드",
              private: false,
              fork: false,
              language: "TypeScript",
              stargazers_count: 45,
              watchers_count: 45,
              forks_count: 12,
              open_issues_count: 3,
              default_branch: "main",
              created_at: "2024-01-15T10:30:00Z",
              updated_at: "2025-01-17T14:20:00Z",
              pushed_at: "2025-01-17T14:20:00Z",
              size: 2048,
              has_issues: true,
              has_projects: true,
              has_wiki: false,
            },
            {
              id: 234567890,
              name: "ai-model-trainer",
              full_name: "alsksssass/ai-model-trainer",
              owner: {
                login: "alsksssass",
                avatar_url: "https://avatars.githubusercontent.com/u/1?v=4",
                html_url: "https://github.com/alsksssass",
              },
              html_url: "https://github.com/alsksssass/ai-model-trainer",
              description: "머신러닝 모델 학습 자동화 도구",
              private: true,
              fork: false,
              language: "Python",
              stargazers_count: 128,
              watchers_count: 130,
              forks_count: 34,
              open_issues_count: 8,
              default_branch: "main",
              created_at: "2023-11-20T09:15:00Z",
              updated_at: "2025-01-16T18:45:00Z",
              pushed_at: "2025-01-16T18:45:00Z",
              size: 5120,
              has_issues: true,
              has_projects: false,
              has_wiki: true,
            },
            {
              id: 345678901,
              name: "kubernetes-deploy-scripts",
              full_name: "alsksssass/kubernetes-deploy-scripts",
              owner: {
                login: "alsksssass",
                avatar_url: "https://avatars.githubusercontent.com/u/1?v=4",
                html_url: "https://github.com/alsksssass",
              },
              html_url:
                "https://github.com/alsksssass/kubernetes-deploy-scripts",
              description: "쿠버네티스 배포 자동화 스크립트 모음",
              private: false,
              fork: false,
              language: "Shell",
              stargazers_count: 67,
              watchers_count: 68,
              forks_count: 23,
              open_issues_count: 2,
              default_branch: "master",
              created_at: "2024-03-10T13:00:00Z",
              updated_at: "2025-01-15T11:30:00Z",
              pushed_at: "2025-01-15T11:30:00Z",
              size: 512,
              has_issues: true,
              has_projects: true,
              has_wiki: true,
            },
            {
              id: 456789012,
              name: "react-component-library",
              full_name: "alsksssass/react-component-library",
              owner: {
                login: "alsksssass",
                avatar_url: "https://avatars.githubusercontent.com/u/1?v=4",
                html_url: "https://github.com/alsksssass",
              },
              html_url: "https://github.com/alsksssass/react-component-library",
              description: "재사용 가능한 React 컴포넌트 라이브러리",
              private: false,
              fork: true,
              language: "JavaScript",
              stargazers_count: 203,
              watchers_count: 205,
              forks_count: 89,
              open_issues_count: 15,
              default_branch: "main",
              created_at: "2023-08-05T16:45:00Z",
              updated_at: "2025-01-14T09:20:00Z",
              pushed_at: "2025-01-14T09:20:00Z",
              size: 3584,
              has_issues: true,
              has_projects: false,
              has_wiki: false,
            },
            {
              id: 567890123,
              name: "data-pipeline",
              full_name: "alsksssass/data-pipeline",
              owner: {
                login: "alsksssass",
                avatar_url: "https://avatars.githubusercontent.com/u/1?v=4",
                html_url: "https://github.com/alsksssass",
              },
              html_url: "https://github.com/alsksssass/data-pipeline",
              description: null,
              private: true,
              fork: false,
              language: "Python",
              stargazers_count: 12,
              watchers_count: 12,
              forks_count: 3,
              open_issues_count: 1,
              default_branch: "develop",
              created_at: "2024-09-22T08:10:00Z",
              updated_at: "2025-01-13T15:55:00Z",
              pushed_at: "2025-01-13T15:55:00Z",
              size: 1024,
              has_issues: false,
              has_projects: false,
              has_wiki: false,
            },
          ],
        });
      }
      return request<{
        repositories: Array<{
          id: number;
          name: string;
          full_name: string;
          owner: {
            login: string;
            avatar_url: string;
            html_url: string;
          };
          html_url: string;
          description: string | null;
          private: boolean;
          fork: boolean;
          language: string | null;
          stargazers_count: number;
          watchers_count: number;
          forks_count: number;
          open_issues_count: number;
          default_branch: string;
          created_at: string;
          updated_at: string;
          pushed_at: string;
          size: number;
          has_issues: boolean;
          has_projects: boolean;
          has_wiki: boolean;
        }>;
      }>("/api/v1/repo/list");
    },

    /**
     * 선택된 레포지토리 분석 요청
     */
    analyzeRepositories: (repoInfos: Record<string, string>[]) =>
      request<void>("/api/v1/repo/analyze", {
        method: "POST",
        body: JSON.stringify({ repos: repoInfos }),
      }),

    /**
     * 저장소 분석 시작
     */
    startAnalysis: (repoUrl: string) =>
      request<{
        analysis_id: number;
        status: string;
        message: string;
      }>("/api/v1/analysis/analyze", {
        method: "POST",
        body: JSON.stringify({ repo_url: repoUrl }),
      }),

    /**
     * 분석 상태 조회
     */
    getAnalysisStatus: (analysisId: number) =>
      request(`/api/v1/analysis/status/${analysisId}`),

    /**
     * 분석 결과 조회
     */
    getAnalysisResults: (analysisId: number) =>
      request(`/api/v1/analysis/results/${analysisId}`),

    /**
     * 분석 히스토리 조회
     */
    getAnalysisHistory: (skip = 0, limit = 10) =>
      request(`/api/v1/analysis/history?skip=${skip}&limit=${limit}`),

    /**
     * 본인 레포지토리 분석 조회
     */
    getMyRepositoryAnalysis: () => {
      const useMock = import.meta.env.VITE_USE_MOCK !== "false";

      if (useMock) {
        return Promise.resolve({
          repositories: [
            {
              name: "sesami-frontend",
              url: "https://github.com/alsksssass/sesami-frontend",
              state: "done" as const,
              result: {
                markdown: `
## 📊 프로젝트 개요

| 항목 | 수치 |
|------|------|
| 총 커밋 수 | **342** 회 |
| 추가된 라인 | **15,420** 라인 |
| 삭제된 라인 | **8,230** 라인 |
| 기여자 수 | **3** 명 |
| 프로젝트 기간 | **6** 개월 |

---

## 💻 사용 언어 분포

\`\`\`
TypeScript  ████████████████████░░  65.2%
JavaScript  ████████░░░░░░░░░░░░░░  20.5%
CSS         ████░░░░░░░░░░░░░░░░░░  10.3%
HTML        █░░░░░░░░░░░░░░░░░░░░░   4.0%
\`\`\`

> 💡 **주 언어**: TypeScript (65.2%)

---

## ✅ 코드 품질 지표

| 지표 | 점수 | 등급 |
|------|------|------|
| 복잡도 점수 | 72/100 | 🟢 양호 |
| 유지보수성 지수 | 68/100 | 🟡 보통 |
| 테스트 커버리지 | 45.8% | 🟡 보통 |

### 💡 개선 제안
- 테스트 커버리지를 **60% 이상**으로 높이는 것을 권장합니다
- 복잡한 함수들을 리팩토링하여 유지보수성을 향상시키세요

---

## 🛠 탐지된 기술 스택

### Frontend
- ⚛️ **React** - UI 라이브러리
- 📘 **TypeScript** - 정적 타입 시스템
- 🎨 **Tailwind CSS** - 유틸리티 CSS 프레임워크

### Build & Tools
- ⚡ **Vite** - 빌드 도구
- 🔌 **REST API** - 백엔드 통신

---

## 🏆 종합 평가

**전체 점수: 71.6/100** 🌟🌟🌟

프로젝트가 안정적으로 관리되고 있으며, 현대적인 기술 스택을 잘 활용하고 있습니다. 테스트 커버리지 개선을 통해 더욱 견고한 코드베이스를 구축할 수 있습니다.
`,
                security_score: 7.5,
                stack: ["React", "TypeScript", "Vite", "Tailwind CSS"],
                user: {
                  contribution: 85.5,
                  language: {
                    typescript: { level: 5, exp: 120 },
                    javascript: { level: 4, exp: 80 },
                  },
                  role: { frontend: 90, backend: 10 },
                },
              },
            },
            {
              name: "ai-model-trainer",
              url: "https://github.com/alsksssass/ai-model-trainer",
              state: "progress" as const,
            },
            {
              name: "data-pipeline",
              url: "https://github.com/alsksssass/data-pipeline",
              state: "error" as const,
              error_log:
                "Repository access denied: Private repository requires additional permissions",
            },
          ],
        });
      }
      return request<{
        repositories: Array<{
          name: string;
          url: string;
          result?: {
            markdown: string;
            security_score: number;
            stack: string[];
            user: {
              contribution: number;
              language: Record<string, { level: number; exp: number }>;
              role: Record<string, number>;
            };
          };
          state: "progress" | "done" | "error";
          error_log?: string;
        }>;
      }>("/api/v1/repo/analyze");
    },

    /**
     * 사용자 종합 분석 조회
     */
    getUserAnalysis: () => {
      const useMock = import.meta.env.VITE_USE_MOCK !== "false";

      if (useMock) {
        return Promise.resolve({
          result: `# 🎯 alsksssass 개발자 종합 분석 보고서

## 👤 개발자 프로필

| 항목 | 내용 |
|------|------|
| GitHub Username | **alsksssass** |
| 활동 기간 | **2년 3개월** |
| 총 레포지토리 | **15개** |
| 분석된 레포지토리 | **3개** |
| 총 기여도 | **2,847** commits |

---

## 💼 개발 역량 분석

### 🎨 주요 기술 스택

| 기술 | 숙련도 | 사용 빈도 |
|------|--------|-----------|
| TypeScript | ⭐⭐⭐⭐⭐ | 85% |
| React | ⭐⭐⭐⭐⭐ | 80% |
| Python | ⭐⭐⭐⭐ | 45% |
| Node.js | ⭐⭐⭐⭐ | 60% |
| Docker | ⭐⭐⭐ | 35% |

### 📊 개발 분야별 역량

\`\`\`
Frontend     ████████████████████  92%
Backend      ███████████████░░░░░  75%
AI/ML        ████████████░░░░░░░░  60%
DevOps       ██████████░░░░░░░░░░  50%
Data         ████████░░░░░░░░░░░░  40%
\`\`\`

## 🏆 개발 스타일 평가

### ✅ 강점

- **일관된 코딩 스타일**: 코드 컨벤션 준수율 **94%**
- **활발한 협업**: PR 리뷰 참여율 **87%**
- **체계적인 문서화**: README 및 주석 작성 **양호**
- **현대적 기술 활용**: 최신 프레임워크 및 도구 적극 사용

### 📌 개선이 필요한 부분

- **테스트 코드**: 평균 커버리지 **47%** → 목표 **70%**
- **커밋 메시지**: 상세도 **보통** → 더 구체적인 설명 권장
- **브랜치 전략**: 일관성 **개선 필요**

---

## 🎓 성장 지표

### 📊 3개월 추이

\`\`\`
커밋 수:      ▁▂▃▅▆▇█  (상승 추세)
코드 품질:    ▁▃▄▅▆▇█  (꾸준한 개선)
협업 활동:    ▁▁▃▅▆▇█  (최근 활발)
\`\`\`

### 🌱 학습 키워드 분석

최근 3개월간 새롭게 시도한 기술:
- 🆕 **Tailwind CSS v4** - 최신 버전 적극 활용
- 🆕 **React 19** - 신규 기능 학습 중
- 🆕 **Vite** - 빌드 도구 전환
- 🆕 **FastAPI** - 백엔드 프레임워크 확장

---

## 💡 맞춤형 추천

### 🎯 다음 단계 학습 로드맵

1. **테스트 주도 개발 (TDD)**
   - Jest, Vitest 심화 학습
   - E2E 테스트 도입 (Playwright, Cypress)

2. **성능 최적화**
   - React 성능 프로파일링
   - 번들 사이즈 최적화

3. **백엔드 역량 강화**
   - 데이터베이스 설계 심화
   - 마이크로서비스 아키텍처 학습

### 📚 추천 프로젝트

- **오픈소스 기여**: TypeScript 관련 라이브러리
- **사이드 프로젝트**: 풀스택 SaaS 제품 개발
- **스터디**: 시스템 디자인 및 알고리즘 강화

---

## 🌟 종합 평가

**개발자 등급: Senior Junior Developer**

**총점: 78.5/100** ⭐⭐⭐⭐

- **기술 역량**: 82/100
- **협업 능력**: 79/100
- **코드 품질**: 75/100
- **성장 잠재력**: 88/100

> 🎉 **종합 의견**: 탄탄한 기술 기반과 꾸준한 성장세를 보이는 개발자입니다. 테스트 코드 작성과 문서화를 더욱 강화한다면 시니어 개발자로 성장할 수 있는 잠재력이 충분합니다!
`,
        });
      }
      return request<{ result: string }>("/api/v1/user/analyze");
    },

    /**
     * 공용 사용자 분석 조회 (닉네임 기반)
     * @param nickname - 조회할 사용자의 닉네임 (URL 인코딩 필요)
     */
    getPublicUserAnalysis: (nickname: string) => {
      const useMock = import.meta.env.VITE_USE_MOCK !== "false";

      if (useMock) {
        return Promise.resolve({
          result: `# 🎯 ${nickname} 개발자 종합 분석 보고서

## 💼 개발 역량 분석

### 🎨 주요 기술 스택

| 기술 | 숙련도 | 사용 빈도 |
|------|--------|-----------|
| Python | ⭐⭐⭐⭐⭐ | 90% |
| FastAPI | ⭐⭐⭐⭐ | 70% |
| PostgreSQL | ⭐⭐⭐⭐ | 65% |
| Docker | ⭐⭐⭐⭐ | 55% |
| React | ⭐⭐⭐ | 40% |

### 📊 개발 분야별 역량

\`\`\`
Backend      ████████████████████  95%
Data         ███████████████░░░░░  75%
DevOps       ██████████████░░░░░░  70%
Frontend     ██████████░░░░░░░░░░  50%
AI/ML        █████████░░░░░░░░░░░  45%
\`\`\`

---

## 🏆 개발 스타일 평가

### ✅ 강점

- **백엔드 전문성**: API 설계 및 데이터베이스 최적화 능력 **우수**
- **코드 품질**: 클린 코드 작성 및 리팩토링 역량 **양호**
- **문제 해결**: 복잡한 비즈니스 로직 구현 능력 **뛰어남**
- **성능 최적화**: 쿼리 최적화 및 캐싱 전략 **효과적**

### 📌 개선이 필요한 부분

- **프론트엔드 역량**: UI/UX 구현 경험 **부족** → 풀스택 역량 강화 권장
- **테스트 커버리지**: 유닛 테스트 **52%** → 목표 **75%**
- **문서화**: API 문서 **보통** → OpenAPI/Swagger 적극 활용 권장

---

## 🎓 성장 지표

### 📊 6개월 추이

\`\`\`
커밋 수:      ▁▃▄▆▇▇█  (꾸준한 성장)
코드 품질:    ▁▂▄▆▇██  (지속적 개선)
협업 활동:    ▁▁▂▄▆▇█  (활발해짐)
\`\`\`

### 🌱 학습 키워드 분석

최근 6개월간 새롭게 시도한 기술:
- 🆕 **FastAPI** - 주력 백엔드 프레임워크로 전환
- 🆕 **Redis** - 캐싱 및 세션 관리 도입
- 🆕 **Celery** - 비동기 작업 처리 구현
- 🆕 **Docker Compose** - 로컬 개발 환경 개선

---

## 💡 맞춤형 추천

### 🎯 다음 단계 학습 로드맵

1. **프론트엔드 역량 강화**
   - React 심화 학습
   - TypeScript 마스터
   - 상태 관리 라이브러리 (Redux, Zustand)

2. **테스트 전략 수립**
   - pytest 고급 기법
   - 통합 테스트 자동화
   - TDD 실전 적용

3. **시스템 아키텍처**
   - 마이크로서비스 패턴
   - 이벤트 드리븐 아키텍처
   - 클라우드 네이티브 설계

### 📚 추천 프로젝트

- **풀스택 개발**: 백엔드 강점을 살린 SaaS 제품 개발
- **오픈소스**: FastAPI 생태계 기여
- **블로그/기술 공유**: 백엔드 최적화 노하우 공유

---

## 🌟 종합 평가

**개발자 등급: Mid-level Backend Developer**

**총점: 74.2/100** ⭐⭐⭐⭐

- **기술 역량**: 80/100
- **협업 능력**: 72/100
- **코드 품질**: 75/100
- **성장 잠재력**: 70/100

> 💼 **종합 의견**: 백엔드 개발에 강점을 가진 개발자로, 특히 API 설계와 데이터베이스 최적화 능력이 뛰어납니다. 프론트엔드 역량을 보완하여 풀스택 개발자로 성장하거나, 백엔드 전문성을 더욱 심화시켜 시니어 백엔드 개발자로 발전할 수 있는 잠재력이 있습니다.
`,
        });
      }
      return request<{ result: string }>(
        `/api/v1/public/analyze/${encodeURIComponent(nickname)}`
      );
    },
  },

  // 헬스체크
  health: () => request<{ status: string; database: string }>("/health"),
};

export default api;
