import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

interface OngoingAnalysis {
  analysisId: string;
  repoUrl: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  errorMessage?: string | null;
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

const POLLING_INTERVAL = 3000; // 3 seconds
const STORAGE_KEY = 'ongoingAnalyses';

export function useAnalysisPolling() {
  const [ongoingAnalyses, setOngoingAnalyses] = useState<Map<string, OngoingAnalysis>>(new Map());

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as Array<[string, OngoingAnalysis]>;
        setOngoingAnalyses(new Map(parsed));
      }
    } catch (error) {
      console.error('Failed to load ongoing analyses from localStorage:', error);
    }
  }, []);

  // Save to localStorage when changed
  useEffect(() => {
    try {
      const data = Array.from(ongoingAnalyses.entries());
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('Failed to save ongoing analyses to localStorage:', error);
    }
  }, [ongoingAnalyses]);

  // Polling effect
  useEffect(() => {
    const activeAnalyses = Array.from(ongoingAnalyses.values()).filter(
      (analysis) => analysis.status === 'pending' || analysis.status === 'processing'
    );

    if (activeAnalyses.length === 0) {
      return; // No active analyses, don't start polling
    }

    const pollStatus = async () => {
      for (const analysis of activeAnalyses) {
        try {
          const data = await api.get<AnalysisStatusResponse>(
            `/api/v1/analysis/status/${analysis.analysisId}`
          );

          setOngoingAnalyses((prev) => {
            const next = new Map(prev);
            const current = next.get(analysis.repoUrl);

            if (current) {
              next.set(analysis.repoUrl, {
                ...current,
                status: data.status as OngoingAnalysis['status'],
                errorMessage: data.error_message
              });
            }

            return next;
          });
        } catch (error) {
          console.error(`Failed to poll status for ${analysis.analysisId}:`, error);
        }
      }
    };

    // Initial poll
    pollStatus();

    // Set up interval
    const interval = setInterval(pollStatus, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [ongoingAnalyses]);

  // Add analysis to tracking
  const addAnalysis = useCallback((analysisId: string, repoUrl: string) => {
    setOngoingAnalyses((prev) => {
      const next = new Map(prev);
      next.set(repoUrl, {
        analysisId,
        repoUrl,
        status: 'pending'
      });
      return next;
    });
  }, []);

  // Remove analysis from tracking
  const removeAnalysis = useCallback((repoUrl: string) => {
    setOngoingAnalyses((prev) => {
      const next = new Map(prev);
      next.delete(repoUrl);
      return next;
    });
  }, []);

  // Get analysis for specific repo
  const getAnalysis = useCallback(
    (repoUrl: string): OngoingAnalysis | undefined => {
      return ongoingAnalyses.get(repoUrl);
    },
    [ongoingAnalyses]
  );

  // Clear completed/failed analyses
  const clearCompleted = useCallback(() => {
    setOngoingAnalyses((prev) => {
      const next = new Map(prev);
      for (const [repoUrl, analysis] of next.entries()) {
        if (analysis.status === 'completed' || analysis.status === 'failed') {
          next.delete(repoUrl);
        }
      }
      return next;
    });
  }, []);

  return {
    ongoingAnalyses,
    addAnalysis,
    removeAnalysis,
    getAnalysis,
    clearCompleted
  };
}
