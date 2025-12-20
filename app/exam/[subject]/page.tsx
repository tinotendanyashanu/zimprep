"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, Clock, FileText, ArrowRight, ArrowLeft } from "lucide-react";

export default function SubjectExamPage({ params }: { params: Promise<{ subject: string }> }) {
  const { subject } = use(params);
  const subjectName = subject.charAt(0).toUpperCase() + subject.slice(1);

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
        {/* Subject Header */}
        <div className="mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#065F46]/10 rounded-full mb-4">
            <BookOpen className="w-4 h-4 text-[#065F46]" />
            <span className="text-sm font-medium text-[#065F46]">{subjectName}</span>
          </div>
          <h1 className="text-4xl font-bold text-zinc-900 mb-2">Choose Exam Paper</h1>
          <p className="text-zinc-600">Select the paper you want to practice</p>
        </div>

        {/* Papers Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Paper 1 */}
          <Card className="border-zinc-200 bg-white hover-lift cursor-pointer group">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-zinc-900 mb-2">Paper 1</h3>
                  <p className="text-sm text-zinc-600 mb-4">Multiple Choice Questions</p>
                  <div className="flex items-center gap-4 text-sm text-zinc-500">
                    <div className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      <span>40 questions</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>1h 30m</span>
                    </div>
                  </div>
                </div>
                <div className="w-16 h-16 rounded-xl bg-[#065F46]/10 flex items-center justify-center group-hover:bg-[#065F46] transition-colors">
                  <span className="text-2xl font-bold text-[#065F46] group-hover:text-white transition-colors">1</span>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-600">Your Progress</span>
                  <span className="font-medium text-zinc-900">3/5 attempts</span>
                </div>
                <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#065F46] rounded-full" style={{ width: "60%" }} />
                </div>
                <div className="flex justify-between text-xs text-zinc-500">
                  <span>Best: 78%</span>
                  <span>Last: 82%</span>
                </div>
              </div>

              <div className="space-y-2">
                <Button asChild className="w-full bg-[#065F46] hover:bg-[#055444]">
                  <Link href={`/exam/${subject}/paper1/timed`}>
                    Start Timed Exam
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </Button>
                <Button asChild variant="outline" className="w-full">
                  <Link href={`/exam/${subject}/paper1/practice`}>
                    Practice Mode
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Paper 2 */}
          <Card className="border-zinc-200 bg-white hover-lift cursor-pointer group">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-zinc-900 mb-2">Paper 2</h3>
                  <p className="text-sm text-zinc-600 mb-4">Structured Questions</p>
                  <div className="flex items-center gap-4 text-sm text-zinc-500">
                    <div className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      <span>8 questions</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>2h 30m</span>
                    </div>
                  </div>
                </div>
                <div className="w-16 h-16 rounded-xl bg-[#065F46]/10 flex items-center justify-center group-hover:bg-[#065F46] transition-colors">
                  <span className="text-2xl font-bold text-[#065F46] group-hover:text-white transition-colors">2</span>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-600">Your Progress</span>
                  <span className="font-medium text-zinc-900">2/5 attempts</span>
                </div>
                <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#065F46] rounded-full" style={{ width: "40%" }} />
                </div>
                <div className="flex justify-between text-xs text-zinc-500">
                  <span>Best: 71%</span>
                  <span>Last: 76%</span>
                </div>
              </div>

              <div className="space-y-2">
                <Button asChild className="w-full bg-[#065F46] hover:bg-[#055444]">
                  <Link href={`/exam/${subject}/paper2/timed`}>
                    Start Timed Exam
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </Button>
                <Button asChild variant="outline" className="w-full">
                  <Link href={`/exam/${subject}/paper2/practice`}>
                    Practice Mode
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Info Box */}
        <Card className="mt-12 border-blue-200 bg-blue-50/50">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h4 className="font-medium text-zinc-900 mb-1">About Exam Modes</h4>
                <p className="text-sm text-zinc-600 leading-relaxed">
                  <strong>Timed Mode:</strong> Simulates real exam conditions with strict time limits.{" "}
                  <strong>Practice Mode:</strong> No time pressure, get instant feedback on each question.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
