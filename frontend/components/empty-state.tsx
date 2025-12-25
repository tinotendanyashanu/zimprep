/**
 * Empty state component for when no data is available
 * 
 * Preserves existing visual design
 */

import { FileQuestion } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ 
  title = 'No data available',
  description = 'There is nothing to display here yet.',
  action 
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <div className="rounded-full bg-slate-50 p-4 mb-4">
        <FileQuestion className="h-8 w-8 text-slate-400" />
      </div>
      
      <h3 className="text-lg font-semibold text-slate-900 mb-2">
        {title}
      </h3>
      
      <p className="text-slate-600 mb-6 max-w-md">
        {description}
      </p>
      
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
