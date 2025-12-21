/**
 * ZimPrep Engine Contracts - Reasoning & Marking Engine (AI)
 * 
 * Responsibility: Apply rubric-constrained reasoning to produce marks.
 * 
 * This is the core AI marking engine. It takes student answers and
 * marking evidence, then applies rubric-constrained reasoning to
 * determine marks with full explainability.
 * 
 * @module contracts/marking
 * @version 1.0.0
 */

import { BaseEngineError } from './common';
import { QuestionType } from './exam-structure';

// ============================================================================
// Input Types
// ============================================================================

/**
 * Context about the question being marked.
 */
export interface QuestionContext {
  /** Question identifier */
  question_id: string;
  
  /** Full question text */
  question_text: string;
  
  /** Maximum marks available */
  max_marks: number;
  
  /** Type of question */
  question_type: QuestionType;
}

/**
 * Input for marking operation.
 */
export interface MarkingInput {
  /** The student's answer text */
  student_answer: string;
  
  /** Retrieved marking evidence/rubric content */
  marking_evidence: string[];
  
  /** Context about the question */
  question_context: QuestionContext;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Individual marking criterion assessment.
 */
export interface MarkingCriterion {
  /** Unique identifier for this criterion */
  criterion_id: string;
  
  /** Description of what this criterion assesses */
  description: string;
  
  /** Marks awarded for this criterion */
  marks_awarded: number;
  
  /** Maximum marks possible for this criterion */
  marks_possible: number;
  
  /** Evidence snippets used to make this determination */
  evidence_used: string[];
}

/**
 * Complete marking output.
 */
export interface MarkingOutput {
  /** Total marks awarded */
  total_marks: number;
  
  /** Maximum marks available */
  max_marks: number;
  
  /** Per-criterion breakdown */
  criteria: MarkingCriterion[];
  
  /** Human-readable summary of the reasoning */
  reasoning_summary: string;
  
  /** Actionable hints for improvement */
  improvement_hints: string[];
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Marking Engine.
 */
export type MarkingErrorCode = 
  | "INVALID_ANSWER" 
  | "NO_RUBRIC_MATCH" 
  | "REASONING_FAILED";

/**
 * Error response from the Marking Engine.
 */
export interface MarkingError extends BaseEngineError {
  code: MarkingErrorCode;
}
