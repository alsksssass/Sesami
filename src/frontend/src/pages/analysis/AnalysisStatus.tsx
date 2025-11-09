import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface AnalysisStatusResponse {
  analysis_id: string;
  repo_url: string;
  target_user: string;
  branch: string;
  status: string;
  task_id: string | null;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export default function AnalysisStatus() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<AnalysisStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!analysisId) return;

    const fetchStatus = async () => {
      try {
        const data = await api.get<AnalysisStatusResponse>(
          `/api/v1/analysis/status/${analysisId}`
        );
        setAnalysis(data);

        // 완료되면 결과 페이지로 이동
        if (data.status === 'completed') {
          navigate(`/analysis/${analysisId}/result`);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to fetch analysis status');
      } finally {
        setLoading(false);
      }
    };

    // 초기 로드
    fetchStatus();

    // pending 또는 processing 상태면 3초마다 폴링
    const interval = setInterval(() => {
      if (analysis && (analysis.status === 'pending' || analysis.status === 'processing')) {
        fetchStatus();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [analysisId, analysis?.status, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
          {error || 'Analysis not found'}
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-3 py-1 rounded-full text-sm font-medium';
    switch (status) {
      case 'pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'processing':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Analysis Status</h2>
            <span className={getStatusBadge(analysis.status)}>
              {analysis.status.toUpperCase()}
            </span>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Repository</label>
              <p className="mt-1 text-gray-900">{analysis.repo_url}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500">Target User</label>
              <p className="mt-1 text-gray-900">{analysis.target_user}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500">Branch</label>
              <p className="mt-1 text-gray-900">{analysis.branch}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500">Created At</label>
              <p className="mt-1 text-gray-900">
                {new Date(analysis.created_at).toLocaleString()}
              </p>
            </div>

            {analysis.completed_at && (
              <div>
                <label className="block text-sm font-medium text-gray-500">Completed At</label>
                <p className="mt-1 text-gray-900">
                  {new Date(analysis.completed_at).toLocaleString()}
                </p>
              </div>
            )}

            {analysis.error_message && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                <p className="font-medium">Error:</p>
                <p className="mt-1">{analysis.error_message}</p>
              </div>
            )}

            {(analysis.status === 'pending' || analysis.status === 'processing') && (
              <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-700 mr-3"></div>
                  <p>
                    {analysis.status === 'pending'
                      ? 'Waiting for worker to pick up the task...'
                      : 'Analyzing repository contributions...'}
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 flex space-x-4">
            <button
              onClick={() => navigate('/analysis/history')}
              className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              View History
            </button>
            <button
              onClick={() => navigate('/analysis/new')}
              className="flex-1 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              New Analysis
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
