/**
 * 로그인 페이지
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";

export default function Login() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  // 이미 로그인된 경우 홈으로 리다이렉트
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, navigate]);

  const handleGitHubLogin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // 백엔드에서 GitHub OAuth URL 받기
      const { authorization_url } = await api.auth.getGitHubLoginUrl();

      // GitHub 로그인 페이지로 리다이렉트
      window.location.href = authorization_url;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start GitHub login"
      );
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* Header with gradient */}
        <div className="relative bg-linear-to-r from-indigo-50 to-purple-50 border-b border-indigo-100 px-8 py-6">
          <button
            onClick={() => navigate("/")}
            className="absolute right-4 top-4 p-1.5 hover:bg-white/50 rounded-lg transition-colors"
          >
            <span className="text-slate-600 text-xl">✕</span>
          </button>

          <div className="text-center">
            <h1
              className="text-5xl text-indigo-600 font-bold"
              style={{ fontFamily: "Georgia, serif" }}
            >
              Sesami
            </h1>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white px-8 py-10">
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-xl text-slate-900">환영합니다</h2>
              <p className="text-sm text-slate-600">
                GitHub 계정으로 로그인하고
                <br />
                당신의 개발 역량을 '깨알"같이 분석해보세요
              </p>
            </div>

            {/* 에러 메시지 */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            <button
              onClick={handleGitHubLogin}
              disabled={isLoading}
              className="w-full bg-linear-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white py-6 text-lg gap-3 shadow-lg hover:shadow-xl transition-all duration-200 rounded-xl font-semibold flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>로그인 중...</span>
                </>
              ) : (
                <>
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                  <span>GitHub로 로그인</span>
                </>
              )}
            </button>

            <p className="text-xs text-center text-slate-500">
              로그인하면 <span className="text-indigo-600">이용약관</span> 및{" "}
              <span className="text-indigo-600">개인정보처리방침</span>에
              동의하게 됩니다
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
