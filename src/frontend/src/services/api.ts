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
      // 개발 모드에서는 Mock 데이터 반환
      if (import.meta.env.DEV) {
        await new Promise((resolve) => setTimeout(resolve, 300)); // 로딩 시뮬레이션

        return {
          id: "550e8400-e29b-41d4-a716-446655440000",
          github_id: "12345678",
          username: "alsksssass",
          nickname: "소민",
          repo_count: 2,
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
      // 개발 모드에서는 Mock 데이터 반환
      if (import.meta.env.DEV) {
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
      if (import.meta.env.DEV) {
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
    analyzeRepositories: (repoUrls: string[]) =>
      request<void>("/api/v1/repo/analyze", {
        method: "POST",
        body: JSON.stringify({ repo_urls: repoUrls }),
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
  },

  // 헬스체크
  health: () => request<{ status: string; database: string }>("/health"),
};

export default api;
