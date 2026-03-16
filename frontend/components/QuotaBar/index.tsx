"use client";

import Link from "next/link";
import type { QuotaStatus } from "@/lib/subscription";

type Props = {
  quota: QuotaStatus;
};

export function QuotaBar({ quota }: Props) {
  // Paid tiers with no limit: don't show a bar
  if (quota.limit === null) return null;

  const pct = Math.min((quota.used / quota.limit) * 100, 100);
  const exhausted = quota.used >= quota.limit;

  const barColor = exhausted
    ? "bg-red-500"
    : pct >= 80
    ? "bg-amber-400"
    : "bg-blue-500";

  return (
    <div className="rounded-xl border border-gray-200 bg-white px-5 py-3 shadow-sm">
      <div className="mb-1.5 flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">Free questions today</span>
        <span
          className={`font-semibold ${
            exhausted ? "text-red-600" : "text-gray-600"
          }`}
        >
          {quota.used} / {quota.limit}
        </span>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {exhausted && (
        <p className="mt-2 flex items-center justify-between text-xs text-gray-500">
          <span>Daily limit reached — resets at midnight UTC</span>
          <Link
            href="/pricing"
            className="ml-2 shrink-0 font-medium text-blue-600 hover:underline"
          >
            Upgrade
          </Link>
        </p>
      )}

      {!exhausted && (
        <p className="mt-1.5 text-xs text-gray-400">
          {quota.limit - quota.used} question
          {quota.limit - quota.used !== 1 ? "s" : ""} remaining today ·{" "}
          <Link href="/pricing" className="text-blue-500 hover:underline">
            Upgrade for unlimited
          </Link>
        </p>
      )}
    </div>
  );
}
