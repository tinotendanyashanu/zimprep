"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getResults,
  getSession,
  getQuestionsForPaper,
  flagAttempt,
  type ResultsResponse,
  type Question,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export default function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();

  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [flagged, setFlagged] = useState<Record<string, boolean>>({});
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load questions for total-marks calculation
  useEffect(() => {
    getSession(sessionId)
      .then((s) => getQuestionsForPaper(s.paper_id))
      .then(setQuestions)
      .catch(() => {
        // Non-fatal: total possible marks won't display
      });
  }, [sessionId]);

  // Poll results until all marked
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
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    }

    poll(); // immediate first call
    intervalRef.current = setInterval(poll, 3000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [sessionId]);

  async function handleFlag(attemptId: string) {
    try {
      await flagAttempt(attemptId);
      setFlagged((prev) => ({ ...prev, [attemptId]: true }));
    } catch {
      // Silently ignore — not critical
    }
  }

  const questionMarks: Record<string, number> = {};
  const totalPossible = questions.reduce((sum, q) => {
    questionMarks[q.id] = q.marks;
    return sum + q.marks;
  }, 0);

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

  // Loading / polling state
  if (!results || !results.all_marked) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
        <p className="text-muted-foreground text-sm">
          Marking in progress
          {results
            ? ` — ${results.marked_count} / ${results.total_count} done`
            : "..."}
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Your Results</h1>
        <p className="text-muted-foreground mt-1">
          Marking complete — here is your feedback.
        </p>
      </div>

      {/* Overall score */}
      <Card>
        <CardContent className="py-6 px-6 flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Total score</p>
            <p className="text-3xl font-bold text-foreground mt-1">
              {results.total_score}
              {totalPossible > 0 && (
                <span className="text-xl font-normal text-muted-foreground">
                  {" "}/ {totalPossible}
                </span>
              )}
            </p>
          </div>
          {totalPossible > 0 && (
            <div className="text-right">
              <p className="text-2xl font-semibold text-foreground">
                {Math.round((results.total_score / totalPossible) * 100)}%
              </p>
              <p className="text-sm text-muted-foreground">percentage</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Per-question breakdown */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-foreground">Question breakdown</h2>
        <Accordion type="multiple" className="border rounded-lg divide-y">
          {results.attempts.map((attempt, i) => {
            const qMarks = questionMarks[attempt.question_id] ?? "?";
            const isFlagged = flagged[attempt.id] || attempt.flagged;

            return (
              <AccordionItem key={attempt.id} value={attempt.id} className="border-b-0">
                <AccordionTrigger className="px-4 hover:no-underline">
                  <div className="flex items-center gap-3 flex-1 text-left">
                    <span className="font-medium text-foreground">
                      Q{i + 1}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {attempt.ai_score ?? 0} / {qMarks} marks
                    </span>
                    {isFlagged && (
                      <Badge variant="destructive" className="text-xs">
                        Flagged
                      </Badge>
                    )}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4">
                  <div className="space-y-3 pb-2">
                    {/* Student answer */}
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                        Your answer
                      </p>
                      <p className="text-sm text-foreground bg-muted/30 rounded p-2">
                        {attempt.student_answer || (
                          <span className="italic text-muted-foreground">No answer provided</span>
                        )}
                      </p>
                    </div>

                    {attempt.ai_feedback && (
                      <>
                        {attempt.ai_feedback.correct_points.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                              Correct points
                            </p>
                            <ul className="text-sm text-foreground list-disc list-inside space-y-0.5">
                              {attempt.ai_feedback.correct_points.map((pt, j) => (
                                <li key={j}>{pt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {attempt.ai_feedback.missing_points.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                              Missing points
                            </p>
                            <ul className="text-sm text-foreground list-disc list-inside space-y-0.5">
                              {attempt.ai_feedback.missing_points.map((pt, j) => (
                                <li key={j}>{pt}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {attempt.ai_feedback.examiner_note && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                              Examiner note
                            </p>
                            <p className="text-sm text-foreground">
                              {attempt.ai_feedback.examiner_note}
                            </p>
                          </div>
                        )}
                      </>
                    )}

                    {attempt.ai_references && attempt.ai_references.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                          Study topics
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {attempt.ai_references.map((ref, j) => (
                            <Badge key={j} variant="secondary" className="text-xs">
                              {ref}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {!isFlagged && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleFlag(attempt.id)}
                        className="text-xs"
                      >
                        Flag this marking
                      </Button>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      </div>

      <Button variant="outline" onClick={() => router.push("/dashboard")}>
        Back to dashboard
      </Button>
    </div>
  );
}
