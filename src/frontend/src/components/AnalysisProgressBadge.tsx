import { useNavigate } from 'react-router-dom';

interface AnalysisProgressBadgeProps {
  analysisId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  errorMessage?: string | null;
}

export default function AnalysisProgressBadge({
  analysisId,
  status,
  errorMessage
}: AnalysisProgressBadgeProps) {
  const navigate = useNavigate();

  const handleViewResults = () => {
    navigate(`/analysis/${analysisId}/result`);
  };

  const handleViewStatus = () => {
    navigate(`/analysis/${analysisId}`);
  };

  // Pending
  if (status === 'pending') {
    return (
      <div className="flex items-center space-x-2 px-3 py-1.5 bg-yellow-50 border border-yellow-200 rounded-md">
        <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
        <span className="text-sm text-yellow-700 font-medium">Queued</span>
        <button
          onClick={handleViewStatus}
          className="ml-2 text-xs text-yellow-600 hover:text-yellow-800 underline"
        >
          View
        </button>
      </div>
    );
  }

  // Processing
  if (status === 'processing') {
    return (
      <div className="flex items-center space-x-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-md">
        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
        <span className="text-sm text-blue-700 font-medium">Analyzing...</span>
        <button
          onClick={handleViewStatus}
          className="ml-2 text-xs text-blue-600 hover:text-blue-800 underline"
        >
          View
        </button>
      </div>
    );
  }

  // Completed
  if (status === 'completed') {
    return (
      <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-md">
        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <span className="text-sm text-green-700 font-medium">Completed</span>
        <button
          onClick={handleViewResults}
          className="ml-2 px-2 py-0.5 text-xs bg-green-600 text-white rounded hover:bg-green-700"
        >
          View Results
        </button>
      </div>
    );
  }

  // Failed
  if (status === 'failed') {
    return (
      <div className="flex items-center space-x-2 px-3 py-1.5 bg-red-50 border border-red-200 rounded-md">
        <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
        <span className="text-sm text-red-700 font-medium">Failed</span>
        {errorMessage && (
          <span className="text-xs text-red-600 truncate max-w-xs" title={errorMessage}>
            {errorMessage}
          </span>
        )}
        <button
          onClick={handleViewStatus}
          className="ml-2 text-xs text-red-600 hover:text-red-800 underline"
        >
          Details
        </button>
      </div>
    );
  }

  return null;
}
