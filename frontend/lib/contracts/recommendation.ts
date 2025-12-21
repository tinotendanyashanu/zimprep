/**
 * ZimPrep Engine Contracts - Recommendation Engine (AI)
 * 
 * Responsibility: Suggest next actions with evidence.
 * 
 * This engine analyzes student performance history and provides
 * evidence-based recommendations for what to study next.
 * All recommendations must be justifiable and backed by data.
 * 
 * @module contracts/recommendation
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Input Types
// ============================================================================

/**
 * Individual performance history entry.
 */
export interface PerformanceHistoryItem {
  /** Subject of the exam */
  subject: string;
  
  /** Paper identifier */
  paper: string;
  
  /** Score achieved */
  score: number;
  
  /** Total marks available */
  total: number;
  
  /** ISO 8601 timestamp of the attempt */
  timestamp: string;
  
  /** Topics identified as weak in this attempt */
  weak_topics: string[];
}

/**
 * Current context for recommendation generation.
 */
export interface RecommendationContext {
  /** Optional: subject the student is currently focused on */
  subject_focus?: string;
  
  /** Optional: time available for study in minutes */
  time_available_minutes?: number;
}

/**
 * Input for recommendation generation.
 */
export interface RecommendationInput {
  /** User identifier */
  user_id: string;
  
  /** Performance history to analyze */
  history: PerformanceHistoryItem[];
  
  /** Optional: current study context */
  current_context?: RecommendationContext;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Types of recommendations the engine can produce.
 */
export type RecommendationType = 
  | "TOPIC_REVISION"
  | "PAPER_RETRY"
  | "SKILL_FOCUS"
  | "PRACTICE_MODE_SUGGESTION";

/**
 * Action types for recommendations.
 */
export type RecommendationActionType = "NAVIGATE" | "START_EXAM" | "REVIEW";

/**
 * Action to take for a recommendation.
 */
export interface RecommendationAction {
  /** Type of action */
  type: RecommendationActionType;
  
  /** Optional: target resource ID */
  target_id?: string;
  
  /** Optional: navigation path */
  target_path?: string;
}

/**
 * Individual recommendation.
 */
export interface Recommendation {
  /** Unique identifier for this recommendation */
  recommendation_id: string;
  
  /** Type of recommendation */
  type: RecommendationType;
  
  /** Short, clear title */
  title: string;
  
  /** Brief explanation of why this is recommended */
  explanation: string;
  
  /** Summary of evidence supporting this recommendation */
  evidence_summary: string;
  
  /** Action to take */
  action: RecommendationAction;
  
  /** Priority ranking (1-10, higher = more important) */
  priority: number;
}

/**
 * Recommendation generation output.
 */
export interface RecommendationOutput {
  /** List of recommendations, ordered by priority */
  recommendations: Recommendation[];
  
  /** ISO 8601 timestamp of when recommendations were generated */
  generated_at: string;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Recommendation Engine.
 */
export type RecommendationErrorCode = 
  | "INSUFFICIENT_HISTORY" 
  | "RECOMMENDATION_FAILED";

/**
 * Error response from the Recommendation Engine.
 */
export interface RecommendationError extends BaseEngineError {
  code: RecommendationErrorCode;
}
