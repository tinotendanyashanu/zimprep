import { Recommendation } from "./types";

export const MOCK_RECOMMENDATIONS: Recommendation[] = [
  {
    id: "rec-001",
    type: "TOPIC",
    title: "Revise Trigonometry Identities",
    explanation: "Performance in trigonometry questions constitutes your lowest scoring topic area this week.",
    evidence: {
      attempts_considered: 4,
      related_subject: "Mathematics",
      related_topic: "Trigonometry",
      reason: "Missed 3 out of 4 questions related to identities in recent papers.",
    },
    action: {
      label: "Practice Topic",
      route: "/subjects/Mathematics/topics/trigonometry",
    },
  },
  {
    id: "rec-002",
    type: "PAPER",
    title: "Complete Mathematics Paper 1 (2023)",
    explanation: "This paper was started but not submitted.",
    evidence: {
      attempts_considered: 1,
      related_subject: "Mathematics",
      related_paper: "Paper 1 (2023)",
      reason: "Attempt abandoned at question 12 of 40.",
    },
    action: {
      label: "Resume Paper",
      route: "/subjects/Mathematics/papers/paper-1",
    },
  },
  {
    id: "rec-003",
    type: "SKILL",
    title: "Show Full Working",
    explanation: "Examiner feedback indicates loss of method marks despite correct final answers.",
    evidence: {
      attempts_considered: 6,
      related_subject: "Physics",
      reason: "Method marks deducted in 4 recent structured questions.",
    },
    action: {
      label: "View Marking Guide",
      route: "/guides/marking/show-working",
    },
  },
  {
    id: "rec-004",
    type: "MODE",
    title: "Attempt Timed Practice",
    explanation: "You have not yet attempted a paper under strict exam timing conditions.",
    evidence: {
      attempts_considered: 10,
      related_subject: "General",
      reason: "All 10 recent attempts were in 'Untimed' or 'Topic' mode.",
    },
    action: {
      label: "Start Timed Exam",
      route: "/subjects/English/papers/paper-1/start?mode=timed",
    },
  },
];

export const getRecommendations = async (): Promise<Recommendation[]> => {
  // Simulate network delay
  return new Promise((resolve) => {
    setTimeout(() => resolve(MOCK_RECOMMENDATIONS), 800);
  });
};
