export interface MCQOption {
  key: 'A' | 'B' | 'C' | 'D';
  text: string;
}

export interface Question {
  id: string;
  questionNumber: string; // "1", "2a", "3b(i)", etc.
  text: string;
  marks: number;
  type: 'essay' | 'structured' | 'mcq';
  has_image?: boolean;
  imageUrl?: string;
  mcqOptions?: MCQOption[];
  topic?: string;
}

export interface ExamPaper {
  id: string;
  title: string;
  subject: string;
  level: 'Grade7' | 'O' | 'A';
  year: number;
  paperNumber: number;
  durationMinutes: number;
  totalMarks: number;
  instructions: string[];
  questions: Question[];
}

export interface ExamAttempt {
  id: string;
  paperId: string;
  startTime: number;
  answers: Record<string, string>;
  answerImages: Record<string, string>;
  status: 'in-progress' | 'submitted';
}

// Result types (returned from /mark/batch)
export interface QuestionMarkResult {
  question_id: string;
  score: number;
  max_score: number;
  correct_points: string[];
  missing_points: string[];
  feedback_summary: string;
  study_references: string[];
}

export interface BatchMarkingResponse {
  attempt_id: string;
  total_score: number;
  total_max_score: number;
  results: QuestionMarkResult[];
}
