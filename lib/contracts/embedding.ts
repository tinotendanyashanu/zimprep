/**
 * ZimPrep Engine Contracts - Embedding Engine (AI)
 * 
 * Responsibility: Convert text to vectors.
 * 
 * This AI engine transforms text content into vector embeddings
 * for semantic search and similarity matching.
 * 
 * @module contracts/embedding
 * @version 1.0.0
 */

import { BaseEngineError } from './common';

// ============================================================================
// Shared Types
// ============================================================================

/**
 * Types of content that can be embedded.
 */
export type EmbeddingContentType = "ANSWER" | "QUESTION" | "SCHEME";

// ============================================================================
// Input Types
// ============================================================================

/**
 * Input for embedding generation.
 */
export interface EmbeddingInput {
  /** Text content to embed */
  text: string;
  
  /** Type of content being embedded (affects model selection) */
  content_type: EmbeddingContentType;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Embedding generation output.
 */
export interface EmbeddingOutput {
  /** Vector representation of the input text */
  embedding: number[];
  
  /** Number of dimensions in the embedding vector */
  dimensions: number;
  
  /** Identifier of the model used for embedding */
  model_id: string;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Embedding Engine.
 */
export type EmbeddingErrorCode = 
  | "TEXT_TOO_LONG" 
  | "MODEL_UNAVAILABLE";

/**
 * Error response from the Embedding Engine.
 */
export interface EmbeddingError extends BaseEngineError {
  code: EmbeddingErrorCode;
}
