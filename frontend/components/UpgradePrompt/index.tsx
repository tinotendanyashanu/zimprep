"use client";

import Link from "next/link";
import type { QuotaError } from "@/lib/subscription";

type Props = {
  detail: QuotaError;
  onDismiss: () => void;
};

function featureLabel(feature: QuotaError["feature"]): string {
  switch (feature) {
    case "exam":
      return "Exam Mode";
    case "handwriting":
      return "Handwriting Upload";
    default:
      return "Practice Questions";
  }
}

export function UpgradePrompt({ detail, onDismiss }: Props) {
  const isQuotaExceeded = detail.code === "quota_exceeded";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
        {/* Icon */}
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-2xl">
          {isQuotaExceeded ? "🔒" : "⭐"}
        </div>

        {/* Heading */}
        <h2 className="mb-1 text-lg font-bold text-gray-900">
          {isQuotaExceeded
            ? "Daily limit reached"
            : `${featureLabel(detail.feature)} requires a subscription`}
        </h2>

        {/* Body */}
        <p className="mb-5 text-sm text-gray-500">
          {isQuotaExceeded
            ? `You've used all ${detail.limit} free questions today. Your limit resets at midnight UTC.`
            : detail.message}
        </p>

        {/* Usage indicator for quota_exceeded */}
        {isQuotaExceeded && detail.limit !== undefined && (
          <div className="mb-5">
            <div className="mb-1 flex justify-between text-xs text-gray-500">
              <span>Today's usage</span>
              <span>
                {detail.used}/{detail.limit}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full bg-amber-400"
                style={{
                  width: `${Math.min(((detail.used ?? 0) / (detail.limit ?? 1)) * 100, 100)}%`,
                }}
              />
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col gap-2">
          <Link
            href="/subscription/pricing"
            className="block w-full rounded-lg bg-gray-900 px-4 py-2.5 text-center text-sm font-semibold text-white hover:bg-gray-700"
          >
            View plans
          </Link>
          <button
            onClick={onDismiss}
            className="block w-full rounded-lg border border-gray-200 px-4 py-2.5 text-center text-sm text-gray-600 hover:bg-gray-50"
          >
            Maybe later
          </button>
        </div>
      </div>
    </div>
  );
}
