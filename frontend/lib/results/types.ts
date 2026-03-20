export interface ResultSummary {
  attemptId: string;
  subject: string;
  paper: string;
  score: number;
  totalScore: number;
  gradeEstimate: string; // "A", "B", "C", "D", "E", "U"
  formattedDate: string;
  duration: string;
  strengths: string[];
  weaknesses: string[];
}

export interface QuestionFeedback {
  id: string;
  questionNumber: string;
  topic: string;
  awardedMarks: number;
  totalMarks: number;
  studentAnswer: string;
  examinerFeedback: string;     // feedback_summary from marking
  correct_points: string[];
  missingPoints: string[];
  study_references: string[];
  status: "full" | "partial" | "zero";
}

export interface ImprovementSignal {
  category: "topic" | "skill";
  title: string;
  description: string;
  actionLabel: string;
  actionLink: string;
}

// ---------------------------------------------------------------------------
// Mock data (used as fallback when no real results are available)
// ---------------------------------------------------------------------------

export const MOCK_RESULT_SUMMARY: ResultSummary = {
  attemptId: "mock-attempt-1",
  subject: "History",
  paper: "Paper 1",
  score: 24,
  totalScore: 40,
  gradeEstimate: "C",
  formattedDate: "19 Mar 2026",
  duration: "1h 30m",
  strengths: ["World War I causes", "League of Nations analysis"],
  weaknesses: ["Nazi Germany consolidation", "Cold War impact on developing nations"],
};

export const MOCK_FEEDBACK_DATA: QuestionFeedback[] = [
  {
    id: "q1",
    questionNumber: "1",
    topic: "World War I",
    awardedMarks: 8,
    totalMarks: 10,
    studentAnswer: "The main causes were nationalism, imperialism, militarism, and the alliance system. The assassination of Archduke Franz Ferdinand triggered the war because it activated the alliance network.",
    examinerFeedback: "Good understanding of the main causes shown. The answer correctly identifies the alliance system and the assassination. However, the discussion of militarism and the arms race could be more detailed.",
    correct_points: [
      "Correctly identified nationalism, imperialism, and militarism as underlying causes",
      "Strong explanation of how the alliance system escalated the conflict",
      "Good use of the assassination as the immediate trigger",
    ],
    missingPoints: [
      "No discussion of the naval arms race between Britain and Germany",
      "Failed to mention the role of the Balkans as a 'powder keg'",
    ],
    study_references: ["Chapter 3: Origins of WWI", "Syllabus section 1.2 — European Alliance Systems"],
    status: "partial",
  },
  {
    id: "q2",
    questionNumber: "2",
    topic: "League of Nations",
    awardedMarks: 12,
    totalMarks: 12,
    studentAnswer: "I largely agree. Without the USA, the League lacked both moral authority and military power. The absence also encouraged aggressor nations like Japan and Italy.",
    examinerFeedback: "Excellent response. The student correctly uses the source and supplements with own knowledge. Both sides of the argument are clearly presented with well-chosen examples.",
    correct_points: [
      "Used the source evidence effectively",
      "Argued both sides (agree and disagree)",
      "Cited Japan's invasion of Manchuria and Italy's invasion of Ethiopia",
      "Explained lack of military force and economic sanctions failure",
    ],
    missingPoints: [],
    study_references: [],
    status: "full",
  },
  {
    id: "q3",
    questionNumber: "3",
    topic: "Great Depression",
    awardedMarks: 0,
    totalMarks: 2,
    studentAnswer: "A",
    examinerFeedback: "The correct answer was B — The Wall Street Crash of 1929.",
    correct_points: [],
    missingPoints: ["Correct answer is B; you selected A (assassination of Archduke Franz Ferdinand)"],
    study_references: ["Chapter 7: The Great Depression", "Syllabus section 3.1"],
    status: "zero",
  },
  {
    id: "q4",
    questionNumber: "4",
    topic: "Nazi Germany",
    awardedMarks: 4,
    totalMarks: 8,
    studentAnswer: "Hitler used the Enabling Act to give himself dictatorial powers. He also used propaganda through Goebbels.",
    examinerFeedback: "Partial credit awarded. The Enabling Act is correctly mentioned. However, the Night of the Long Knives is a critical event that was omitted.",
    correct_points: [
      "Correctly identified the Enabling Act (March 1933)",
      "Mentioned use of propaganda",
    ],
    missingPoints: [
      "Night of the Long Knives (June 1934) — elimination of SA rivals — not mentioned",
      "No discussion of the merging of Chancellor and President roles after Hindenburg's death",
    ],
    study_references: ["Chapter 8: Rise of Hitler", "Syllabus section 4.2 — Nazi Consolidation of Power"],
    status: "partial",
  },
];

export const MOCK_IMPROVEMENT_SIGNALS: ImprovementSignal[] = [
  {
    category: "topic",
    title: "Nazi Germany Consolidation",
    description: "You missed key events like the Night of the Long Knives. Review the 1933–1934 timeline.",
    actionLabel: "Review Nazi Consolidation",
    actionLink: "/learn/nazi-germany",
  },
  {
    category: "skill",
    title: "Source Evaluation",
    description: "Practice using source quotations directly in your arguments for structured questions.",
    actionLabel: "Source Skills Practice",
    actionLink: "/learn/source-skills",
  },
];
