"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Stats = {
  students: number;
  papers: number;
  questions: number;
  flagged_attempts: number;
  active_subscriptions: number;
  papers_processing: number;
  papers_error: number;
  monthly_revenue_usd: number;
};

type Paper = {
  id: string;
  subject_name: string;
  year: number;
  paper_number: number;
  status: string;
  created_at: string;
};

function StatCard({
  label,
  value,
  sub,
  accent,
  href,
  icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
  href?: string;
  icon: React.ReactNode;
}) {
  const content = (
    <div className="bg-card border border-border rounded-2xl p-5 flex items-start gap-4 hover:border-primary/30 transition-colors group">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${accent ?? "bg-muted"}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-2xl font-semibold text-foreground leading-none">{value}</p>
        <p className="text-sm text-muted-foreground mt-1">{label}</p>
        {sub && <p className="text-xs text-muted-foreground/70 mt-0.5">{sub}</p>}
      </div>
      {href && (
        <svg className="w-4 h-4 text-muted-foreground ml-auto mt-0.5 group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      )}
    </div>
  );
  return href ? <Link href={href}>{content}</Link> : content;
}

function StatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    ready: "bg-green-500",
    processing: "bg-yellow-400 animate-pulse",
    error: "bg-red-500",
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${map[status] ?? "bg-gray-400"}`} />;
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

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`${BACKEND}/admin/stats`).then((r) => r.json()),
      fetch(`${BACKEND}/admin/papers`).then((r) => r.json()),
    ])
      .then(([statsData, papersData]) => {
        setStats(statsData);
        setPapers(Array.isArray(papersData) ? papersData.slice(0, 8) : []);
      })
      .catch(() => setError("Could not load admin data. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-muted rounded-lg" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-muted rounded-2xl" />
          ))}
        </div>
        <div className="h-64 bg-muted rounded-2xl" />
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
      </div>
    );
  }

  const STAT_CARDS = [
    {
      label: "Total Students",
      value: stats?.students ?? 0,
      icon: (
        <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      ),
      accent: "bg-blue-50",
      href: "/admin/users",
    },
    {
      label: "Active Subscriptions",
      value: stats?.active_subscriptions ?? 0,
      sub: `$${stats?.monthly_revenue_usd ?? 0}/mo MRR`,
      icon: (
        <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
        </svg>
      ),
      accent: "bg-primary/10",
      href: "/admin/subscriptions",
    },
    {
      label: "Papers",
      value: stats?.papers ?? 0,
      sub: `${stats?.questions ?? 0} questions extracted`,
      icon: (
        <svg className="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
      ),
      accent: "bg-violet-50",
      href: "/admin/papers",
    },
    {
      label: "Flagged Attempts",
      value: stats?.flagged_attempts ?? 0,
      sub: stats?.flagged_attempts ? "Needs review" : "All clear",
      icon: (
        <svg className="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5" />
        </svg>
      ),
      accent: stats?.flagged_attempts ? "bg-orange-50" : "bg-muted",
      href: "/admin/flagged",
    },
  ];

  return (
    <div className="space-y-7 max-w-5xl">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold text-foreground">Overview</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Platform health at a glance</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      {/* Pipeline health + recent papers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Pipeline health */}
        <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Extraction Pipeline</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                Ready
              </div>
              <span className="text-sm font-medium text-foreground">
                {(stats?.papers ?? 0) - (stats?.papers_processing ?? 0) - (stats?.papers_error ?? 0)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse inline-block" />
                Processing
              </div>
              <span className="text-sm font-medium text-foreground">{stats?.papers_processing ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
                Error
              </div>
              <span className="text-sm font-medium text-foreground">{stats?.papers_error ?? 0}</span>
            </div>
          </div>
          <div className="pt-2 border-t border-border">
            {stats && stats.papers > 0 ? (
              <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden flex gap-0.5">
                <div
                  className="h-full bg-green-500 rounded-l-full"
                  style={{
                    width: `${((stats.papers - stats.papers_processing - stats.papers_error) / stats.papers) * 100}%`,
                  }}
                />
                <div
                  className="h-full bg-yellow-400"
                  style={{ width: `${(stats.papers_processing / stats.papers) * 100}%` }}
                />
                <div
                  className="h-full bg-red-500 rounded-r-full"
                  style={{ width: `${(stats.papers_error / stats.papers) * 100}%` }}
                />
              </div>
            ) : (
              <div className="w-full h-1.5 bg-muted rounded-full" />
            )}
            <p className="text-xs text-muted-foreground mt-2">
              {stats?.papers ?? 0} papers total
            </p>
          </div>
        </div>

        {/* Recent papers */}
        <div className="lg:col-span-2 bg-card border border-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Recent Papers</h2>
            <Link href="/admin/papers" className="text-xs text-primary hover:underline">
              View all →
            </Link>
          </div>
          {papers.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
              No papers uploaded yet
            </div>
          ) : (
            <div className="space-y-1">
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
                  <span className="text-xs text-muted-foreground shrink-0">{relativeTime(p.created_at)}</span>
                  {p.status === "ready" && (
                    <Link
                      href={`/admin/papers/${p.id}/questions`}
                      className="text-xs text-primary font-medium hover:underline shrink-0"
                    >
                      Review
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3">Quick Actions</h2>
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
            {(stats?.flagged_attempts ?? 0) > 0 && (
              <span className="ml-0.5 bg-orange-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {stats?.flagged_attempts}
              </span>
            )}
          </Link>
          <Link
            href="/admin/subscriptions"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-card border border-border text-foreground text-xs font-medium rounded-lg hover:bg-muted/40 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
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
    </div>
  );
}
