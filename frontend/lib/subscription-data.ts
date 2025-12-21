export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  price_display: string; // "Free" or "$5/month" - strictly informational
  features: string[];
  limitations: string[];
  is_current: boolean;
}

export interface SubscriptionStatus {
  plan_id: string;
  is_active: boolean;
  renewal_date?: string; // ISO Scale
}

export const PLANS: SubscriptionPlan[] = [
  {
    id: 'free',
    name: 'Standard Access',
    description: 'Basic access to past papers for independent study.',
    price_display: 'Free',
    features: [
      'Access to past exam papers (limited years)',
      'Basic marking schemes',
      'Study timer'
    ],
    limitations: [
      'No detailed examiner reports',
      'No topic-by-topic analytics',
      'No "Examiner\'s View" feedback'
    ],
    is_current: false,
  },
  {
    id: 'full',
    name: 'Full Access',
    description: 'Complete academic resource library and analysis tools.',
    price_display: '$10 / month', // Example price, neutral display
    features: [
      'Unlimited past papers (all years)',
      'Detailed examiner reports & feedback',
      'Topic strength/weakness analysis',
      'Performance tracking history',
      'Priority marking'
    ],
    limitations: [],
    is_current: false,
  }
];

// Mock for development - toggle these to test different states
export const MOCK_USER_SUBSCRIPTION: SubscriptionStatus = {
  plan_id: 'free', // Change to 'full' to test active state
  is_active: true,
  renewal_date: undefined, 
};

export function getPlan(id: string): SubscriptionPlan | undefined {
  return PLANS.find((p) => p.id === id);
}
