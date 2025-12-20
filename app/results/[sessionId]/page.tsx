"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, AlertCircle, TrendingUp, BookOpen, ArrowRight, ArrowLeft } from "lucide-react";
import { IBM_Plex_Serif } from "next/font/google";

const serif = IBM_Plex_Serif({ subsets: ["latin"], weight: ["400", "500"] });

export default function ResultsPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = use(params);

  return (
    <main className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 text-zinc-600 hover:text-zinc-900">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Dashboard</span>
          </Link>
          <Link href="/" className="flex items-center gap-2">
            <div className="w-6 h-6 bg-[#065F46] rounded-lg flex items-center justify-center">
              <span className="text-xs text-white font-bold">Z</span>
            </div>
            <span className="font-bold text-zinc-900">ZimPrep</span>
          </Link>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-12">
        {/* Results Header */}
        <div className="mb-12 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 rounded-full mb-4">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span className="text-sm font-medium text-emerald-700">Exam Completed</span>
          </div>
          <h1 className="text-4xl font-bold text-zinc-900 mb-2">Your Results</h1>
          <p className="text-zinc-600">Mathematics Paper 2 • Session {sessionId.slice(0, 8)}</p>
        </div>

        {/* Score Card */}
        <Card className="mb-12 border-zinc-200 bg-white shadow-lg">
          <CardContent className="pt-12 pb-12">
            <div className="text-center mb-8">
              <div className="text-7xl font-bold text-[#065F46] mb-2">82%</div>
              <div className="text-xl text-zinc-600">65 / 80 marks</div>
            </div>

            <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto">
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-2">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                </div>
                <div className="text-2xl font-bold text-zinc-900">6</div>
                <div className="text-sm text-zinc-500">Fully Correct</div>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-2">
                  <AlertCircle className="w-6 h-6 text-amber-600" />
                </div>
                <div className="text-2xl font-bold text-zinc-900">2</div>
                <div className="text-sm text-zinc-500">Partial Credit</div>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-2">
                  <XCircle className="w-6 h-6 text-red-600" />
                </div>
                <div className="text-2xl font-bold text-zinc-900">0</div>
                <div className="text-sm text-zinc-500">Incorrect</div>
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-zinc-200 flex items-center justify-center gap-2 text-sm text-zinc-600">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <span>6% improvement from last attempt</span>
            </div>
          </CardContent>
        </Card>

        {/* Question Breakdown */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-zinc-900 mb-6">Question Breakdown</h2>
          <div className="space-y-4">
            {[
              { q: 1, marks: "10/10", status: "full", topic: "Differentiation" },
              { q: 2, marks: "8/10", status: "partial", topic: "Integration" },
              { q: 3, marks: "9/10", status: "full", topic: "Trigonometry" },
              { q: 4, marks: "10/10", status: "full", topic: "Calculus" },
              { q: 5, marks: "10/10", status: "full", topic: "Algebra" },
              { q: 6, marks: "9/10", status: "full", topic: "Geometry" },
              { q: 7, marks: "7/10", status: "partial", topic: "Statistics" },
              { q: 8, marks: "10/10", status: "full", topic: "Probability" },
            ].map((item) => (
              <Card key={item.q} className="border-zinc-200 bg-white hover-lift cursor-pointer">
                <CardContent className="pt-4 pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-zinc-100 flex items-center justify-center">
                        <span className="font-bold text-zinc-900">{item.q}</span>
                      </div>
                      <div>
                        <div className="font-medium text-zinc-900">Question {item.q}</div>
                        <div className="text-sm text-zinc-500">{item.topic}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-lg font-bold text-zinc-900">{item.marks}</div>
                        <div className="text-xs text-zinc-500">marks</div>
                      </div>
                      {item.status === "full" ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-amber-600" />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Detailed Feedback Sample */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-zinc-900 mb-6">Detailed Feedback</h2>
          <Card className="border-zinc-200 bg-white">
            <CardContent className="pt-6">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-zinc-900">Question 2: Integration</h3>
                  <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm font-medium">
                    8/10 marks
                  </span>
                </div>
                <div className={`${serif.className} text-zinc-700 leading-relaxed mb-6`}>
                  <p>Find the definite integral: ∫₀² (3x² + 2x - 1) dx</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="border-l-4 border-emerald-500 pl-4 py-2">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span className="font-medium text-emerald-700">Correct Method (5/5 marks)</span>
                  </div>
                  <p className="text-sm text-zinc-600">
                    You correctly applied the power rule and integrated each term separately.
                  </p>
                </div>

                <div className="border-l-4 border-amber-500 pl-4 py-2">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    <span className="font-medium text-amber-700">Minor Error (3/5 marks)</span>
                  </div>
                  <p className="text-sm text-zinc-600">
                    You made a small calculation error when evaluating at x=2. The final answer should be 10, not 8.
                  </p>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-zinc-200">
                <h4 className="font-medium text-zinc-900 mb-2">Examiner Comment</h4>
                <p className="text-sm text-zinc-600 italic">
                  "Good understanding of integration techniques. Watch your arithmetic when substituting values."
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Next Steps */}
        <div>
          <h2 className="text-2xl font-bold text-zinc-900 mb-6">Recommended Next Steps</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="border-zinc-200 bg-white hover-lift cursor-pointer">
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#065F46]/10 flex items-center justify-center flex-shrink-0">
                    <BookOpen className="w-5 h-5 text-[#065F46]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-zinc-900 mb-2">Practice Integration</h3>
                    <p className="text-sm text-zinc-600 mb-4">
                      Review integration techniques with 5 similar questions
                    </p>
                    <Button asChild size="sm" className="bg-[#065F46] hover:bg-[#055444]">
                      <Link href="/learn/integration">
                        Start Practice
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-zinc-200 bg-white hover-lift cursor-pointer">
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#065F46]/10 flex items-center justify-center flex-shrink-0">
                    <TrendingUp className="w-5 h-5 text-[#065F46]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-zinc-900 mb-2">Try Another Paper</h3>
                    <p className="text-sm text-zinc-600 mb-4">
                      Keep your momentum going with a new exam paper
                    </p>
                    <Button asChild size="sm" variant="outline">
                      <Link href="/dashboard">
                        View Subjects
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}
