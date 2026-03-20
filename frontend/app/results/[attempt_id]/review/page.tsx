"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Accordion } from "@/components/ui/accordion";
import { ArrowLeft, BookOpen, Target } from "lucide-react";
import { MOCK_FEEDBACK_DATA, MOCK_IMPROVEMENT_SIGNALS, QuestionFeedback } from "@/lib/results/types";
import { QuestionFeedbackItem } from "@/components/results/question-feedback-item";
import { ExamPaper, QuestionMarkResult } from "@/lib/exam/types";

interface StoredResults {
  attempt_id: string;
  paper: ExamPaper;
  results: QuestionMarkResult[] | null;
  answers?: Record<string, string>;
  submitted_at: string;
}

function buildFeedback(
  paper: ExamPaper,
  results: QuestionMarkResult[],
  answers: Record<string, string> = {},
): QuestionFeedback[] {
  const resultMap = new Map(results.map((r) => [r.question_id, r]));
  return paper.questions.map((q) => {
    const r = resultMap.get(q.id);
    const awarded = r?.score ?? 0;
    const total = r?.max_score ?? q.marks;
    const pct = total > 0 ? awarded / total : 0;
    return {
      id: q.id,
      questionNumber: q.questionNumber,
      topic: q.topic ?? "",
      awardedMarks: awarded,
      totalMarks: total,
      studentAnswer: answers[q.id] ?? "",
      examinerFeedback: r?.feedback_summary ?? "No feedback available.",
      correct_points: r?.correct_points ?? [],
      missingPoints: r?.missing_points ?? [],
      study_references: r?.study_references ?? [],
      status: pct >= 1 ? "full" : pct > 0 ? "partial" : "zero",
    };
  });
}

export default function ReviewPage({ params }: { params: Promise<{ attempt_id: string }> }) {
  const { attempt_id } = use(params);
  const [feedbackItems, setFeedbackItems] = useState<QuestionFeedback[]>(MOCK_FEEDBACK_DATA);
  const [isMock, setIsMock] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem(`zimprep_results_${attempt_id}`);
    if (!raw) return;
    try {
      const stored: StoredResults = JSON.parse(raw);
      if (stored.results && stored.paper) {
        setFeedbackItems(buildFeedback(stored.paper, stored.results, stored.answers));
        setIsMock(false);
      }
    } catch { /* ignore */ }
  }, [attempt_id]);

  // Build study signals from feedback
  const studySignals = isMock
    ? MOCK_IMPROVEMENT_SIGNALS
    : feedbackItems
        .filter((f) => f.study_references.length > 0)
        .flatMap((f) =>
          f.study_references.map((ref) => ({
            category: "topic" as const,
            title: f.topic || `Question ${f.questionNumber}`,
            description: ref,
            actionLabel: "Review this topic",
            actionLink: "#",
          }))
        )
        .slice(0, 4);

  return (
    <main className="min-h-screen bg-zinc-50 pb-20">
      <header className="border-b border-zinc-200 bg-white sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href={`/results/${attempt_id}`} className="flex items-center gap-2 text-zinc-600 hover:text-zinc-900 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Result Summary</span>
          </Link>
          <div className="text-sm text-zinc-400 font-mono">
            {isMock ? "Demo Results" : "Your Results"}
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {isMock && (
          <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm text-center">
            Showing sample feedback — submit a real paper to see your actual results.
          </div>
        )}

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-900">Detailed Feedback</h1>
          <p className="text-zinc-600">Score, correct points, missing points, and study references per question.</p>
        </div>

        <div className="mb-12">
          <Accordion type="multiple" className="w-full">
            {feedbackItems.map((q) => (
              <QuestionFeedbackItem key={q.id} data={q} />
            ))}
          </Accordion>
        </div>

        {studySignals.length > 0 && (
          <div className="border-t border-zinc-200 pt-12">
            <h2 className="text-xl font-bold text-zinc-900 mb-6 flex items-center gap-2">
              <Target className="w-5 h-5 text-zinc-900" />
              Revision Guidance
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {studySignals.map((signal, idx) => (
                <Card key={idx} className="border-zinc-200 shadow-sm bg-white hover:border-zinc-300 transition-colors">
                  <CardHeader className="pb-3 bg-zinc-50/50 border-b border-zinc-50">
                    <div className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-1">
                      {signal.category === "topic" ? "Focus Topic" : "Skill Gap"}
                    </div>
                    <CardTitle className="text-base font-bold text-zinc-900">{signal.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <p className="text-sm text-zinc-600 mb-4">{signal.description}</p>
                    <Button asChild variant="outline" size="sm" className="w-full justify-between group">
                      <Link href={signal.actionLink}>
                        {signal.actionLabel}
                        <BookOpen className="w-4 h-4 text-zinc-400 group-hover:text-zinc-600" />
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
