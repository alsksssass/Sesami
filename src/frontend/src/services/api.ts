/**
 * API 서비스
 * 백엔드와 통신하는 모든 API 호출을 관리
 */

import type { RepositoryAnalysis } from "../pages/Profile";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api";

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
      request<{ authorization_url: string }>("/v1/auth/github/login"),

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
      }>("/v1/auth/github/callback", {
        method: "POST",
        body: JSON.stringify({ code }),
      }),

    /**
     * 현재 사용자 정보 조회
     */
    getCurrentUser: async () => {
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
      }>("/v1/auth/me");
    },

    /**
     * 로그아웃
     */
    logout: () =>
      request<{ message: string }>("/v1/auth/logout", {
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
      dev_type?: "Backend" | "Frontend" | "AI/ML" | "Data";
      page?: number;
      size?: number;
    }) => {

      // 프로덕션에서는 실제 API 호출
      const queryParams = new URLSearchParams();
      if (params?.dev_type) queryParams.append("dev_type", params.dev_type);
      if (params?.page) queryParams.append("page", params.page.toString());
      if (params?.size) queryParams.append("size", params.size.toString());

      const queryString = queryParams.toString();
      const endpoint = queryString
        ? `/v1/search?${queryString}`
        : "/v1/search";

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
      }>("/v1/repo/list");
    },

    /**
     * 선택된 레포지토리 분석 요청
     */
    analyzeRepositories: (repoInfos: Record<string, string>[]) =>
      request<void>("/v1/repo/analyze", {
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
      }>("/v1/analysis/analyze", {
        method: "POST",
        body: JSON.stringify({ repo_url: repoUrl }),
      }),

    /**
     * 분석 상태 조회
     */
    getAnalysisStatus: (analysisId: number) =>
      request(`/v1/analysis/status/${analysisId}`),

    /**
     * 분석 결과 조회
     */
    getAnalysisResults: (analysisId: number) =>
      request(`/v1/analysis/results/${analysisId}`),

    /**
     * 분석 히스토리 조회
     */
    getAnalysisHistory: (skip = 0, limit = 10) =>
      request(`/v1/analysis/history?skip=${skip}&limit=${limit}`),

    /**
     * 본인 레포지토리 분석 조회
     */
    getMyRepositoryAnalysis: () => {
      return request<{ repositories: RepositoryAnalysis[] }>("/v1/repo/analyze");
    },

    /**
     * 사용자 종합 분석 조회
     */
    getUserAnalysis: () => {
      return request<{ result: string }>("/v1/user/analyze");
    },

    /**
     * 공용 사용자 분석 조회 (닉네임 기반)
     * @param nickname - 조회할 사용자의 닉네임 (URL 인코딩 필요)
     */
    getPublicUserAnalysis: (nickname: string) => {
      return request<{ result: string }>(
        `/v1/public/analyze/${encodeURIComponent(nickname)}`
      );
    },
  },

  // 헬스체크
  health: () => request<{ status: string; database: string }>("/health"),
};

export default api;
