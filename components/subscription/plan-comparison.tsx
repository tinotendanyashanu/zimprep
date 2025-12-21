import { SubscriptionPlan } from '@/lib/subscription-data';
import { PlanCard } from './plan-card';

interface PlanComparisonProps {
  plans: SubscriptionPlan[];
  currentPlanId?: string;
}

export function PlanComparison({ plans, currentPlanId }: PlanComparisonProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8 max-w-5xl mx-auto">
      {plans.map((plan) => (
        <PlanCard 
            key={plan.id} 
            plan={plan} 
            isCurrentPlan={plan.id === currentPlanId} 
        />
      ))}
    </div>
  );
}
