"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Paper = {
  id: string;
  subject_name: string;
  year: number;
  paper_number: number;
  exam_session: string | null;
  status: string;
  created_at: string;
};

const STATUS_COLORS: Record<string, string> = {
  ready: "bg-emerald-50 text-emerald-700 border-emerald-200",
  processing: "bg-blue-50 text-blue-700 border-blue-200",
  error: "bg-red-50 text-red-700 border-red-200",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export default function WorkstationPapersPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    createClient().auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      fetch(`${BACKEND}/admin/papers`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      })
        .then((r) => r.json())
        .then((data) => setPapers(Array.isArray(data) ? data : []))
        .catch(() => {})
        .finally(() => setLoading(false));
    });
  }, []);

  const filtered = filter === "all" ? papers : papers.filter((p) => p.status === filter);

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Papers</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{papers.length} total</p>
        </div>
        <div className="inline-flex items-center gap-1 border border-border rounded-lg bg-card p-1">
          {["all", "ready", "processing", "error"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-all ${
                filter === s ? "bg-foreground text-background shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-2 animate-pulse">
          {[...Array(6)].map((_, i) => <div key={i} className="h-12 bg-muted rounded-xl" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-2 bg-card border border-border rounded-2xl">
          <p className="text-sm text-muted-foreground">No papers found</p>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr className="text-left text-muted-foreground border-b border-border">
                <th className="py-3 px-4 font-medium">Subject</th>
                <th className="py-3 px-4 font-medium">Year / Paper</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium hidden md:table-cell">Uploaded</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((p) => (
                <tr key={p.id} className="hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-4 font-medium text-foreground truncate max-w-[140px]">{p.subject_name}</td>
                  <td className="py-3 px-4 text-muted-foreground text-xs">
                    {p.year} P{p.paper_number}{p.exam_session ? ` · ${p.exam_session}` : ""}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border capitalize ${STATUS_COLORS[p.status] ?? "bg-muted text-muted-foreground border-border"}`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-muted-foreground text-xs hidden md:table-cell">{formatDate(p.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
