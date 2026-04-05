"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import {
  TIER_CONFIG,
  PAID_TIERS,
  initializeCheckout,
  getSubscriptionStatus,
  type Tier,
  type TierConfig,
} from "@/lib/subscription";
import { getSubjects, type Subject } from "@/lib/api";
import { useStudent } from "@/lib/student-context";

// ── Helpers ────────────────────────────────────────────────────────────────────

function PriceTag({ config }: { config: TierConfig }) {
  if (config.price === 0) {
    return <span className="text-3xl font-black text-gray-900">Free</span>;
  }
  return (
    <div className="flex items-end gap-0.5">
      <span className="text-sm font-medium text-gray-500">$</span>
      <span className="text-3xl font-black text-gray-900">{config.price}</span>
      <span className="mb-0.5 text-sm text-gray-500">/mo</span>
    </div>
  );
}

function Feature({ ok, label }: { ok: boolean; label: string }) {
  return (
    <li className="flex items-center gap-2 text-sm">
      <span className={ok ? "text-green-500" : "text-gray-300"}>
        {ok ? "✓" : "✗"}
      </span>
      <span className={ok ? "text-gray-700" : "text-gray-400"}>{label}</span>
    </li>
  );
}

// ── Subject selector modal ─────────────────────────────────────────────────────

