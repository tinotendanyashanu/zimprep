/**
 * Dashboard Hook - Fetches real data from backend pipeline
 * 
 * Replaces mock data with real student_dashboard_v1 pipeline
 */

'use client';

import { useState, useEffect } from 'react';
import { executePipeline } from './api-client';
import { getUser } from './auth';

export interface DashboardData {
  recent_exams: Array<{
    exam_id: string;
    exam_name: string;
    date: string;
    grade: string;
    marks: number;
    max_marks: number;
    trace_id?: string;
    can_appeal?: boolean;
  }>;
  upcoming_exams: Array<{
    exam_id: string;
    exam_name: string;
    scheduled_date: string;
  }>;
  performance: {
    average_grade: string;
    improvement_trend: 'up' | 'down' | 'stable';
    strengths: string[];
    weaknesses: string[];
  };
  recommendations: Array<{
    topic: string;
    reason: string;
    resources: string[];
  }>;
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      const user = getUser();
      
      if (!user) {
        // Not authenticated - redirect handled by API client
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const result = await executePipeline('student_dashboard_v1', {
          user_id: user.id,
        });

        // Backend returns: engine_outputs -> reporting -> data_payload -> dashboard
        const reportingOutput = result.engine_outputs?.reporting;
        const dashboardData = reportingOutput?.data_payload?.dashboard || reportingOutput?.dashboard || result.engine_outputs?.dashboard;
        setData(dashboardData);
        setTraceId(result.trace_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
        setTraceId((err as any).trace_id || null);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  return { data, loading, error, traceId };
}
