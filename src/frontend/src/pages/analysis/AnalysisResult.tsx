import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface ContributionResult {
  total_lines: number;
  added_lines: number;
  deleted_lines: number;
  commits: number;
  files_changed: number;
}

interface AnalysisResultResponse {
  analysis_id: string;
  repo_url: string;
  target_user: string;
  branch: string;
  status: string;
  results: ContributionResult | null;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export default function AnalysisResult() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!analysisId) return;

    const fetchResult = async () => {
      try {
        const data = await api.get<AnalysisResultResponse>(
          `/api/v1/analysis/result/${analysisId}`
        );
        setAnalysis(data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch analysis result');
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [analysisId]);

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

  if (analysis.status !== 'completed' || !analysis.results) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-6 py-4 rounded-lg">
          <p>Analysis is not completed yet.</p>
          <button
            onClick={() => navigate(`/analysis/${analysisId}`)}
            className="mt-2 text-blue-600 hover:text-blue-800 font-medium"
          >
            View Status
          </button>
        </div>
      </div>
    );
  }

  const { results } = analysis;

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              COMPLETED
            </span>
          </div>

          <div className="space-y-4 mb-8">
            <div>
              <label className="block text-sm font-medium text-gray-500">Repository</label>
              <p className="mt-1 text-gray-900">{analysis.repo_url}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500">Target User</label>
              <p className="mt-1 text-gray-900 font-medium">{analysis.target_user}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500">Branch</label>
                <p className="mt-1 text-gray-900">{analysis.branch}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Completed At</label>
                <p className="mt-1 text-gray-900">
                  {analysis.completed_at
                    ? new Date(analysis.completed_at).toLocaleString()
                    : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Contribution Statistics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-sm font-medium text-blue-600 mb-1">Total Lines</div>
                <div className="text-2xl font-bold text-blue-900">
                  {results.total_lines.toLocaleString()}
                </div>
                <div className="text-xs text-blue-600 mt-1">Current codebase</div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-sm font-medium text-green-600 mb-1">Added Lines</div>
                <div className="text-2xl font-bold text-green-900">
                  +{results.added_lines.toLocaleString()}
                </div>
                <div className="text-xs text-green-600 mt-1">All-time additions</div>
              </div>

              <div className="bg-red-50 rounded-lg p-4">
                <div className="text-sm font-medium text-red-600 mb-1">Deleted Lines</div>
                <div className="text-2xl font-bold text-red-900">
                  -{results.deleted_lines.toLocaleString()}
                </div>
                <div className="text-xs text-red-600 mt-1">All-time deletions</div>
              </div>

              <div className="bg-purple-50 rounded-lg p-4">
                <div className="text-sm font-medium text-purple-600 mb-1">Commits</div>
                <div className="text-2xl font-bold text-purple-900">
                  {results.commits.toLocaleString()}
                </div>
                <div className="text-xs text-purple-600 mt-1">Total commits</div>
              </div>

              <div className="bg-yellow-50 rounded-lg p-4">
                <div className="text-sm font-medium text-yellow-600 mb-1">Files Changed</div>
                <div className="text-2xl font-bold text-yellow-900">
                  {results.files_changed.toLocaleString()}
                </div>
                <div className="text-xs text-yellow-600 mt-1">Unique files</div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm font-medium text-gray-600 mb-1">Net Change</div>
                <div className="text-2xl font-bold text-gray-900">
                  {(results.added_lines - results.deleted_lines).toLocaleString()}
                </div>
                <div className="text-xs text-gray-600 mt-1">Added - Deleted</div>
              </div>
            </div>
          </div>

          <div className="mt-8 flex space-x-4">
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
