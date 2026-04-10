"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type FlaggedAttempt = {
  id: string;
  student_answer: string | null;
  ai_score: number | null;
  flag_reason: string | null;
  flag_resolved: boolean;
  created_at: string;
  question: { id: string; text: string; marks: number; question_number: string } | null;
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export default function WorkstationFlaggedPage() {
  const [items, setItems] = useState<FlaggedAttempt[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [resolving, setResolving] = useState<string | null>(null);

  useEffect(() => {
    createClient().auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      setToken(session.access_token);
      load(session.access_token);
    });
  }, []);

  function load(t: string) {
    setLoading(true);
    fetch(`${BACKEND}/admin/flagged-attempts?limit=50`, { headers: { Authorization: `Bearer ${t}` } })
      .then((r) => r.json())
      .then((d) => { setItems(d.attempts ?? []); setTotal(d.total ?? 0); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  async function resolve(id: string) {
    if (!token) return;
    setResolving(id);
    await fetch(`${BACKEND}/admin/attempts/${id}/resolve`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });
    setItems((prev) => prev.filter((a) => a.id !== id));
    setTotal((t) => t - 1);
    setResolving(null);
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Flagged attempts</h1>
        <p className="text-sm text-muted-foreground mt-0.5">{total} unresolved</p>
      </div>

      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(5)].map((_, i) => <div key={i} className="h-20 bg-muted rounded-xl" />)}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-2 bg-card border border-border rounded-2xl">
          <svg className="w-10 h-10 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-muted-foreground font-medium">All clear — no flagged attempts</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((attempt) => (
            <div key={attempt.id} className="bg-card border border-border rounded-2xl p-4 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-foreground">
                      Q{attempt.question?.question_number ?? "?"}
                    </span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium border ${
                      attempt.flag_reason === "question_issue"
                        ? "bg-amber-50 text-amber-700 border-amber-200"
                        : "bg-red-50 text-red-700 border-red-200"
                    }`}>
                      {attempt.flag_reason?.replace(/_/g, " ") ?? "flagged"}
                    </span>
                    {attempt.ai_score !== null && (
                      <span className="text-xs text-muted-foreground">{attempt.ai_score} / {attempt.question?.marks ?? "?"} marks</span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {attempt.question?.text ?? "—"}
                  </p>
                </div>
                <button
                  onClick={() => resolve(attempt.id)}
                  disabled={resolving === attempt.id}
                  className="shrink-0 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition disabled:opacity-60"
                >
                  {resolving === attempt.id ? "…" : "Resolve"}
                </button>
              </div>
              {attempt.student_answer && (
                <div className="bg-muted/40 rounded-lg px-3 py-2">
                  <p className="text-[10px] text-muted-foreground uppercase font-medium mb-1">Student answer</p>
                  <p className="text-xs text-foreground line-clamp-3">{attempt.student_answer}</p>
                </div>
              )}
              <p className="text-[10px] text-muted-foreground">{formatDate(attempt.created_at)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
