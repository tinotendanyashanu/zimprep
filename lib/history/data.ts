import { AttemptHistoryItem, SubjectProgress } from "./types";

// Mock Data Generators

export const MOCK_HISTORY: AttemptHistoryItem[] = [
  {
    attempt_id: "att_001",
    subject: "Mathematics",
    paper: "Paper 1",
    score: 42,
    total: 100,
    date: "2024-05-15",
    status: "Completed",
  },
  {
    attempt_id: "att_002",
    subject: "English Language",
    paper: "Paper 2",
    score: 65,
    total: 100,
    date: "2024-05-14",
    status: "Completed",
  },
  {
    attempt_id: "att_003",
    subject: "Mathematics",
    paper: "Paper 1",
    score: 38,
    total: 100,
    date: "2024-05-10",
    status: "Completed",
  },
  {
    attempt_id: "att_004",
    subject: "Combined Science",
    paper: "Paper 1",
    score: 55,
    total: 100,
    date: "2024-05-08",
    status: "Completed",
  },
  {
    attempt_id: "att_005",
    subject: "Geography",
    paper: "Paper 1",
    score: 72,
    total: 100,
    date: "2024-05-05",
    status: "Completed",
  },
];

export const MOCK_KNOWLEDGE_GAPS = [
  "Algebraic Fractions",
  "Vector Geometry",
  "Matrices",
  "Circle Theorems",
];

export const MOCK_SUGGESTED_FOCUS = [
  "Review Algebra Basics",
  "Practice Vector Addition",
  "Study Circle Properties",
];

export function getHistory(): AttemptHistoryItem[] {
  // Sort by date desc
  return [...MOCK_HISTORY].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

export function getSubjectProgress(subject: string): SubjectProgress {
    // Generate some deterministic mock trends based on subject name length
    const baseScore = 40 + (subject.length * 2); 
    const trend = [
        { date: "2024-04-01", score: Math.min(100, Math.max(0, baseScore - 10)) },
        { date: "2024-04-15", score: Math.min(100, Math.max(0, baseScore - 5)) },
        { date: "2024-05-01", score: Math.min(100, Math.max(0, baseScore + 2)) },
        { date: "2024-05-15", score: Math.min(100, Math.max(0, baseScore + 8)) },
    ];

    const attemptsCount = 12; // Mock count
    const scores = trend.map(t => t.score);
    const avg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
    const best = Math.max(...scores);

    return {
        subject,
        level: "Form 4", // verifiable Default
        attempts: attemptsCount,
        average_score: avg,
        best_score: best,
        trend,
        weak_topics: subject === "Mathematics" ? MOCK_KNOWLEDGE_GAPS : ["Topic A", "Topic B"],
        suggested_focus: subject === "Mathematics" ? MOCK_SUGGESTED_FOCUS : ["Focus Area 1", "Focus Area 2"],
    };
}
