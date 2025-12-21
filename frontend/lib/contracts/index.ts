/**
 * ZimPrep Engine Contracts - Barrel Export
 * 
 * This file exports all engine contracts from a single entry point.
 * Import from this file for clean, consolidated access to all contracts.
 * 
 * @example
 * import { IdentityInput, MarkingOutput, EngineTrace } from '@/lib/contracts';
 * 
 * @module contracts
 * @version 1.0.0
 */

// =============================================================================
// Common Types (System-wide)
// =============================================================================
export type {
  EngineTrace,
  BaseEngineError,
  EngineResponse,
  EngineResult,
} from './common';

// =============================================================================
// Core Engines (Non-AI)
// =============================================================================

// Identity & Subscription Engine
export type {
  IdentityInput,
  IdentityOutput,
  IdentityError,
  IdentityErrorCode,
  UserRole,
  SubscriptionStatus,
} from './identity';

// Exam Structure Engine
export type {
  ExamStructureInput,
  ExamStructureOutput,
  ExamStructureError,
  ExamStructureErrorCode,
  ExamLevel,
  QuestionType,
  ExamQuestion,
} from './exam-structure';

// Session & Timing Engine
export type {
  SessionInput,
  SessionOutput,
  SessionError,
  SessionErrorCode,
  SessionAction,
  SessionStatus,
} from './session';

// Submission Engine
export type {
  SubmissionInput,
  SubmissionOutput,
  SubmissionError,
  SubmissionErrorCode,
  AnswerSubmission,
} from './submission';

// Results Engine
export type {
  ResultsInput,
  ResultsOutput,
  ResultsError,
  ResultsErrorCode,
  QuestionResult,
} from './results';

// =============================================================================
// AI Engines
// =============================================================================

// Embedding Engine
export type {
  EmbeddingInput,
  EmbeddingOutput,
  EmbeddingError,
  EmbeddingErrorCode,
  EmbeddingContentType,
} from './embedding';

// Retrieval Engine
export type {
  RetrievalInput,
  RetrievalOutput,
  RetrievalError,
  RetrievalErrorCode,
  RetrievalFilters,
  RetrievedEvidence,
  EvidenceSource,
  SearchMetadata,
} from './retrieval';

// Reasoning & Marking Engine
export type {
  MarkingInput,
  MarkingOutput,
  MarkingError,
  MarkingErrorCode,
  QuestionContext,
  MarkingCriterion,
} from './marking';

// Validation & Consistency Engine
export type {
  ValidationInput,
  ValidationOutput,
  ValidationError,
  ValidationErrorCode,
  ValidationFlag,
  ValidationFlagType,
  ValidationSeverity,
  HistoricalDistribution,
} from './validation';

// Recommendation Engine
export type {
  RecommendationInput,
  RecommendationOutput,
  RecommendationError,
  RecommendationErrorCode,
  Recommendation,
  RecommendationType,
  RecommendationAction,
  RecommendationActionType,
  RecommendationContext,
  PerformanceHistoryItem,
} from './recommendation';
