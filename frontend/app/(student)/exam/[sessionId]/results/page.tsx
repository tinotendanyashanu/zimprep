"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getResults, getSession, getQuestionsForPaper, flagAttempt,
  type ResultsResponse, type Question,
} from "@/lib/api";
import { MathText } from "@/components/math-text";
import { cn } from "@/lib/utils";

// ── Helpers ────────────────────────────────────────────────────────────────────

function getGrade(pct: number) {
  if (pct >= 80) return { letter: "A*", color: "text-green-600",  bg: "bg-green-50",  border: "border-green-200", msg: "Outstanding!" };
  if (pct >= 70) return { letter: "A",  color: "text-green-600",  bg: "bg-green-50",  border: "border-green-200", msg: "Excellent work!" };
  if (pct >= 60) return { letter: "B",  color: "text-blue-600",   bg: "bg-blue-50",   border: "border-blue-200",  msg: "Good job!" };
  if (pct >= 50) return { letter: "C",  color: "text-amber-600",  bg: "bg-amber-50",  border: "border-amber-200", msg: "Satisfactory" };
  if (pct >= 40) return { letter: "D",  color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200",msg: "Keep practising" };
  return           { letter: "U",  color: "text-red-600",    bg: "bg-red-50",    border: "border-red-200",   msg: "More work needed" };
}

function ScoreRing({ pct }: { pct: number }) {
  const grade = getGrade(pct);
  const r = 54;
  const circ = 2 * Math.PI * r;
  const filled = (pct / 100) * circ;
  const strokeColor = pct >= 70 ? "#16a34a" : pct >= 50 ? "#2563eb" : pct >= 40 ? "#d97706" : "#dc2626";

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r={r} fill="none" stroke="#e5e7eb" strokeWidth="10" />
          <circle
            cx="60" cy="60" r={r} fill="none"
            stroke={strokeColor} strokeWidth="10"
            strokeDasharray={`${filled} ${circ}`}
            strokeLinecap="round"
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("text-3xl font-black", grade.color)}>{Math.round(pct)}%</span>
          <span className={cn("text-xl font-bold", grade.color)}>{grade.letter}</span>
        </div>
      </div>
      <p className="text-sm font-medium text-muted-foreground">{grade.msg}</p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();

  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [flagged, setFlagged] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    getSession(sessionId)
      .then((s) => getQuestionsForPaper(s.paper_id))
      .then(setQuestions)
      .catch(() => {});
  }, [sessionId]);

  useEffect(() => {
    async function poll() {
      try {
        const data = await getResults(sessionId);
        setResults(data);
        if (data.all_marked && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } catch (e) {
        setError((e as Error).message);
        if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      }
    }
    poll();
    intervalRef.current = setInterval(poll, 3000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [sessionId]);

  async function handleFlag(attemptId: string) {
    try { await flagAttempt(attemptId); setFlagged((p) => ({ ...p, [attemptId]: true })); }
    catch {}
  }

  const questionMarks: Record<string, number> = {};
  const totalPossible = questions.reduce((sum, q) => { questionMarks[q.id] = q.marks; return sum + q.marks; }, 0);

  if (error) return (
    <div className="max-w-md mx-auto px-6 py-16 text-center">
      <p className="text-red-600 mb-4">{error}</p>
      <button onClick={() => router.push("/dashboard")} className="btn-secondary text-sm">
        Back to dashboard
      </button>
    </div>
  );

  if (!results || !results.all_marked) return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] gap-5">
      <div className="relative w-16 h-16">
        <div className="w-16 h-16 rounded-full border-4 border-border border-t-primary animate-spin" />
        <span className="absolute inset-0 flex items-center justify-center text-xl">✏</span>
      </div>
      <div className="text-center">
        <p className="font-semibold text-foreground">Marking your answers…</p>
        <p className="text-sm text-muted-foreground mt-1">
          {results ? `${results.marked_count} of ${results.total_count} marked` : "AI examiner is reviewing your work"}
        </p>
      </div>
      {results && (
        <div className="w-48 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-500"
            style={{ width: `${(results.marked_count / results.total_count) * 100}%` }}
          />
        </div>
      )}
    </div>
  );

  const pct = totalPossible > 0 ? (results.total_score / totalPossible) * 100 : 0;
  const grade = getGrade(pct);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      {/* Score hero */}
      <div className={cn("rounded-2xl border p-6 text-center space-y-4", grade.bg, grade.border)}>
        <ScoreRing pct={pct} />
        <div>
          <p className={cn("text-2xl font-bold", grade.color)}>
            {results.total_score}{totalPossible > 0 ? ` / ${totalPossible}` : ""} marks
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {results.total_count} question{results.total_count !== 1 ? "s" : ""} marked
          </p>
        </div>
      </div>

      {/* Question breakdown */}
      <div className="space-y-2">
        <h2 className="text-base font-semibold text-foreground">Question Breakdown</h2>

        <div className="space-y-2">
          {results.attempts.map((attempt, i) => {
            const qMarks = questionMarks[attempt.question_id] ?? 1;
            const score = attempt.ai_score ?? 0;
            const qPct = (score / qMarks) * 100;
            const isFlagged = flagged[attempt.id] || attempt.flagged;
            const isOpen = expanded === attempt.id;
            const barColor = qPct >= 70 ? "bg-green-500" : qPct >= 40 ? "bg-amber-400" : "bg-red-400";

            return (
              <div key={attempt.id} className="border border-border rounded-xl overflow-hidden bg-card">
                <button
                  onClick={() => setExpanded(isOpen ? null : attempt.id)}
                  className="w-full px-4 py-3 flex items-center gap-3 text-left hover:bg-muted/30 transition"
                >
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0",
                    qPct >= 70 ? "bg-green-100 text-green-700" :
                    qPct >= 40 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
                  )}>
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-sm font-medium text-foreground">Question {i + 1}</span>
                      <div className="flex items-center gap-2">
                        {isFlagged && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-medium">
                            Flagged
                          </span>
                        )}
                        <span className="text-sm font-semibold text-foreground">
                          {score}/{qMarks}
                        </span>
                      </div>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                      <div className={cn("h-full rounded-full transition-all", barColor)} style={{ width: `${qPct}%` }} />
                    </div>
                  </div>
                  <span className="text-muted-foreground text-sm shrink-0">{isOpen ? "▲" : "▼"}</span>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 space-y-3 border-t border-border pt-3">
                    {/* Student's answer */}
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">
                        Your answer
                      </p>
                      {attempt.answer_image_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={attempt.answer_image_url} alt="Your photo answer" className="max-h-48 rounded-lg border border-border object-contain bg-white" />
                      ) : (
                        <p className="text-sm text-foreground bg-muted/40 rounded-lg px-3 py-2">
                          {attempt.student_answer || <span className="italic text-muted-foreground">No answer</span>}
                        </p>
                      )}
                    </div>

                    {attempt.ai_feedback && (
                      <>
                        {attempt.ai_feedback.correct_points.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-1.5">✓ Correct</p>
                            <ul className="text-sm space-y-1 pl-3 border-l-2 border-green-200 text-muted-foreground">
                              {attempt.ai_feedback.correct_points.map((pt, j) => (
                                <li key={j}><MathText text={pt} /></li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {attempt.ai_feedback.missing_points.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-1.5">✗ Missing</p>
                            <ul className="text-sm space-y-1 pl-3 border-l-2 border-red-200 text-muted-foreground">
                              {attempt.ai_feedback.missing_points.map((pt, j) => (
                                <li key={j}><MathText text={pt} /></li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {attempt.ai_feedback.examiner_note && (
                          <div className="bg-muted/40 rounded-lg px-3 py-2 text-sm">
                            <span className="font-medium text-foreground">Examiner: </span>
                            <MathText text={attempt.ai_feedback.examiner_note} className="text-muted-foreground" />
                          </div>
                        )}
                      </>
                    )}

                    {attempt.ai_references && attempt.ai_references.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {attempt.ai_references.map((r, j) => (
                          <span key={j} className="text-xs px-2 py-0.5 rounded-full bg-muted border border-border text-muted-foreground">
                            {r}
                          </span>
                        ))}
                      </div>
                    )}

                    {!isFlagged && (
                      <button
                        onClick={() => handleFlag(attempt.id)}
                        className="text-xs text-muted-foreground hover:text-foreground border border-border rounded-lg px-3 py-1.5 transition hover:bg-muted"
                      >
                        Flag this marking
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="grid grid-cols-2 gap-3">
        <Link
          href="/practice"
          className="flex flex-col items-center gap-1 border border-border rounded-xl p-4 text-center hover:bg-muted/40 transition"
        >
          <span className="text-2xl">✏</span>
          <span className="text-sm font-semibold text-foreground">Practice Weak Topics</span>
          <span className="text-xs text-muted-foreground">Improve your score</span>
        </Link>
        <Link
          href="/exam/select"
          className="flex flex-col items-center gap-1 border border-border rounded-xl p-4 text-center hover:bg-muted/40 transition"
        >
          <span className="text-2xl">📄</span>
          <span className="text-sm font-semibold text-foreground">Try Another Paper</span>
          <span className="text-xs text-muted-foreground">Keep the momentum</span>
        </Link>
      </div>

      <button
        onClick={() => router.push("/dashboard")}
        className="w-full py-2.5 border border-border rounded-xl text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition"
      >
        Back to Dashboard
      </button>
    </div>
  );
}
