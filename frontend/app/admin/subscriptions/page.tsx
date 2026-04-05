"use client";

import { useEffect, useState } from "react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Subscription = {
  id: string;
  tier: string;
  status: string;
  amount_usd: number | null;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
  student_id: string;
  student_name: string;
  student_email: string;
};

const TIER_PRICE: Record<string, number> = {
  standard: 5,
  bundle: 12,
  all_subjects: 18,
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-50 text-green-700 border-green-200",
  cancelled: "bg-muted text-muted-foreground border-border",
  past_due: "bg-orange-50 text-orange-700 border-orange-200",
  expired: "bg-red-50 text-red-600 border-red-200",
};

const TIER_COLORS: Record<string, string> = {
  standard: "bg-blue-50 text-blue-700 border-blue-200",
  bundle: "bg-violet-50 text-violet-700 border-violet-200",
  all_subjects: "bg-primary/10 text-primary border-primary/20",
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function Badge({ label, colors }: { label: string; colors: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border capitalize ${colors}`}>
      {label.replace(/_/g, " ")}
    </span>
  );
}

export default function AdminSubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterTier, setFilterTier] = useState("all");

  useEffect(() => {
    setLoading(true);
    fetch(`${BACKEND}/admin/subscriptions?limit=100`)
      .then((r) => r.json())
      .then((data) => {
        setSubscriptions(data.subscriptions ?? []);
        setTotal(data.total ?? 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = subscriptions.filter((s) => {
    if (filterStatus !== "all" && s.status !== filterStatus) return false;
    if (filterTier !== "all" && s.tier !== filterTier) return false;
    return true;
  });

  // Summary stats
  const active = subscriptions.filter((s) => s.status === "active");
  const mrr = active.reduce((sum, s) => sum + (s.amount_usd ?? TIER_PRICE[s.tier] ?? 0), 0);
  const tierBreakdown = Object.entries(
    active.reduce((acc, s) => {
      acc[s.tier] = (acc[s.tier] ?? 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).sort((a, b) => b[1] - a[1]);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse max-w-5xl">
        <div className="h-8 w-48 bg-muted rounded-lg" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <div key={i} className="h-20 bg-muted rounded-2xl" />)}
        </div>
        <div className="h-64 bg-muted rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-foreground">Subscriptions</h1>
        <p className="text-sm text-muted-foreground mt-0.5">{total} total subscriptions</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-2xl p-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1.5">Monthly Recurring Revenue</p>
          <p className="text-2xl font-semibold text-foreground">
            ${mrr.toFixed(2)}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">{active.length} active subscriptions</p>
        </div>
        <div className="bg-card border border-border rounded-2xl p-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2.5">Plan Breakdown</p>
          <div className="space-y-1.5">
            {tierBreakdown.length === 0 ? (
              <p className="text-sm text-muted-foreground">No active subscriptions</p>
            ) : (
              tierBreakdown.map(([t, count]) => (
                <div key={t} className="flex items-center justify-between">
                  <Badge label={t} colors={TIER_COLORS[t] ?? "bg-muted text-muted-foreground border-border"} />
                  <span className="text-sm font-medium text-foreground">{count}</span>
                </div>
              ))
            )}
          </div>
        </div>
        <div className="bg-card border border-border rounded-2xl p-4">
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2.5">Status Breakdown</p>
          <div className="space-y-1.5">
            {(["active", "cancelled", "past_due", "expired"] as const).map((s) => {
              const count = subscriptions.filter((sub) => sub.status === s).length;
              return (
                <div key={s} className="flex items-center justify-between">
                  <Badge label={s} colors={STATUS_COLORS[s]} />
                  <span className="text-sm font-medium text-foreground">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-2">
        <div className="inline-flex items-center gap-1 border border-border rounded-lg bg-card p-1">
          {["all", "active", "cancelled", "past_due", "expired"].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-all ${
                filterStatus === s
                  ? "bg-foreground text-background shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {s === "all" ? "All status" : s.replace(/_/g, " ")}
            </button>
          ))}
        </div>
        <div className="inline-flex items-center gap-1 border border-border rounded-lg bg-card p-1">
          {["all", "standard", "bundle", "all_subjects"].map((t) => (
            <button
              key={t}
              onClick={() => setFilterTier(t)}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-all ${
                filterTier === t
                  ? "bg-foreground text-background shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t === "all" ? "All plans" : t.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-2xl overflow-hidden">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-2 text-center">
            <svg className="w-10 h-10 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
            </svg>
            <p className="text-sm text-muted-foreground">No subscriptions match the current filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-3 px-4 font-medium">Student</th>
                  <th className="py-3 px-4 font-medium">Plan</th>
                  <th className="py-3 px-4 font-medium">Status</th>
                  <th className="py-3 px-4 font-medium hidden md:table-cell">Amount</th>
                  <th className="py-3 px-4 font-medium hidden lg:table-cell">Period</th>
                  <th className="py-3 px-4 font-medium hidden lg:table-cell">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((sub) => (
                  <tr key={sub.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                          <span className="text-xs font-semibold text-primary">
                            {(sub.student_name || "?")[0].toUpperCase()}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-foreground truncate max-w-[130px]">
                            {sub.student_name || "Unknown"}
                          </p>
                          <p className="text-xs text-muted-foreground truncate max-w-[130px]">
                            {sub.student_email}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        label={sub.tier}
                        colors={TIER_COLORS[sub.tier] ?? "bg-muted text-muted-foreground border-border"}
                      />
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        label={sub.status}
                        colors={STATUS_COLORS[sub.status] ?? "bg-muted text-muted-foreground border-border"}
                      />
                    </td>
                    <td className="py-3 px-4 text-muted-foreground hidden md:table-cell">
                      {sub.amount_usd != null
                        ? `$${Number(sub.amount_usd).toFixed(2)}/mo`
                        : TIER_PRICE[sub.tier]
                          ? `$${TIER_PRICE[sub.tier]}/mo`
                          : "—"}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs hidden lg:table-cell">
                      {sub.period_start && sub.period_end
                        ? `${formatDate(sub.period_start)} → ${formatDate(sub.period_end)}`
                        : "—"}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs hidden lg:table-cell">
                      {formatDate(sub.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Table footer */}
        <div className="px-4 py-3 border-t border-border bg-muted/20 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Showing {filtered.length} of {total} subscriptions
          </p>
          {active.length > 0 && (
            <p className="text-xs font-medium text-foreground">
              MRR: <span className="text-primary">${mrr.toFixed(2)}</span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
