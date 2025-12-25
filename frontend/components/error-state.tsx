/**
 * Error state component for displaying errors with trace_id
 * 
 * Preserves existing visual design
 */

import { AlertCircle } from 'lucide-react';

interface ErrorStateProps {
  error: string;
  traceId?: string;
  onRetry?: () => void;
}

export function ErrorState({ error, traceId, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="rounded-full bg-red-50 p-3 mb-4">
        <AlertCircle className="h-6 w-6 text-red-600" />
      </div>
      
      <h3 className="text-lg font-semibold text-slate-900 mb-2">
        Something went wrong
      </h3>
      
      <p className="text-slate-600 mb-4 max-w-md">
        {error}
      </p>
      
      {traceId && (
        <p className="text-xs text-slate-400 mb-4 font-mono">
          Trace ID: {traceId}
        </p>
      )}
      
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
