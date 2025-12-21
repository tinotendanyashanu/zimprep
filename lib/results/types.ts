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
  questionNumber: number;
  topic: string;
  awardedMarks: number;
  totalMarks: number;
  studentAnswer: string;
  examinerFeedback: string;
  missingPoints: string[];
  status: "full" | "partial" | "zero"; // helper for UI styling
}

export interface ImprovementSignal {
  category: "topic" | "skill";
  title: string;
  description: string;
  actionLabel: string;
  actionLink: string;
}

export const MOCK_RESULT_SUMMARY: ResultSummary = {
  attemptId: "mock-attempt-1",
  subject: "Mathematics",
  paper: "Paper 2",
  score: 65,
  totalScore: 80,
  gradeEstimate: "B",
  formattedDate: "21 Dec 2025",
  duration: "1h 45m",
  strengths: ["Calculus", "Differentiation", "Geometry"],
  weaknesses: ["Integration Statistics", "Probability"],
};

export const MOCK_FEEDBACK_DATA: QuestionFeedback[] = [
  {
    id: "q1",
    questionNumber: 1,
    topic: "Differentiation",
    awardedMarks: 10,
    totalMarks: 10,
    studentAnswer: "f'(x) = 3x^2 + 2x",
    examinerFeedback: "Correct application of power rule. Notation is clear and final answer is simplified appropriately.",
    missingPoints: [],
    status: "full",
  },
  {
    id: "q2",
    questionNumber: 2,
    topic: "Integration",
    awardedMarks: 8,
    totalMarks: 10,
    studentAnswer: "∫(3x^2 + 2x - 1)dx = x^3 + x^2 - x + C -> evaluated at limits gives 8",
    examinerFeedback: "Method is correct for indefinite integral. However, substitution of limits contains an arithmetic error.",
    missingPoints: [
      "Evaluation at upper limit x=2 is correct (8 + 4 - 2 = 10)",
      "Subtraction of lower limit x=0 was omitted or calculated incorrectly in final step",
    ],
    status: "partial",
  },
  {
    id: "q3",
    questionNumber: 3,
    topic: "Trigonometry",
    awardedMarks: 9,
    totalMarks: 10,
    studentAnswer: "sin^2(x) + cos^2(x) = 1 used to substitution...",
    examinerFeedback: "Good use of identities. Final angle solution is correct but missing one valid range solution.",
    missingPoints: ["Missing solution x = 330° in the given range 0 ≤ x ≤ 360°"],
    status: "partial",
  },
];

export const MOCK_IMPROVEMENT_SIGNALS: ImprovementSignal[] = [
  {
    category: "topic",
    title: "Integration Reliability",
    description: "You have the method down, but arithmetic errors are costing marks.",
    actionLabel: "Review Integration Basics",
    actionLink: "/learn/integration",
  },
  {
    category: "skill",
    title: "Checking Solutions",
    description: "Always verify if multiple solutions exist for trigonometric equations within the range.",
    actionLabel: "Trig Eq Practice",
    actionLink: "/learn/trig-equations",
  },
];
