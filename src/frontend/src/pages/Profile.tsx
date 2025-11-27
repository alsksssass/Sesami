/**
 * 개인 페이지 (기존 Home.tsx 내용)
 */
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Folder, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../services/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface RepositoryAnalysisResult {
  skill_profile_result?: any;
  result?: string; // ← 마크다운 문자열
  reporter_result?: any;
  user_aggregator_result?: any;
  static_analyzer_result?: any;
}

export interface RepositoryAnalysis {
  name: string;
  url: string;
  result?: RepositoryAnalysisResult; // 분석 결과 객체
  state: "PROCESSING" | "COMPLETED" | "FAILED";
  error_log?: string;
}

interface UserAnalysis {
  result: string; // 마크다운 형태의 종합 분석 결과
  status?: "PROCESSING" | "COMPLETED" | "FAILED";
}

export default function Profile() {
  const { user, isAuthenticated, isLoading, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [repositories, setRepositories] = useState<RepositoryAnalysis[]>([]);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [userAnalysis, setUserAnalysis] = useState<UserAnalysis | null>(null);
  const [userAnalysisLoading, setUserAnalysisLoading] = useState(false);

  // 마크다운 텍스트 전처리 함수
  const preprocessMarkdown = (text: string): string => {
    // 이스케이프된 개행 문자를 실제 개행으로 변환
    return text.replace(/\\n/g, "\n");
  };

  // 페이지 마운트 시 user 정보 백그라운드 재검증
  useEffect(() => {
    // 백그라운드에서 실제 user 정보 가져오기 (낙관적 업데이트 보정)
    refreshUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // repo_count가 0보다 클 때 분석 결과 조회
  useEffect(() => {
    if ((user?.repo_count ?? 0) > 0) {
      fetchRepositoryAnalysis();
      fetchUserAnalysis();
    }
  }, [user]);

  const fetchRepositoryAnalysis = async () => {
    try {
      setAnalysisLoading(true);
      const data = await api.analysis.getMyRepositoryAnalysis();
      console.log("[Repository Analysis Raw Data]", data);
      data.repositories.forEach((repo: RepositoryAnalysis, index: number) => {
        console.log(
          `[Repository ${index + 1}: ${repo.name}]`,
          repo.result?.result
        );
      });
      setRepositories(data.repositories);
    } catch (error) {
      console.error("분석 결과 조회 실패:", error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const fetchUserAnalysis = async () => {
    try {
      setUserAnalysisLoading(true);
      const data = await api.analysis.getUserAnalysis();
      setUserAnalysis(data);
    } catch (error) {
      console.error("종합 분석 조회 실패:", error);
    } finally {
      setUserAnalysisLoading(false);
    }
  };

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
    <div className="min-h-screen bg-linear-to-br from-slate-50 to-indigo-50/30">
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-6xl mx-auto">
          {/* Profile Header */}
          <div className="mb-8 shadow-lg overflow-hidden">
            <div className="bg-linear-to-r from-indigo-50 to-purple-50 border-b border-indigo-100">
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
            // repo_count가 0보다 클 때: 분석 결과 표시
            <div className="space-y-6">
              {/* 사용자 종합 분석 */}
              <div className="shadow-lg overflow-hidden rounded-lg">
                <div className="border-b bg-linear-to-r from-indigo-50 to-purple-50 p-6">
                  <h3 className="text-xl text-slate-900 font-semibold">
                    개발자 종합 분석
                  </h3>
                </div>
                <div className="p-6 bg-white">
                  {userAnalysisLoading ||
                  userAnalysis?.status === "PROCESSING" ? (
                    <div className="text-center py-8">
                      <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto" />
                      <p className="mt-3 text-slate-600">
                        종합 분석을 생성하는 중...
                      </p>
                    </div>
                  ) : userAnalysis?.status === "COMPLETED" ? (
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {preprocessMarkdown(userAnalysis.result)}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      종합 분석 결과를 불러올 수 없습니다.
                    </div>
                  )}
                </div>
              </div>

              {/* Repository 분석 결과 */}
              <div className="mb-4">
                <h3 className="text-xl text-slate-900 font-semibold">
                  Repository별 상세 분석
                </h3>
              </div>

              {analysisLoading ? (
                <div className="text-center py-12 bg-white shadow-lg rounded-lg">
                  <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mx-auto" />
                  <p className="mt-4 text-slate-600">
                    분석 결과를 불러오는 중...
                  </p>
                </div>
              ) : (
                repositories.map((repo, index) => (
                  <div
                    key={repo.url}
                    className="shadow-lg overflow-hidden rounded-lg"
                  >
                    <div className="border-b bg-linear-to-r from-indigo-50 to-purple-50 p-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-white rounded-lg shadow-sm">
                          <Folder className="w-5 h-5 text-indigo-600" />
                        </div>
                        <h3 className="text-xl text-slate-900 font-semibold">
                          {repo.name}
                        </h3>
                        <span className="ml-auto px-3 py-1 rounded-full border border-indigo-300 text-indigo-700 text-sm">
                          Repository {index + 1}
                        </span>
                      </div>
                    </div>
                    <div className="p-6 bg-white">
                      {repo.state === "COMPLETED" && repo.result ? (
                        <div className="markdown-content">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {preprocessMarkdown(repo.result?.result || "")}
                          </ReactMarkdown>
                        </div>
                      ) : repo.state === "PROCESSING" ? (
                        <div className="text-center py-8">
                          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto" />
                          <p className="mt-3 text-slate-600">분석 진행 중...</p>
                        </div>
                      ) : repo.state === "FAILED" ? (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                          <p className="text-red-800">
                            <strong>오류:</strong> {repo.error_log}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
