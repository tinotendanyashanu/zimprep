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
  exam_board: "zimsec" | "cambridge";
  paper_count: number;
};

export type Paper = {
  id: string;
  year: number;
  paper_number: number;
  status: string;
};

export type MCQOption = { letter: string; text: string };

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
  mcq_options: MCQOption[] | null;
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
    duration_minutes: number;
    subject: { id: string; name: string; level: string };
  };
};

export type Attempt = {
  id: string;
  session_id: string;
  question_id: string;
  student_answer: string | null;
  answer_image_url: string | null;
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

export type WeakTopic = {
  topic: string;
  fail_ratio: number;
  attempt_count: number;
};

export type PracticeAttemptResult = Attempt;

export type ReadinessData = {
  readiness_index: number;
  accuracy: number;
  coverage: number;
  consistency: number;
};

export type StreakData = {
  current: number;
  longest: number;
};

export type SessionSummary = {
  session_id: string;
  mode: string;
  completed_at: string | null;
  paper_year: number | null;
  paper_number: number | null;
  subject_name: string | null;
  score: number;
  total_marks: number;
  percentage: number | null;
};

export type CoverageEntry = {
  topic: string;
  attempt_count: number;
  last_attempted: string | null;
};

export type CoverageData = {
  covered: CoverageEntry[];
  uncovered: CoverageEntry[];
  covered_count: number;
  total_count: number;
};

export type SubjectSummary = {
  id: string;
  name: string;
  level: string;
};

export type DashboardData = {
  has_data: boolean;
  subject_id?: string;
  subjects: SubjectSummary[];
  readiness: ReadinessData | null;
  streak: StreakData;
  coverage: CoverageData | null;
  weak_topics: WeakTopic[];
  recent_sessions: SessionSummary[];
};

export type ParentChild = {
  id: string;
  name: string;
  email: string;
  level: string;
  created_at: string;
};

export type ChildStatus = "Improving" | "Stable" | "At Risk";

export type ChildSummary = {
  student_id: string;
  name: string;
  level: string;
  avg_score: number;
  study_hours_this_week: number;
  questions_this_week: number;
  streak: number;
  status: ChildStatus;
  strong_subjects: string[];
  weak_subjects: string[];
  subjects: string[];
  days_inactive: number | null;
  avg_last7: number | null;
  avg_prev7: number | null;
  readiness_index: number;
  coverage: number;
  consistency: number;
};

export type FamilySummary = {
  total_study_hours: number;
  total_questions_attempted: number;
  avg_family_score: number;
  children_needing_attention: number;
  top_performing_child: string | null;
};

export type FamilyDashboard = {
  total_children: number;
  family_summary: FamilySummary;
  children: ChildSummary[];
};

export type ChildReportSection = {
  name: string;
  status: ChildStatus;
  avg_score: number;
  study_hours: number;
  questions_attempted: number;
  streak: number;
  strong_areas: string[];
  weak_areas: string[];
  performance_trend: string;
  readiness_index: number;
  recommendations_for_child: string[];
  recommendations_for_parent: string[];
};

export type WeeklyFamilyReport = {
  report_id?: string;
  week_ending: string;
  generated_at?: string;
  total_children: number;
  family_summary: FamilySummary;
  parent_insights: string[];
  children: ChildReportSection[];
};

export type ParentAlert = {
  id: string;
  student_id: string;
  alert_type: "inactivity" | "performance_drop" | "improving" | "goal_not_met";
  message: string;
  is_read: boolean;
  created_at: string;
};

export type ParentGoals = {
  weekly_hours_target: number;
  target_grade_percent: number;
  updated_at: string | null;
};

// ── Core fetch helper ──────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, init);
  if (!res.ok) {
    const json = await res.json().catch(() => ({}));
    const detail = (json as { detail?: unknown }).detail;
    const message =
      typeof detail === "string" ? detail : `Request failed (${res.status})`;
    throw new ApiError(message, res.status, detail ?? json);
  }
  return res.json() as Promise<T>;
}

// ── API functions ──────────────────────────────────────────────────────────────

export const getSubjects = (exam_board?: string, level?: string) => {
  const params = new URLSearchParams();
  if (exam_board) params.set("exam_board", exam_board);
  if (level) params.set("level", level);
  const qs = params.toString();
  return apiFetch<Subject[]>(`/papers/subjects${qs ? `?${qs}` : ""}`);
};

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
  answerImageUrl?: string,
) =>
  apiFetch<Attempt>("/attempts/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      student_answer: answer || null,
      answer_image_url: answerImageUrl || null,
    }),
  });

