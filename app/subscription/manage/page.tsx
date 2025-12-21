import { MOCK_USER_SUBSCRIPTION } from '@/lib/subscription-data';
import { SubscriptionStatusView } from '@/components/subscription/subscription-status';

export default function ManageSubscriptionPage() {
  return (
    <div className="min-h-screen bg-background text-foreground py-12 md:py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-8">
        
        <div className="space-y-2">
            <h1 className="text-calm-h2">Account Management</h1>
            <p className="text-calm-body">View and update your subscription details.</p>
        </div>

        <SubscriptionStatusView status={MOCK_USER_SUBSCRIPTION} />
        
      </div>
    </div>
  );
}
