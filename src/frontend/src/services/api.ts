/**
 * API 서비스
 * 백엔드와 통신하는 모든 API 호출을 관리
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/**
 * HTTP 요청 헬퍼
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('access_token');

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // JWT 토큰이 있으면 Authorization 헤더 추가
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Generic HTTP methods
 */
export const get = <T>(endpoint: string): Promise<T> => {
  return request<T>(endpoint, { method: 'GET' });
};

export const post = <T>(endpoint: string, data?: any): Promise<T> => {
  return request<T>(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
};

export const put = <T>(endpoint: string, data?: any): Promise<T> => {
  return request<T>(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
};

export const del = <T>(endpoint: string): Promise<T> => {
  return request<T>(endpoint, { method: 'DELETE' });
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
      request<{ authorization_url: string }>('/api/v1/auth/github/login'),

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
      }>('/api/v1/auth/github/callback', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),

    /**
     * 현재 사용자 정보 조회
     */
    getCurrentUser: () =>
      request<{
        id: number;
        github_id: string;
        username: string;
        email: string;
        avatar_url: string;
        created_at: string;
      }>('/api/v1/auth/me'),

    /**
     * 로그아웃
     */
    logout: () =>
      request<{ message: string }>('/api/v1/auth/logout', {
        method: 'POST',
      }),
  },

  // 분석 관련
  analysis: {
    /**
     * 저장소 분석 시작
     */
    startAnalysis: (repoUrl: string) =>
      request<{
        analysis_id: number;
        status: string;
        message: string;
      }>('/api/v1/analysis/analyze', {
        method: 'POST',
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
  health: () => request<{ status: string; database: string }>('/health'),
};

export default api;
