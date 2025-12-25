import { create } from 'zustand';
import { ExamPaper, Question } from './types';
import { executePipeline } from '../api-client';
import { getUser } from '../auth';

interface ExamState {
  paper: ExamPaper | null;
  currentQuestionIndex: number;
  answers: Record<string, string>; // questionId -> answer
  timeLeft: number; // in seconds
  status: 'idle' | 'running' | 'paused' | 'submitted';
  isSubmitting: boolean;
  submitError: string | null;
  traceId: string | null;
  
  // Actions
  initializeExam: (paper: ExamPaper) => void;
  setAnswer: (questionId: string, answer: string) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  jumpToQuestion: (index: number) => void;
  tickTimer: () => void;
  submitExam: () => Promise<void>;
}

export const useExamStore = create<ExamState>((set, get) => ({
  paper: null,
  currentQuestionIndex: 0,
  answers: {},
  timeLeft: 0,
  status: 'idle',
  isSubmitting: false,
  submitError: null,
  traceId: null,

  initializeExam: (paper) => set({
    paper,
    currentQuestionIndex: 0,
    answers: {},
    timeLeft: paper.durationMinutes * 60,
    status: 'running',
    submitError: null,
    traceId: null,
  }),

  setAnswer: (questionId, answer) => set((state) => ({
    answers: { ...state.answers, [questionId]: answer }
  })),

  nextQuestion: () => set((state) => {
    if (!state.paper) return state;
    const nextIndex = state.currentQuestionIndex + 1;
    return nextIndex < state.paper.questions.length 
      ? { currentQuestionIndex: nextIndex } 
      : state;
  }),

  prevQuestion: () => set((state) => {
    const prevIndex = state.currentQuestionIndex - 1;
    return prevIndex >= 0 
      ? { currentQuestionIndex: prevIndex } 
      : state;
  }),

  jumpToQuestion: (index) => set((state) => {
    if (!state.paper) return state;
    return (index >= 0 && index < state.paper.questions.length)
      ? { currentQuestionIndex: index }
      : state;
  }),

  tickTimer: () => set((state) => {
    if (state.status !== 'running') return state;
    const newTime = state.timeLeft - 1;
    if (newTime <= 0) {
      // Auto-submit when time runs out
      get().submitExam();
      return { timeLeft: 0 };
    }
    return { timeLeft: newTime };
  }),

  submitExam: async () => {
    const state = get();
    const user = getUser();
    
    if (!user) {
      set({ 
        submitError: 'Not authenticated. Please login first.',
        isSubmitting: false 
      });
      return;
    }

    // Set submitting state
    set({ 
      isSubmitting: true, 
      submitError: null,
      status: 'submitted' // Show submitted UI immediately
    });

    try {
      // Call backend pipeline
      const result = await executePipeline('exam_attempt_v1', {
        user_id: user.id,
        exam_id: state.paper?.id || 'unknown',
        subject_code: state.paper?.subject || 'unknown',
        answers: Object.entries(state.answers).map(([questionId, answer]) => ({
          question_id: questionId,
          student_answer: answer,
          submitted_at: new Date().toISOString(),
        })),
        submitted_at: new Date().toISOString(),
      });

      console.log('✅ Exam submitted successfully:', result.trace_id);

      set({ 
        isSubmitting: false,
        traceId: result.trace_id,
      });

      // Navigate to results page with trace_id
      if (typeof window !== 'undefined') {
        window.location.href = `/results/${result.trace_id}`;
      }
    } catch (error) {
      console.error('❌ Exam submission failed:', error);
      
      set({ 
        submitError: error instanceof Error ? error.message : 'Submission failed',
        isSubmitting: false,
        // Keep status as submitted - don't confuse user by resetting
      });
    }
  },
}));
