"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { verifyPayment, type Tier } from "@/lib/subscription";

type State = "verifying" | "success" | "failed";

export default function SubscriptionCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [state, setState] = useState<State>("verifying");
  const [tier, setTier] = useState<Tier | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const reference = searchParams.get("reference") || searchParams.get("trxref");
    if (!reference) {
      setState("failed");
      setError("No payment reference found in the URL.");
      return;
    }

    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data: { user } }) => {
      if (!user) {
        router.push("/login");
        return;
      }

      try {
        const result = await verifyPayment({
          reference,
          student_id: user.id,
        });

        if (result.status === "activated" || result.status === "already_active") {
          setTier(result.tier);
          setState("success");

          // Redirect to dashboard after 3s
          setTimeout(() => router.push("/dashboard"), 3000);
        } else {
          setState("failed");
          setError("Payment could not be confirmed. Please contact support.");
        }
      } catch (err) {
        setState("failed");
        setError(err instanceof Error ? err.message : "Verification failed");
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (state === "verifying") {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-gray-900" />
        <p className="text-gray-500">Confirming your payment…</p>
      </div>
    );
  }

  if (state === "success") {
    const tierLabels: Record<string, string> = {
      standard: "Standard",
      bundle: "Bundle",
      all_subjects: "All Subjects",
    };

    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-4 text-center">
        <span className="text-5xl">🎉</span>
        <h1 className="text-2xl font-bold">You&apos;re all set!</h1>
        <p className="text-gray-500">
          Your <strong>{tier ? tierLabels[tier] ?? tier : ""}</strong> subscription is active.
          Enjoy unlimited AI feedback on your ZIMSEC preparation.
        </p>
        <p className="text-sm text-gray-400">Redirecting to dashboard…</p>
        <Link
          href="/dashboard"
          className="mt-2 rounded-lg bg-gray-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-gray-700"
        >
          Go to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-4 text-center">
      <span className="text-5xl">❌</span>
      <h1 className="text-2xl font-bold">Payment not confirmed</h1>
      <p className="max-w-sm text-gray-500">{error}</p>
      <div className="flex gap-3">
        <Link
          href="/pricing"
          className="rounded-lg bg-gray-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-gray-700"
        >
          Try again
        </Link>
        <Link
          href="/dashboard"
          className="rounded-lg border border-gray-200 px-6 py-2.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
