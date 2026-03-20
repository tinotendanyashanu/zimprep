import { AttemptHistoryItem, SubjectProgress } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getHistory(studentId: string): Promise<AttemptHistoryItem[]> {
  const res = await fetch(`${API_URL}/students/${studentId}/history`);
  if (!res.ok) return [];
  const data = await res.json();
  return data as AttemptHistoryItem[];
}

export async function getSubjectProgress(
  studentId: string,
  subjectId: string,
): Promise<SubjectProgress> {
  const res = await fetch(`${API_URL}/students/${studentId}/progress/${subjectId}`);
  if (!res.ok) {
    return {
      subject: "",
      level: "",
      attempts: 0,
      average_score: 0,
      best_score: 0,
      trend: [],
      weak_topics: [],
      suggested_focus: [],
    };
  }
  return res.json();
}

// Legacy sync stubs — kept so existing pages that call these don't crash
// before they're updated to async.
export const MOCK_HISTORY: AttemptHistoryItem[] = [];
export const MOCK_KNOWLEDGE_GAPS: string[] = [];
export const MOCK_SUGGESTED_FOCUS: string[] = [];
