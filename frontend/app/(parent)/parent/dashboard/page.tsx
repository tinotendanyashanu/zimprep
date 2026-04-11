"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import { createClient } from "@/lib/supabase/client";
import {
  getParentChildren,
  getParentFamilyDashboard,
  getParentReport,
  generateParentReport,
  getParentAlerts,
  markAllAlertsRead,
  getChildGoals,
  setChildGoals,
  getChildProgress,
  linkChild,
  type ParentChild,
  type DashboardData,
  type WeakTopic,
  type SessionSummary,
  type FamilyDashboard,
  type ChildSummary,
  type WeeklyFamilyReport,
  type ChildReportSection,
  type ParentAlert,
  type ParentGoals,
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

// ── Shared primitives (same styles as student dashboard) ─────────────────────

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

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const cls = {
    Improving: "bg-green-100 text-green-700",
    Stable: "bg-blue-100 text-blue-700",
    "At Risk": "bg-red-100 text-red-700",
  }[status] ?? "bg-gray-100 text-gray-600";

  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-semibold", cls)}>
      {status}
    </span>
  );
}

// ── Family Summary ────────────────────────────────────────────────────────────

function FamilySummarySection({ data }: { data: FamilyDashboard }) {
  const s = data.family_summary;
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      <StatCard
        label="Total Study Time"
        value={`${s.total_study_hours}h`}
        sub="this week"
        valueClass="text-blue-600"
      />
      <StatCard
        label="Questions Attempted"
        value={String(s.total_questions_attempted)}
        sub="this week"
        valueClass="text-purple-600"
      />
      <StatCard
        label="Family Average"
        value={`${s.avg_family_score}%`}
        sub="avg score"
        valueClass={s.avg_family_score >= 60 ? "text-green-600" : "text-amber-500"}
      />
      <StatCard
        label="Need Attention"
        value={String(s.children_needing_attention)}
        sub="children"
        valueClass={s.children_needing_attention > 0 ? "text-red-500" : "text-green-600"}
      />
      <StatCard
        label="Top Performer"
        value={s.top_performing_child ?? "—"}
        sub="this week"
        valueClass="text-orange-500"
      />
    </div>
  );
}

// ── Child Card ────────────────────────────────────────────────────────────────

