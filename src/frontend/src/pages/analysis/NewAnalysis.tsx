import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface AnalysisResponse {
  analysis_id: string;
  task_id: string;
  status: string;
  message: string;
}

export default function NewAnalysis() {
  const navigate = useNavigate();
  const [repoUrl, setRepoUrl] = useState('');
  const [targetUser, setTargetUser] = useState('');
  const [branch, setBranch] = useState('main');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post<AnalysisResponse>('/api/v1/analysis/analyze', {
        repo_url: repoUrl,
        target_user: targetUser,
        branch
      });

      // 분석 상태 페이지로 이동
      navigate(`/analysis/${response.analysis_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">New Analysis</h2>
          <p className="mt-2 text-gray-600">
            Analyze GitHub repository contributions
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="repoUrl" className="block text-sm font-medium text-gray-700">
                Repository URL
              </label>
              <input
                id="repoUrl"
                type="text"
                required
                placeholder="https://github.com/owner/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="targetUser" className="block text-sm font-medium text-gray-700">
                Target User
              </label>
              <input
                id="targetUser"
                type="text"
                required
                placeholder="GitHub username"
                value={targetUser}
                onChange={(e) => setTargetUser(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="branch" className="block text-sm font-medium text-gray-700">
                Branch
              </label>
              <input
                id="branch"
                type="text"
                placeholder="main"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Starting Analysis...' : 'Start Analysis'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
