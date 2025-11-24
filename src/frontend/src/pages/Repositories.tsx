import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import { Lock, Unlock, Calendar, Code } from "lucide-react";

interface RepositoryOwner {
  login: string;
  avatar_url: string;
  html_url: string;
}

interface Repository {
  id: number;
  name: string;
  full_name: string;
  owner: RepositoryOwner;
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
}

const Repositories: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRepos, setSelectedRepos] = useState<number[]>([]);
  const maxSelection = 3;

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }

    fetchRepositories();
  }, [user, navigate]);

  const fetchRepositories = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.analysis.getRepositories();
      setRepos(response.repositories);
    } catch (err: unknown) {
      console.error("레포지토리 조회 실패:", err);
      setError(
        err instanceof Error
          ? err.message
          : "레포지토리를 불러오는데 실패했습니다."
      );
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const toggleRepo = (id: number) => {
    setSelectedRepos((prev) => {
      if (prev.includes(id)) {
        return prev.filter((repoId) => repoId !== id);
      } else if (prev.length < maxSelection) {
        return [...prev, id];
      }
      return prev;
    });
  };

  const handleComplete = async () => {
    try {
      // 선택된 레포지토리의 URL 가져오기
      const selectedRepoUrls = repos
        .filter((repo) => selectedRepos.includes(repo.id))
        .map((repo) => repo.html_url);

      if (selectedRepoUrls.length === 0) {
        return;
      }

      await api.analysis.analyzeRepositories(selectedRepoUrls);

      // 성공 메시지 표시
      alert(`${selectedRepoUrls.length}개의 레포지토리 분석이 시작되었습니다.`);

      // 프로필 페이지로 이동
      navigate("/profile");
    } catch (err: unknown) {
      console.error("분석 요청 실패:", err);
      alert(
        err instanceof Error
          ? err.message
          : "레포지토리 분석 요청에 실패했습니다."
      );
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 to-indigo-50/30">
      {/* Header */}
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl text-slate-900 mb-2">레포지토리 선택</h1>
              <p className="text-slate-600">
                총 {repos.length}개 (최대 {maxSelection}개 선택 가능)
              </p>
            </div>
            <button
              className={`px-8 py-2 rounded-md font-medium transition-colors ${
                selectedRepos.length === 0
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-700 text-white"
              }`}
              disabled={selectedRepos.length === 0}
              onClick={handleComplete}
            >
              선택완료 ({selectedRepos.length}/{maxSelection})
            </button>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              <p className="mt-4 text-slate-600">레포지토리를 불러오는 중...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Repository List */}
          {!loading && !error && (
            <div className="space-y-4">
              {repos.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                  <p className="text-slate-600">레포지토리가 없습니다.</p>
                </div>
              ) : (
                repos.map((repo) => {
                  const isSelected = selectedRepos.includes(repo.id);
                  const isDisabled =
                    !isSelected && selectedRepos.length >= maxSelection;

                  return (
                    <div
                      key={repo.id}
                      className={`rounded-lg border shadow-sm transition-all hover:shadow-md p-6 ${
                        isSelected
                          ? "ring-2 ring-indigo-500 bg-indigo-50"
                          : "bg-white border-gray-200"
                      } ${
                        isDisabled
                          ? "opacity-50 cursor-not-allowed"
                          : "cursor-pointer"
                      }`}
                      onClick={() => !isDisabled && toggleRepo(repo.id)}
                    >
                      <div className="flex items-center gap-4">
                        {/* Checkbox */}
                        <input
                          type="checkbox"
                          checked={isSelected}
                          disabled={isDisabled}
                          onChange={() => !isDisabled && toggleRepo(repo.id)}
                          className="w-5 h-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          onClick={(e) => e.stopPropagation()}
                        />

                        {/* Project Name */}
                        <div className="flex-1">
                          <h3 className="text-xl text-slate-900 mb-1">
                            {repo.name}
                          </h3>
                        </div>

                        {/* Visibility Badge */}
                        <div
                          className={`flex items-center gap-1.5 px-3 py-1 rounded ${
                            repo.private
                              ? "bg-slate-200 text-slate-700"
                              : "bg-green-100 text-green-700"
                          }`}
                        >
                          {repo.private ? (
                            <>
                              <Lock className="w-3.5 h-3.5" />
                              비공개
                            </>
                          ) : (
                            <>
                              <Unlock className="w-3.5 h-3.5" />
                              공개
                            </>
                          )}
                        </div>

                        {/* Language */}
                        {repo.language && (
                          <div className="flex items-center gap-2 text-slate-600">
                            <Code className="w-4 h-4" />
                            <span>{repo.language}</span>
                          </div>
                        )}

                        {/* Created Date */}
                        <div className="flex items-center gap-2 text-slate-500">
                          <Calendar className="w-4 h-4" />
                          <span className="text-sm">
                            생성일: {formatDate(repo.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Repositories;
