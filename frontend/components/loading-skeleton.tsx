/**
 * Loading skeleton component for smooth loading states
 * 
 * Preserves existing visual design
 */

interface LoadingSkeletonProps {
  className?: string;
}

export function LoadingSkeleton({ className = '' }: LoadingSkeletonProps) {
  return (
    <div className={`animate-pulse ${className}`}>
      <div className="h-full w-full bg-slate-200 rounded-lg"></div>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 p-6">
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <LoadingSkeleton className="h-24" />
        <LoadingSkeleton className="h-24" />
        <LoadingSkeleton className="h-24" />
      </div>
      
      {/* Recent exams */}
      <div className="space-y-4">
        <LoadingSkeleton className="h-8 w-48" />
        <LoadingSkeleton className="h-32" />
        <LoadingSkeleton className="h-32" />
      </div>
      
      {/* Recommendations */}
      <div className="space-y-4">
        <LoadingSkeleton className="h-8 w-48" />
        <LoadingSkeleton className="h-24" />
      </div>
    </div>
  );
}
