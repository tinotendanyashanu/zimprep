"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  getParentChildren,
  linkChild,
  getChildProgress,
  type ParentChild,
  type DashboardData,
  type WeakTopic,
  type SessionSummary,
} from "@/lib/api";
import { cn } from "@/lib/utils";

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

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
      <div
        className={cn("h-full rounded-full", color)}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

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
      <td className="py-2 font-medium">
        {s.total_marks > 0
          ? `${s.score}/${s.total_marks} (${s.percentage}%)`
          : "Marking…"}
      </td>
    </tr>
  );
}

function ChildProgress({
  data,
  childName,
}: {
  data: DashboardData;
  childName: string;
}) {
  const [selectedSubject, setSelectedSubject] = useState(data.subject_id);

  if (!data.has_data) {
    return (
      <p className="py-8 text-center text-sm text-gray-400">
        {childName} hasn&apos;t attempted any papers yet.
      </p>
    );
  }

  const ri = data.readiness!;
  const streak = data.streak;
  const coverage = data.coverage;
  const weakTopics: WeakTopic[] = data.weak_topics;

  return (
    <div className="space-y-6">
      {/* Subject switcher */}
      {data.subjects.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Subject:</span>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm shadow-sm focus:outline-none"
          >
            {data.subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* RI hero */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <p className="mb-1 text-sm text-gray-500">Readiness Index</p>
        <div className="mb-2 flex items-end gap-4">
          <p className={cn("text-4xl font-black", riColor(ri.readiness_index))}>
            {ri.readiness_index}%
          </p>
          <div className="mb-1 flex-1">
            <ProgressBar
              value={ri.readiness_index}
              color={riBarColor(ri.readiness_index)}
            />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div>
            <p className="text-gray-400">Accuracy</p>
            <p className="font-semibold text-blue-600">{fmt(ri.accuracy)}</p>
          </div>
          <div>
            <p className="text-gray-400">Coverage</p>
            <p className="font-semibold text-purple-600">{fmt(ri.coverage)}</p>
          </div>
          <div>
            <p className="text-gray-400">Consistency</p>
            <p className="font-semibold text-orange-500">{fmt(ri.consistency)}</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Accuracy" value={fmt(ri.accuracy)} valueClass="text-blue-600" />
        <StatCard
          label="Streak"
          value={`${streak.current}d`}
          sub={`Longest: ${streak.longest}d`}
          valueClass="text-orange-500"
        />
        <StatCard
          label="Coverage"
          value={fmt(ri.coverage)}
          sub={coverage ? `${coverage.covered_count}/${coverage.total_count} topics` : undefined}
          valueClass="text-purple-600"
        />
        <StatCard label="Consistency" value={fmt(ri.consistency)} valueClass="text-amber-500" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent activity */}
        <div className="lg:col-span-2 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 font-semibold">Recent Activity</h3>
          {data.recent_sessions.length === 0 ? (
            <p className="text-sm text-gray-400">No sessions yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-gray-400">
                    <th className="pb-2 pr-4">Date</th>
                    <th className="pb-2 pr-4">Paper</th>
                    <th className="pb-2 pr-4">Mode</th>
                    <th className="pb-2">Score</th>
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
        </div>

        {/* Weak topics + coverage */}
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="mb-3 font-semibold">Weak Topics</h3>
            {weakTopics.length === 0 ? (
              <p className="text-sm text-gray-400">No data yet.</p>
            ) : (
              <ul className="space-y-3">
                {weakTopics.slice(0, 5).map((t) => (
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

          {coverage && coverage.uncovered.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
              <h3 className="mb-2 font-semibold text-amber-800">
                Uncovered Topics ({coverage.uncovered.length})
              </h3>
              <ul className="space-y-1 text-sm text-amber-700">
                {coverage.uncovered.slice(0, 5).map((t) => (
                  <li key={t.topic} className="truncate">
                    {t.topic}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Link Child Form ───────────────────────────────────────────────────────────

function LinkChildForm({
  parentId,
  token,
  onLinked,
}: {
  parentId: string;
  token: string;
  onLinked: (child: ParentChild) => void;
}) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await linkChild(parentId, email.trim(), token);
      if (result.success) {
        onLinked({
          id: result.student_id,
          name: result.name,
          email: email.trim(),
          level: "",
          created_at: new Date().toISOString(),
        });
        setEmail("");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to link child");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      <div className="flex-1">
        <label className="mb-1 block text-xs text-gray-500">
          Child&apos;s student email
        </label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="student@example.com"
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
      </div>
      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
      >
        {loading ? "Linking…" : "Link Child"}
      </button>
    </form>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ParentDashboardPage() {
  const [parentId, setParentId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [children, setChildren] = useState<ParentChild[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [childData, setChildData] = useState<DashboardData | null>(null);
  const [loadingChildren, setLoadingChildren] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(false);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(async ({ data: session }) => {
      const user = session?.session?.user;
      const accessToken = session?.session?.access_token;
      if (!user || !accessToken) return;
      setParentId(user.id);
      setToken(accessToken);

      try {
        const kids = await getParentChildren(user.id, accessToken);
        setChildren(kids);
        if (kids.length > 0) setSelectedChildId(kids[0].id);
      } finally {
        setLoadingChildren(false);
      }
    });
  }, []);

  useEffect(() => {
    if (!parentId || !token || !selectedChildId) return;
    setLoadingProgress(true);
    setChildData(null);
    getChildProgress(parentId, selectedChildId, undefined, token)
      .then(setChildData)
      .catch(() => setChildData(null))
      .finally(() => setLoadingProgress(false));
  }, [parentId, token, selectedChildId]);

  const selectedChild = children.find((c) => c.id === selectedChildId);

  if (loadingChildren) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Parent Dashboard</h1>
        <p className="text-sm text-gray-500">Monitor your child&apos;s exam preparation</p>
      </div>

      {/* Link child form */}
      {parentId && token && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 font-semibold">Link a Child</h2>
          <LinkChildForm
            parentId={parentId}
            token={token}
            onLinked={(child) => {
              setChildren((prev) => {
                if (prev.find((c) => c.id === child.id)) return prev;
                return [...prev, child];
              });
              setSelectedChildId(child.id);
            }}
          />
        </div>
      )}

      {children.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <p>No children linked yet.</p>
          <p className="mt-1 text-sm">Enter your child&apos;s student email above to get started.</p>
        </div>
      ) : (
        <>
          {/* Child tabs */}
          {children.length > 1 && (
            <div className="mb-6 flex gap-2 overflow-x-auto">
              {children.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedChildId(c.id)}
                  className={cn(
                    "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                    selectedChildId === c.id
                      ? "bg-gray-900 text-white"
                      : "border border-gray-200 bg-white hover:bg-gray-50",
                  )}
                >
                  {c.name}
                </button>
              ))}
            </div>
          )}

          {/* Child progress */}
          {loadingProgress ? (
            <div className="py-12 text-center text-gray-400">Loading progress…</div>
          ) : childData && selectedChild ? (
            <ChildProgress data={childData} childName={selectedChild.name} />
          ) : null}
        </>
      )}
    </div>
  );
}
