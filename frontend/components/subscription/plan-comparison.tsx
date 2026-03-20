import { SubscriptionPlan } from '@/lib/subscription-data';
import { PlanCard } from './plan-card';

interface PlanComparisonProps {
  plans: SubscriptionPlan[];
  currentTier?: string;
  accessToken?: string;
}

export function PlanComparison({ plans, currentTier, accessToken }: PlanComparisonProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8 max-w-5xl mx-auto">
      {plans.map((plan) => (
        <PlanCard
          key={plan.id}
          plan={plan}
          isCurrentPlan={plan.tier === currentTier || (plan.tier === null && (!currentTier || currentTier === 'starter'))}
          accessToken={accessToken}
        />
      ))}
    </div>
  );
}
