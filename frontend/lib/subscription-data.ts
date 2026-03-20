export interface SubscriptionPlan {
  id: string;
  tier: string | null; // DB tier value; null for the free/starter plan
  name: string;
  description: string;
  price_display: string;
  features: string[];
  limitations: string[];
}

export interface SubscriptionStatus {
  plan_id: string;
  tier: string; // matches student.subscription_tier
  is_active: boolean;
  renewal_date?: string;
}

export const PLANS: SubscriptionPlan[] = [
  {
    id: 'free',
    tier: null,
    name: 'Standard Access',
    description: 'Basic access to past papers for independent study.',
    price_display: 'Free',
    features: [
      'Access to past exam papers (limited years)',
      'Basic marking schemes',
      'Study timer',
    ],
    limitations: [
      'No detailed examiner reports',
      'No topic-by-topic analytics',
      "No \"Examiner's View\" feedback",
    ],
  },
  {
    id: 'full',
    tier: 'all_subjects',
    name: 'Full Access',
    description: 'Complete academic resource library and analysis tools.',
    price_display: '$10 / month',
    features: [
      'Unlimited past papers (all years)',
      'Detailed examiner reports & feedback',
      'Topic strength/weakness analysis',
      'Performance tracking history',
      'Priority marking',
    ],
    limitations: [],
  },
];

export function getPlanByTier(tier: string): SubscriptionPlan {
  return PLANS.find((p) => p.tier === tier) ?? PLANS[0];
}

export function getPlan(id: string): SubscriptionPlan | undefined {
  return PLANS.find((p) => p.id === id);
}
