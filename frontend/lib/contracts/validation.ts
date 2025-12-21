/**
 * ZimPrep Engine Contracts - Validation & Consistency Engine (AI)
 * 
 * Responsibility: Veto invalid AI outputs.
 * 
 * This engine acts as a guardrail, validating AI marking outputs
 * before they are presented to users. It can veto or adjust marks
 * that appear invalid, inconsistent, or statistically anomalous.
 * 
 * @module contracts/validation
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Input Types
// ============================================================================

/**
 * Historical distribution data for statistical validation.
 */
export interface HistoricalDistribution {
  /** Mean score in historical data */
  mean: number;
  
  /** Standard deviation of historical scores */
  std_dev: number;
  
  /** Number of samples in historical data */
  sample_size: number;
}

/**
 * Input for validation operation.
 */
export interface ValidationInput {
  /** Marks proposed by the Marking Engine */
  proposed_marks: number;
  
  /** Maximum marks available for the question */
  max_marks: number;
  
  /** Optional: reasoning trace from Marking Engine */
  reasoning_trace?: string;
  
  /** Optional: historical distribution for statistical validation */
  historical_distribution?: HistoricalDistribution;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Types of validation flags.
 */
export type ValidationFlagType = 
  | "EXCEEDS_MAX" 
  | "STATISTICAL_OUTLIER" 
  | "REASONING_GAP" 
  | "LOW_CONFIDENCE";

/**
 * Severity levels for validation flags.
 */
export type ValidationSeverity = "WARNING" | "ERROR";

/**
 * Individual validation flag.
 */
export interface ValidationFlag {
  /** Type of issue detected */
  flag_type: ValidationFlagType;
  
  /** Severity of the issue */
  severity: ValidationSeverity;
  
  /** Human-readable description of the issue */
  description: string;
}

/**
 * Validation operation output.
 */
export interface ValidationOutput {
  /** Whether the proposed marks are valid */
  is_valid: boolean;
  
  /** Adjusted marks if validation modified them */
  adjusted_marks?: number;
  
  /** Reason for veto if marks were rejected */
  veto_reason?: string;
  
  /** All flags raised during validation */
  flags: ValidationFlag[];
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Validation Engine.
 */
export type ValidationErrorCode = "VALIDATION_SYSTEM_ERROR";

/**
 * Error response from the Validation Engine.
 */
export interface ValidationError extends BaseEngineError {
  code: ValidationErrorCode;
}
