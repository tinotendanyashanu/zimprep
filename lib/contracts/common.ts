/**
 * ZimPrep Engine Contracts - Common Types
 * 
 * Global types shared across all engines.
 * This is the foundation of the engine contract system.
 * 
 * @module contracts/common
 * @version 1.0.0
 */

/**
 * EngineTrace - Mandatory metadata for every engine response.
 * This is how AI decisions are audited and traced.
 * 
 * Every engine MUST emit this trace data with every response.
 */
export interface EngineTrace {
  /** Unique identifier for this specific engine invocation */
  trace_id: string;
  
  /** Name of the engine that produced this response */
  engine_name: string;
  
  /** Version of the engine (semver format) */
  engine_version: string;
  
  /** ISO 8601 timestamp of when this response was generated */
  timestamp: string;
  
  /** Confidence score from 0.0 (no confidence) to 1.0 (full confidence) */
  confidence: number;
  
  /** Optional human-readable notes about this trace */
  notes?: string;
}

/**
 * Base error shape for all engines.
 * All engine-specific errors extend this interface.
 */
export interface BaseEngineError {
  /** Error code for programmatic handling */
  code: string;
  
  /** Human-readable error message */
  message: string;
}

/**
 * Standard engine response wrapper.
 * All engines return responses in this format.
 * 
 * @template TOutput - The engine's output type
 * @template TError - The engine's error type (extends BaseEngineError)
 */
export interface EngineResponse<TOutput, TError extends BaseEngineError> {
  /** Whether the engine call succeeded */
  success: boolean;
  
  /** The engine's output data (present if success is true) */
  data?: TOutput;
  
  /** Error information (present if success is false) */
  error?: TError;
  
  /** Trace metadata - ALWAYS present regardless of success/failure */
  trace: EngineTrace;
}

/**
 * Utility type for creating typed engine responses.
 */
export type EngineResult<TOutput, TError extends BaseEngineError> = 
  | { success: true; data: TOutput; error?: never; trace: EngineTrace }
  | { success: false; data?: never; error: TError; trace: EngineTrace };
