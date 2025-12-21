import { Recommendation } from "@/lib/recommendations/types";
import { ArrowRight, BookOpen, Clock, FileText, Target } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface RecommendationCardProps {
  recommendation: Recommendation;
}

const TYPE_ICONS = {
  TOPIC: BookOpen,
  PAPER: FileText,
  SKILL: Target,
  MODE: Clock,
};

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const Icon = TYPE_ICONS[recommendation.type] || Target;

  return (
    <div className="group flex flex-col border border-border/50 bg-card/50 p-6 transition-colors hover:border-emerald-500/20 hover:bg-card">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex gap-4">
          <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border bg-background text-muted-foreground">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <div className="mb-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {recommendation.evidence.related_subject} • {recommendation.type}
            </div>
            <h3 className="text-lg font-medium text-foreground">
              {recommendation.title}
            </h3>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mb-6 flex-1 space-y-4">
        <p className="text-sm text-muted-foreground">
          {recommendation.explanation}
        </p>
        
        <div className="relative overflow-hidden rounded-md border border-border/50 bg-muted/30 p-3">
          <div className="absolute inset-y-0 left-0 w-1 bg-emerald-500/50" />
          <p className="text-xs font-medium text-emerald-600/90 dark:text-emerald-400/90">
            EVIDENCE
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {recommendation.evidence.reason}
            <span className="ml-1 opacity-70">
              (Based on {recommendation.evidence.attempts_considered} attempts)
            </span>
          </p>
        </div>
      </div>

      {/* Action */}
      <div className="mt-auto">
        <Link
          href={recommendation.action.route}
          className={cn(
            "inline-flex w-full items-center justify-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-sm font-medium transition-colors",
            "hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            "group-hover:border-emerald-500/20 group-hover:text-emerald-500"
          )}
        >
          {recommendation.action.label}
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
