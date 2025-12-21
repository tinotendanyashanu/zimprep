export interface AttemptHistoryItem {
  attempt_id: string;
  subject: string;
  paper: string;
  score: number;
  total: number;
  date: string; // ISO 8601 format YYYY-MM-DD
  status: 'Completed' | 'In Progress'; // Expanded for future use, but main focus is Completed
}

export interface SubjectProgress {
  subject: string;
  level: string; // e.g., 'Grade 7', 'Form 4'
  attempts: number;
  average_score: number;
  best_score: number;
  trend: {
    date: string;
    score: number;
  }[];
  weak_topics: string[];
  suggested_focus: string[];
}
