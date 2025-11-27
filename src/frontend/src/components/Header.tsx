import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { User } from "lucide-react";

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  // 현재 페이지 감지
  const currentPage =
    location.pathname === "/"
      ? "home"
      : location.pathname === "/profile"
      ? "profile"
      : location.pathname === "/evaluatechart"
      ? "evaluatechart"
      : "other";

  const handleLogout = () => {
    alert("감사합니다! 지원이 완료되었습니다.");
    logout();
    navigate("/");
  };

  // 로그인/콜백 페이지에서는 헤더 숨김
  if (
    location.pathname === "/login" ||
    location.pathname === "/auth/callback"
  ) {
    return null;
  }

  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        {/* 로고 */}
        <button
          onClick={() => navigate("/")}
          className="text-5xl text-indigo-600 hover:text-indigo-700 transition-colors font-bold"
          style={{ fontFamily: "Georgia, serif" }}
        >
          Sesami
        </button>

        {/* 우측 버튼들 */}
        <div className="flex items-center gap-4">
          {/* Profile 페이지가 아닐 때만 평가 기준 버튼 표시 */}
          {currentPage !== "profile" && (
            <button
              onClick={() => navigate("/evaluatechart")}
              className="px-4 py-2 text-slate-700 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors flex items-center gap-2"
            >
              <span className="text-base">ⓘ</span>
              <span>평가 기준</span>
            </button>
          )}

          {/* 로그인 / 내 페이지 / 로그아웃 */}
          {!isAuthenticated ? (
            <button
              onClick={() => navigate("/login")}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
            >
              지원하기
            </button>
          ) : currentPage === "home" || currentPage === "evaluatechart" ? (
            <button
              onClick={() => navigate("/profile")}
              className="px-6 py-2 border border-indigo-200 hover:bg-indigo-50 text-slate-700 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <User />
              <span>지원 페이지</span>
            </button>
          ) : (
            <button
              onClick={handleLogout}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
            >
              지원 완료
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