function ChildCard({
  child,
  isSelected,
  onClick,
}: {
  child: ChildSummary;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <div
      className={cn(
        "cursor-pointer rounded-xl border bg-white p-5 shadow-sm transition-all",
        isSelected ? "border-gray-900 ring-2 ring-gray-900/10" : "border-gray-200 hover:border-gray-400",
      )}
      onClick={onClick}
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-gray-900">{child.name}</p>
          <p className="text-xs text-gray-400">{child.level || "Student"}</p>
        </div>
        <StatusBadge status={child.status} />
      </div>

      <div className="mb-3">
        <div className="mb-1 flex items-end gap-1">
          <span className={cn("text-2xl font-black", riColor(child.readiness_index))}>
            {child.readiness_index}%
          </span>
          <span className="mb-0.5 text-xs text-gray-400">readiness</span>
        </div>
        <ProgressBar value={child.readiness_index} color={riBarColor(child.readiness_index)} />
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-gray-50 px-3 py-2">
          <p className="text-gray-400">Avg Score</p>
          <p className="font-semibold text-gray-800">{child.avg_score.toFixed(0)}%</p>
        </div>
        <div className="rounded-lg bg-gray-50 px-3 py-2">
          <p className="text-gray-400">Study Time</p>
          <p className="font-semibold text-gray-800">{child.study_hours_this_week}h</p>
        </div>
        <div className="rounded-lg bg-gray-50 px-3 py-2">
          <p className="text-gray-400">Streak</p>
          <p className="font-semibold text-orange-500">{child.streak}d</p>
        </div>
        <div className="rounded-lg bg-gray-50 px-3 py-2">
          <p className="text-gray-400">Questions</p>
          <p className="font-semibold text-gray-800">{child.questions_this_week}</p>
        </div>
      </div>

      {child.weak_subjects.length > 0 && (
        <div className="mt-3">
          <p className="mb-1 text-xs text-gray-400">Needs work</p>
          <div className="flex flex-wrap gap-1">
            {child.weak_subjects.slice(0, 3).map((s) => (
              <span key={s} className="rounded-full bg-red-50 px-2 py-0.5 text-xs text-red-600">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {child.strong_subjects.length > 0 && (
        <div className="mt-2">
          <p className="mb-1 text-xs text-gray-400">Doing well in</p>
          <div className="flex flex-wrap gap-1">
            {child.strong_subjects.slice(0, 3).map((s) => (
              <span key={s} className="rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-600">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      <button className="mt-4 w-full rounded-lg border border-gray-200 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50">
        View Details
      </button>
    </div>
  );
}

// ── Alerts Panel ──────────────────────────────────────────────────────────────

function AlertsPanel({
  alerts,
  onMarkAllRead,
}: {
  alerts: ParentAlert[];
  onMarkAllRead: () => void;
}) {
  const iconMap: Record<string, string> = {
    inactivity: "⏰",
    performance_drop: "⚠️",
    improving: "🎉",
    goal_not_met: "🎯",
  };

  const unread = alerts.filter((a) => !a.is_read).length;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold">Alerts</h3>
          {unread > 0 && (
            <span className="rounded-full bg-red-500 px-2 py-0.5 text-xs font-bold text-white">
              {unread}
            </span>
          )}
        </div>
        {unread > 0 && (
          <button
            onClick={onMarkAllRead}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Mark all read
          </button>
        )}
      </div>

      {alerts.length === 0 ? (
        <p className="text-sm text-gray-400">No alerts. Everything looks good.</p>
      ) : (
        <ul className="space-y-3">
          {alerts.slice(0, 6).map((a) => (
            <li
              key={a.id}
              className={cn(
                "rounded-lg p-3 text-sm",
                a.is_read ? "bg-gray-50 text-gray-500" : "bg-amber-50 text-gray-800",
              )}
            >
              <span className="mr-2">{iconMap[a.alert_type] ?? "📌"}</span>
              {a.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ── Goal Tracker ──────────────────────────────────────────────────────────────

function GoalTracker({
  child,
  parentId,
  token,
}: {
  child: ChildSummary;
  parentId: string;
  token: string;
}) {
  const [goals, setGoals] = useState<ParentGoals | null>(null);
  const [editing, setEditing] = useState(false);
  const [hours, setHours] = useState("5");
  const [grade, setGrade] = useState("70");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getChildGoals(parentId, child.student_id, token)
      .then((g) => {
        setGoals(g);
        setHours(String(g.weekly_hours_target));
        setGrade(String(g.target_grade_percent));
      })
      .catch(() => {});
  }, [parentId, child.student_id, token]);

  async function handleSave() {
    setSaving(true);
    try {
      await setChildGoals(
        parentId,
        child.student_id,
        {
          weekly_hours_target: parseFloat(hours) || 5,
          target_grade_percent: parseInt(grade, 10) || 70,
        },
        token,
      );
      setGoals((prev) => ({
        ...prev!,
        weekly_hours_target: parseFloat(hours) || 5,
        target_grade_percent: parseInt(grade, 10) || 70,
      }));
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  if (!goals) return null;

  const hoursTarget = goals.weekly_hours_target;
  const gradeTarget = goals.target_grade_percent;
  const hoursMet = child.study_hours_this_week >= hoursTarget;
  const gradeMet = child.avg_score >= gradeTarget;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">Goals — {child.name}</h3>
        <button
          onClick={() => setEditing((v) => !v)}
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          {editing ? "Cancel" : "Edit"}
        </button>
      </div>

      {editing ? (
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-xs text-gray-500">Weekly hours target</label>
            <input
              type="number"
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              min="0.5"
              max="40"
              step="0.5"
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-500">Target grade (%)</label>
            <input
              type="number"
              value={grade}
              onChange={(e) => setGrade(e.target.value)}
              min="1"
              max="100"
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full rounded-lg bg-gray-900 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Goals"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <div className="mb-1 flex justify-between text-xs text-gray-500">
              <span>Weekly Study Hours</span>
              <span>
                {child.study_hours_this_week}h / {hoursTarget}h
              </span>
            </div>
            <ProgressBar
              value={(child.study_hours_this_week / hoursTarget) * 100}
              color={hoursMet ? "bg-green-500" : "bg-amber-400"}
            />
            <p className={cn("mt-1 text-xs font-medium", hoursMet ? "text-green-600" : "text-amber-600")}>
              {hoursMet ? "Goal met" : `${(hoursTarget - child.study_hours_this_week).toFixed(1)}h to go`}
            </p>
          </div>

          <div>
            <div className="mb-1 flex justify-between text-xs text-gray-500">
              <span>Target Grade</span>
              <span>
                {child.avg_score.toFixed(0)}% / {gradeTarget}%
              </span>
            </div>
            <ProgressBar
              value={(child.avg_score / gradeTarget) * 100}
              color={gradeMet ? "bg-green-500" : "bg-amber-400"}
            />
            <p className={cn("mt-1 text-xs font-medium", gradeMet ? "text-green-600" : "text-amber-600")}>
              {gradeMet ? "Goal met" : `${(gradeTarget - child.avg_score).toFixed(0)}% below target`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Weekly Report ─────────────────────────────────────────────────────────────

function WeeklyReport({
  report,
  onRegenerate,
  loading,
}: {
  report: WeeklyFamilyReport;
  onRegenerate: () => void;
  loading: boolean;
}) {
  const [expanded, setExpanded] = useState<string | null>(null);

  function trendColor(trend: string) {
    if (trend === "Trending up") return "text-green-600";
    if (trend === "Trending down") return "text-red-500";
    return "text-gray-500";
  }

  const genDate = report.generated_at
    ? new Date(report.generated_at).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "—";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold">Weekly Family Report</h2>
          <p className="text-sm text-gray-400">Generated {genDate}</p>
        </div>
        <button
          onClick={onRegenerate}
          disabled={loading}
          className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? "Generating…" : "Refresh Report"}
        </button>
      </div>

      {/* Parent insights */}
      {report.parent_insights.length > 0 && (
        <div className="mb-6 rounded-xl bg-blue-50 p-4">
          <p className="mb-2 text-sm font-semibold text-blue-900">What you should know</p>
          <ul className="space-y-1.5">
            {report.parent_insights.map((insight, i) => (
              <li key={i} className="text-sm text-blue-800">
                • {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Per-child sections */}
      <div className="space-y-3">
        {report.children.map((child) => (
          <div
            key={child.name}
            className="rounded-xl border border-gray-100 bg-gray-50"
          >
            <button
              className="flex w-full items-center justify-between px-5 py-4 text-left"
              onClick={() =>
                setExpanded((prev) => (prev === child.name ? null : child.name))
              }
            >
              <div className="flex items-center gap-3">
                <span className="font-semibold">{child.name}</span>
                <StatusBadge status={child.status} />
                <span className={cn("text-xs font-medium", trendColor(child.performance_trend))}>
                  {child.performance_trend}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>{child.avg_score.toFixed(0)}% avg</span>
                <span>{child.study_hours}h studied</span>
                <span className="text-gray-300">{expanded === child.name ? "▲" : "▼"}</span>
              </div>
            </button>

            {expanded === child.name && (
              <div className="border-t border-gray-200 px-5 pb-5 pt-4">
                <div className="grid gap-6 md:grid-cols-2">
                  <div>
                    <div className="mb-4 grid grid-cols-3 gap-3 text-sm">
                      <div className="rounded-lg bg-white p-3 shadow-sm">
                        <p className="text-xs text-gray-400">Questions</p>
                        <p className="font-bold text-gray-800">{child.questions_attempted}</p>
                      </div>
                      <div className="rounded-lg bg-white p-3 shadow-sm">
                        <p className="text-xs text-gray-400">Readiness</p>
                        <p className={cn("font-bold", riColor(child.readiness_index))}>
                          {child.readiness_index}%
                        </p>
                      </div>
                      <div className="rounded-lg bg-white p-3 shadow-sm">
                        <p className="text-xs text-gray-400">Streak</p>
                        <p className="font-bold text-orange-500">{child.streak}d</p>
                      </div>
                    </div>

                    {child.strong_areas.length > 0 && (
                      <div className="mb-3">
                        <p className="mb-1 text-xs font-semibold text-green-700">Strong areas</p>
                        <div className="flex flex-wrap gap-1">
                          {child.strong_areas.map((a) => (
                            <span
                              key={a}
                              className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs text-green-700"
                            >
                              {a}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {child.weak_areas.length > 0 && (
                      <div>
                        <p className="mb-1 text-xs font-semibold text-red-600">Needs work</p>
                        <div className="flex flex-wrap gap-1">
                          {child.weak_areas.map((a) => (
                            <span
                              key={a}
                              className="rounded-full bg-red-50 px-2.5 py-0.5 text-xs text-red-600"
                            >
                              {a}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-3">
                    {child.recommendations_for_parent.length > 0 && (
                      <div className="rounded-xl bg-amber-50 p-4">
                        <p className="mb-1 text-xs font-semibold text-amber-800">What you should do</p>
                        <ul className="space-y-1">
                          {child.recommendations_for_parent.map((r, i) => (
                            <li key={i} className="text-sm text-amber-900">
                              {r}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {child.recommendations_for_child.length > 0 && (
                      <div className="rounded-xl bg-blue-50 p-4">
                        <p className="mb-1 text-xs font-semibold text-blue-800">What {child.name} should do</p>
                        <ul className="space-y-1">
                          {child.recommendations_for_child.map((r, i) => (
                            <li key={i} className="text-sm text-blue-900">
                              • {r}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Performance Line Chart ────────────────────────────────────────────────────

const SUBJECT_COLORS = [
  "#6366f1", "#10b981", "#f59e0b", "#ef4444", "#3b82f6",
  "#8b5cf6", "#14b8a6", "#f97316",
];

function PerformanceLineChart({ sessions }: { sessions: SessionSummary[] }) {
  const valid = sessions
    .filter((s) => s.completed_at && s.percentage != null)
    .sort((a, b) => new Date(a.completed_at!).getTime() - new Date(b.completed_at!).getTime());

  if (valid.length < 2) {
    return (
      <div className="flex h-40 items-center justify-center rounded-xl border border-gray-200 bg-gray-50 text-sm text-gray-400">
        Not enough session data for a performance graph yet.
      </div>
    );
  }

  // Group by subject to render one line per subject
  const subjects = Array.from(new Set(valid.map((s) => s.subject_name ?? "Unknown")));
  const multiSubject = subjects.length > 1;

  // Build chart data: one entry per session, keyed by date label
  const chartData = valid.map((s) => {
    const d = new Date(s.completed_at!);
    const label = d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
    const entry: Record<string, string | number> = {
      date: label,
      fullDate: s.completed_at!,
    };
    if (multiSubject) {
      entry[s.subject_name ?? "Unknown"] = s.percentage!;
    } else {
      entry["Score"] = s.percentage!;
    }
    return entry;
  });

  const lines = multiSubject ? subjects : ["Score"];

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="mb-1 font-semibold">Performance Over Time</h3>
      <p className="mb-4 text-xs text-gray-400">Score % per completed session</p>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            {lines.map((name, i) => (
              <linearGradient
                key={name}
                id={`grad-${i}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="5%" stopColor={SUBJECT_COLORS[i % SUBJECT_COLORS.length]} stopOpacity={0.25} />
                <stop offset="95%" stopColor={SUBJECT_COLORS[i % SUBJECT_COLORS.length]} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              background: "#fff",
              border: "1px solid #e2e8f0",
              borderRadius: "10px",
              fontSize: 12,
            }}
            formatter={(value: number | undefined, name: string | undefined) => [`${value ?? "—"}%`, name ?? ""]}
          />
          {lines.length > 1 && (
            <Legend
              wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
              iconType="circle"
            />
          )}
          <ReferenceLine y={50} stroke="#fca5a5" strokeDasharray="4 4" label={{ value: "50%", fontSize: 10, fill: "#ef4444" }} />
          {lines.map((name, i) => (
            <Area
              key={name}
              type="monotone"
              dataKey={name}
              stroke={SUBJECT_COLORS[i % SUBJECT_COLORS.length]}
              strokeWidth={2.5}
              fill={`url(#grad-${i})`}
              dot={{ r: 4, fill: SUBJECT_COLORS[i % SUBJECT_COLORS.length], strokeWidth: 0 }}
              activeDot={{ r: 6 }}
              connectNulls
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Detailed child progress (preserved from original, unchanged) ──────────────

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
      {/* RI hero */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <p className="mb-1 text-sm text-gray-500">Readiness Index</p>
        <div className="mb-2 flex items-end gap-4">
          <p className={cn("text-4xl font-black", riColor(ri.readiness_index))}>
            {ri.readiness_index}%
          </p>
          <div className="mb-1 flex-1">
            <ProgressBar value={ri.readiness_index} color={riBarColor(ri.readiness_index)} />
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

      {/* Performance line chart */}
      {data.recent_sessions.length > 0 && (
        <PerformanceLineChart sessions={data.recent_sessions} />
      )}

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

// ── Tab Navigation ────────────────────────────────────────────────────────────

type Tab = "overview" | "report" | "alerts";

function TabBar({
  active,
  onChange,
  unreadAlerts,
}: {
  active: Tab;
  onChange: (t: Tab) => void;
  unreadAlerts: number;
}) {
  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "report", label: "Weekly Report" },
    { id: "alerts", label: "Alerts" },
  ];

  return (
    <div className="mb-6 flex gap-1 rounded-xl border border-gray-200 bg-gray-50 p-1">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={cn(
            "relative flex-1 rounded-lg py-2 text-sm font-medium transition-colors",
            active === t.id
              ? "bg-white shadow-sm text-gray-900"
              : "text-gray-500 hover:text-gray-700",
          )}
        >
          {t.label}
          {t.id === "alerts" && unreadAlerts > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              {unreadAlerts}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ParentDashboardPage() {
  const [parentId, setParentId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  // Children & progress
  const [children, setChildren] = useState<ParentChild[]>([]);
  const [loadingChildren, setLoadingChildren] = useState(true);

  // Family dashboard
  const [familyDashboard, setFamilyDashboard] = useState<FamilyDashboard | null>(null);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [childData, setChildData] = useState<DashboardData | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(false);

  // Report
  const [report, setReport] = useState<WeeklyFamilyReport | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);

  // Alerts
  const [alerts, setAlerts] = useState<ParentAlert[]>([]);
  const unreadAlerts = alerts.filter((a) => !a.is_read).length;

  // Tab
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  // ── Init ──────────────────────────────────────────────────────────────────

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(async ({ data: session }) => {
      const user = session?.session?.user;
      const accessToken = session?.session?.access_token;
      if (!user || !accessToken) return;

      setParentId(user.id);
      setToken(accessToken);

      try {
        const [kids, family, alertList] = await Promise.all([
          getParentChildren(user.id, accessToken),
          getParentFamilyDashboard(user.id, accessToken).catch(() => null),
          getParentAlerts(user.id, accessToken).catch(() => []),
        ]);

        setChildren(kids);
        setFamilyDashboard(family);
        setAlerts(alertList);

        if (kids.length > 0) setSelectedChildId(kids[0].id);
      } finally {
        setLoadingChildren(false);
      }
    });
  }, []);

  // ── Load child detail ──────────────────────────────────────────────────────

  useEffect(() => {
    if (!parentId || !token || !selectedChildId) return;
    setLoadingProgress(true);
    setChildData(null);
    getChildProgress(parentId, selectedChildId, undefined, token)
      .then(setChildData)
      .catch(() => setChildData(null))
      .finally(() => setLoadingProgress(false));
  }, [parentId, token, selectedChildId]);

  // ── Load report when tab switches ─────────────────────────────────────────

  useEffect(() => {
    if (activeTab !== "report" || !parentId || !token || report) return;
    setLoadingReport(true);
    getParentReport(parentId, token)
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoadingReport(false));
  }, [activeTab, parentId, token, report]);

  const handleRegenerate = useCallback(async () => {
    if (!parentId || !token) return;
    setLoadingReport(true);
    try {
      const r = await generateParentReport(parentId, token);
      setReport(r);
    } finally {
      setLoadingReport(false);
    }
  }, [parentId, token]);

  const handleMarkAllRead = useCallback(async () => {
    if (!parentId || !token) return;
    await markAllAlertsRead(parentId, token).catch(() => {});
    setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
  }, [parentId, token]);

  // ── Derived ───────────────────────────────────────────────────────────────

  const selectedChild = children.find((c) => c.id === selectedChildId);
  const familyChild = familyDashboard?.children.find(
    (c) => c.student_id === selectedChildId,
  );

  // ── Render ────────────────────────────────────────────────────────────────

  if (loadingChildren) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Parent Command Center</h1>
        <p className="text-sm text-gray-500">
          Monitor your family&apos;s exam preparation
        </p>
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
              // Refresh family dashboard
              if (parentId && token) {
                getParentFamilyDashboard(parentId, token)
                  .then(setFamilyDashboard)
                  .catch(() => {});
              }
            }}
          />
        </div>
      )}

      {children.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <p>No children linked yet.</p>
          <p className="mt-1 text-sm">
            Enter your child&apos;s student email above to get started.
          </p>
        </div>
      ) : (
        <>
          {/* Tab navigation */}
          <TabBar
            active={activeTab}
            onChange={setActiveTab}
            unreadAlerts={unreadAlerts}
          />

          {/* ── OVERVIEW TAB ─────────────────────────────────────────────── */}
          {activeTab === "overview" && (
            <div className="space-y-8">
              {/* Family summary */}
              {familyDashboard && (
                <section>
                  <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-400">
                    Family Summary — This Week
                  </h2>
                  <FamilySummarySection data={familyDashboard} />
                </section>
              )}

              {/* Child cards */}
              {familyDashboard && familyDashboard.children.length > 0 && (
                <section>
                  <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-400">
                    Your Children
                  </h2>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {familyDashboard.children.map((child) => (
                      <ChildCard
                        key={child.student_id}
                        child={child}
                        isSelected={selectedChildId === child.student_id}
                        onClick={() => setSelectedChildId(child.student_id)}
                      />
                    ))}
                  </div>
                </section>
              )}

              {/* Selected child detail */}
              {selectedChild && (
                <section>
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
                      {selectedChild.name} — Detailed Progress
                    </h2>
                    {/* Child tabs if multiple children */}
                    {children.length > 1 && (
                      <div className="flex gap-2 overflow-x-auto">
                        {children.map((c) => (
                          <button
                            key={c.id}
                            onClick={() => setSelectedChildId(c.id)}
                            className={cn(
                              "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
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
                  </div>

                  {/* Goals + Progress side by side on large screens */}
                  <div className="grid gap-6 lg:grid-cols-4">
                    <div className="lg:col-span-3">
                      {loadingProgress ? (
                        <div className="py-12 text-center text-gray-400">
                          Loading progress…
                        </div>
                      ) : childData ? (
                        <ChildProgress
                          data={childData}
                          childName={selectedChild.name}
                        />
                      ) : null}
                    </div>

                    {/* Goal tracker sidebar */}
                    {parentId && token && familyChild && (
                      <div className="space-y-4">
                        <GoalTracker
                          child={familyChild}
                          parentId={parentId}
                          token={token}
                        />
                      </div>
                    )}
                  </div>
                </section>
              )}
            </div>
          )}

          {/* ── REPORT TAB ───────────────────────────────────────────────── */}
          {activeTab === "report" && (
            <div>
              {loadingReport ? (
                <div className="py-12 text-center text-gray-400">
                  Generating report…
                </div>
              ) : report ? (
                <WeeklyReport
                  report={report}
                  onRegenerate={handleRegenerate}
                  loading={loadingReport}
                />
              ) : (
                <div className="py-12 text-center">
                  <p className="text-gray-400">No report generated yet.</p>
                  <button
                    onClick={handleRegenerate}
                    className="mt-4 rounded-lg bg-gray-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-gray-700"
                  >
                    Generate Report
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ── ALERTS TAB ───────────────────────────────────────────────── */}
          {activeTab === "alerts" && (
            <div className="max-w-2xl">
              <AlertsPanel alerts={alerts} onMarkAllRead={handleMarkAllRead} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
