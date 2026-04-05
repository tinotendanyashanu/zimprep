"use client";

import { useEffect, useRef, useState } from "react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Student = {
  id: string;
  name: string;
  email: string;
  level: string;
  exam_board: "zimsec" | "cambridge";
  subscription_tier: string;
  created_at: string;
};

const TIER_COLORS: Record<string, string> = {
  starter: "bg-muted text-muted-foreground border-border",
  standard: "bg-blue-50 text-blue-700 border-blue-200",
  bundle: "bg-violet-50 text-violet-700 border-violet-200",
  all_subjects: "bg-primary/10 text-primary border-primary/20",
};

const LEVEL_LABELS: Record<string, string> = {
  Grade7: "Grade 7",
  O: "O Level",
  A: "A Level",
  IGCSE: "IGCSE",
  AS_Level: "AS Level",
  A_Level: "A Level",
};

const TIERS = ["all", "starter", "standard", "bundle", "all_subjects"];

function TierBadge({ tier }: { tier: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border capitalize ${
        TIER_COLORS[tier] ?? "bg-muted text-muted-foreground border-border"
      }`}
    >
      {tier.replace(/_/g, " ")}
    </span>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function AdminUsersPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [tier, setTier] = useState("all");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<Student | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const LIMIT = 20;

  function fetchStudents(q: string, t: string, p: number) {
    setLoading(true);
    const params = new URLSearchParams({
      limit: String(LIMIT),
      offset: String(p * LIMIT),
    });
    if (q.trim()) params.set("search", q.trim());
    if (t !== "all") params.set("tier", t);

    fetch(`${BACKEND}/admin/students?${params}`)
      .then((r) => r.json())
      .then((data) => {
        setStudents(data.students ?? []);
        setTotal(data.total ?? 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchStudents(search, tier, page);
  }, [tier, page]); // eslint-disable-line react-hooks/exhaustive-deps

  function onSearchChange(v: string) {
    setSearch(v);
    setPage(0);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchStudents(v, tier, 0), 300);
  }

  const totalPages = Math.ceil(total / LIMIT);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Users</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{total} students registered</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.75}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            placeholder="Search by name or email…"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3.5 py-2 rounded-lg border border-border bg-card text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div className="inline-flex items-center gap-1 border border-border rounded-lg bg-card p-1">
          {TIERS.map((t) => (
            <button
              key={t}
              onClick={() => { setTier(t); setPage(0); }}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-all ${
                tier === t
                  ? "bg-foreground text-background shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t === "all" ? "All tiers" : t.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3 animate-pulse">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-10 bg-muted rounded-lg" />
            ))}
          </div>
        ) : students.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-2 text-center">
            <svg className="w-10 h-10 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
            </svg>
            <p className="text-sm text-muted-foreground">No students found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-3 px-4 font-medium">Name</th>
                  <th className="py-3 px-4 font-medium hidden sm:table-cell">Email</th>
                  <th className="py-3 px-4 font-medium hidden md:table-cell">Level</th>
                  <th className="py-3 px-4 font-medium hidden md:table-cell">Board</th>
                  <th className="py-3 px-4 font-medium">Plan</th>
                  <th className="py-3 px-4 font-medium hidden lg:table-cell">Joined</th>
                  <th className="py-3 px-4 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {students.map((s) => (
                  <tr key={s.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4 font-medium text-foreground">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                          <span className="text-xs font-semibold text-primary">
                            {(s.name || "?")[0].toUpperCase()}
                          </span>
                        </div>
                        <span className="truncate max-w-[120px]">{s.name || "—"}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground hidden sm:table-cell truncate max-w-[180px]">
                      {s.email}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground hidden md:table-cell">
                      {LEVEL_LABELS[s.level] ?? s.level ?? "—"}
                    </td>
                    <td className="py-3 px-4 hidden md:table-cell">
                      <span className="text-xs capitalize text-muted-foreground">{s.exam_board ?? "—"}</span>
                    </td>
                    <td className="py-3 px-4">
                      <TierBadge tier={s.subscription_tier ?? "starter"} />
                    </td>
                    <td className="py-3 px-4 text-muted-foreground text-xs hidden lg:table-cell">
                      {s.created_at ? formatDate(s.created_at) : "—"}
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => setSelected(s)}
                        className="text-xs text-primary font-medium hover:underline"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/20">
            <p className="text-xs text-muted-foreground">
              {page * LIMIT + 1}–{Math.min((page + 1) * LIMIT, total)} of {total}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="w-8 h-8 flex items-center justify-center rounded-lg border border-border text-sm hover:bg-muted/40 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                ‹
              </button>
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const pg = page < 3 ? i : page - 2 + i;
                if (pg >= totalPages) return null;
                return (
                  <button
                    key={pg}
                    onClick={() => setPage(pg)}
                    className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs font-medium transition ${
                      pg === page
                        ? "bg-primary text-primary-foreground"
                        : "border border-border hover:bg-muted/40"
                    }`}
                  >
                    {pg + 1}
                  </button>
                );
              })}
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="w-8 h-8 flex items-center justify-center rounded-lg border border-border text-sm hover:bg-muted/40 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                ›
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Student detail drawer */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-end">
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setSelected(null)}
          />
          <div className="relative z-10 w-full max-w-sm h-full bg-card border-l border-border shadow-2xl flex flex-col animate-in slide-in-from-bottom-4">
            {/* Drawer header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-semibold text-primary">
                    {(selected.name || "?")[0].toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">{selected.name || "Unknown"}</p>
                  <p className="text-xs text-muted-foreground">{selected.email}</p>
                </div>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-muted/40 transition text-muted-foreground"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Drawer body */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Plan", value: <TierBadge tier={selected.subscription_tier ?? "starter"} /> },
                  { label: "Level", value: LEVEL_LABELS[selected.level] ?? selected.level ?? "—" },
                  { label: "Exam Board", value: <span className="capitalize">{selected.exam_board ?? "—"}</span> },
                  { label: "Joined", value: selected.created_at ? formatDate(selected.created_at) : "—" },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-muted/40 rounded-xl p-3">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">{label}</p>
                    <p className="text-sm font-medium text-foreground">{value}</p>
                  </div>
                ))}
              </div>

              <div className="bg-muted/40 rounded-xl p-3">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-1">Student ID</p>
                <p className="text-xs text-muted-foreground font-mono break-all">{selected.id}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