function SubjectSelector({
  tier,
  subjects,
  onConfirm,
  onCancel,
}: {
  tier: TierConfig;
  subjects: Subject[];
  onConfirm: (ids: string[]) => void;
  onCancel: () => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const needed = tier.id === "all_subjects" ? null : (TIER_CONFIG[tier.id].id === "bundle" ? 3 : 1);

  function toggle(id: string) {
    if (tier.id === "all_subjects") return; // all_subjects gets everything
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((s) => s !== id);
      if (needed !== null && prev.length >= needed) return prev; // max reached
      return [...prev, id];
    });
  }

  function handleConfirm() {
    if (tier.id === "all_subjects") {
      onConfirm(subjects.map((s) => s.id));
    } else {
      onConfirm(selected);
    }
  }

  const canConfirm =
    tier.id === "all_subjects" || (needed !== null && selected.length === needed);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <h2 className="mb-1 text-lg font-bold">Choose your subject{needed !== 1 ? "s" : ""}</h2>
        {tier.id !== "all_subjects" && needed && (
          <p className="mb-4 text-sm text-gray-500">
            Select {needed} subject{needed > 1 ? "s" : ""} to include in your {tier.label} plan.
          </p>
        )}
        {tier.id === "all_subjects" && (
          <p className="mb-4 text-sm text-gray-500">
            Your All Subjects plan includes everything — no selection needed!
          </p>
        )}

        {tier.id !== "all_subjects" && (
          <div className="mb-5 grid grid-cols-2 gap-2">
            {subjects.map((s) => {
              const isSelected = selected.includes(s.id);
              const isDisabled = !isSelected && needed !== null && selected.length >= needed;
              return (
                <button
                  key={s.id}
                  onClick={() => toggle(s.id)}
                  disabled={isDisabled}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                    isSelected
                      ? "border-gray-900 bg-gray-900 text-white"
                      : isDisabled
                      ? "cursor-not-allowed border-gray-100 bg-gray-50 text-gray-300"
                      : "border-gray-200 hover:border-gray-400"
                  }`}
                >
                  <p className="font-medium">{s.name}</p>
                  <p className="text-xs opacity-70">{s.level}</p>
                </button>
              );
            })}
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={handleConfirm}
            disabled={!canConfirm}
            className="flex-1 rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40 hover:bg-gray-700 disabled:cursor-not-allowed"
          >
            Continue to payment
          </button>
          <button
            onClick={onCancel}
            className="rounded-lg border border-gray-200 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function PricingPage() {
  const router = useRouter();
  const { id: studentId, examBoard, level } = useStudent();
  const [email, setEmail] = useState<string>("");
  const [token, setToken] = useState<string | null>(null);
  const [currentTier, setCurrentTier] = useState<Tier>("starter");
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectingFor, setSelectingFor] = useState<TierConfig | null>(null);
  const [checkingOut, setCheckingOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data }) => {
      setEmail(data.session?.user?.email ?? "");
      setToken(data.session?.access_token ?? null);
    });
    getSubjects(examBoard || undefined, level || undefined)
      .then(setSubjects)
      .catch(() => {});
  }, [examBoard, level]);

  useEffect(() => {
    if (!studentId || !token) return;
    getSubscriptionStatus(studentId, token)
      .then((s) => setCurrentTier(s.tier))
      .catch(() => {});
  }, [studentId, token]);

  async function handleSelectTier(tier: TierConfig) {
    if (!studentId || !email) {
      router.push("/login");
      return;
    }
    if (tier.price === 0) return;
    setSelectingFor(tier);
  }

  async function handleConfirmSubjects(subjectIds: string[]) {
    if (!selectingFor || !studentId || !email) return;
    setSelectingFor(null);
    setCheckingOut(true);
    setError(null);

    const callbackUrl =
      typeof window !== "undefined"
        ? `${window.location.origin}/subscription/callback`
        : "/subscription/callback";

    try {
      const res = await initializeCheckout({
        student_id: studentId,
        tier: selectingFor.id,
        subject_ids: subjectIds,
        email,
        callback_url: callbackUrl,
      });
      window.location.href = res.authorization_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start checkout");
      setCheckingOut(false);
    }
  }

  const tiers = Object.values(TIER_CONFIG);

  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
      {/* Heading */}
      <div className="mb-10 text-center">
        <h1 className="mb-2 text-3xl font-black">Simple, honest pricing</h1>
        <p className="text-gray-500">
          Start free. Upgrade when you&apos;re ready for unlimited AI feedback.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {checkingOut && (
        <div className="mb-6 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          Redirecting to payment…
        </div>
      )}

      {/* Tier cards */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {tiers.map((tier) => {
          const isCurrent = currentTier === tier.id;
          return (
            <div
              key={tier.id}
              className={`relative flex flex-col rounded-2xl border p-6 shadow-sm ${
                tier.highlight
                  ? "border-gray-900 ring-2 ring-gray-900"
                  : "border-gray-200"
              }`}
            >
              {tier.highlight && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gray-900 px-3 py-0.5 text-xs font-semibold text-white">
                  Most popular
                </span>
              )}
              {isCurrent && (
                <span className="absolute -top-3 right-4 rounded-full bg-green-600 px-3 py-0.5 text-xs font-semibold text-white">
                  Current plan
                </span>
              )}

              <div className="mb-3">
                <p className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                  {tier.label}
                </p>
                <div className="mt-1">
                  <PriceTag config={tier} />
                </div>
              </div>

              <p className="mb-4 text-sm text-gray-500">{tier.subjects}</p>

              <ul className="mb-6 flex-1 space-y-2">
                <Feature
                  ok={tier.dailyLimit === null}
                  label={
                    tier.dailyLimit !== null
                      ? `${tier.dailyLimit} questions/day`
                      : "Unlimited questions"
                  }
                />
                <Feature ok={tier.handwriting} label="Handwriting upload" />
                <Feature ok={tier.examMode} label="Exam Mode" />
                <Feature ok={tier.price > 0} label="Progress tracking" />
              </ul>

              {tier.price === 0 ? (
                <div className="rounded-lg border border-gray-200 px-4 py-2.5 text-center text-sm text-gray-400">
                  {isCurrent ? "Your current plan" : "Free forever"}
                </div>
              ) : (
                <button
                  onClick={() => handleSelectTier(tier)}
                  disabled={isCurrent || checkingOut}
                  className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                    tier.highlight
                      ? "bg-gray-900 text-white hover:bg-gray-700"
                      : "border border-gray-900 text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  {isCurrent ? "Current plan" : `Get ${tier.label}`}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Manage link for paid users */}
      {PAID_TIERS.includes(currentTier) && (
        <p className="mt-8 text-center text-sm text-gray-500">
          Manage or cancel your subscription in{" "}
          <Link href="/subscription/manage" className="text-blue-600 hover:underline">
            subscription settings
          </Link>
          .
        </p>
      )}

      {/* Subject selector modal */}
      {selectingFor && (
        <SubjectSelector
          tier={selectingFor}
          subjects={subjects}
          onConfirm={handleConfirmSubjects}
          onCancel={() => setSelectingFor(null)}
        />
      )}
    </div>
  );
}
