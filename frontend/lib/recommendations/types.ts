export type RecommendationType = "TOPIC" | "PAPER" | "SKILL" | "MODE";

export interface Evidence {
  attempts_considered: number;
  related_subject: string;
  related_topic?: string;
  related_paper?: string;
  reason: string; // The explicit "why" formatted for display
}

export interface RecommendationAction {
  label: string;
  route: string;
}

export interface Recommendation {
  id: string;
  type: RecommendationType;
  title: string;
  explanation: string;
  evidence: Evidence;
  action: RecommendationAction;
}
