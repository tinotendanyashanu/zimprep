/**
 * Error state component for displaying errors with trace_id
 * standardizing with ZimPrep Design System
 */

import { AlertCircle } from 'lucide-react';
import { Button } from './ui/button';

interface ErrorStateProps {
  error: string;
  traceId?: string;
  onRetry?: () => void;
}

export function ErrorState({ error, traceId, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center panel shadow-none border-none">
      <div className="rounded-full bg-destructive/10 p-4 mb-6">
        <AlertCircle className="h-8 w-8 text-destructive" />
      </div>
      
      <h3 className="text-xl font-semibold text-foreground mb-2 tracking-tight">
        Something went wrong
      </h3>
      
      <p className="text-muted-foreground mb-6 max-w-md leading-relaxed text-base">
        {error}
      </p>
      
      {traceId && (
        <p className="text-xs text-muted-foreground/60 mb-6 font-mono bg-muted p-2 rounded-md">
          Trace ID: {traceId}
        </p>
      )}
      
      {onRetry && (
        <Button onClick={onRetry} size="lg" className="w-full sm:w-auto">
          Try Again
        </Button>
      )}
    </div>
  );
}