export const flagAttempt = (attemptId: string) =>
  apiFetch<{ flagged: boolean }>(`/attempts/${attemptId}/flag`, {
    method: "PATCH",
  });

export const getPracticeSession = (studentId: string, subjectId: string) =>
  apiFetch<{ session_id: string }>("/sessions/practice", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: studentId, subject_id: subjectId }),
  });

export const getNextQuestion = (subjectId: string, studentId: string, topic?: string, paperNumber?: number) => {
  const params = new URLSearchParams({ subject_id: subjectId, student_id: studentId });
  if (topic) params.set("topic", topic);
  if (paperNumber !== undefined) params.set("paper_number", String(paperNumber));
  return apiFetch<Question>(`/papers/questions/next?${params}`);
};

export const getSubjectTopics = (subjectId: string) =>
  apiFetch<string[]>(`/papers/subjects/${subjectId}/topics`);

export const getWeakTopics = (subjectId: string, studentId: string) =>
  apiFetch<WeakTopic[]>(
    `/papers/subjects/${subjectId}/weak-topics?student_id=${studentId}`,
  );

// ── Dashboard / Student analytics ──────────────────────────────────────────────

export const getStudentDashboard = (
  studentId: string,
  subjectId?: string,
  token?: string,
) => {
  const params = subjectId ? `?subject_id=${subjectId}` : "";
  return apiFetch<DashboardData>(`/students/${studentId}/dashboard${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
};

export const getStudentSubjects = (studentId: string, token?: string) =>
  apiFetch<SubjectSummary[]>(`/students/${studentId}/subjects`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const getStudentCoverage = (
  studentId: string,
  subjectId: string,
  token?: string,
) =>
  apiFetch<CoverageData>(`/students/${studentId}/coverage/${subjectId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const getStudentSessions = (
  studentId: string,
  limit = 10,
  token?: string,
) =>
  apiFetch<SessionSummary[]>(
    `/students/${studentId}/sessions?limit=${limit}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );

export const getStudentStreak = (studentId: string, token?: string) =>
  apiFetch<StreakData>(`/students/${studentId}/streak`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

// ── Parent account ──────────────────────────────────────────────────────────────

export const getParentChildren = (parentId: string, token?: string) =>
  apiFetch<ParentChild[]>(`/parents/${parentId}/children`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const linkChild = (
  parentId: string,
  childEmail: string,
  token?: string,
) =>
  apiFetch<{ success: boolean; student_id: string; name: string }>(
    `/parents/${parentId}/children/link`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ child_email: childEmail }),
    },
  );

export const getChildProgress = (
  parentId: string,
  studentId: string,
  subjectId?: string,
  token?: string,
) => {
  const params = subjectId ? `?subject_id=${subjectId}` : "";
  return apiFetch<DashboardData>(
    `/parents/${parentId}/children/${studentId}/progress${params}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
};

export const getParentFamilyDashboard = (parentId: string, token?: string) =>
  apiFetch<FamilyDashboard>(`/parents/${parentId}/family-dashboard`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const getParentReport = (parentId: string, token?: string) =>
  apiFetch<WeeklyFamilyReport>(`/parents/${parentId}/report`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const generateParentReport = (parentId: string, token?: string) =>
  apiFetch<WeeklyFamilyReport>(`/parents/${parentId}/report/generate`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const getParentAlerts = (parentId: string, token?: string, unreadOnly = false) => {
  const qs = unreadOnly ? "?unread_only=true" : "";
  return apiFetch<ParentAlert[]>(`/parents/${parentId}/alerts${qs}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
};

export const markAlertRead = (parentId: string, alertId: string, token?: string) =>
  apiFetch<{ success: boolean }>(`/parents/${parentId}/alerts/${alertId}/read`, {
    method: "PATCH",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const markAllAlertsRead = (parentId: string, token?: string) =>
  apiFetch<{ success: boolean }>(`/parents/${parentId}/alerts/read-all`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const getChildGoals = (parentId: string, studentId: string, token?: string) =>
  apiFetch<ParentGoals>(`/parents/${parentId}/children/${studentId}/goals`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const setChildGoals = (
  parentId: string,
  studentId: string,
  goals: { weekly_hours_target: number; target_grade_percent: number },
  token?: string,
) =>
  apiFetch<{ success: boolean }>(`/parents/${parentId}/children/${studentId}/goals`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(goals),
  });

export const checkParentAlerts = (parentId: string, token?: string) =>
  apiFetch<{ created: number; alerts: ParentAlert[] }>(
    `/parents/${parentId}/alerts/check`,
    {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  );
