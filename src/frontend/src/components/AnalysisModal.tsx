import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

interface Repository {
  id: number;
  name: string;
  full_name: string;
  html_url: string;
  default_branch: string;
  owner: {
    login: string;
  };
}

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  repository: Repository | null;
  onAnalysisStarted?: (analysisId: string, repoUrl: string) => void;
}

type ModalStep = 'configure' | 'processing' | 'completed' | 'failed';

interface AnalysisResponse {
  analysis_id: string;
  task_id: string;
  status: string;
  message: string;
}

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

export default function AnalysisModal({
  isOpen,
  onClose,
  repository,
  onAnalysisStarted
}: AnalysisModalProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState<ModalStep>('configure');
  const [targetUser, setTargetUser] = useState('');
  const [branch, setBranch] = useState('');
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [status, setStatus] = useState<AnalysisStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Reset modal when opened
  useEffect(() => {
    if (isOpen && repository) {
      setStep('configure');
      setTargetUser('');
      setBranch(repository.default_branch);
      setAnalysisId(null);
      setStatus(null);
      setError('');
    }
  }, [isOpen, repository]);

  // Polling when processing
  useEffect(() => {
    if (!analysisId || step !== 'processing') return;

    const fetchStatus = async () => {
      try {
        const data = await api.get<AnalysisStatusResponse>(
          `/api/v1/analysis/status/${analysisId}`
        );
        setStatus(data);

        if (data.status === 'completed') {
          setStep('completed');
        } else if (data.status === 'failed') {
          setStep('failed');
          setError(data.error_message || 'Analysis failed');
        }
      } catch (err: any) {
        console.error('Failed to fetch status:', err);
      }
    };

    // Initial fetch
    fetchStatus();

    // Poll every 3 seconds
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [analysisId, step]);

  const handleStartAnalysis = async () => {
    if (!repository || !targetUser.trim()) {
      setError('Please enter target user');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post<AnalysisResponse>('/api/v1/analysis/analyze', {
        repo_url: repository.html_url,
        target_user: targetUser.trim(),
        branch: branch || repository.default_branch
      });

      setAnalysisId(response.analysis_id);
      setStep('processing');

      // Notify parent
      if (onAnalysisStarted) {
        onAnalysisStarted(response.analysis_id, repository.html_url);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleViewResults = () => {
    if (analysisId) {
      navigate(`/analysis/${analysisId}/result`);
      onClose();
    }
  };

  const handleClose = () => {
    // Don't close if processing
    if (step === 'processing') {
      const confirm = window.confirm(
        'Analysis is in progress. Close this modal? You can check the status from the repository list.'
      );
      if (!confirm) return;
    }
    onClose();
  };

  if (!isOpen || !repository) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Analyze Repository
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {/* Repository Info */}
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <div className="text-sm font-medium text-gray-900">{repository.full_name}</div>
            <div className="text-xs text-gray-500 mt-1">{repository.html_url}</div>
          </div>

          {/* Configure Step */}
          {step === 'configure' && (
            <div className="space-y-4">
              <div>
                <label htmlFor="targetUser" className="block text-sm font-medium text-gray-700 mb-1">
                  Target User *
                </label>
                <input
                  id="targetUser"
                  type="text"
                  required
                  placeholder="GitHub username"
                  value={targetUser}
                  onChange={(e) => setTargetUser(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter the GitHub username to analyze contributions
                </p>
              </div>

              <div>
                <label htmlFor="branch" className="block text-sm font-medium text-gray-700 mb-1">
                  Branch
                </label>
                <input
                  id="branch"
                  type="text"
                  placeholder={repository.default_branch}
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                  {error}
                </div>
              )}

              <button
                onClick={handleStartAnalysis}
                disabled={loading || !targetUser.trim()}
                className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Starting...' : 'Start Analysis'}
              </button>
            </div>
          )}

          {/* Processing Step */}
          {step === 'processing' && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Analyzing Repository
              </h4>
              <p className="text-sm text-gray-600 mb-4">
                {status?.status === 'pending' && 'Waiting for worker to pick up the task...'}
                {status?.status === 'processing' && 'Analyzing contributions...'}
              </p>
              <div className="text-xs text-gray-500">
                <p>Target User: {status?.target_user}</p>
                <p>Branch: {status?.branch}</p>
              </div>
              <button
                onClick={handleClose}
                className="mt-6 text-sm text-gray-600 hover:text-gray-900"
              >
                Close and check later
              </button>
            </div>
          )}

          {/* Completed Step */}
          {step === 'completed' && (
            <div className="text-center py-8">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Analysis Completed!
              </h4>
              <p className="text-sm text-gray-600 mb-6">
                The repository analysis has been completed successfully.
              </p>
              <div className="space-y-3">
                <button
                  onClick={handleViewResults}
                  className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  View Results
                </button>
                <button
                  onClick={onClose}
                  className="w-full py-2 px-4 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* Failed Step */}
          {step === 'failed' && (
            <div className="text-center py-8">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Analysis Failed
              </h4>
              <p className="text-sm text-red-600 mb-6">
                {error}
              </p>
              <button
                onClick={onClose}
                className="w-full py-2 px-4 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
