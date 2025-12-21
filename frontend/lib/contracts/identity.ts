/**
 * ZimPrep Engine Contracts - Identity & Subscription Engine
 * 
 * Responsibility: "Who is this user and what are they allowed to access?"
 * 
 * This engine handles user identity resolution and subscription status.
 * It is the gatekeeper for all authenticated functionality.
 * 
 * @module contracts/identity
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Input Types
// ============================================================================

/**
 * Input for identity resolution.
 */
export interface IdentityInput {
  /** Unique identifier of the user to look up */
  user_id: string;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * User roles in the ZimPrep system.
 */
export type UserRole = "STUDENT" | "PARENT" | "ADMIN" | "EXAMINER";

/**
 * Subscription status details.
 */
export interface SubscriptionStatus {
  /** Current subscription plan identifier */
  plan: string;
  
  /** List of feature flags that are enabled for this subscription */
  features_enabled: string[];
  
  /** List of feature flags that are disabled for this subscription */
  features_disabled: string[];
}

/**
 * Output from identity resolution.
 */
export interface IdentityOutput {
  /** The user's role in the system */
  role: UserRole;
  
  /** For PARENT role: the linked student's ID (optional) */
  linked_student_id?: string;
  
  /** Current subscription status and feature access */
  subscription_status: SubscriptionStatus;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Identity Engine.
 */
export type IdentityErrorCode = 
  | "USER_NOT_FOUND" 
  | "SUBSCRIPTION_INVALID";

/**
 * Error response from the Identity Engine.
 */
export interface IdentityError extends BaseEngineError {
  code: IdentityErrorCode;
}
