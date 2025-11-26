/**
 * 홈 페이지 (공개 랜딩 페이지)
 * 로그인 없이도 접근 가능
 */
import { useAuth } from "../contexts/AuthContext";
import { useState, useEffect } from "react";
import { api } from "../services/api";
import { X, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

const categories = [
  { id: undefined, label: "전체" },
  { id: "Frontend", label: "프론트엔드" },
  { id: "Backend", label: "백엔드" },
  { id: "AI/ML", label: "AI / 머신러닝" },
  { id: "Data", label: "데이터" },
] as const;

interface Developer {
  order: number;
  nickname: string;
  level: number;
  stack: string[];
  dev_type: string[];
}

export default function Home() {
  const { isLoading } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState<
    "Backend" | "Frontend" | "AI/ML" | "Data" | undefined
  >(undefined);
  const [developers, setDevelopers] = useState<Developer[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDeveloper, setSelectedDeveloper] = useState<string | null>(
    null
  );
  const [analysisResult, setAnalysisResult] = useState<string>("");
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // API 호출
  const fetchDevelopers = async (
    devType?: "Backend" | "Frontend" | "AI/ML" | "Data"
  ) => {
    try {
      setLoading(true);
      const response = await api.search.searchUsers({
        dev_type: devType,
        page: 1,
        size: 10,
      });
      setDevelopers(response.items);
    } catch (err) {
      console.error("개발자 조회 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드 & 카테고리 변경 시
  useEffect(() => {
    fetchDevelopers(selectedCategory);
  }, [selectedCategory]);

  // 개발자 클릭 시 분석 결과 조회
  const handleDeveloperClick = async (nickname: string) => {
    setSelectedDeveloper(nickname);
    setAnalysisLoading(true);
    try {
      const data = await api.analysis.getPublicUserAnalysis(nickname);
      setAnalysisResult(data.result);
    } catch (error) {
      console.error("분석 결과 조회 실패:", error);
      setAnalysisResult("분석 결과를 불러올 수 없습니다.");
    } finally {
      setAnalysisLoading(false);
    }
  };

  // 팝업 닫기
  const closeModal = () => {
    setSelectedDeveloper(null);
    setAnalysisResult("");
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

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 to-indigo-50/30">
      <div className="container mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="bg-white rounded-2xl shadow-sm border border-indigo-100 px-8 py-10 text-center">
            <h2 className="text-4xl font-bold bg-linear-to-r from-slate-900 to-indigo-900 bg-clip-text text-transparent mb-4">
              GitHub Contribution Analyzer
            </h2>
            <p className="text-xl text-slate-600">
              GitHub 저장소의 코드를 분석하고 시각화합니다
            </p>
          </div>
        </div>

        {/* Categories */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="flex flex-wrap gap-3 justify-center">
            {categories.map((category) => (
              <button
                key={category.label}
                onClick={() => setSelectedCategory(category.id)}
                className={`rounded-full px-6 py-2 font-medium transition-colors ${
                  selectedCategory === category.id
                    ? "bg-indigo-600 text-white hover:bg-indigo-700"
                    : "border-2 border-slate-300 text-slate-700 hover:border-indigo-400 hover:bg-indigo-50"
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
        </div>

        {/* Results Table */}
        <div className="max-w-6xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <p className="mt-2 text-slate-600">로딩 중...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-slate-700 font-semibold">
                      순위
                    </th>
                    <th className="px-6 py-4 text-left text-slate-700 font-semibold">
                      이름
                    </th>
                    <th className="px-6 py-4 text-left text-slate-700 font-semibold">
                      레벨
                    </th>
                    <th className="px-6 py-4 text-left text-slate-700 font-semibold">
                      분야
                    </th>
                    <th className="px-6 py-4 text-left text-slate-700 font-semibold">
                      기술 스택
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {developers.map((dev) => (
                    <tr
                      key={dev.nickname}
                      onClick={() => handleDeveloperClick(dev.nickname)}
                      className="hover:bg-indigo-50/50 transition-colors cursor-pointer"
                    >
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-500 font-medium">
                            #{dev.order}
                          </span>
                          {dev.order <= 3 && (
                            <span className="text-lg">
                              {dev.order === 1
                                ? "🥇"
                                : dev.order === 2
                                ? "🥈"
                                : "🥉"}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-5 text-slate-900 font-medium">
                        {dev.nickname}
                      </td>
                      <td className="px-6 py-5">
                        <span className="inline-block px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                          Lv.{dev.level}
                        </span>
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex flex-wrap gap-1">
                          {dev.dev_type.map((type) => (
                            <span
                              key={type}
                              className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium"
                            >
                              {type}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-5 text-slate-600 text-sm">
                        {dev.stack.join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 분석 결과 모달 */}
        {selectedDeveloper && (
          <div
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={closeModal}
          >
            <div
              className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 모달 헤더 */}
              <div className="border-b bg-linear-to-r from-indigo-50 to-purple-50 p-6 flex items-center justify-between">
                <h3 className="text-2xl text-slate-900 font-bold">
                  {selectedDeveloper} 분석 결과
                </h3>
                <button
                  onClick={closeModal}
                  className="p-2 hover:bg-white/50 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6 text-slate-600" />
                </button>
              </div>

              {/* 모달 내용 */}
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-88px)]">
                {analysisLoading ? (
                  <div className="text-center py-12">
                    <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mx-auto" />
                    <p className="mt-4 text-slate-600">
                      분석 결과를 불러오는 중...
                    </p>
                  </div>
                ) : (
                  <div className="markdown-content">
                    <ReactMarkdown>{analysisResult}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
