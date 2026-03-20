/**
 * Typed API client for the ZimPrep backend.
 * All calls go through /api/* which Next.js rewrites to the FastAPI server.
 */
import { supabase } from './supabase';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function getAccessToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('zimprep_token');
  localStorage.removeItem('zimprep_user');
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const res = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (res.status === 401) {
    clearAuth();
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Session expired. Please login again.');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Request failed: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

/** For multipart/form-data uploads — does not set Content-Type so browser sets the boundary. */
async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const token = await getAccessToken();
  const res = await fetch(path, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (res.status === 401) {
    clearAuth();
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Session expired. Please login again.');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Request failed: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Students
// ---------------------------------------------------------------------------

export interface HistoryEntry {
  attempt_id: string;
  subject: string;
  paper: string;
  year: number | null;
  score: number;
  total: number;
  date: string;
  status: string;
  mode: string;
}

export interface Recommendation {
  id: string;
  type: string;
  title: string;
  explanation: string;
  evidence: Record<string, unknown>;
  action: { label: string; route: string };
}

export interface SubjectProgress {
  subject: string;
  level: string;
  attempts: number;
  average_score: number;
  best_score: number;
  weak_topics: string[];
  suggested_focus: string[];
}

export interface ParentOverview {
  student_name: string;
  exam_level: string;
  subjects: string[];
  total_attempts: number;
  last_activity: string;
  engagement_status: string;
}

export const getStudentHistory = (studentId: string, limit = 30) =>
  apiFetch<HistoryEntry[]>(`/api/students/${studentId}/history?limit=${limit}`);

export const getStudentRecommendations = (studentId: string) =>
  apiFetch<Recommendation[]>(`/api/students/${studentId}/recommendations`);

export const getSubjectProgress = (studentId: string, subjectId: string) =>
  apiFetch<SubjectProgress>(`/api/students/${studentId}/progress/${subjectId}`);

export const getParentOverview = (parentId: string) =>
  apiFetch<ParentOverview>(`/api/students/parent/${parentId}/overview`);

// ---------------------------------------------------------------------------
// Marking
// ---------------------------------------------------------------------------

export interface AnswerSubmission {
  question_id: string;
  question_text: string;
  student_answer: string;
  max_score: number;
  question_type?: 'written' | 'mcq';
  answer_image_url?: string;
  topic?: string;
}

export interface QuestionMarkResult {
  question_id: string;
  score: number;
  max_score: number;
  correct_points: string[];
  missing_points: string[];
  feedback_summary: string;
  study_references: string[];
}

export interface BatchMarkResponse {
  attempt_id: string;
  total_score: number;
  total_max_score: number;
  results: QuestionMarkResult[];
}

export const batchMark = (paperId: string, answers: AnswerSubmission[]) =>
  apiFetch<BatchMarkResponse>('/api/mark/batch', {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId, answers }),
  });

export interface PracticeMarkRequest {
  question_id: string;
  question_text: string;
  student_answer: string;
  max_score: number;
  question_type?: 'written' | 'mcq';
  answer_image_url?: string;
  topic?: string;
  subject_id?: string;
  student_id?: string;
}

export const practiceMark = (req: PracticeMarkRequest) =>
  apiFetch<QuestionMarkResult & { attempt_id?: string }>('/api/practice/mark', {
    method: 'POST',
    body: JSON.stringify(req),
  });

export const flagAttempt = (attemptId: string) =>
  apiFetch<{ ok: boolean }>(`/api/attempts/${attemptId}/flag`, { method: 'POST' });

// ---------------------------------------------------------------------------
// Questions / catalog
// ---------------------------------------------------------------------------

export const getPaperQuestions = (paperId: string) =>
  apiFetch<unknown[]>(`/api/papers/${paperId}/questions`);

export const practiceNext = (subjectId: string, studentId?: string, topic?: string) => {
  const params = new URLSearchParams({ subject_id: subjectId });
  if (studentId) params.set('student_id', studentId);
  if (topic) params.set('topic', topic);
  return apiFetch<unknown>(`/api/practice/next?${params}`);
};

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

export interface AdminSubject {
  id: string;
  name: string;
  level: string;
}

export interface AdminPaper {
  id: string;
  subject_id: string;
  subject: AdminSubject | null;
  year: number;
  paper_number: number;
  status: 'processing' | 'ready' | 'error';
  pdf_url: string;
  created_at: string;
  qa_counts: { pending: number; approved: number; rejected: number };
}

export interface AdminQuestion {
  id: string;
  paper_id: string;
  question_number: string;
  sub_question: string | null;
  section: string | null;
  marks: number;
  text: string;
  question_type: 'written' | 'mcq';
  topic_tags: string[];
  has_image: boolean;
  image_url: string | null;
  qa_status: 'pending' | 'approved' | 'rejected';
  mcq_answer: { id: string; correct_option: string }[] | null;
}

export interface AdminQuestionPatch {
  qa_status?: 'approved' | 'rejected';
  question_number?: string;
  marks?: number;
  text?: string;
  question_type?: 'written' | 'mcq';
  topic_tags?: string[];
  mcq_correct_option?: 'A' | 'B' | 'C' | 'D';
}

export const adminListSubjects = () =>
  apiFetch<AdminSubject[]>('/api/admin/subjects');

export const adminListPapers = () =>
  apiFetch<AdminPaper[]>('/api/admin/papers');

export const adminUploadPaper = (formData: FormData) =>
  apiUpload<{ paper_id: string; status: string }>('/api/admin/papers', formData);

export const adminListPaperQuestions = (paperId: string, qaStatus?: string) => {
  const params = qaStatus ? `?qa_status=${qaStatus}` : '';
  return apiFetch<AdminQuestion[]>(`/api/admin/papers/${paperId}/questions${params}`);
};

export const adminPatchQuestion = (questionId: string, patch: AdminQuestionPatch) =>
  apiFetch<{ ok: boolean }>(`/api/admin/questions/${questionId}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });

export const adminDeleteQuestion = (questionId: string) =>
  apiFetch<void>(`/api/admin/questions/${questionId}`, { method: 'DELETE' });

export const adminUploadSyllabus = (formData: FormData) =>
  apiUpload<{ chunks_inserted: number }>('/api/admin/syllabus', formData);
