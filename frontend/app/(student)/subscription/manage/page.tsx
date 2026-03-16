"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import {
  getSubscriptionStatus,
  cancelSubscription,
  TIER_CONFIG,
  type Subscription,
  type Tier,
} from "@/lib/subscription";

export default function ManageSubscriptionPage() {
  const [studentId, setStudentId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [tier, setTier] = useState<Tier | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [cancelUntil, setCancelUntil] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmCancel, setConfirmCancel] = useState(false);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(async ({ data }) => {
      const user = data.session?.user;
      if (!user) return;
      setStudentId(user.id);
      setToken(data.session?.access_token ?? null);
    });
  }, []);

  useEffect(() => {
    if (!studentId || !token) return;
    setLoading(true);
    getSubscriptionStatus(studentId, token)
      .then((data) => {
        setTier(data.tier);
        setSubscription(data.subscription);
      })
      .catch(() => setError("Failed to load subscription details"))
      .finally(() => setLoading(false));
  }, [studentId, token]);

  async function handleCancel() {
    if (!studentId) return;
    setCancelling(true);
    setError(null);
    try {
      const res = await cancelSubscription(studentId, token ?? undefined);
      setCancelled(true);
      setCancelUntil(res.access_until);
      setConfirmCancel(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel subscription");
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  const config = tier ? TIER_CONFIG[tier] : null;

  if (!subscription || tier === "starter") {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="mb-4 text-gray-500">You don&apos;t have an active subscription.</p>
        <Link
          href="/pricing"
          className="rounded-lg bg-gray-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-gray-700"
        >
          View plans
        </Link>
      </div>
    );
  }

  const periodEnd = new Date(subscription.period_end).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  const statusColors: Record<string, string> = {
    active: "text-green-700 bg-green-50 border-green-200",
    cancelled: "text-amber-700 bg-amber-50 border-amber-200",
    past_due: "text-red-700 bg-red-50 border-red-200",
    expired: "text-gray-700 bg-gray-50 border-gray-200",
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-12">
      <h1 className="mb-6 text-2xl font-bold">Subscription</h1>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {cancelled && cancelUntil && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Subscription cancelled. You&apos;ll keep access until{" "}
          <strong>
            {new Date(cancelUntil).toLocaleDateString("en-GB", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </strong>
          .
        </div>
      )}

      {/* Subscription card */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-500">Current plan</p>
            <p className="text-xl font-bold">{config?.label ?? tier}</p>
          </div>
          <span
            className={`rounded-full border px-3 py-0.5 text-xs font-semibold capitalize ${
              statusColors[subscription.status] ?? statusColors.expired
            }`}
          >
            {subscription.status.replace("_", " ")}
          </span>
        </div>

        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">Price</dt>
            <dd className="font-medium">${subscription.amount_usd}/month</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">
              {subscription.status === "cancelled" ? "Access until" : "Next renewal"}
            </dt>
            <dd className="font-medium">{periodEnd}</dd>
          </div>
          {subscription.subject_ids.length > 0 &&
            subscription.subject_ids.length <
              Object.keys(TIER_CONFIG).length && (
              <div className="flex justify-between">
                <dt className="text-gray-500">Subjects</dt>
                <dd className="font-medium">{subscription.subject_ids.length} selected</dd>
              </div>
            )}
        </dl>
      </div>

      {/* Actions */}
      <div className="mt-6 space-y-3">
        <Link
          href="/pricing"
          className="block w-full rounded-lg border border-gray-200 px-4 py-2.5 text-center text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Change plan
        </Link>

        {subscription.status === "active" && !cancelled && (
          <>
            {!confirmCancel ? (
              <button
                onClick={() => setConfirmCancel(true)}
                className="block w-full rounded-lg border border-red-200 px-4 py-2.5 text-center text-sm font-medium text-red-600 hover:bg-red-50"
              >
                Cancel subscription
              </button>
            ) : (
              <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm">
                <p className="mb-3 font-medium text-red-800">
                  Are you sure? You&apos;ll lose access on {periodEnd}.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleCancel}
                    disabled={cancelling}
                    className="flex-1 rounded-lg bg-red-600 px-3 py-2 text-center font-semibold text-white disabled:opacity-50 hover:bg-red-700"
                  >
                    {cancelling ? "Cancelling…" : "Yes, cancel"}
                  </button>
                  <button
                    onClick={() => setConfirmCancel(false)}
                    className="flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-700 hover:bg-gray-50"
                  >
                    Keep subscription
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <p className="mt-6 text-center text-xs text-gray-400">
        Payments are processed securely by{" "}
        <a
          href="https://paystack.com"
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          Paystack
        </a>
        .
      </p>
    </div>
  );
}
