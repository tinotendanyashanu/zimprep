/**
 * ZimPrep Engine Contracts - Exam Structure Engine
 * 
 * Responsibility: "What does this exam look like?"
 * 
 * This engine provides the structure and metadata for exams,
 * including duration, marks allocation, and question composition.
 * 
 * @module contracts/exam-structure
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Shared Types
// ============================================================================

/**
 * Academic levels supported by ZIMSEC.
 */
export type ExamLevel = "O_LEVEL" | "A_LEVEL";

/**
 * Question types in ZIMSEC examinations.
 */
export type QuestionType = "MCQ" | "STRUCTURED" | "ESSAY";

// ============================================================================
// Input Types
// ============================================================================

/**
 * Input for retrieving exam structure.
 */
export interface ExamStructureInput {
  /** Subject code or name (e.g., "MATHEMATICS", "BIOLOGY") */
  subject: string;
  
  /** Paper identifier (e.g., "PAPER_1", "PAPER_2") */
  paper: string;
  
  /** Academic level */
  level: ExamLevel;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Individual question metadata within an exam.
 */
export interface ExamQuestion {
  /** Unique identifier for this question */
  question_id: string;
  
  /** Maximum marks available for this question */
  marks: number;
  
  /** Type of question */
  type: QuestionType;
}

/**
 * Complete exam structure output.
 */
export interface ExamStructureOutput {
  /** Total duration of the exam in minutes */
  duration_minutes: number;
  
  /** Total marks available in the exam */
  total_marks: number;
  
  /** List of questions with their metadata */
  questions: ExamQuestion[];
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Exam Structure Engine.
 */
export type ExamStructureErrorCode = 
  | "EXAM_NOT_FOUND" 
  | "INVALID_PAPER";

/**
 * Error response from the Exam Structure Engine.
 */
export interface ExamStructureError extends BaseEngineError {
  code: ExamStructureErrorCode;
}
