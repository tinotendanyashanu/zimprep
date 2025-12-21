import { SubscriptionStatus, getPlan } from '@/lib/subscription-data'; // Fixed import path
import { CreditCard, Calendar } from 'lucide-react';

interface SubscriptionStatusProps {
  status: SubscriptionStatus;
}

export function SubscriptionStatusView({ status }: SubscriptionStatusProps) {
  const currentPlan = getPlan(status.plan_id);

  if (!currentPlan) return null;

  return (
    <div className="panel space-y-8">
      <div>
        <h2 className="text-calm-h2 mb-2">Current Subscription</h2>
        <p className="text-calm-body">Manage your account access and billing details.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Plan Details Block */}
        <div className="p-6 rounded-2xl bg-secondary/50 border border-border/50 space-y-4">
            <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-background rounded-lg shadow-sm">
                   <CreditCard className="w-5 h-5 text-foreground/70" />
                </div>
                <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Plan</span>
            </div>
            <div>
                 <div className="text-2xl font-semibold tracking-tight">{currentPlan.name}</div>
                 <div className="text-muted-foreground">{currentPlan.price_display}</div>
            </div>
        </div>

        {/* Renewal/Status Block */}
        <div className="p-6 rounded-2xl bg-secondary/50 border border-border/50 space-y-4">
             <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-background rounded-lg shadow-sm">
                   <Calendar className="w-5 h-5 text-foreground/70" />
                </div>
                <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Status</span>
            </div>
            <div>
                 <div className="text-2xl font-semibold tracking-tight">
                    {status.is_active ? 'Active' : 'Inactive'}
                 </div>
                 <div className="text-muted-foreground">
                    {status.renewal_date 
                        ? `Renews on ${status.renewal_date}` 
                        : 'No active renewal'}
                 </div>
            </div>
        </div>
      </div>

      <div className="pt-8 border-t border-border/40">
        <h3 className="text-lg font-medium mb-4">Actions</h3>
        <div className="flex flex-wrap gap-4">
            <button className="btn-secondary text-foreground border border-input bg-background hover:bg-accent/50 text-sm h-10 px-6 rounded-md">
                Update Payment Method
            </button>
             <button className="inline-flex items-center justify-center rounded-md px-6 h-10 text-sm font-medium text-red-600/80 hover:text-red-600 hover:bg-red-50 transition-colors">
                Cancel Subscription
            </button>
        </div>
        <p className="mt-4 text-sm text-muted-foreground/60 max-w-xl">
            Cancellation will take effect at the end of your current billing period. You will retain access to all history and data.
        </p>
      </div>
    </div>
  );
}
