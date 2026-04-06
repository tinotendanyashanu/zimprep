"use client";

import { useEffect, useState } from "react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type AiFeedback = {
  correct_points: string[];
  missing_points: string[];
  examiner_note: string;
} | null;

type FlaggedAttempt = {
  id: string;
  student_answer: string | null;
  answer_image_url: string | null;
  ai_score: number | null;
  ai_feedback: AiFeedback;
  marked_at: string | null;
  flagged: boolean;
  flag_reason: "question_issue" | "marking_issue" | null;
  flag_resolved: boolean;
  created_at: string;
  session: { student_id: string; paper_id: string; mode: string } | null;
  question: {
    id: string;
    text: string;
    marks: number;
    question_number: string;
    topic_tags: string[];
  } | null;
};

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function ScoreBadge({ score, max }: { score: number | null; max: number }) {
  if (score === null) return <span className="text-xs text-muted-foreground">—</span>;
  const pct = Math.round((score / 100) * max);
  const color = pct / max >= 0.6 ? "text-green-700 bg-green-50 border-green-200" : "text-red-700 bg-red-50 border-red-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${color}`}>
      {pct}/{max}
    </span>
  );
}

export default function AdminFlaggedPage() {
  const [attempts, setAttempts] = useState<FlaggedAttempt[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  function load() {
    setLoading(true);
    fetch(`${BACKEND}/admin/flagged-attempts?limit=50`)
      .then((r) => r.json())
      .then((data) => {
        setAttempts(data.attempts ?? []);
        setTotal(data.total ?? 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function resolve(id: string) {
    setResolving(id);
    try {
      const res = await fetch(`${BACKEND}/admin/attempts/${id}/resolve`, { method: "PATCH" });
      if (res.ok) {
        setAttempts((prev) => prev.filter((a) => a.id !== id));
        setTotal((t) => t - 1);
        if (expanded === id) setExpanded(null);
      }
    } finally {
      setResolving(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse max-w-4xl">
        <div className="h-8 w-48 bg-muted rounded-lg" />
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 bg-muted rounded-2xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Flagged Attempts</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {total === 0
              ? "All caught up — no unresolved flags"
              : `${total} attempt${total !== 1 ? "s" : ""} flagged for manual review`}
          </p>
        </div>
        <button
          onClick={load}
          className="text-xs text-muted-foreground hover:text-foreground transition flex items-center gap-1.5"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Refresh
        </button>
      </div>

      {attempts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 bg-card border border-border rounded-2xl text-center">
          <div className="w-14 h-14 rounded-2xl bg-green-50 flex items-center justify-center">
            <svg className="w-7 h-7 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-foreground">No flagged attempts</p>
          <p className="text-xs text-muted-foreground">Students flag attempts they believe were marked incorrectly.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {attempts.map((a) => {
            const isOpen = expanded === a.id;
            const q = a.question;
            return (
              <div
                key={a.id}
                className="bg-card border border-border rounded-2xl overflow-hidden transition-all"
              >
                {/* Row */}
                <div className="flex items-start gap-4 p-4">
                  {/* Flag icon */}
                  <div className="w-8 h-8 rounded-lg bg-orange-50 flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5" />
                    </svg>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-foreground line-clamp-2">
                          {q ? `Q${q.question_number}: ${q.text.slice(0, 120)}${q.text.length > 120 ? "…" : ""}` : "Question not found"}
                        </p>
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                          {a.flag_reason === "question_issue" && (
                            <span className="text-[11px] px-2 py-0.5 rounded-full border bg-red-50 text-red-700 border-red-200 font-medium">
                              Question issue
                            </span>
                          )}
                          {a.flag_reason === "marking_issue" && (
                            <span className="text-[11px] px-2 py-0.5 rounded-full border bg-orange-50 text-orange-700 border-orange-200 font-medium">
                              Marking dispute
                            </span>
                          )}
                          {q?.topic_tags?.map((tag) => (
                            <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                              {tag}
                            </span>
                          ))}
                          {q && <ScoreBadge score={a.ai_score} max={q.marks} />}
                          <span className="text-[11px] text-muted-foreground">{relativeTime(a.created_at)}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => setExpanded(isOpen ? null : a.id)}
                          className="text-xs text-muted-foreground hover:text-foreground transition px-2.5 py-1.5 rounded-lg border border-border hover:bg-muted/40"
                        >
                          {isOpen ? "Collapse" : "Review"}
                        </button>
                        <button
                          onClick={() => resolve(a.id)}
                          disabled={resolving === a.id}
                          className="text-xs font-medium text-white bg-primary px-3 py-1.5 rounded-lg hover:opacity-90 transition disabled:opacity-50 flex items-center gap-1.5"
                        >
                          {resolving === a.id ? (
                            <>
                              <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                              </svg>
                              Resolving…
                            </>
                          ) : (
                            <>
                              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                              </svg>
                              Resolve
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded review panel */}
                {isOpen && (
                  <div className="px-4 pb-4 border-t border-border pt-4 space-y-4 bg-muted/20">
                    {/* Full question */}
                    {q && (
                      <div>
                        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Question ({q.marks} marks)</p>
                        <p className="text-sm text-foreground">{q.text}</p>
                      </div>
                    )}

                    {/* Student answer */}
                    <div>
                      <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Student Answer</p>
                      {a.answer_image_url ? (
                        <img
                          src={a.answer_image_url}
                          alt="Student handwritten answer"
                          className="max-w-sm rounded-lg border border-border"
                        />
                      ) : (
                        <p className="text-sm text-foreground bg-background border border-border rounded-lg px-3 py-2.5 whitespace-pre-wrap">
                          {a.student_answer || <span className="text-muted-foreground italic">No answer text</span>}
                        </p>
                      )}
                    </div>

                    {/* AI feedback */}
                    {a.ai_feedback && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {a.ai_feedback.correct_points?.length > 0 && (
                          <div className="bg-green-50 border border-green-200 rounded-xl p-3">
                            <p className="text-[10px] font-semibold text-green-700 uppercase tracking-wider mb-2">Correct Points</p>
                            <ul className="space-y-1">
                              {a.ai_feedback.correct_points.map((pt, i) => (
                                <li key={i} className="text-xs text-green-800 flex items-start gap-1.5">
                                  <svg className="w-3 h-3 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                  </svg>
                                  {pt}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {a.ai_feedback.missing_points?.length > 0 && (
                          <div className="bg-red-50 border border-red-200 rounded-xl p-3">
                            <p className="text-[10px] font-semibold text-red-700 uppercase tracking-wider mb-2">Missing Points</p>
                            <ul className="space-y-1">
                              {a.ai_feedback.missing_points.map((pt, i) => (
                                <li key={i} className="text-xs text-red-800 flex items-start gap-1.5">
                                  <svg className="w-3 h-3 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                  {pt}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {a.ai_feedback.examiner_note && (
                          <div className="sm:col-span-2 bg-muted border border-border rounded-xl p-3">
                            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Examiner Note</p>
                            <p className="text-xs text-foreground">{a.ai_feedback.examiner_note}</p>
                          </div>
                        )}
                      </div>
                    )}

                    <p className="text-[10px] text-muted-foreground font-mono">ID: {a.id}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
