"use client";

import { useExamStore } from "@/lib/exam/store";
import { ExamTimer } from "./exam-timer";
import { Button } from "@/components/ui/button";
import { Save } from "lucide-react";

export function ExamHeader({ onFinish }: { onFinish?: () => void }) {
    const paper = useExamStore((state) => state.paper);
    const answers = useExamStore((state) => state.answers);
    const answerImages = useExamStore((state) => state.answerImages);
    const totalAnswered = Object.keys(answers).length + Object.keys(answerImages).filter(k => !answers[k]).length;

    if (!paper) return null;

    return (
        <header className="h-16 border-b bg-white flex items-center justify-between px-6 sticky top-0 z-10 w-full shrink-0">
            <div className="flex items-center gap-4">
                <div className="font-bold text-lg text-zinc-900 truncate max-w-sm">
                    {paper.title}
                </div>
                <div className="h-6 w-px bg-zinc-200 hidden md:block" />
                <div className="text-sm text-zinc-500 hidden md:block">
                    {paper.subject} · {paper.level === "Grade7" ? "Grade 7" : paper.level === "O" ? "O Level" : "A Level"} · {paper.year}
                </div>
            </div>

            <div className="flex items-center gap-4">
                <ExamTimer />

                {/* Autosave indicator */}
                <div className="hidden sm:flex items-center gap-1.5 text-xs text-zinc-400">
                    <Save className="w-3 h-3" />
                    <span>Auto-saved ({totalAnswered}/{paper.questions.length})</span>
                </div>

                <Button
                    variant="default"
                    onClick={onFinish}
                    className="bg-zinc-900 hover:bg-zinc-800 text-white shadow-none"
                >
                    Finish Exam
                </Button>
            </div>
        </header>
    );
}
