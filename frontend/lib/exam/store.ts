import { create } from 'zustand';
import { ExamPaper, QuestionMarkResult } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Fetch with exponential-backoff retry (server errors only)
// ---------------------------------------------------------------------------

async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries = 3,
  baseDelayMs = 800,
): Promise<Response> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (!res.ok && attempt < retries && res.status >= 500) {
        await new Promise((r) => setTimeout(r, baseDelayMs * 2 ** attempt));
        continue;
      }
      return res;
    } catch (err) {
      if (attempt === retries) throw err;
      await new Promise((r) => setTimeout(r, baseDelayMs * 2 ** attempt));
    }
  }
  throw new Error('Max retries exceeded');
}

// ---------------------------------------------------------------------------
// localStorage helpers
// ---------------------------------------------------------------------------

function lsSave(key: string, val: unknown) {
  if (typeof window === 'undefined') return;
  try { localStorage.setItem(key, JSON.stringify(val)); } catch { /* quota */ }
}

function lsLoad<T>(key: string): T | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function lsClear(key: string) {
  if (typeof window === 'undefined') return;
  try { localStorage.removeItem(key); } catch { /* ignore */ }
}

// ---------------------------------------------------------------------------
// Store types
// ---------------------------------------------------------------------------

interface ExamState {
  paper: ExamPaper | null;
  attemptId: string | null;
  currentQuestionIndex: number;

  // Text answers (typed or confirmed OCR)
  answers: Record<string, string>;
  // Uploaded image URLs per question
  answerImages: Record<string, string>;

  timeLeft: number;
  status: 'idle' | 'running' | 'paused' | 'submitted' | 'marking';
  isSubmitting: boolean;
  submitError: string | null;
  markingResults: QuestionMarkResult[] | null;

  // Actions
  initializeExam: (paper: ExamPaper) => void;
  setAnswer: (questionId: string, answer: string) => void;
  setAnswerImage: (questionId: string, imageUrl: string) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  jumpToQuestion: (index: number) => void;
  tickTimer: () => void;
  submitExam: () => Promise<void>;
  /** Restore in-progress exam from localStorage after a refresh. Returns true if restored. */
  restoreSession: () => boolean;
}

// ---------------------------------------------------------------------------
// Auto-save key helpers
// ---------------------------------------------------------------------------

