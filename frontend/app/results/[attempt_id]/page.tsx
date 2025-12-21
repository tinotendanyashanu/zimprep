"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, ArrowRight, ArrowLeft } from "lucide-react";
import { MOCK_RESULT_SUMMARY } from "@/lib/results/types";
import { IBM_Plex_Serif } from "next/font/google";

const serif = IBM_Plex_Serif({ subsets: ["latin"], weight: ["400", "500", "600"] });

export default function ResultsSummaryPage({ params }: { params: Promise<{ attemptId: string }> }) {
  const { attemptId } = use(params);
  
  // In a real app, we would fetch data based on attemptId
  const result = MOCK_RESULT_SUMMARY;

  return (
    <main className="min-h-screen bg-zinc-50">
      {/* Header */}
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
        {/* Title Section */}
        <div className="mb-8 text-center">
          <h1 className={`${serif.className} text-3xl font-semibold text-zinc-900 mb-2`}>
            Examination Result
          </h1>
          <p className="text-zinc-600">
            {result.subject} • {result.paper}
          </p>
          <div className="text-xs text-zinc-400 mt-1 uppercase tracking-wider">
            Attempt ID: {result.attemptId}
          </div>
        </div>

        {/* Primary Score Card */}
        <Card className="mb-8 border-zinc-200 shadow-sm bg-white">
          <CardContent className="pt-8 pb-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 px-4">
              
              {/* Score Display */}
              <div className="text-center md:text-left">
                <div className="text-sm font-medium text-zinc-500 mb-1 uppercase tracking-wide">
                  Total Score
                </div>
                <div className="flex items-baseline gap-2 justify-center md:justify-start">
                  <span className="text-5xl font-bold text-zinc-900 tracking-tight">
                    {result.score}
                  </span>
                  <span className="text-xl text-zinc-400 font-medium">
                    / {result.totalScore}
                  </span>
                </div>
              </div>

              {/* Grade Estimate */}
              <div className="text-center md:text-right border-t md:border-t-0 md:border-l border-zinc-100 pt-6 md:pt-0 md:pl-8 w-full md:w-auto">
                <div className="text-sm font-medium text-zinc-500 mb-1 uppercase tracking-wide">
                  Grade Estimate
                </div>
                <div className="text-4xl font-serif text-zinc-900">
                  {result.gradeEstimate}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {/* Strengths */}
          <Card className="border-zinc-200 shadow-sm">
            <CardHeader className="pb-3 border-b border-zinc-50 bg-zinc-50/50">
              <CardTitle className="text-sm font-medium text-zinc-900 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-zinc-500" />
                Valid Responses
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <ul className="space-y-2">
                {result.strengths.map((strength, i) => (
                  <li key={i} className="text-sm text-zinc-600 flex items-start gap-2">
                    <span className="block w-1 h-1 rounded-full bg-zinc-300 mt-2" />
                    {strength}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Weaknesses */}
          <Card className="border-zinc-200 shadow-sm">
            <CardHeader className="pb-3 border-b border-zinc-50 bg-zinc-50/50">
              <CardTitle className="text-sm font-medium text-zinc-900 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-zinc-500" />
                Areas for Review
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <ul className="space-y-2">
                {result.weaknesses.map((weakness, i) => (
                  <li key={i} className="text-sm text-zinc-600 flex items-start gap-2">
                     <span className="block w-1 h-1 rounded-full bg-zinc-300 mt-2" />
                    {weakness}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Primary Action */}
        <div className="flex justify-center">
            <Button asChild size="lg" className="bg-zinc-900 hover:bg-zinc-800 text-white min-w-[240px]">
                <Link href={`/results/${attemptId}/review`}>
                    Review Detailed Feedback
                    <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
            </Button>
        </div>

      </div>
    </main>
  );
}
