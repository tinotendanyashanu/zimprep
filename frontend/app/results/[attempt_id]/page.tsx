"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, ArrowRight, ArrowLeft, Loader2 } from "lucide-react";
import { MOCK_RESULT_SUMMARY } from "@/lib/results/types";
import { IBM_Plex_Serif } from "next/font/google";
import { ExamPaper, QuestionMarkResult } from "@/lib/exam/types";

const serif = IBM_Plex_Serif({ subsets: ["latin"], weight: ["400", "500", "600"] });

interface StoredResults {
  attempt_id: string;
  paper: ExamPaper;
  results: QuestionMarkResult[] | null;
  total_score: number | null;
  total_max_score: number | null;
  submitted_at: string;
  error?: string;
}

function calcGrade(score: number, max: number): string {
  const pct = max > 0 ? (score / max) * 100 : 0;
  if (pct >= 80) return "A";
  if (pct >= 70) return "B";
  if (pct >= 60) return "C";
  if (pct >= 50) return "D";
  if (pct >= 40) return "E";
  return "U";
}

export default function ResultsSummaryPage({ params }: { params: Promise<{ attempt_id: string }> }) {
  const { attempt_id } = use(params);
  const [stored, setStored] = useState<StoredResults | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem(`zimprep_results_${attempt_id}`);
    if (raw) {
      try {
        setStored(JSON.parse(raw));
      } catch { /* ignore */ }
    }
    setLoading(false);
  }, [attempt_id]);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  // If no real results, fall back to mock
  const isMock = !stored || !stored.results;
  const score = stored?.total_score ?? MOCK_RESULT_SUMMARY.score;
  const maxScore = stored?.total_max_score ?? MOCK_RESULT_SUMMARY.totalScore;
  const grade = calcGrade(score, maxScore);
  const subject = stored?.paper?.subject ?? MOCK_RESULT_SUMMARY.subject;
  const paperTitle = stored?.paper?.title ?? MOCK_RESULT_SUMMARY.paper;

  // Derive strengths / weaknesses from results
  const strengths: string[] = [];
  const weaknesses: string[] = [];
  if (stored?.results) {
    for (const r of stored.results) {
      const pct = r.max_score > 0 ? r.score / r.max_score : 0;
      const qNum = `Q${r.question_id.slice(-2)}`;
      if (pct >= 0.8) strengths.push(qNum);
      else if (pct < 0.5) weaknesses.push(qNum);
    }
  } else {
    strengths.push(...MOCK_RESULT_SUMMARY.strengths);
    weaknesses.push(...MOCK_RESULT_SUMMARY.weaknesses);
  }

  return (
    <main className="min-h-screen bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 text-zinc-600 hover:text-zinc-900 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Dashboard</span>
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-zinc-900 rounded flex items-center justify-center">
              <span className="text-xs text-white font-bold">Z</span>
            </div>
            <span className="font-bold text-zinc-900">ZimPrep</span>
          </div>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-6 py-12">
        {isMock && (
          <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm text-center">
            {stored?.error
              ? `Marking failed: ${stored.error} — showing demo results below.`
              : "No marking results found — showing sample results."}
          </div>
        )}

        <div className="mb-8 text-center">
          <h1 className={`${serif.className} text-3xl font-semibold text-zinc-900 mb-2`}>
            Examination Result
          </h1>
          <p className="text-zinc-600">{subject} • {paperTitle}</p>
          <div className="text-xs text-zinc-400 mt-1 uppercase tracking-wider">Attempt: {attempt_id}</div>
        </div>

        {/* Score Card */}
        <Card className="mb-8 border-zinc-200 shadow-sm bg-white">
          <CardContent className="pt-8 pb-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 px-4">
              <div className="text-center md:text-left">
                <div className="text-sm font-medium text-zinc-500 mb-1 uppercase tracking-wide">Total Score</div>
                <div className="flex items-baseline gap-2 justify-center md:justify-start">
                  <span className="text-5xl font-bold text-zinc-900 tracking-tight">{score}</span>
                  <span className="text-xl text-zinc-400 font-medium">/ {maxScore}</span>
                </div>
              </div>
              <div className="text-center md:text-right border-t md:border-t-0 md:border-l border-zinc-100 pt-6 md:pt-0 md:pl-8 w-full md:w-auto">
                <div className="text-sm font-medium text-zinc-500 mb-1 uppercase tracking-wide">Grade Estimate</div>
                <div className="text-4xl font-serif text-zinc-900">{grade}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          <Card className="border-zinc-200 shadow-sm">
            <CardHeader className="pb-3 border-b border-zinc-50 bg-zinc-50/50">
              <CardTitle className="text-sm font-medium text-zinc-900 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-zinc-500" />
                Strong Areas
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {strengths.length > 0 ? (
                <ul className="space-y-2">
                  {strengths.map((s, i) => (
                    <li key={i} className="text-sm text-zinc-600 flex items-start gap-2">
                      <span className="block w-1 h-1 rounded-full bg-zinc-300 mt-2" />
                      {s}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-zinc-400 italic">Review all questions for improvement.</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-zinc-200 shadow-sm">
            <CardHeader className="pb-3 border-b border-zinc-50 bg-zinc-50/50">
              <CardTitle className="text-sm font-medium text-zinc-900 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-zinc-500" />
                Areas for Review
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {weaknesses.length > 0 ? (
                <ul className="space-y-2">
                  {weaknesses.map((w, i) => (
                    <li key={i} className="text-sm text-zinc-600 flex items-start gap-2">
                      <span className="block w-1 h-1 rounded-full bg-zinc-300 mt-2" />
                      {w}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-zinc-400 italic">No significant weak areas detected.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-center">
          <Button asChild size="lg" className="bg-zinc-900 hover:bg-zinc-800 text-white min-w-[240px]">
            <Link href={`/results/${attempt_id}/review`}>
              Review Detailed Feedback
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