function answersKey(paperId: string) { return `zimprep_answers_${paperId}`; }
function imagesKey(paperId: string) { return `zimprep_images_${paperId}`; }
function timeKey(paperId: string) { return `zimprep_time_${paperId}`; }
function sessionKey(paperId: string) { return `zimprep_session_${paperId}`; }
function resultsKey(attemptId: string) { return `zimprep_results_${attemptId}`; }

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useExamStore = create<ExamState>((set, get) => ({
  paper: null,
  attemptId: null,
  currentQuestionIndex: 0,
  answers: {},
  answerImages: {},
  timeLeft: 0,
  status: 'idle',
  isSubmitting: false,
  submitError: null,
  markingResults: null,

  initializeExam: (paper) => {
    const attemptId = `attempt-${Date.now()}`;
    // Persist session info so refresh can restore
    lsSave(sessionKey(paper.id), { paper, attemptId, startedAt: Date.now() });

    set({
      paper,
      attemptId,
      currentQuestionIndex: 0,
      answers: {},
      answerImages: {},
      timeLeft: paper.durationMinutes * 60,
      status: 'running',
      submitError: null,
      markingResults: null,
    });
  },

  setAnswer: (questionId, answer) => set((state) => {
    const next = { ...state.answers, [questionId]: answer };
    if (state.paper) lsSave(answersKey(state.paper.id), next);
    return { answers: next };
  }),

  setAnswerImage: (questionId, imageUrl) => set((state) => {
    const next = { ...state.answerImages, [questionId]: imageUrl };
    if (state.paper) lsSave(imagesKey(state.paper.id), next);
    return { answerImages: next };
  }),

  nextQuestion: () => set((state) => {
    if (!state.paper) return state;
    const nextIdx = state.currentQuestionIndex + 1;
    return nextIdx < state.paper.questions.length
      ? { currentQuestionIndex: nextIdx }
      : state;
  }),

  prevQuestion: () => set((state) => {
    const prevIdx = state.currentQuestionIndex - 1;
    return prevIdx >= 0 ? { currentQuestionIndex: prevIdx } : state;
  }),

  jumpToQuestion: (index) => set((state) => {
    if (!state.paper) return state;
    return index >= 0 && index < state.paper.questions.length
      ? { currentQuestionIndex: index }
      : state;
  }),

  tickTimer: () => set((state) => {
    if (state.status !== 'running') return state;
    const newTime = state.timeLeft - 1;
    // Auto-save time so a refresh can restore roughly-correct remaining time
    if (state.paper && newTime % 30 === 0) lsSave(timeKey(state.paper.id), newTime);
    if (newTime <= 0) {
      get().submitExam();
      return { timeLeft: 0 };
    }
    return { timeLeft: newTime };
  }),

  submitExam: async () => {
    const state = get();
    if (!state.paper) return;

    set({ isSubmitting: true, submitError: null, status: 'marking' });

    const answers = state.paper.questions.map((q) => ({
      question_id: q.id,
      question_text: q.text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim(),
      student_answer: state.answers[q.id] || '',
      max_score: q.marks,
      question_type: q.type === 'mcq' ? 'mcq' : 'written',
      answer_image_url: state.answerImages[q.id] || null,
      topic: q.topic || '',
    }));

    try {
      const response = await fetchWithRetry(`${API_URL}/mark/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paper_id: state.paper.id,
          answers,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Submission failed' }));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      const attemptId = state.attemptId || result.attempt_id;

      // Persist results to localStorage so the results page can read them
      lsSave(resultsKey(attemptId), {
        attempt_id: attemptId,
        paper: state.paper,
        results: result.results,
        total_score: result.total_score,
        total_max_score: result.total_max_score,
        answers: state.answers,
        submitted_at: new Date().toISOString(),
      });

      // Clean up in-progress autosave
      lsClear(answersKey(state.paper.id));
      lsClear(imagesKey(state.paper.id));
      lsClear(timeKey(state.paper.id));
      lsClear(sessionKey(state.paper.id));

      set({ isSubmitting: false, status: 'submitted', markingResults: result.results });

      if (typeof window !== 'undefined') {
        window.location.href = `/results/${attemptId}`;
      }
    } catch (error) {
      // If backend unavailable, save answers to localStorage and show error
      const attemptId = state.attemptId || `attempt-${Date.now()}`;
      lsSave(resultsKey(attemptId), {
        attempt_id: attemptId,
        paper: state.paper,
        results: null,
        total_score: null,
        total_max_score: null,
        submitted_at: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Submission failed',
      });

      set({
        submitError: error instanceof Error ? error.message : 'Submission failed',
        isSubmitting: false,
        status: 'submitted',
      });
    }
  },

  restoreSession: () => {
    // Try to find any active session in localStorage
    if (typeof window === 'undefined') return false;
    const keys = Object.keys(localStorage).filter((k) => k.startsWith('zimprep_session_'));
    if (!keys.length) return false;

    // Use the most recent session
    for (const key of keys) {
      const session = lsLoad<{ paper: ExamPaper; attemptId: string; startedAt: number }>(key);
      if (!session?.paper) continue;

      const savedAnswers = lsLoad<Record<string, string>>(answersKey(session.paper.id)) || {};
      const savedImages = lsLoad<Record<string, string>>(imagesKey(session.paper.id)) || {};
      const savedTime = lsLoad<number>(timeKey(session.paper.id)) || session.paper.durationMinutes * 60;

      set({
        paper: session.paper,
        attemptId: session.attemptId,
        answers: savedAnswers,
        answerImages: savedImages,
        timeLeft: savedTime,
        status: 'running',
        currentQuestionIndex: 0,
        submitError: null,
        markingResults: null,
      });
      return true;
    }
    return false;
  },
}));
