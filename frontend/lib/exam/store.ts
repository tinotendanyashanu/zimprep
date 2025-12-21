import { create } from 'zustand';
import { ExamPaper, Question } from './types';

interface ExamState {
  paper: ExamPaper | null;
  currentQuestionIndex: number;
  answers: Record<string, string>; // questionId -> answer
  timeLeft: number; // in seconds
  status: 'idle' | 'running' | 'paused' | 'submitted';
  
  // Actions
  initializeExam: (paper: ExamPaper) => void;
  setAnswer: (questionId: string, answer: string) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  jumpToQuestion: (index: number) => void;
  tickTimer: () => void;
  submitExam: () => void;
}

export const useExamStore = create<ExamState>((set, get) => ({
  paper: null,
  currentQuestionIndex: 0,
  answers: {},
  timeLeft: 0,
  status: 'idle',

  initializeExam: (paper) => set({
    paper,
    currentQuestionIndex: 0,
    answers: {},
    timeLeft: paper.durationMinutes * 60,
    status: 'running',
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
      return { timeLeft: 0, status: 'submitted' }; // Auto-submit? Or just pause? Let's say submitted for now or handled by UI
    }
    return { timeLeft: newTime };
  }),

  submitExam: () => set({ status: 'submitted' }),
}));
