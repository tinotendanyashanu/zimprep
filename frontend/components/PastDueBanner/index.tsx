"use client";

import type { Subscription } from "@/lib/subscription";

type Props = {
  subscription: Subscription;
};

export function PastDueBanner({ subscription }: Props) {
  if (subscription.status !== "past_due") return null;

  const endDate = new Date(subscription.period_end).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 shrink-0 text-xl">⚠️</span>
        <div className="flex-1">
          <p className="font-semibold text-red-800">Payment failed</p>
          <p className="mt-0.5 text-sm text-red-600">
            Your last payment didn&apos;t go through. You have a 7-day grace
            period — access continues until {endDate}. Please update your
            payment method to avoid losing access.
          </p>
          <a
            href="https://paystack.com"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 inline-block text-sm font-medium text-red-700 underline hover:text-red-900"
          >
            Update payment method →
          </a>
        </div>
      </div>
    </div>
  );
}
