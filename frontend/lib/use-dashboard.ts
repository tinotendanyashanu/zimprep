'use client';

import { useState, useEffect } from 'react';
import { getStudentHistory, getStudentRecommendations, HistoryEntry, Recommendation } from './api-client';
import { getUser } from './auth';

export interface DashboardData {
  recent_exams: Array<{
    exam_id: string;
    exam_name: string;
    date: string;
    grade: string;
    marks: number;
    max_marks: number;
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

function pctToGrade(pct: number): string {
  if (pct >= 80) return 'A';
  if (pct >= 70) return 'B';
  if (pct >= 60) return 'C';
  if (pct >= 50) return 'D';
  if (pct >= 40) return 'E';
  return 'U';
}

function derivePerformance(history: HistoryEntry[]): DashboardData['performance'] {
  if (!history.length) {
    return { average_grade: 'N/A', improvement_trend: 'stable', strengths: [], weaknesses: [] };
  }

  const pcts = history.map(h => (h.total > 0 ? (h.score / h.total) * 100 : 0));
  const avg = pcts.reduce((a, b) => a + b, 0) / pcts.length;

  let trend: 'up' | 'down' | 'stable' = 'stable';
  if (pcts.length >= 2) {
    const recent = pcts.slice(0, Math.ceil(pcts.length / 2));
    const older = pcts.slice(Math.ceil(pcts.length / 2));
    const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;
    if (recentAvg > olderAvg + 5) trend = 'up';
    else if (recentAvg < olderAvg - 5) trend = 'down';
  }

  const strengths = history.filter(h => h.total > 0 && (h.score / h.total) >= 0.7).map(h => h.subject);
  const weaknesses = history.filter(h => h.total > 0 && (h.score / h.total) < 0.5).map(h => h.subject);

  return {
    average_grade: pctToGrade(avg),
    improvement_trend: trend,
    strengths: [...new Set(strengths)].slice(0, 3),
    weaknesses: [...new Set(weaknesses)].slice(0, 3),
  };
}

function mapHistory(history: HistoryEntry[]): DashboardData['recent_exams'] {
  return history.slice(0, 10).map(h => ({
    exam_id: h.attempt_id,
    exam_name: `${h.subject} — ${h.paper}${h.year ? ` (${h.year})` : ''}`,
    date: h.date,
    grade: h.total > 0 ? pctToGrade((h.score / h.total) * 100) : 'N/A',
    marks: h.score,
    max_marks: h.total,
    can_appeal: true,
  }));
}

function mapRecommendations(recs: Recommendation[]): DashboardData['recommendations'] {
  return recs.map(r => ({
    topic: r.evidence?.related_topic as string ?? r.title,
    reason: r.explanation,
    resources: [],
  }));
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const user = getUser();
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const [history, recs] = await Promise.all([
          getStudentHistory(user.id),
          getStudentRecommendations(user.id),
        ]);

        setData({
          recent_exams: mapHistory(history),
          upcoming_exams: [],
          performance: derivePerformance(history),
          recommendations: mapRecommendations(recs),
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return { data, loading, error };
}
