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
        href="/subscription/pricing"
        className="rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700"
      >
        View plans
      </Link>
    </div>
  );
}

export function FeatureGate({ children }: FeatureGateProps) {
  return <>{children}</>;
}

// ── ExamModeGate ───────────────────────────────────────────────────────────────

type ExamModeGateProps = {
  tier: Tier | null;
  children: React.ReactNode;
};

export function ExamModeGate({ children }: ExamModeGateProps) {
  return <>{children}</>;
}
