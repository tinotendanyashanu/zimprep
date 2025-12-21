import { SubscriptionPlan } from '@/lib/subscription-data';
import { Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PlanCardProps {
  plan: SubscriptionPlan;
  isCurrentPlan: boolean;
}

export function PlanCard({ plan, isCurrentPlan }: PlanCardProps) {
  return (
    <div
      className={cn(
        'relative flex flex-col p-8 md:p-10 rounded-3xl border transition-all duration-300',
        'bg-card text-card-foreground',
        isCurrentPlan
          ? 'border-primary/50 ring-1 ring-primary/20 shadow-sm'
          : 'border-border/60 hover:border-border/80'
      )}
    >
      {/* Header Section */}
      <div className="mb-8 space-y-4">
        {isCurrentPlan && (
          <span className="inline-block px-3 py-1 text-xs font-medium tracking-wide rounded-full bg-primary/10 text-primary">
            Current Plan
          </span>
        )}
        <h3 className="text-calm-h3">{plan.name}</h3>
        <p className="text-calm-body text-base">{plan.description}</p>
        <div className="pt-2">
          <span className="text-2xl md:text-3xl font-semibold tracking-tight">
            {plan.price_display}
          </span>
        </div>
      </div>

      {/* Features List */}
      <div className="flex-1 space-y-6">
        <div className="space-y-3">
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Includes
          </p>
          <ul className="space-y-3">
            {plan.features.map((feature, i) => (
              <li key={i} className="flex items-start gap-3 text-sm md:text-base">
                <Check className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <span className="text-foreground/90">{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        {plan.limitations.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-border/40">
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Not Included
            </p>
            <ul className="space-y-3">
              {plan.limitations.map((limitation, i) => (
                <li key={i} className="flex items-start gap-3 text-sm md:text-base text-muted-foreground">
                  <X className="w-5 h-5 text-muted-foreground/50 shrink-0 mt-0.5" />
                  <span>{limitation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
