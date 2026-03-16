"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import {
  getStudentDashboard,
  type DashboardData,
  type WeakTopic,
  type SessionSummary,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { QuotaBar, PastDueBanner } from "@/components";
import { useQuota } from "@/hooks/useQuota";

// ── Helpers ───────────────────────────────────────────────────────────────────

function riColor(ri: number) {
  if (ri >= 70) return "text-green-600";
  if (ri >= 40) return "text-amber-500";
  return "text-red-500";
}

function riBarColor(ri: number) {
  if (ri >= 70) return "bg-green-500";
  if (ri >= 40) return "bg-amber-400";
  return "bg-red-500";
}

function fmt(n: number | null | undefined) {
  return n != null ? `${n}%` : "—";
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  valueClass,
}: {
  label: string;
  value: string;
  sub?: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={cn("mt-1 text-3xl font-bold", valueClass)}>{value}</p>
      {sub && <p className="mt-1 text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
      <div
        className={cn("h-full rounded-full transition-all", color)}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

function ReadinessBreakdown({
  accuracy,
  coverage,
  consistency,
}: {
  accuracy: number;
  coverage: number;
  consistency: number;
}) {
  const bars = [
    { label: "Accuracy (40%)", value: accuracy, color: "bg-blue-500" },
    { label: "Coverage (35%)", value: coverage, color: "bg-purple-500" },
    { label: "Consistency (25%)", value: consistency, color: "bg-orange-400" },
  ];
  return (
    <div className="space-y-3">
      {bars.map((b) => (
        <div key={b.label}>
          <div className="mb-1 flex justify-between text-sm">
            <span className="text-gray-600">{b.label}</span>
            <span className="font-medium">{fmt(b.value)}</span>
          </div>
          <ProgressBar value={b.value} color={b.color} />
        </div>
      ))}
    </div>
  );
}

function SessionRow({ s }: { s: SessionSummary }) {
  const date = s.completed_at
    ? new Date(s.completed_at).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
      })
    : "—";
  const label = s.subject_name
    ? `${s.subject_name} ${s.paper_year} P${s.paper_number}`
    : "—";
  return (
    <tr className="border-t border-gray-100 text-sm">
      <td className="py-2 pr-4 text-gray-500">{date}</td>
      <td className="py-2 pr-4">{label}</td>
      <td className="py-2 pr-4 capitalize text-gray-500">{s.mode}</td>
      <td className="py-2 pr-4 font-medium">
        {s.total_marks > 0
          ? `${s.score}/${s.total_marks} (${s.percentage}%)`
          : "Marking…"}
      </td>
      <td className="py-2">
        <Link
          href={`/exam/${s.session_id}/results`}
          className="text-blue-600 hover:underline"
        >
          View
        </Link>
      </td>
    </tr>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [studentId, setStudentId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { quota, subscription } = useQuota();

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(async ({ data: session }) => {
      const user = session?.session?.user;
      const accessToken = session?.session?.access_token;
      if (!user) return;
      setStudentId(user.id);
      setToken(accessToken ?? null);

      const { data: student } = await supabase
        .from("student")
        .select("name")
        .eq("id", user.id)
        .single();
      setName(student?.name ?? "");
    });
  }, []);

  useEffect(() => {
    if (!studentId || !token) return;
    setLoading(true);
    getStudentDashboard(studentId, selectedSubject, token)
      .then((d) => {
        setData(d);
        if (!selectedSubject && d.subject_id) setSelectedSubject(d.subject_id);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [studentId, token, selectedSubject]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading dashboard…
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl p-8 text-center text-red-500">
        {error}
      </div>
    );
  }

  // Empty state
  if (!data?.has_data) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="mb-2 text-2xl font-bold">
          Welcome{name ? `, ${name}` : ""}!
        </h1>
        <p className="mb-8 text-gray-500">
          You haven&apos;t attempted any papers yet. Get started below.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Link
            href="/exam/select"
            className="rounded-xl border border-gray-200 bg-white p-6 text-left shadow-sm transition-shadow hover:shadow-md"
          >
            <p className="mb-1 font-semibold">Exam Mode</p>
            <p className="text-sm text-gray-500">
              Timed past paper under exam conditions.
            </p>
          </Link>
          <Link
            href="/practice"
            className="rounded-xl border border-gray-200 bg-white p-6 text-left shadow-sm transition-shadow hover:shadow-md"
          >
            <p className="mb-1 font-semibold">Practice Mode</p>
            <p className="text-sm text-gray-500">
              Adaptive questions with instant AI feedback.
            </p>
          </Link>
        </div>
      </div>
    );
  }

  const ri = data.readiness!;
  const streak = data.streak;
  const coverage = data.coverage;
  const weakTopics: WeakTopic[] = data.weak_topics;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Paywall banners */}
      {subscription && subscription.status === "past_due" && (
        <div className="mb-4">
          <PastDueBanner subscription={subscription} />
        </div>
      )}
      {quota && quota.limit !== null && (
        <div className="mb-4">
          <QuotaBar quota={quota} />
        </div>
      )}

      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">
            {name ? `${name}'s Dashboard` : "Dashboard"}
          </h1>
          <p className="text-sm text-gray-500">Track your exam readiness</p>
        </div>

        {data.subjects.length > 1 && (
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {data.subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Readiness Index hero */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-3 flex items-end gap-4">
          <div>
            <p className="text-sm text-gray-500">Readiness Index</p>
            <p className={cn("text-5xl font-black", riColor(ri.readiness_index))}>
              {ri.readiness_index}%
            </p>
          </div>
          <div className="mb-1 flex-1">
            <ProgressBar
              value={ri.readiness_index}
              color={riBarColor(ri.readiness_index)}
            />
          </div>
        </div>
        <p className="mb-4 text-xs text-gray-400">
          RI = Accuracy × 40% + Coverage × 35% + Consistency × 25%
        </p>
        <ReadinessBreakdown
          accuracy={ri.accuracy}
          coverage={ri.coverage}
          consistency={ri.consistency}
        />
      </div>

      {/* Stat cards */}
      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Accuracy"
          value={fmt(ri.accuracy)}
          valueClass="text-blue-600"
        />
        <StatCard
          label="Streak"
          value={`${streak.current}d`}
          sub={`Longest: ${streak.longest}d`}
          valueClass="text-orange-500"
        />
        <StatCard
          label="Coverage"
          value={fmt(ri.coverage)}
          sub={
            coverage
              ? `${coverage.covered_count}/${coverage.total_count} topics`
              : undefined
          }
          valueClass="text-purple-600"
        />
        <StatCard
          label="Consistency"
          value={fmt(ri.consistency)}
          valueClass="text-amber-500"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent sessions */}
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-semibold">Recent Sessions</h2>
            {data.recent_sessions.length === 0 ? (
              <p className="text-sm text-gray-400">No completed sessions yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-400">
                      <th className="pb-2 pr-4">Date</th>
                      <th className="pb-2 pr-4">Paper</th>
                      <th className="pb-2 pr-4">Mode</th>
                      <th className="pb-2 pr-4">Score</th>
                      <th className="pb-2" />
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_sessions.map((s) => (
                      <SessionRow key={s.session_id} s={s} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="mt-4 flex gap-3">
              <Link
                href="/exam/select"
                className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
              >
                New Exam
              </Link>
              <Link
                href="/practice"
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium hover:bg-gray-50"
              >
                Practice
              </Link>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Weak topics */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 font-semibold">Weak Topics</h2>
            {weakTopics.length === 0 ? (
              <p className="text-sm text-gray-400">No data yet.</p>
            ) : (
              <ul className="space-y-3">
                {weakTopics.slice(0, 6).map((t) => (
                  <li key={t.topic}>
                    <div className="mb-1 flex justify-between text-xs">
                      <span className="truncate text-gray-700">{t.topic}</span>
                      <span className="ml-2 shrink-0 text-red-500">
                        {Math.round(t.fail_ratio * 100)}% fail
                      </span>
                    </div>
                    <ProgressBar value={t.fail_ratio * 100} color="bg-red-400" />
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Coverage */}
          {coverage && (
            <>
              {coverage.uncovered.length > 0 && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
                  <h2 className="mb-3 font-semibold text-amber-800">
                    Uncovered Topics ({coverage.uncovered.length})
                  </h2>
                  <ul className="space-y-1">
                    {coverage.uncovered.slice(0, 5).map((t) => (
                      <li
                        key={t.topic}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="truncate text-amber-700">{t.topic}</span>
                        <Link
                          href={`/practice?topic=${encodeURIComponent(t.topic)}`}
                          className="ml-2 shrink-0 text-xs text-blue-600 hover:underline"
                        >
                          Practice
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {coverage.covered.length > 0 && (
                <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                  <h2 className="mb-3 font-semibold">
                    Covered Topics ({coverage.covered_count}/{coverage.total_count})
                  </h2>
                  <ul className="space-y-1">
                    {coverage.covered.slice(0, 8).map((t) => (
                      <li
                        key={t.topic}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="truncate text-gray-700">{t.topic}</span>
                        {t.attempt_count > 0 && (
                          <span className="ml-2 shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                            {t.attempt_count}×
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
