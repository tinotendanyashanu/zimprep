/**
 * Typed API client for all ZimPrep backend calls.
 * All pages import from here — no raw fetch calls in components.
 */

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────────

export type Subject = {
  id: string;
  name: string;
  level: string;
  paper_count: number;
};

export type Paper = {
  id: string;
  year: number;
  paper_number: number;
  status: string;
};

export type Question = {
  id: string;
  paper_id: string;
  question_number: string;
  sub_question: string | null;
  section: string | null;
  marks: number;
  text: string;
  has_image: boolean;
  image_url: string | null;
  topic_tags: string[];
  question_type: "written" | "mcq";
  mcq_answer: string | null;
};

export type Session = {
  id: string;
  student_id: string;
  paper_id: string;
  mode: "exam" | "practice";
  started_at: string;
  completed_at: string | null;
  status: string;
  paper?: {
    id: string;
    year: number;
    paper_number: number;
    subject: { id: string; name: string; level: string };
  };
};

export type Attempt = {
  id: string;
  session_id: string;
  question_id: string;
  student_answer: string | null;
  ai_score: number | null;
  ai_feedback: {
    correct_points: string[];
    missing_points: string[];
    examiner_note: string;
  } | null;
  ai_references: string[] | null;
  marked_at: string | null;
  flagged: boolean;
};

export type ResultsResponse = {
  all_marked: boolean;
  marked_count: number;
  total_count: number;
  total_score: number;
  attempts: Attempt[];
};

// ── Core fetch helper ──────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

// ── API functions ──────────────────────────────────────────────────────────────

export const getSubjects = () =>
  apiFetch<Subject[]>("/papers/subjects");

export const getPapersForSubject = (subjectId: string) =>
  apiFetch<Paper[]>(`/papers/subjects/${subjectId}/papers`);

export const getQuestionsForPaper = (paperId: string) =>
  apiFetch<Question[]>(`/papers/${paperId}/questions`);

export const createSession = (studentId: string, paperId: string, mode: string) =>
  apiFetch<{ session_id: string }>("/sessions/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: studentId, paper_id: paperId, mode }),
  });

export const getSession = (sessionId: string) =>
  apiFetch<Session>(`/sessions/${sessionId}`);

export const autosaveSession = (sessionId: string, answers: Record<string, string>) =>
  apiFetch<{ saved: boolean }>(`/sessions/${sessionId}/autosave`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });

export const submitSession = (sessionId: string, answers: Record<string, string>) =>
  apiFetch<{ status: string; session_id: string }>(`/sessions/${sessionId}/submit`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });

export const getResults = (sessionId: string) =>
  apiFetch<ResultsResponse>(`/sessions/${sessionId}/results`);

export const submitAttempt = (
  sessionId: string,
  questionId: string,
  answer: string,
) =>
  apiFetch<Attempt>("/attempts/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      student_answer: answer,
    }),
  });

export const flagAttempt = (attemptId: string) =>
  apiFetch<{ flagged: boolean }>(`/attempts/${attemptId}/flag`, {
    method: "PATCH",
  });
