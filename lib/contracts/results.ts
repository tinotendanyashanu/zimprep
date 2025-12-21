/**
 * ZimPrep Engine Contracts - Results Engine
 * 
 * Responsibility: "Present marking results in a stable format."
 * 
 * This engine provides the final marked results for submissions.
 * It presents scores in a consistent, frontend-friendly format.
 * 
 * @module contracts/results
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Input Types
// ============================================================================

/**
 * Input for retrieving results.
 */
export interface ResultsInput {
  /** Submission ID to retrieve results for */
  submission_id: string;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Result for an individual question.
 */
export interface QuestionResult {
  /** Question identifier */
  question_id: string;
  
  /** Marks awarded for this question */
  awarded_marks: number;
  
  /** Maximum marks available for this question */
  total_marks: number;
}

/**
 * Complete results output.
 */
export interface ResultsOutput {
  /** Total score achieved */
  score: number;
  
  /** Maximum possible score */
  total: number;
  
  /** Per-question breakdown */
  per_question: QuestionResult[];
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Results Engine.
 */
export type ResultsErrorCode = 
  | "SUBMISSION_NOT_FOUND" 
  | "RESULTS_NOT_READY";

/**
 * Error response from the Results Engine.
 */
export interface ResultsError extends BaseEngineError {
  code: ResultsErrorCode;
}
