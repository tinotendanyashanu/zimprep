import { PLANS, MOCK_USER_SUBSCRIPTION } from '@/lib/subscription-data';
import { PlanComparison } from '@/components/subscription/plan-comparison';

export default function SubscriptionPage() {
  return (
    <div className="min-h-screen bg-background text-foreground py-12 md:py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-16">
        
        {/* Header - Calm, Informational */}
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <h1 className="text-calm-h1">Access Plans</h1>
          <p className="text-calm-body">
            Choose the level of access that matches your study requirements.
            All plans include basic exam resources.
          </p>
        </div>

        {/* Plan Comparison */}
        <PlanComparison 
            plans={PLANS} 
            currentPlanId={MOCK_USER_SUBSCRIPTION.plan_id} 
        />

        {/* FAQ - Minimalist */}
        <div className="max-w-3xl mx-auto pt-12 space-y-8">
            <h2 className="text-calm-h2 text-center">Common Questions</h2>
            <div className="grid gap-6 md:grid-cols-2">
                <div className="panel bg-secondary/30 p-8 border border-border/40">
                    <h3 className="font-semibold mb-2">Can I cancel anytime?</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">Yes. Access continues until the end of your billing period. There are no cancellation fees.</p>
                </div>
                 <div className="panel bg-secondary/30 p-8 border border-border/40">
                    <h3 className="font-semibold mb-2">Is payment secure?</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">Transactions are processed securely. We do not store your card details directly.</p>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
}
