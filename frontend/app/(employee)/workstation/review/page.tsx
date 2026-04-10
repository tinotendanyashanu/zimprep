"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type Question = {
  id: string;
  question_number: string;
  marks: number;
  text: string;
  needs_review: boolean;
  review_reasons: string[] | null;
  hidden: boolean;
  paper: {
    year: number;
    paper_number: number;
    subject: { name: string; level: string };
  } | null;
};

export default function WorkstationReviewPage() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    createClient().auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      setToken(session.access_token);
      load(session.access_token);
    });
  }, []);

  function load(t: string) {
    setLoading(true);
    fetch(`${BACKEND}/admin/questions/review-queue?limit=100`, {
      headers: { Authorization: `Bearer ${t}` },
    })
      .then((r) => r.json())
      .then((d) => { setQuestions(d.questions ?? []); setTotal(d.total ?? 0); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  async function toggleHidden(id: string) {
    if (!token) return;
    await fetch(`${BACKEND}/admin/questions/${id}/hidden`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, hidden: !q.hidden } : q))
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Review queue</h1>
        <p className="text-sm text-muted-foreground mt-0.5">{total} questions need attention</p>
      </div>

      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(5)].map((_, i) => <div key={i} className="h-16 bg-muted rounded-xl" />)}
        </div>
      ) : questions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-2 bg-card border border-border rounded-2xl">
          <svg className="w-10 h-10 text-muted-foreground/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-muted-foreground font-medium">Review queue is empty</p>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="divide-y divide-border">
            {questions.map((q) => (
              <div key={q.id} className="px-4 py-3 flex items-start gap-4">
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-foreground">
                      {q.paper?.subject?.name} · {q.paper?.year} P{q.paper?.paper_number} · Q{q.question_number}
                    </span>
                    <span className="text-xs text-muted-foreground">{q.marks} marks</span>
                    {q.hidden && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">hidden</span>
                    )}
                  </div>
                  {q.review_reasons && q.review_reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {q.review_reasons.map((r) => (
                        <span key={r} className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                          {r.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground line-clamp-2">{q.text}</p>
                </div>
                <button
                  onClick={() => toggleHidden(q.id)}
                  className="shrink-0 text-xs text-muted-foreground hover:text-foreground font-medium hover:underline"
                >
                  {q.hidden ? "Unhide" : "Hide"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
