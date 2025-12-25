/**
 * Centralized API Client for ZimPrep Frontend
 * 
 * RULES:
 * - All backend communication goes through executePipeline()
 * - No direct feature endpoint calls
 * - Consistent error handling (401/403/500)
 * - Every response must have trace_id
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// TYPES
// ============================================================================

export interface PipelineResponse {
  trace_id: string;
  request_id: string;
  pipeline_name: string;
  success: boolean;
  engine_outputs: Record<string, any>;
  started_at: string;
  completed_at: string;
  total_duration_ms: number;
}

export interface PipelineError {
  detail: {
    error?: string;
    message?: string;
    pipeline_name?: string;
    failed_engine?: string;
  };
  trace_id?: string;
}

// ============================================================================
// AUTH HELPERS (imported from ./auth.ts)
// ============================================================================

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('zimprep_token');
}

function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('zimprep_token');
  localStorage.removeItem('zimprep_user');
}

// ============================================================================
// MAIN API FUNCTION
// ============================================================================

/**
 * Execute a backend pipeline.
 * 
 * This is the ONLY function that should be used for backend communication.
 * 
 * @param pipelineName - Name of pipeline (e.g., "exam_attempt_v1")
 * @param inputData - Pipeline-specific input data
 * @returns Pipeline execution result with trace_id
 * @throws Error with appropriate message for different error types
 */
export async function executePipeline(
  pipelineName: string,
  inputData: Record<string, any>
): Promise<PipelineResponse> {
  const token = getAuthToken();

  try {
    const response = await fetch(`${API_URL}/api/v1/pipeline/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify({
        pipeline_name: pipelineName,
        input_data: inputData,
      }),
    });

    // Handle 401 - Unauthorized (token expired/invalid)
    if (response.status === 401) {
      clearAuth();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please login again.');
    }

    // Handle 403 - Forbidden (wrong role)
    if (response.status === 403) {
      const errorData: PipelineError = await response.json();
      throw new Error(errorData.detail?.message || 'Access denied. You do not have permission to access this resource.');
    }

    // Handle other errors
    if (!response.ok) {
      const errorData: PipelineError = await response.json();
      const errorMessage = errorData.detail?.error || errorData.detail?.message || `Pipeline execution failed: ${response.statusText}`;
      
      // Include trace_id in error for debugging
      const error = new Error(errorMessage);
      (error as any).trace_id = errorData.trace_id;
      (error as any).failed_engine = errorData.detail?.failed_engine;
      
      throw error;
    }

    const data: PipelineResponse = await response.json();

    // Verify trace_id exists (required for audit)
    if (!data.trace_id) {
      console.error('⚠️ WARNING: Response missing trace_id. This violates audit requirements.');
    }

    return data;
  } catch (error) {
    // Re-throw if it's already our custom error
    if (error instanceof Error) {
      throw error;
    }

    // Network error or other unexpected error
    throw new Error('Network error. Please check your connection and try again.');
  }
}

// ============================================================================
// HEALTH CHECK HELPERS
// ============================================================================

/**
 * Check API health (no auth required)
 */
export async function checkHealth(): Promise<{ status: string; timestamp: number }> {
  const response = await fetch(`${API_URL}/health`);
  
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  
  return response.json();
}

/**
 * Check API readiness (no auth required)
 */
export async function checkReadiness(): Promise<any> {
  const response = await fetch(`${API_URL}/readiness`);
  
  if (!response.ok) {
    throw new Error('Readiness check failed');
  }
  
  return response.json();
}
