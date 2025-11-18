/**
 * GitHub OAuth 콜백 페이지
 * GitHub에서 리다이렉트된 후 authorization code를 처리
 */
import { useEffect, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState<"processing" | "success" | "error">(
    "processing"
  );
  const [error, setError] = useState<string | null>(null);
  const hasProcessed = useRef(false);

  useEffect(() => {
    // 이미 처리했으면 다시 실행하지 않음
    if (hasProcessed.current) return;

    const handleCallback = async () => {
      hasProcessed.current = true; // 처리 시작 표시

      // URL에서 code 파라미터 추출
      const code = searchParams.get("code");
      const errorParam = searchParams.get("error");

      // 에러가 있는 경우
      if (errorParam) {
        setStatus("error");
        setError(`GitHub 로그인 실패: ${errorParam}`);
        setTimeout(() => navigate("/login"), 3000);
        return;
      }

      // code가 없는 경우
      if (!code) {
        setStatus("error");
        setError("인증 코드가 없습니다");
        setTimeout(() => navigate("/login"), 3000);
        return;
      }

      try {
        // 백엔드에 code 전송하여 JWT 토큰 받기
        const response = await api.auth.handleGitHubCallback(code);

        // 로그인 상태 업데이트
        login(response.access_token, response.user);

        setStatus("success");

        // Profile 페이지로 리다이렉트
        setTimeout(() => {
          navigate("/profile", { replace: true });
        }, 1500);
      } catch (err) {
        setStatus("error");
        setError(
          err instanceof Error
            ? err.message
            : "로그인 처리 중 오류가 발생했습니다"
        );
        setTimeout(() => navigate("/login"), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, login]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden">
        {status === "processing" && (
          <>
            {/* Header with gradient */}
            <div className="relative bg-linear-to-r from-indigo-50 to-purple-50 border-b border-indigo-100 px-8 py-6">
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
            <div className="bg-white px-8 py-16">
              <div className="text-center space-y-6">
                {/* 로딩 스피너 */}
                <div className="flex justify-center">
                  <svg
                    className="animate-spin h-16 w-16 text-indigo-600"
                    viewBox="0 0 24 24"
                  >
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
                </div>

                <div className="space-y-2">
                  <h2 className="text-2xl font-bold text-slate-900">
                    로그인 처리 중...
                  </h2>
                  <p className="text-sm text-slate-600">잠시만 기다려주세요</p>
                </div>
              </div>
            </div>
          </>
        )}

        {status === "success" && (
          <>
            {/* Header with gradient */}
            <div className="relative bg-linear-to-r from-indigo-50 to-purple-50 border-b border-indigo-100 px-8 py-6">
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
            <div className="bg-white px-8 py-16">
              <div className="text-center space-y-6">
                {/* 성공 아이콘 */}
                <div className="flex justify-center">
                  <div className="bg-green-100 rounded-full p-4">
                    <svg
                      className="h-16 w-16 text-green-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                </div>

                <div className="space-y-2">
                  <h2 className="text-2xl font-bold text-slate-900">
                    로그인 성공!
                  </h2>
                  <p className="text-sm text-slate-600">
                    환영합니다! 곧 홈으로 이동합니다...
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {status === "error" && (
          <>
            {/* Header with gradient */}
            <div className="relative bg-linear-to-r from-indigo-50 to-purple-50 border-b border-indigo-100 px-8 py-6">
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
            <div className="bg-white px-8 py-16">
              <div className="text-center space-y-6">
                {/* 에러 아이콘 */}
                <div className="flex justify-center">
                  <div className="bg-red-100 rounded-full p-4">
                    <svg
                      className="h-16 w-16 text-red-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </div>
                </div>

                <div className="space-y-2">
                  <h2 className="text-2xl font-bold text-slate-900">
                    로그인 실패
                  </h2>
                  <p className="text-sm text-red-600">{error}</p>
                  <p className="text-xs text-slate-500">
                    로그인 페이지로 돌아갑니다...
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
