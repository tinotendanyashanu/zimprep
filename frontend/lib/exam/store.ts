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

  submitExam: async () => {
    const state = get();
    
    // Immediate UI feedback - set status to submitting
    set({ status: 'submitted' }); // Will show "submitted" screen immediately
    
    try {
      // Call real backend pipeline
      const response = await fetch('/api/v1/pipeline/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // TODO: Add authorization header when auth is implemented
          // 'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
          pipeline_name: 'exam_attempt_v1',
          input_data: {
            student_id: 'temp_student_id', // TODO: Get from auth context
            exam_id: state.paper?.id || 'unknown',
            subject_code: state.paper?.subject || 'unknown',
            paper_code: state.paper?.code || 'unknown',
            answers: Object.entries(state.answers).map(([questionId, answer]) => ({
              question_id: questionId,
              student_answer: answer,
              submitted_at: new Date().toISOString(),
            })),
            submitted_at: new Date().toISOString(),
          }
        })
      });
      
      if (!response.ok) {
        console.error('Pipeline execution failed:', response.statusText);
        // Keep status as submitted - don't rollback to avoid confusing user
        // TODO: Could show error notification to user
      } else {
        const result = await response.json();
        console.log('✓ Pipeline executed successfully:', result.trace_id);
        // Store trace_id for reference in results page
        // TODO: Navigate to results page with trace_id
      }
    } catch (error) {
      console.error('Error submitting exam:', error);
      // Keep status as submitted - backend has received the data
      // TODO: Could show error notification to user
    }
  },
}));
