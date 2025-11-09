import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import AnalysisModal from '../components/AnalysisModal';
import AnalysisProgressBadge from '../components/AnalysisProgressBadge';
import { useAnalysisPolling } from '../hooks/useAnalysisPolling';

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
  forks_count: number;
  open_issues_count: number;
  default_branch: string;
  created_at: string;
  updated_at: string;
}

interface RepositoryListResponse {
  total_count: number;
  repositories: Repository[];
}

const Repositories: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'public' | 'private'>('all');

  // Analysis modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);

  // Analysis polling hook
  const { ongoingAnalyses, addAnalysis, getAnalysis, clearCompleted } = useAnalysisPolling();

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    fetchRepositories();
  }, [user, navigate, filter]);

  const fetchRepositories = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<RepositoryListResponse>(
        `/api/v1/analysis/repos/all?visibility=${filter}`
      );
      setRepos(response.repositories);
    } catch (err: any) {
      console.error('레포지토리 조회 실패:', err);
      setError(err instanceof Error ? err.message : '레포지토리를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getLanguageColor = (language: string | null) => {
    const colors: Record<string, string> = {
      JavaScript: 'bg-yellow-400',
      TypeScript: 'bg-blue-500',
      Python: 'bg-blue-600',
      Java: 'bg-red-500',
      Go: 'bg-cyan-500',
      Rust: 'bg-orange-600',
      Ruby: 'bg-red-600',
      PHP: 'bg-purple-500',
      C: 'bg-gray-600',
      'C++': 'bg-pink-600',
      'C#': 'bg-green-600',
      Swift: 'bg-orange-500',
      Kotlin: 'bg-purple-600',
    };
    return colors[language || ''] || 'bg-gray-400';
  };

  // Open analysis modal
  const handleAnalyzeClick = (repo: Repository) => {
    setSelectedRepo(repo);
    setIsModalOpen(true);
  };

  // Quick analyze (current user)
  const handleQuickAnalyze = async (repo: Repository) => {
    if (!user) return;

    const confirmed = window.confirm(
      `Analyze your contributions to ${repo.name}?\n\nTarget User: ${user.username}\nBranch: ${repo.default_branch}`
    );

    if (!confirmed) return;

    try {
      const response = await api.post<{
        analysis_id: string;
        task_id: string;
        status: string;
        message: string;
      }>('/api/v1/analysis/analyze', {
        repo_url: repo.html_url,
        target_user: user.username,
        branch: repo.default_branch
      });

      addAnalysis(response.analysis_id, repo.html_url);
    } catch (err: any) {
      alert(`Failed to start analysis: ${err.message}`);
    }
  };

  // Handle analysis started from modal
  const handleAnalysisStarted = (analysisId: string, repoUrl: string) => {
    addAnalysis(analysisId, repoUrl);
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">내 레포지토리</h1>
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                {repos.length}개
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                홈으로
              </button>
              <button
                onClick={() => navigate('/analysis/history')}
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                분석 히스토리
              </button>
              {ongoingAnalyses.size > 0 && (
                <button
                  onClick={clearCompleted}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium hover:bg-blue-200"
                >
                  진행 중 {ongoingAnalyses.size}개
                </button>
              )}
              <div className="flex items-center space-x-3">
                <img
                  src={user.avatar_url || ''}
                  alt={user.username}
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-gray-700 font-medium">{user.username}</span>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Filter Buttons */}
        <div className="mb-6 flex space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            전체
          </button>
          <button
            onClick={() => setFilter('public')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'public'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            공개
          </button>
          <button
            onClick={() => setFilter('private')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'private'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            비공개
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">레포지토리를 불러오는 중...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Repositories List */}
        {!loading && !error && (
          <div className="space-y-4">
            {repos.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                <p className="text-gray-600">레포지토리가 없습니다.</p>
              </div>
            ) : (
              repos.map((repo) => (
                <div
                  key={repo.id}
                  className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Repository Name */}
                      <div className="flex items-center space-x-2 mb-2">
                        <a
                          href={repo.html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xl font-bold text-blue-600 hover:underline"
                        >
                          {repo.name}
                        </a>
                        {repo.private ? (
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded border border-yellow-300">
                            비공개
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded border border-green-300">
                            공개
                          </span>
                        )}
                        {repo.fork && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">
                            Fork
                          </span>
                        )}
                      </div>

                      {/* Description */}
                      {repo.description && (
                        <p className="text-gray-600 mb-3">{repo.description}</p>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        {repo.language && (
                          <div className="flex items-center space-x-1">
                            <span
                              className={`w-3 h-3 rounded-full ${getLanguageColor(
                                repo.language
                              )}`}
                            ></span>
                            <span>{repo.language}</span>
                          </div>
                        )}
                        <div className="flex items-center space-x-1">
                          <svg
                            className="w-4 h-4"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          <span>{repo.stargazers_count}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <svg
                            className="w-4 h-4"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span>{repo.forks_count}</span>
                        </div>
                        {repo.open_issues_count > 0 && (
                          <div className="flex items-center space-x-1">
                            <svg
                              className="w-4 h-4"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                                clipRule="evenodd"
                              />
                            </svg>
                            <span>{repo.open_issues_count} issues</span>
                          </div>
                        )}
                        <span className="text-gray-400">
                          업데이트: {formatDate(repo.updated_at)}
                        </span>
                      </div>
                    </div>

                    {/* Analysis Actions */}
                    <div className="ml-4 flex flex-col items-end space-y-2">
                      {/* Ongoing analysis badge */}
                      {getAnalysis(repo.html_url) && (
                        <AnalysisProgressBadge
                          analysisId={getAnalysis(repo.html_url)!.analysisId}
                          status={getAnalysis(repo.html_url)!.status}
                          errorMessage={getAnalysis(repo.html_url)!.errorMessage}
                        />
                      )}

                      {/* Analysis buttons */}
                      {!getAnalysis(repo.html_url) && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleQuickAnalyze(repo)}
                            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
                          >
                            빠른 분석
                          </button>
                          <button
                            onClick={() => handleAnalyzeClick(repo)}
                            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50 transition-colors"
                          >
                            분석...
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>

      {/* Analysis Modal */}
      <AnalysisModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        repository={selectedRepo}
        onAnalysisStarted={handleAnalysisStarted}
      />
    </div>
  );
};

export default Repositories;
