"use client";

import { useExamStore } from "@/lib/exam/store";
import { cn } from "@/lib/utils";
import { CheckCircle2, Circle } from "lucide-react";

export function QuestionList() {
    const questions = useExamStore((state) => state.paper?.questions);
    const currentQuestionIndex = useExamStore((state) => state.currentQuestionIndex);
    const answers = useExamStore((state) => state.answers);
    const jumpToQuestion = useExamStore((state) => state.jumpToQuestion);

    if (!questions) return null;

    return (
        <div className="w-64 border-r bg-zinc-50 flex flex-col h-[calc(100vh-4rem)] sticky top-16 hidden md:flex">
            <div className="p-4 border-b bg-white">
                <h3 className="font-semibold text-sm uppercase tracking-wider text-zinc-500">Questions</h3>
                <div className="text-xs text-zinc-400 mt-1">
                    {questions.length} questions total
                </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {questions.map((q, idx) => {
                    const isActive = idx === currentQuestionIndex;
                    const isAnswered = !!answers[q.id];

                    return (
                        <button
                            key={q.id}
                            onClick={() => jumpToQuestion(idx)}
                            className={cn(
                                "w-full text-left px-3 py-2.5 rounded-md text-sm transition-all flex items-center justify-between group",
                                isActive 
                                    ? "bg-zinc-900 text-white shadow-sm" 
                                    : "text-zinc-600 hover:bg-zinc-200/50"
                            )}
                        >
                            <span className={cn("font-medium", isActive ? "text-white" : "text-zinc-700")}>
                                Question {idx + 1}
                            </span>
                            
                            {isAnswered ? (
                                <CheckCircle2 className={cn("w-4 h-4", isActive ? "text-zinc-400" : "text-green-600")} />
                            ) : (
                                <Circle className={cn("w-4 h-4 text-zinc-300", isActive && "text-zinc-600")} />
                            )}
                        </button>
                    );
                })}
            </div>
            
            <div className="p-4 border-t bg-zinc-50 text-xs text-zinc-400 text-center">
                ZimPrep Secure Browser
            </div>
        </div>
    );
}
