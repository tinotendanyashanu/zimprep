import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface AccessDeniedStateProps {
  title?: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function AccessDeniedState({
  title = "Access Restricted",
  description,
  action,
  className,
}: AccessDeniedStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-12 text-center rounded-lg border bg-card/50",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-4">
        <Lock className="h-5 w-5 text-foreground/70" aria-hidden="true" />
      </div>
      <h3 className="text-xl font-medium text-foreground mb-3">{title}</h3>
      <p className="text-base text-muted-foreground max-w-md mb-8 leading-relaxed">
        {description}
      </p>
      {action && (
        <Button onClick={action.onClick} size="lg">
          {action.label}
        </Button>
      )}
    </div>
  );
}
