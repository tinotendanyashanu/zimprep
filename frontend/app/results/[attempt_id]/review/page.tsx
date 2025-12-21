"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Accordion } from "@/components/ui/accordion";
import { ArrowLeft, BookOpen, Target } from "lucide-react";
import { MOCK_FEEDBACK_DATA, MOCK_IMPROVEMENT_SIGNALS } from "@/lib/results/types";
import { QuestionFeedbackItem } from "@/components/results/question-feedback-item";

export default function ReviewPage({ params }: { params: Promise<{ attemptId: string }> }) {
  const { attemptId } = use(params);
  
  // mock data fetch
  const questions = MOCK_FEEDBACK_DATA;
  const signals = MOCK_IMPROVEMENT_SIGNALS;

  return (
    <main className="min-h-screen bg-zinc-50 pb-20">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href={`/results/${attemptId}`} className="flex items-center gap-2 text-zinc-600 hover:text-zinc-900 transition-colors">
             <ArrowLeft className="w-4 h-4" />
             <span className="text-sm font-medium">Back to Result Summary</span>
          </Link>
          <div className="text-sm text-zinc-400 font-mono">
             Review Mode
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        
        {/* Intro */}
        <div className="mb-8">
            <h1 className="text-2xl font-bold text-zinc-900">Detailed Feedback</h1>
            <p className="text-zinc-600">Review your answers against the examiner's feedback.</p>
        </div>

        {/* Question List */}
        <div className="mb-12">
            <Accordion type="multiple" className="w-full">
                {questions.map((q) => (
                    <QuestionFeedbackItem key={q.id} data={q} />
                ))}
            </Accordion>
        </div>

        {/* Improvement Guidance */}
        <div className="border-t border-zinc-200 pt-12">
            <h2 className="text-xl font-bold text-zinc-900 mb-6 flex items-center gap-2">
                <Target className="w-5 h-5 text-zinc-900" />
                Examiner's Revision Guidance
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {signals.map((signal, idx) => (
                    <Card key={idx} className="border-zinc-200 shadow-sm bg-white hover:border-zinc-300 transition-colors">
                        <CardHeader className="pb-3 bg-zinc-50/50 border-b border-zinc-50">
                             <div className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-1">
                                {signal.category === 'topic' ? 'Focus Topic' : 'Skill Gap'}
                             </div>
                             <CardTitle className="text-base font-bold text-zinc-900">
                                {signal.title}
                             </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-4">
                            <p className="text-sm text-zinc-600 mb-4 h-10">
                                {signal.description}
                            </p>
                            <Button asChild variant="outline" size="sm" className="w-full justify-between items-center group">
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

      </div>
    </main>
  );
}
