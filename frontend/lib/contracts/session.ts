/**
 * ZimPrep Engine Contracts - Session & Timing Engine
 * 
 * Responsibility: "Is this exam session valid and within time?"
 * 
 * This engine manages exam session lifecycle including start, check, and end.
 * It enforces timing constraints and session validity.
 * 
 * @module contracts/session
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Shared Types
// ============================================================================

/**
 * Actions that can be performed on a session.
 */
export type SessionAction = "START" | "CHECK" | "END";

/**
 * Possible states of an exam session.
 */
export type SessionStatus = "ACTIVE" | "EXPIRED" | "COMPLETED";

// ============================================================================
// Input Types
// ============================================================================

/**
 * Input for session operations.
 */
export interface SessionInput {
  /** Unique identifier for this exam attempt */
  attempt_id: string;
  
  /** Action to perform on the session */
  action: SessionAction;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Session operation result.
 */
export interface SessionOutput {
  /** Current status of the session */
  status: SessionStatus;
  
  /** Remaining time in seconds (0 if expired or completed) */
  remaining_seconds: number;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Session Engine.
 */
export type SessionErrorCode = 
  | "SESSION_NOT_FOUND" 
  | "SESSION_ALREADY_ENDED";

/**
 * Error response from the Session Engine.
 */
export interface SessionError extends BaseEngineError {
  code: SessionErrorCode;
}
