"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getSession,
  getQuestionsForPaper,
  autosaveSession,
  submitSession,
  submitAttempt,
  type Session,
  type Question,
  type Attempt,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const EXAM_DURATION = 2 * 60 * 60; // 7200 seconds
const MCQ_OPTIONS = ["A", "B", "C", "D"] as const;

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`;
}

export default function ExamSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();

  const [session, setSession] = useState<Session | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(EXAM_DURATION);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // Practice mode: per-question result
  const [practiceResult, setPracticeResult] = useState<Attempt | null>(null);
  const [practiceSubmitting, setPracticeSubmitting] = useState(false);

  const answersRef = useRef(answers);
  answersRef.current = answers;

  // ── Load session + questions ─────────────────────────────────────────────────
  useEffect(() => {
    async function load() {
      try {
        const s = await getSession(sessionId);
        // If already submitted, go directly to results
        if (s.status !== "active") {
          router.replace(`/exam/${sessionId}/results`);
          return;
        }
        setSession(s);
        const qs = await getQuestionsForPaper(s.paper_id);
        setQuestions(qs);

        // Restore draft answers from localStorage
        const saved = localStorage.getItem(`exam_${sessionId}`);
        if (saved) {
          try {
            setAnswers(JSON.parse(saved));
          } catch {
            // ignore corrupt cache
          }
        }
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [sessionId, router]);

  // ── Countdown timer ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (loading || session?.mode !== "exam") return;
    const interval = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(interval);
          handleSubmitExam(answersRef.current);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, session?.mode]);

  // ── Auto-save to localStorage ────────────────────────────────────────────────
  useEffect(() => {
    if (Object.keys(answers).length > 0) {
      localStorage.setItem(`exam_${sessionId}`, JSON.stringify(answers));
    }
  }, [answers, sessionId]);

  // ── Server autosave every 30s ────────────────────────────────────────────────
  useEffect(() => {
    if (loading) return;
    const interval = setInterval(() => {
      const current = answersRef.current;
      if (Object.keys(current).length > 0) {
        autosaveSession(sessionId, current).catch(() => {
          // silent — localStorage is the safety net
        });
      }
    }, 30_000);
    return () => clearInterval(interval);
  }, [loading, sessionId]);

  // ── Submit exam ──────────────────────────────────────────────────────────────
  const handleSubmitExam = useCallback(
    async (currentAnswers: Record<string, string>) => {
      if (submitting) return;
      setSubmitting(true);
      try {
        await submitSession(sessionId, currentAnswers);
        localStorage.removeItem(`exam_${sessionId}`);
        router.push(`/exam/${sessionId}/results`);
      } catch (e) {
        setError((e as Error).message);
        setSubmitting(false);
      }
    },
    [sessionId, router, submitting],
  );

  // ── Submit practice answer ───────────────────────────────────────────────────
  async function handleSubmitPractice() {
    const q = questions[currentIdx];
    if (!q) return;
    setPracticeSubmitting(true);
    setPracticeResult(null);
    try {
      const result = await submitAttempt(sessionId, q.id, answers[q.id] ?? "");
      setPracticeResult(result);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPracticeSubmitting(false);
    }
  }

  function handleAnswerChange(questionId: string, value: string) {
    setPracticeResult(null);
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  // ── Render guards ────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <p className="text-destructive">{error}</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/dashboard")}>
          Back to dashboard
        </Button>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12 text-center">
        <p className="text-muted-foreground">No questions found for this paper.</p>
      </div>
    );
  }

  const currentQ = questions[currentIdx];
  const isExamMode = session?.mode === "exam";
  const unansweredCount = questions.filter((q) => !answers[q.id]).length;

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top bar */}
      <div className="border-b border-border bg-background sticky top-0 z-40 px-6 py-2 flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          {session?.paper?.subject?.name} · {session?.paper?.year} Paper {session?.paper?.paper_number}
        </span>
        {isExamMode && (
          <span
            className={cn(
              "text-sm font-mono font-semibold",
              timeLeft < 300 ? "text-destructive" : "text-foreground",
            )}
          >
            {formatTime(timeLeft)}
          </span>
        )}
        {isExamMode && (
          <Button
            size="sm"
            onClick={() => setShowConfirm(true)}
            disabled={submitting}
          >
            {submitting ? "Submitting..." : "Submit exam"}
          </Button>
        )}
      </div>

      <div className="flex flex-1">
        {/* Question nav panel */}
        <aside className="hidden sm:block w-16 border-r border-border py-4 px-2">
          <div className="flex flex-col gap-1">
            {questions.map((q, i) => (
              <button
                key={q.id}
                onClick={() => {
                  setCurrentIdx(i);
                  setPracticeResult(null);
                }}
                className={cn(
                  "w-10 h-10 rounded text-xs font-medium mx-auto block",
                  i === currentIdx
                    ? "bg-primary text-primary-foreground"
                    : answers[q.id]
                      ? "bg-green-100 text-green-800"
                      : "bg-muted text-muted-foreground hover:bg-muted/80",
                )}
              >
                {i + 1}
              </button>
            ))}
          </div>
        </aside>

        {/* Question area */}
        <main className="flex-1 max-w-2xl mx-auto px-6 py-8 space-y-6">
          {/* Mobile question nav */}
          <div className="flex sm:hidden flex-wrap gap-1">
            {questions.map((q, i) => (
              <button
                key={q.id}
                onClick={() => {
                  setCurrentIdx(i);
                  setPracticeResult(null);
                }}
                className={cn(
                  "w-8 h-8 rounded text-xs font-medium",
                  i === currentIdx
                    ? "bg-primary text-primary-foreground"
                    : answers[q.id]
                      ? "bg-green-100 text-green-800"
                      : "bg-muted text-muted-foreground",
                )}
              >
                {i + 1}
              </button>
            ))}
          </div>

          {/* Question header */}
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Question {currentQ.question_number}{currentQ.sub_question ? `(${currentQ.sub_question})` : ""}</span>
              <span>·</span>
              <span>{currentQ.marks} mark{currentQ.marks !== 1 ? "s" : ""}</span>
              {currentQ.section && (
                <>
                  <span>·</span>
                  <span>Section {currentQ.section}</span>
                </>
              )}
            </div>
            <p className="text-foreground leading-relaxed">{currentQ.text}</p>
          </div>

          {/* Answer input */}
          {currentQ.question_type === "mcq" ? (
            <div className="space-y-2">
              {MCQ_OPTIONS.map((opt) => (
                <label
                  key={opt}
                  className={cn(
                    "flex items-center gap-3 border rounded-lg p-3 cursor-pointer transition-colors",
                    answers[currentQ.id] === opt
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50",
                  )}
                >
                  <input
                    type="radio"
                    name={`mcq-${currentQ.id}`}
                    value={opt}
                    checked={answers[currentQ.id] === opt}
                    onChange={() => handleAnswerChange(currentQ.id, opt)}
                    className="accent-primary"
                  />
                  <span className="font-medium">{opt}</span>
                  <span className="text-muted-foreground text-sm">Option {opt}</span>
                </label>
              ))}
            </div>
          ) : (
            <textarea
              value={answers[currentQ.id] ?? ""}
              onChange={(e) => handleAnswerChange(currentQ.id, e.target.value)}
              placeholder="Write your answer here..."
              rows={8}
              className="w-full border border-border rounded-lg px-3 py-2 text-sm text-foreground bg-background resize-y focus:outline-none focus:ring-2 focus:ring-ring"
            />
          )}

          {/* Practice mode: submit + feedback */}
          {!isExamMode && (
            <div className="space-y-4">
              <Button
                onClick={handleSubmitPractice}
                disabled={practiceSubmitting || !answers[currentQ.id]}
              >
                {practiceSubmitting ? "Marking..." : "Submit Answer"}
              </Button>

              {practiceResult && (
                <div className="border rounded-lg p-4 space-y-3 bg-muted/30">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-foreground">
                      Score: {practiceResult.ai_score} / {currentQ.marks}
                    </span>
                  </div>
                  {practiceResult.ai_feedback && (
                    <>
                      {practiceResult.ai_feedback.correct_points.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-foreground">Correct points:</p>
                          <ul className="text-sm text-muted-foreground list-disc list-inside">
                            {practiceResult.ai_feedback.correct_points.map((p, i) => (
                              <li key={i}>{p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {practiceResult.ai_feedback.missing_points.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-foreground">Missing points:</p>
                          <ul className="text-sm text-muted-foreground list-disc list-inside">
                            {practiceResult.ai_feedback.missing_points.map((p, i) => (
                              <li key={i}>{p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <p className="text-sm text-foreground">
                        <span className="font-medium">Examiner note: </span>
                        {practiceResult.ai_feedback.examiner_note}
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-2">
            <Button
              variant="outline"
              disabled={currentIdx === 0}
              onClick={() => {
                setCurrentIdx((i) => i - 1);
                setPracticeResult(null);
              }}
            >
              ← Previous
            </Button>
            <Button
              variant="outline"
              disabled={currentIdx === questions.length - 1}
              onClick={() => {
                setCurrentIdx((i) => i + 1);
                setPracticeResult(null);
              }}
            >
              Next →
            </Button>
          </div>
        </main>
      </div>

      {/* Submit confirmation dialog */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-background border border-border rounded-xl p-6 max-w-sm w-full space-y-4">
            <h2 className="text-lg font-semibold text-foreground">Submit exam?</h2>
            <p className="text-sm text-muted-foreground">
              {unansweredCount > 0
                ? `You have ${unansweredCount} unanswered question${unansweredCount !== 1 ? "s" : ""}. This cannot be undone.`
                : "All questions answered. This cannot be undone."}
            </p>
            <div className="flex gap-3">
              <Button
                className="flex-1"
                onClick={() => {
                  setShowConfirm(false);
                  handleSubmitExam(answersRef.current);
                }}
                disabled={submitting}
              >
                {submitting ? "Submitting..." : "Confirm submit"}
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowConfirm(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
