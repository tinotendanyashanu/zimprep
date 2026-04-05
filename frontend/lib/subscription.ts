/**
 * Subscription types, tier config, and API client for paywall features.
 */

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────────

export type Tier = "starter" | "standard" | "bundle" | "all_subjects";

export type SubscriptionStatus = "active" | "cancelled" | "past_due" | "expired";

export type Subscription = {
  id: string;
  student_id: string;
  tier: Tier;
  status: SubscriptionStatus;
  subject_ids: string[];
  paystack_customer_code: string | null;
  paystack_subscription_code: string | null;
  amount_usd: number;
  period_start: string;
  period_end: string;
  created_at: string;
  updated_at: string;
};

export type QuotaStatus = {
  tier: Tier;
  allowed: boolean;
  used: number;
  limit: number | null; // null = unlimited
  feature: "practice" | "exam" | "handwriting";
};

export type SubscriptionStatusResponse = {
  tier: Tier;
  subscription: Subscription | null;
  quota: QuotaStatus;
};

export type QuotaError = {
  code: "quota_exceeded" | "tier_required";
  tier: Tier;
  used?: number;
  limit?: number;
  feature: "practice" | "exam" | "handwriting";
  message: string;
};

export type InitializeCheckoutPayload = {
  student_id: string;
  tier: Tier;
  subject_ids: string[];
  email: string;
  callback_url: string;
};

export type CheckoutResponse = {
  authorization_url: string;
  reference: string;
  access_code: string;
};

export type VerifyPaymentPayload = {
  reference: string;
  student_id: string;
};

// ── Tier display config ────────────────────────────────────────────────────────

export type TierConfig = {
  id: Tier;
  label: string;
  price: number; // USD/month, 0 = free
  subjects: string; // human-readable subject access description
  dailyLimit: number | null; // null = unlimited
  handwriting: boolean;
  examMode: boolean;
  highlight?: boolean; // show as "most popular"
};

export const TIER_CONFIG: Record<Tier, TierConfig> = {
  starter: {
    id: "starter",
    label: "Starter",
    price: 0,
    subjects: "Any 1 subject",
    dailyLimit: 5,
    handwriting: false,
    examMode: false,
  },
  standard: {
    id: "standard",
    label: "Standard",
    price: 5,
    subjects: "1 subject of your choice",
    dailyLimit: null,
    handwriting: true,
    examMode: true,
    highlight: true,
  },
  bundle: {
    id: "bundle",
    label: "Bundle",
    price: 12,
    subjects: "3 subjects of your choice",
    dailyLimit: null,
    handwriting: true,
    examMode: true,
  },
  all_subjects: {
    id: "all_subjects",
    label: "All Subjects",
    price: 18,
    subjects: "Unlimited subjects",
    dailyLimit: null,
    handwriting: true,
    examMode: true,
  },
};

export const PAID_TIERS: Tier[] = ["standard", "bundle", "all_subjects"];

export function isPaid(_tier: Tier): boolean {
  return true;
}

// ── Custom error class ─────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  body: unknown;
  quotaError: QuotaError | null;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.quotaError = status === 402 && isQuotaError(body) ? (body as QuotaError) : null;
  }
}

function isQuotaError(body: unknown): body is QuotaError {
  return (
    typeof body === "object" &&
    body !== null &&
    "code" in body &&
    ((body as QuotaError).code === "quota_exceeded" ||
      (body as QuotaError).code === "tier_required")
  );
}

// ── API functions ──────────────────────────────────────────────────────────────

async function subFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, init);
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (json as { detail?: unknown }).detail;
    const message =
      typeof detail === "string"
        ? detail
        : `Request failed (${res.status})`;
    throw new ApiError(message, res.status, detail ?? json);
  }
  return json as T;
}

export const getSubscriptionStatus = (studentId: string, token?: string) =>
  subFetch<SubscriptionStatusResponse>(`/subscriptions/status/${studentId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

export const initializeCheckout = (payload: InitializeCheckoutPayload) =>
  subFetch<CheckoutResponse>("/subscriptions/initialize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

export const verifyPayment = (payload: VerifyPaymentPayload) =>
  subFetch<{ status: string; tier: Tier; subscription: Subscription }>(
    "/subscriptions/verify",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );

export const cancelSubscription = (studentId: string, token?: string) =>
  subFetch<{ status: string; access_until: string }>(
    `/subscriptions/${studentId}`,
    {
      method: "DELETE",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  );
