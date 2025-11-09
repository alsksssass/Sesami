/**
 * GitHub OAuth 콜백 페이지
 * GitHub에서 리다이렉트된 후 authorization code를 처리
 */
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      // URL에서 code 파라미터 추출
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');

      // 에러가 있는 경우
      if (errorParam) {
        setStatus('error');
        setError(`GitHub 로그인 실패: ${errorParam}`);
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      // code가 없는 경우
      if (!code) {
        setStatus('error');
        setError('인증 코드가 없습니다');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      try {
        // 백엔드에 code 전송하여 JWT 토큰 받기
        const response = await api.auth.handleGitHubCallback(code);

        // 로그인 상태 업데이트
        login(response.access_token, response.user);

        setStatus('success');

        // 홈으로 리다이렉트
        setTimeout(() => navigate('/'), 1000);
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : '로그인 처리 중 오류가 발생했습니다');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, login]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="max-w-md w-full p-10 bg-white rounded-xl shadow-2xl">
        {status === 'processing' && (
          <div className="text-center space-y-4">
            {/* 로딩 스피너 */}
            <div className="flex justify-center">
              <svg
                className="animate-spin h-16 w-16 text-blue-600"
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

            <h2 className="text-2xl font-bold text-gray-900">
              로그인 처리 중...
            </h2>
            <p className="text-gray-600">
              잠시만 기다려주세요
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center space-y-4">
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

            <h2 className="text-2xl font-bold text-gray-900">
              로그인 성공!
            </h2>
            <p className="text-gray-600">
              환영합니다! 곧 홈으로 이동합니다...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center space-y-4">
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

            <h2 className="text-2xl font-bold text-gray-900">
              로그인 실패
            </h2>
            <p className="text-red-600">
              {error}
            </p>
            <p className="text-gray-600 text-sm">
              로그인 페이지로 돌아갑니다...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
