"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type TopSubject = {
  name: string;
  level: string;
  exam_board: string;
  question_count: number;
};

type Stats = {
  // Core
  students: number;
  papers: number;
  questions: number;
  subjects: number;
  // Pipeline
  papers_processing: number;
  papers_error: number;
  // Moderation
  flagged_attempts: number;
  diagram_review_count: number;
  // Revenue
  active_subscriptions: number;
  monthly_revenue_usd: number;
  paid_students: number;
  conversion_rate: number;
  new_students_this_week: number;
  // Engagement
  sessions_today: number;
  sessions_this_week: number;
  completed_sessions: number;
  // AI Marking
  total_attempts: number;
  marked_attempts: number;
  avg_ai_score: number | null;
  mark_rate: number;
  // Content
  top_subjects: TopSubject[];
  tier_distribution: Record<string, number>;
};

type Paper = {
  id: string;
  subject_name: string;
  year: number;
  paper_number: number;
  status: string;
  created_at: string;
};

// ── Shared components ──────────────────────────────────────────────────────────

function MetricCard({
  label,
  value,
  sub,
  accent,
  href,
  icon,
  trend,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
  href?: string;
  icon: React.ReactNode;
  trend?: { direction: "up" | "down" | "neutral"; label: string };
}) {
  const content = (
    <div className="bg-card border border-border rounded-2xl p-5 flex flex-col gap-3 hover:border-primary/30 transition-colors group h-full">
      <div className="flex items-start justify-between">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${accent ?? "bg-muted"}`}>
          {icon}
        </div>
        {trend && (
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
              trend.direction === "up"
                ? "bg-green-50 text-green-700"
                : trend.direction === "down"
                ? "bg-red-50 text-red-600"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "—"} {trend.label}
          </span>
        )}
      </div>
      <div>
        <p className="text-2xl font-semibold text-foreground leading-none tracking-tight">{value}</p>
        <p className="text-sm text-muted-foreground mt-1">{label}</p>
        {sub && <p className="text-[11px] text-muted-foreground/70 mt-0.5">{sub}</p>}
      </div>
      {href && (
        <div className="mt-auto pt-1">
          <span className="text-xs text-primary font-medium group-hover:underline">View details →</span>
        </div>
      )}
    </div>
  );
  return href ? <Link href={href} className="block h-full">{content}</Link> : content;
}

function KpiRow({
  label,
  value,
  bar,
  barColor,
  note,
}: {
  label: string;
  value: string;
  bar?: number; // 0–100
  barColor?: string;
  note?: string;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-foreground">{label}</span>
        <span className="text-sm font-semibold text-foreground">{value}</span>
      </div>
      {bar !== undefined && (
        <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor ?? "bg-primary"}`}
            style={{ width: `${Math.min(100, bar)}%` }}
          />
        </div>
      )}
      {note && <p className="text-[10px] text-muted-foreground">{note}</p>}
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    ready: "bg-green-500",
    processing: "bg-yellow-400 animate-pulse",
    error: "bg-red-500",
  };
  return <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${map[status] ?? "bg-gray-400"}`} />;
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const TIER_ORDER = ["starter", "standard", "bundle", "all_subjects"];
const TIER_COLORS: Record<string, string> = {
  starter: "bg-muted-foreground/30",
  standard: "bg-blue-500",
  bundle: "bg-violet-500",
  all_subjects: "bg-primary",
};
const TIER_LABELS: Record<string, string> = {
  starter: "Starter",
  standard: "Standard",
  bundle: "Bundle",
  all_subjects: "All Subjects",
};

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<Date>(new Date());
  const [mcqResolving, setMcqResolving] = useState(false);
  const [mcqResult, setMcqResult] = useState<{ queued: number; papers?: number; message: string } | null>(null);
  const [auditing, setAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState<{ scanned?: number; message: string } | null>(null);

  function load() {
    setLoading(true);
    Promise.all([
      fetch(`${BACKEND}/admin/stats`).then((r) => r.json()),
      fetch(`${BACKEND}/admin/papers`).then((r) => r.json()),
    ])
      .then(([statsData, papersData]) => {
        setStats(statsData);
        setPapers(Array.isArray(papersData) ? papersData.slice(0, 8) : []);
        setRefreshedAt(new Date());
      })
      .catch(() => setError("Could not load admin data. Is the backend running?"))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function handleAuditQuestions() {
    setAuditing(true);
    setAuditResult(null);
    try {
      const res = await fetch(`${BACKEND}/admin/questions/audit`, { method: "POST" });
      const data = await res.json();
      setAuditResult(data);
    } catch {
      setAuditResult({ message: "Request failed — is the backend running?" });
    } finally {
      setAuditing(false);
    }
  }

  async function handleResolveMcqAnswers() {
    setMcqResolving(true);
    setMcqResult(null);
    try {
      const res = await fetch(`${BACKEND}/admin/mcq/resolve-answers`, { method: "POST" });
      const data = await res.json();
      setMcqResult(data);
    } catch {
      setMcqResult({ queued: 0, message: "Request failed — is the backend running?" });
    } finally {
      setMcqResolving(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse max-w-6xl">
        <div className="flex items-center justify-between">
          <div className="h-7 w-32 bg-muted rounded-lg" />
          <div className="h-7 w-20 bg-muted rounded-lg" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-32 bg-muted rounded-2xl" />)}
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-muted rounded-2xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="h-48 bg-muted rounded-2xl" />
          <div className="lg:col-span-2 h-48 bg-muted rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-center">
        <div className="w-12 h-12 rounded-2xl bg-red-50 flex items-center justify-center">
          <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <p className="text-sm font-medium text-foreground">Backend unreachable</p>
        <p className="text-xs text-muted-foreground max-w-xs">{error}</p>
        <button
          onClick={load}
          className="text-xs text-primary hover:underline mt-1"
        >
          Try again
        </button>
      </div>
    );
  }

  const s = stats!;
  const papersReady = s.papers - s.papers_processing - s.papers_error;

  // Tier distribution total for bars
  const tierTotal = Object.values(s.tier_distribution ?? {}).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-8 max-w-6xl">

      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Overview</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Last updated {refreshedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </p>
        </div>
        <button
          onClick={load}
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition px-3 py-1.5 rounded-lg border border-border hover:bg-muted/40"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Refresh
        </button>
      </div>

      {/* ── Row 1: Core platform metrics ─────────────────────────────────── */}
      <section>
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Platform</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            label="Total Students"
            value={s.students.toLocaleString()}
            sub={`+${s.new_students_this_week} this week`}
            accent="bg-blue-50"
            href="/admin/users"
            trend={s.new_students_this_week > 0 ? { direction: "up", label: `${s.new_students_this_week} new` } : undefined}
            icon={
              <svg className="w-4.5 h-4.5 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
              </svg>
            }
          />
          <MetricCard
            label="Monthly Revenue"
            value={`$${s.monthly_revenue_usd.toFixed(2)}`}
            sub={`${s.active_subscriptions} active subscriptions`}
            accent="bg-primary/10"
            href="/admin/subscriptions"
            icon={
              <svg className="w-4.5 h-4.5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <MetricCard
            label="Papers"
            value={s.papers.toLocaleString()}
            sub={`${s.questions.toLocaleString()} questions across ${s.subjects} subjects`}
            accent="bg-violet-50"
            href="/admin/papers"
            icon={
              <svg className="w-4.5 h-4.5 text-violet-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            }
          />
          <MetricCard
            label="Flagged Attempts"
            value={s.flagged_attempts}
            sub={s.flagged_attempts === 0 ? "All disputes resolved" : "Awaiting manual review"}
            accent={s.flagged_attempts > 0 ? "bg-orange-50" : "bg-muted"}
            href="/admin/flagged"
            trend={s.flagged_attempts > 0 ? { direction: "down", label: "Needs review" } : { direction: "neutral", label: "Clear" }}
            icon={
              <svg className={`w-4.5 h-4.5 ${s.flagged_attempts > 0 ? "text-orange-500" : "text-muted-foreground"}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5" />
              </svg>
            }
          />
          <MetricCard
            label="Diagram Review"
            value={s.diagram_review_count ?? 0}
            sub={(s.diagram_review_count ?? 0) === 0 ? "All diagrams extracted" : "Questions hidden from students"}
            accent={(s.diagram_review_count ?? 0) > 0 ? "bg-amber-50" : "bg-muted"}
            href="/admin/diagrams"
            trend={(s.diagram_review_count ?? 0) > 0 ? { direction: "down", label: "Needs image" } : { direction: "neutral", label: "Clear" }}
            icon={
              <svg className={`w-4.5 h-4.5 ${(s.diagram_review_count ?? 0) > 0 ? "text-amber-500" : "text-muted-foreground"}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
              </svg>
            }
          />
        </div>
      </section>

      {/* ── Row 2: KPI metrics ───────────────────────────────────────────── */}
      <section>
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Key Performance Indicators</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

          {/* Paid conversion */}
          <MetricCard
            label="Paid Conversion"
            value={`${s.conversion_rate}%`}
            sub={`${s.paid_students} of ${s.students} students on paid plan`}
            accent="bg-emerald-50"
            icon={
              <svg className="w-4.5 h-4.5 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
              </svg>
            }
          />

          {/* Sessions this week */}
          <MetricCard
            label="Sessions This Week"
            value={s.sessions_this_week.toLocaleString()}
            sub={`${s.sessions_today} today · ${s.completed_sessions.toLocaleString()} completed all-time`}
            accent="bg-sky-50"
            icon={
              <svg className="w-4.5 h-4.5 text-sky-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
              </svg>
            }
            trend={s.sessions_today > 0 ? { direction: "up", label: `${s.sessions_today} today` } : undefined}
          />

          {/* AI Marking throughput */}
          <MetricCard
            label="Attempts Marked"
            value={s.marked_attempts.toLocaleString()}
            sub={`${s.mark_rate}% mark rate · ${s.total_attempts.toLocaleString()} total`}
            accent="bg-indigo-50"
            icon={
              <svg className="w-4.5 h-4.5 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
              </svg>
            }
          />

          {/* Avg AI Score */}
          <MetricCard
            label="Avg AI Score"
            value={s.avg_ai_score !== null ? `${s.avg_ai_score}%` : "—"}
            sub={
              s.avg_ai_score === null
                ? "No marked attempts yet"
                : s.avg_ai_score >= 70
                ? "Students performing well"
                : s.avg_ai_score >= 50
                ? "Moderate performance"
                : "Students need support"
            }
            accent={
              s.avg_ai_score === null
                ? "bg-muted"
                : s.avg_ai_score >= 70
                ? "bg-green-50"
                : s.avg_ai_score >= 50
                ? "bg-yellow-50"
                : "bg-red-50"
            }
            icon={
              <svg
                className={`w-4.5 h-4.5 ${
                  s.avg_ai_score === null
                    ? "text-muted-foreground"
                    : s.avg_ai_score >= 70
                    ? "text-green-600"
                    : s.avg_ai_score >= 50
                    ? "text-yellow-600"
                    : "text-red-500"
                }`}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.75}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
            }
          />
        </div>
      </section>

      {/* ── Row 3: Breakdown panels ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Tier distribution */}
        <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Plan Distribution</h2>
            <Link href="/admin/subscriptions" className="text-xs text-primary hover:underline">View →</Link>
          </div>
          <div className="space-y-3">
            {TIER_ORDER.map((tier) => {
              const count = s.tier_distribution?.[tier] ?? 0;
              const pct = tierTotal > 0 ? (count / tierTotal) * 100 : 0;
              return (
                <div key={tier} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-foreground font-medium">{TIER_LABELS[tier]}</span>
                    <span className="text-xs text-muted-foreground">{count} · {pct.toFixed(0)}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${TIER_COLORS[tier]}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="pt-2 border-t border-border">
            <p className="text-xs text-muted-foreground">
              <span className="font-semibold text-foreground">{s.conversion_rate}%</span> paid conversion
              &nbsp;·&nbsp;
              <span className="font-semibold text-foreground">${s.monthly_revenue_usd.toFixed(2)}</span> MRR
            </p>
          </div>
        </div>

        {/* AI Marking health */}
        <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-foreground">AI Marking Health</h2>
          <div className="space-y-3.5">
            <KpiRow
              label="Mark Rate"
              value={`${s.mark_rate}%`}
              bar={s.mark_rate}
              barColor="bg-indigo-500"
              note={`${s.marked_attempts.toLocaleString()} of ${s.total_attempts.toLocaleString()} attempts processed`}
            />
            <KpiRow
              label="Avg Score"
              value={s.avg_ai_score !== null ? `${s.avg_ai_score}%` : "—"}
              bar={s.avg_ai_score ?? 0}
              barColor={
                s.avg_ai_score === null
                  ? "bg-muted-foreground"
                  : s.avg_ai_score >= 70
                  ? "bg-green-500"
                  : s.avg_ai_score >= 50
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }
              note="Based on sample of up to 500 marked attempts"
            />
            <KpiRow
              label="Flagged (open)"
              value={String(s.flagged_attempts)}
              bar={s.total_attempts > 0 ? (s.flagged_attempts / s.total_attempts) * 100 : 0}
              barColor="bg-orange-400"
              note="Student-disputed marking results"
            />
          </div>
          <div className="pt-2 border-t border-border flex items-center justify-between">
            <p className="text-xs text-muted-foreground">{s.total_attempts.toLocaleString()} total submissions</p>
            {s.flagged_attempts > 0 && (
              <Link href="/admin/flagged" className="text-xs text-orange-600 font-medium hover:underline">
                Review {s.flagged_attempts} →
              </Link>
            )}
          </div>
        </div>

        {/* Content pipeline */}
        <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Content Pipeline</h2>
            <Link href="/admin/papers" className="text-xs text-primary hover:underline">Manage →</Link>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-1.5 border-b border-border">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <span className="w-2 h-2 rounded-full bg-green-500" />Ready
              </div>
              <span className="text-sm font-semibold text-foreground">{papersReady}</span>
            </div>
            <div className="flex items-center justify-between py-1.5 border-b border-border">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />Processing
              </div>
              <span className="text-sm font-semibold text-foreground">{s.papers_processing}</span>
            </div>
            <div className="flex items-center justify-between py-1.5 border-b border-border">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <span className="w-2 h-2 rounded-full bg-red-500" />Error
              </div>
              <span className="text-sm font-semibold text-foreground">{s.papers_error}</span>
            </div>
            <div className="flex items-center justify-between py-1.5">
              <span className="text-sm text-muted-foreground">Subjects</span>
              <span className="text-sm font-semibold text-foreground">{s.subjects}</span>
            </div>
          </div>
          {s.papers > 0 && (
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden flex">
              <div className="h-full bg-green-500" style={{ width: `${(papersReady / s.papers) * 100}%` }} />
              <div className="h-full bg-yellow-400" style={{ width: `${(s.papers_processing / s.papers) * 100}%` }} />
              <div className="h-full bg-red-500" style={{ width: `${(s.papers_error / s.papers) * 100}%` }} />
            </div>
          )}
        </div>
      </div>

      {/* ── Row 4: Top subjects + Recent papers ─────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Top subjects */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Top Subjects by Content</h2>
          </div>
          {s.top_subjects?.length === 0 ? (
            <div className="flex items-center justify-center h-28 text-sm text-muted-foreground">
              No subjects yet
            </div>
          ) : (
            <div className="space-y-3">
              {(s.top_subjects ?? []).map((sub, i) => {
                const maxQ = s.top_subjects[0]?.question_count || 1;
                return (
                  <div key={sub.name + sub.level} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-[10px] font-semibold text-muted-foreground w-4 shrink-0">
                          {i + 1}
                        </span>
                        <p className="text-sm font-medium text-foreground truncate">{sub.name}</p>
                        <span className="text-[10px] text-muted-foreground shrink-0 capitalize">
                          {sub.exam_board} · {sub.level.replace(/_/g, " ")}
                        </span>
                      </div>
                      <span className="text-xs font-semibold text-muted-foreground ml-2 shrink-0">
                        {sub.question_count}q
                      </span>
                    </div>
                    <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary/70 rounded-full"
                        style={{ width: `${(sub.question_count / maxQ) * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent papers */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Recent Papers</h2>
            <Link href="/admin/papers" className="text-xs text-primary hover:underline">View all →</Link>
          </div>
          {papers.length === 0 ? (
            <div className="flex items-center justify-center h-28 text-sm text-muted-foreground">
              No papers uploaded yet
            </div>
          ) : (
            <div className="space-y-0.5">
              {papers.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-3 py-2 px-2.5 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <StatusDot status={p.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {p.subject_name} {p.year} P{p.paper_number}
                    </p>
                  </div>
                  <span className="text-[11px] text-muted-foreground shrink-0">{relativeTime(p.created_at)}</span>
                  {p.status === "ready" && (
                    <Link
                      href={`/admin/papers/${p.id}/questions`}
                      className="text-xs text-primary font-medium hover:underline shrink-0"
                    >
                      Review
                    </Link>
                  )}
                  {p.status === "error" && (
                    <span className="text-xs text-red-500 font-medium shrink-0">Failed</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Quick actions ─────────────────────────────────────────────────── */}
      <div>
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Quick Actions</p>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/admin/papers"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:opacity-90 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Upload Paper
          </Link>
          <Link
            href="/admin/flagged"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-card border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted/40 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5" />
            </svg>
            Review Flagged
            {s.flagged_attempts > 0 && (
              <span className="ml-0.5 bg-orange-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {s.flagged_attempts}
              </span>
            )}
          </Link>
          <Link
            href="/admin/diagrams"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-card border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted/40 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
            </svg>
            Review Diagrams
            {(s.diagram_review_count ?? 0) > 0 && (
              <span className="ml-0.5 bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {s.diagram_review_count}
              </span>
            )}
          </Link>
          <Link
            href="/admin/subscriptions"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-card border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted/40 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            View Revenue
          </Link>
          <Link
            href="/admin/users"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-card border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted/40 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
            </svg>
            Manage Users
          </Link>
        </div>
      </div>

      {/* ── Maintenance tools ─────────────────────────────────────────────── */}
      <div>
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Maintenance</p>
        <div className="bg-card border border-border rounded-2xl p-5 space-y-3">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-foreground">Resolve MCQ Answers</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Backfill correct answers for existing MCQ questions that have no stored answer key.
                One batched Gemini call per paper — runs in the background.
              </p>
            </div>
            <button
              onClick={handleResolveMcqAnswers}
              disabled={mcqResolving}
              className="shrink-0 inline-flex items-center gap-1.5 px-3.5 py-2 bg-card border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted/40 transition disabled:opacity-50"
            >
              {mcqResolving ? (
                <>
                  <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Running…
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Run Now
                </>
              )}
            </button>
          </div>
          {mcqResult && (
            <div className={`text-xs px-3 py-2 rounded-lg border ${mcqResult.queued > 0 ? "bg-green-50 border-green-200 text-green-800" : "bg-muted border-border text-muted-foreground"}`}>
              {mcqResult.message}
            </div>
          )}

          <div className="border-t border-border pt-3 flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-foreground">Audit Question Quality</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Scan all visible questions for missing marks, short text, failed diagrams, or MCQ questions without options.
                Issues are sent to the Review Queue for admin approval.
              </p>
            </div>
            <button
              onClick={handleAuditQuestions}
              disabled={auditing}
              className="shrink-0 inline-flex items-center gap-1.5 px-3.5 py-2 bg-card border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted/40 transition disabled:opacity-50"
            >
              {auditing ? (
                <>
                  <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Scanning…
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                  Run Audit
                </>
              )}
            </button>
          </div>
          {auditResult && (
            <div className={`text-xs px-3 py-2 rounded-lg border ${auditResult.scanned ? "bg-blue-50 border-blue-200 text-blue-800" : "bg-muted border-border text-muted-foreground"}`}>
              {auditResult.message}
              {auditResult.scanned && (
                <Link href="/admin/review" className="ml-2 font-medium underline">Open Review Queue →</Link>
              )}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
