/**
 * 개인 페이지 (기존 Home.tsx 내용)
 */
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Folder } from "lucide-react";

export default function Profile() {
  const { user, isAuthenticated, isLoading } = useAuth();
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
    navigate("/");
    return null;
  }

  // 로그인된 경우
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50/30">
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-6xl mx-auto">
          {/* Profile Header */}
          <div className="mb-8 shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-indigo-100">
              <div className="p-8">
                <div className="flex items-center gap-6">
                  <div className="w-28 h-28 rounded-full border-4 border-white shadow-md overflow-hidden">
                    <img
                      className="w-full h-full object-cover"
                      src={user?.avatar_url}
                      alt="Profile"
                    />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="px-6 py-2.5 rounded-lg bg-indigo-100 text-indigo-700 border-indigo-300">
                        <span className="text-2xl">{user?.username}</span>
                      </div>
                    </div>
                    <p className="text-slate-600">
                      <strong>Email: </strong>
                      {user?.email || "N/A"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* Repository Analysis Section */}
          <div className="mb-6">
            <h2 className="text-2xl text-slate-900">Repository 분석</h2>
          </div>

          {/* repo_count에 따라 다른 UI 표시 */}
          {(user?.repo_count ?? 0) <= 0 ? (
            // repo_count가 0 이하일 때: Repository 선택 안내
            <div className="shadow-lg overflow-hidden">
              <div className="p-16 text-center bg-linear-to-br from-slate-50 to-indigo-50/20">
                <div className="max-w-md mx-auto space-y-6">
                  <div className="w-20 h-20 mx-auto rounded-full bg-linear-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
                    <Folder className="w-10 h-10 text-indigo-600" />
                  </div>
                  <div>
                    <p className="text-2xl text-slate-900 mb-2">
                      Repository를 선택해주세요
                    </p>
                    <p className="text-slate-600">
                      최대 3개의 Repository를 선택하여 분석받을 수 있습니다
                    </p>
                  </div>
                  <button
                    onClick={() => navigate("/repositories")}
                    className="bg-linear-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-lg px-10 py-6 h-auto shadow-lg hover:shadow-xl transition-all duration-200"
                  >
                    Repository 선택하기
                  </button>
                </div>
              </div>
            </div>
          ) : (
            // repo_count가 0보다 클 때: 공백 (추후 분석 결과 표시)
            <div className="shadow-lg overflow-hidden">
              <div className="p-16 text-center bg-white">
                {/* 추후 분석 결과 UI 추가 예정 */}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// // 로그인된 경우
// return (
//   <div className="min-h-screen bg-gray-50">
//     {/* 메인 콘텐츠 */}
//     <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
//       <div className="bg-white rounded-lg shadow p-8">
//         <h2 className="text-2xl font-bold text-gray-900 mb-4">
//           환영합니다! 🎉
//         </h2>

//         <div className="space-y-4">
//           <p className="text-gray-700">
//             GitHub OAuth 로그인이 성공적으로 완료되었습니다.
//           </p>

//           <div className="bg-green-50 border border-green-200 rounded-lg p-4">
//             <h3 className="font-semibold text-green-900 mb-2">
//               ✅ 인증 정보
//             </h3>
//             <div className="space-y-1 text-sm text-green-800">
//               <p><strong>GitHub ID:</strong> {user?.github_id}</p>
//               <p><strong>Username:</strong> {user?.username}</p>
//               <p><strong>Email:</strong> {user?.email || 'N/A'}</p>
//               <p><strong>가입일:</strong> {new Date(user?.created_at || '').toLocaleDateString()}</p>
//             </div>
//           </div>

//           <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
//             <h3 className="font-semibold text-blue-900 mb-2">
//               📊 다음 단계
//             </h3>
//             <ul className="space-y-2 text-sm text-blue-800">
//               <li>• GitHub 저장소 URL을 입력하여 분석 시작</li>
//               <li>• 실시간으로 분석 진행률 확인</li>
//               <li>• 기여자별 상세 통계 확인</li>
//             </ul>
//           </div>

//           <div className="pt-4 flex gap-4">
//             <button
//               onClick={() => navigate('/repositories')}
//               className="px-6 py-3 bg-blue-600 text-black rounded-lg font-semibold
//                        hover:bg-blue-700 transition-colors"
//             >
//               내 레포지토리 보기
//             </button>
//             <button
//               className="px-6 py-3 bg-green-600 text-black rounded-lg font-semibold
//                        hover:bg-green-700 transition-colors"
//             >
//               저장소 분석 시작
//             </button>
//           </div>
//         </div>
//       </div>
//     </main>
//   </div>

// );
