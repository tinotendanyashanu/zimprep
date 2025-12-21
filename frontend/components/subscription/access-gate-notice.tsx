import { Lock } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

interface AccessGateNoticeProps {
  featureName: string;
  className?: string;
}

export function AccessGateNotice({ featureName, className }: AccessGateNoticeProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center p-12 md:p-16 text-center border border-dashed rounded-3xl bg-muted/30",
      className
    )}>
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-6 icon-wrapper-calm">
        <Lock className="h-5 w-5 text-muted-foreground" />
      </div>
      
      <h3 className="text-xl md:text-2xl font-medium tracking-tight mb-2">
        {featureName} Included in Full Access
      </h3>
      
      <p className="text-muted-foreground max-w-md mb-8 leading-relaxed">
        This feature is available as part of the Full Access plan. 
        Your current plan provides standard access to past papers and marking schemes.
      </p>

      <Link 
        href="/subscription" 
        className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-8 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        View Access Options
      </Link>
    </div>
  );
}
