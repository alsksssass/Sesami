/**
 * 홈 페이지
 */
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Home() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();

  // 로딩 중
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // 로그인하지 않은 경우
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Sesami
          </h1>
          <p className="text-gray-600 mb-8">
            GitHub Contribution Analyzer
          </p>
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold
                     hover:bg-blue-700 transition-colors"
          >
            시작하기
          </button>
        </div>
      </div>
    );
  }

  // 로그인된 경우
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              Sesami
            </h1>

            {/* 사용자 정보 */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <img
                  src={user?.avatar_url}
                  alt={user?.username}
                  className="w-10 h-10 rounded-full"
                />
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">
                    {user?.username}
                  </p>
                  <p className="text-xs text-gray-500">
                    {user?.email}
                  </p>
                </div>
              </div>

              <button
                onClick={logout}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900
                         border border-gray-300 rounded-lg hover:bg-gray-50
                         transition-colors"
              >
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            환영합니다! 🎉
          </h2>

          <div className="space-y-4">
            <p className="text-gray-700">
              GitHub OAuth 로그인이 성공적으로 완료되었습니다.
            </p>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-2">
                ✅ 인증 정보
              </h3>
              <div className="space-y-1 text-sm text-green-800">
                <p><strong>GitHub ID:</strong> {user?.github_id}</p>
                <p><strong>Username:</strong> {user?.username}</p>
                <p><strong>Email:</strong> {user?.email || 'N/A'}</p>
                <p><strong>가입일:</strong> {new Date(user?.created_at || '').toLocaleDateString()}</p>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">
                📊 다음 단계
              </h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li>• GitHub 저장소 URL을 입력하여 분석 시작</li>
                <li>• 실시간으로 분석 진행률 확인</li>
                <li>• 기여자별 상세 통계 확인</li>
              </ul>
            </div>

            <div className="pt-4 flex gap-4">
              <button
                onClick={() => navigate('/repositories')}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold
                         hover:bg-blue-700 transition-colors"
              >
                내 레포지토리 보기
              </button>
              <button
                className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold
                         hover:bg-green-700 transition-colors"
              >
                저장소 분석 시작
              </button>
            </div>
          </div>
        </div>

        {/* API 테스트 섹션 */}
        <div className="mt-8 bg-white rounded-lg shadow p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            🧪 API 테스트
          </h3>

          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              JWT 토큰이 localStorage에 저장되어 있습니다:
            </p>
            <div className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
              <code className="text-xs text-gray-800 break-all">
                {localStorage.getItem('access_token')?.substring(0, 100)}...
              </code>
            </div>

            <p className="text-sm text-gray-600">
              이제 모든 API 요청에 자동으로 Authorization 헤더가 포함됩니다.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
