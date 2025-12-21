/**
 * ZimPrep Engine Contracts - Retrieval Engine (AI)
 * 
 * Responsibility: Retrieve marking evidence from vector store.
 * 
 * This AI engine performs semantic search against the marking
 * scheme database to find relevant evidence for grading.
 * 
 * @module contracts/retrieval
 * @version 1.0.0
 */

import { BaseEngineError } from './common';
import { ExamLevel } from './exam-structure';

// ============================================================================
// Input Types
// ============================================================================

/**
 * Filters for constraining retrieval search.
 */
export interface RetrievalFilters {
  /** Subject to search within */
  subject: string;
  
  /** Paper to search within */
  paper: string;
  
  /** Optional: academic level filter */
  level?: ExamLevel;
  
  /** Optional: exam year filter */
  year?: number;
}

/**
 * Input for evidence retrieval.
 */
export interface RetrievalInput {
  /** Vector embedding to search with */
  embedding: number[];
  
  /** Filters to constrain the search */
  filters: RetrievalFilters;
  
  /** Number of results to return (default: 5) */
  top_k?: number;
}

// ============================================================================
// Output Types
// ============================================================================

/**
 * Source information for retrieved evidence.
 */
export interface EvidenceSource {
  /** Document identifier */
  document_id: string;
  
  /** Optional page number within the document */
  page?: number;
}

/**
 * Individual piece of retrieved evidence.
 */
export interface RetrievedEvidence {
  /** Unique identifier for this evidence */
  evidence_id: string;
  
  /** The evidence content text */
  content: string;
  
  /** Similarity score (0.0 - 1.0) */
  similarity_score: number;
  
  /** Source document information */
  source: EvidenceSource;
}

/**
 * Metadata about the search operation.
 */
export interface SearchMetadata {
  /** Total candidates considered */
  total_candidates: number;
  
  /** Search duration in milliseconds */
  search_time_ms: number;
}

/**
 * Retrieval operation output.
 */
export interface RetrievalOutput {
  /** Retrieved evidence items */
  evidence: RetrievedEvidence[];
  
  /** Search operation metadata */
  search_metadata: SearchMetadata;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * Possible error codes from the Retrieval Engine.
 */
export type RetrievalErrorCode = 
  | "NO_EVIDENCE_FOUND" 
  | "VECTOR_STORE_ERROR";

/**
 * Error response from the Retrieval Engine.
 */
export interface RetrievalError extends BaseEngineError {
  code: RetrievalErrorCode;
}
