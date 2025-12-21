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
export {
  EngineTrace,
  BaseEngineError,
  EngineResponse,
  EngineResult,
} from './common';

// =============================================================================
// Core Engines (Non-AI)
// =============================================================================

// Identity & Subscription Engine
export {
  IdentityInput,
  IdentityOutput,
  IdentityError,
  IdentityErrorCode,
  UserRole,
  SubscriptionStatus,
} from './identity';

// Exam Structure Engine
export {
  ExamStructureInput,
  ExamStructureOutput,
  ExamStructureError,
  ExamStructureErrorCode,
  ExamLevel,
  QuestionType,
  ExamQuestion,
} from './exam-structure';

// Session & Timing Engine
export {
  SessionInput,
  SessionOutput,
  SessionError,
  SessionErrorCode,
  SessionAction,
  SessionStatus,
} from './session';

// Submission Engine
export {
  SubmissionInput,
  SubmissionOutput,
  SubmissionError,
  SubmissionErrorCode,
  AnswerSubmission,
} from './submission';

// Results Engine
export {
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
export {
  EmbeddingInput,
  EmbeddingOutput,
  EmbeddingError,
  EmbeddingErrorCode,
  EmbeddingContentType,
} from './embedding';

// Retrieval Engine
export {
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
export {
  MarkingInput,
  MarkingOutput,
  MarkingError,
  MarkingErrorCode,
  QuestionContext,
  MarkingCriterion,
} from './marking';

// Validation & Consistency Engine
export {
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
export {
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
