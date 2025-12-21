import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  variant?: "skeleton" | "spinner" | "card";
  className?: string;
  text?: string;
}

export function LoadingState({
  variant = "skeleton",
  className,
  text,
}: LoadingStateProps) {
  if (variant === "spinner") {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center p-8 space-y-4",
          className
        )}
      >
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        {text && <p className="text-sm text-muted-foreground">{text}</p>}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div
        className={cn(
          "rounded-xl border bg-card text-card-foreground shadow-sm p-6 space-y-4",
          className
        )}
      >
        <div className="h-4 w-1/3 bg-muted/50 rounded animate-pulse" />
        <div className="space-y-2">
          <div className="h-3 w-full bg-muted/30 rounded animate-pulse" />
          <div className="h-3 w-5/6 bg-muted/30 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  // Default block skeleton
  return (
    <div
      className={cn(
        "w-full h-24 bg-muted/20 rounded-lg animate-pulse",
        className
      )}
    />
  );
}
