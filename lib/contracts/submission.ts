/**
 * ZimPrep Engine Contracts - Submission Engine
 * 
 * Responsibility: "Store this attempt safely and immutably."
 * 
 * This engine handles the permanent storage of exam submissions.
 * All submissions are immutable once received.
 * 
 * @module contracts/submission
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Input Types
// ============================================================================

/**
 * Individual answer within a submission.
 */
export interface AnswerSubmission {
  /** Question this answer responds to */
  question_id: string;
  
  /** The student's response content */
  response: string;
}

/**
 * Input for submitting exam answers.
 */
export interface SubmissionInput {
  /** Unique identifier for this exam attempt */
  attempt_id: string;
  
  /** All answers being submitted */
  answers: AnswerSubmission[];
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Submission confirmation output.
 */
export interface SubmissionOutput {
  /** Unique identifier for this submission (for tracking) */
  submission_id: string;
  
  /** ISO 8601 timestamp of when submission was received */
  received_at: string;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Submission Engine.
 */
export type SubmissionErrorCode = 
  | "ATTEMPT_NOT_FOUND" 
  | "SUBMISSION_DUPLICATE" 
  | "VALIDATION_FAILED";

/**
 * Error response from the Submission Engine.
 */
export interface SubmissionError extends BaseEngineError {
  code: SubmissionErrorCode;
}
