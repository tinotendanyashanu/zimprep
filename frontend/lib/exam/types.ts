
export interface Question {
  id: string;
  text: string; // The markdown/HTML content of the question
  marks: number;
  type: 'essay' | 'structured' | 'multiple-choice'; // For now, focus on essay/text
  // Optional: Image URL for diagrams
  imageUrl?: string;
}

export interface ExamPaper {
    id: string;
    title: string;
    subject: string;
    durationMinutes: number;
    totalMarks: number;
    instructions: string[];
    questions: Question[];
}

export interface ExamAttempt {
    id: string;
    paperId: string;
    startTime: number; // Timestamp
    answers: Record<string, string>; // questionId -> answer text
    status: 'in-progress' | 'submitted';
}
