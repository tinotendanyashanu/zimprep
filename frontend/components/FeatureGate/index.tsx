"use client";

import Link from "next/link";
import type { Tier } from "@/lib/subscription";
import { isPaid } from "@/lib/subscription";

// ── FeatureGate ────────────────────────────────────────────────────────────────

type FeatureGateProps = {
  tier: Tier | null;
  required: "paid" | "handwriting" | "exam";
  children: React.ReactNode;
  /** Fallback UI. If omitted, renders a default upgrade CTA. */
  fallback?: React.ReactNode;
};

function DefaultFallback({ feature }: { feature: FeatureGateProps["required"] }) {
  const labels: Record<typeof feature, { title: string; desc: string }> = {
    paid: {
      title: "Premium feature",
      desc: "Upgrade to a paid plan to access this feature.",
    },
    handwriting: {
      title: "Handwriting upload — PRO",
      desc: "Upload photos of handwritten answers and get AI marking. Available on all paid plans.",
    },
    exam: {
      title: "Exam Mode — PRO",
      desc: "Sit full past papers under timed exam conditions. Available on all paid plans.",
    },
  };

  const { title, desc } = labels[feature];
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 px-6 py-10 text-center">
      <span className="mb-3 text-3xl">🔒</span>
      <p className="mb-1 font-semibold text-gray-800">{title}</p>
      <p className="mb-4 max-w-xs text-sm text-gray-500">{desc}</p>
      <Link
        href="/pricing"
        className="rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700"
      >
        View plans
      </Link>
    </div>
  );
}

export function FeatureGate({ tier, required, children, fallback }: FeatureGateProps) {
  const allowed =
    tier !== null &&
    (required === "paid"
      ? isPaid(tier)
      : required === "handwriting" || required === "exam"
      ? isPaid(tier)
      : false);

  if (!allowed) {
    return <>{fallback ?? <DefaultFallback feature={required} />}</>;
  }
  return <>{children}</>;
}

// ── ExamModeGate ───────────────────────────────────────────────────────────────

type ExamModeGateProps = {
  tier: Tier | null;
  children: React.ReactNode;
};

export function ExamModeGate({ tier, children }: ExamModeGateProps) {
  if (tier !== null && isPaid(tier)) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 text-center">
      <span className="mb-4 text-5xl">📋</span>
      <h2 className="mb-2 text-2xl font-bold">Exam Mode</h2>
      <p className="mb-6 max-w-sm text-gray-500">
        Sit full past papers under timed conditions and get comprehensive AI
        marking. Available on all paid plans.
      </p>
      <Link
        href="/pricing"
        className="rounded-xl bg-gray-900 px-8 py-3 font-semibold text-white hover:bg-gray-700"
      >
        Unlock Exam Mode
      </Link>
      <Link
        href="/practice"
        className="mt-3 text-sm text-gray-400 hover:text-gray-600 hover:underline"
      >
        Continue with free practice →
      </Link>
    </div>
  );
}
